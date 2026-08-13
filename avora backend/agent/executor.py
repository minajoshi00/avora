"""
============================================================
AVORA Secure Command Executor
============================================================

Real subprocess execution with:
- stdout / stderr / exit code capture
- hard timeouts and process-tree termination
- cooperative cancellation
- working directory preservation
- output truncation and secret redaction
- error classification so the recovery engine can act

Security posture
----------------
- Hard-blocked patterns are rejected before spawning anything.
- shell=False by default: commands are tokenised with shlex so
  chained/piped injection (`a && rm -rf x`) cannot happen unless
  the caller explicitly opts into a shell AND passes the risk gate.
- Output is treated as DATA. `classify_error` never executes
  anything found in output.
"""

from __future__ import annotations

import logging
import os
import re
import shlex
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("AgentExecutor")

MAX_OUTPUT_CHARS = 20000
DEFAULT_TIMEOUT = 120

#: Commands considered read-only inspection.
SAFE_COMMANDS = {
    "git", "python", "py", "pip", "node", "npm", "npx", "yarn", "pnpm",
    "dir", "ls", "type", "cat", "echo", "where", "which", "whoami",
    "hostname", "systeminfo", "tasklist", "ipconfig", "ping", "nslookup",
    "pytest", "eslint", "tsc", "ruff", "flake8", "mypy", "black",
    "vercel", "netlify", "gh", "docker", "cargo", "go", "java", "javac",
    "dotnet", "mvn", "gradle", "code", "explorer", "cmd", "powershell",
}

#: Subcommands that make an otherwise-safe binary mutating.
MUTATING_SUBCOMMANDS = {
    "git": {"push", "commit", "reset", "revert", "rebase", "merge", "clean",
            "checkout", "switch", "restore", "rm", "mv", "stash", "tag",
            "remote", "config", "cherry-pick", "am", "apply"},
    "pip": {"install", "uninstall", "download"},
    "npm": {"install", "i", "uninstall", "remove", "publish", "update", "ci", "link"},
    "yarn": {"add", "remove", "install", "publish", "upgrade"},
    "pnpm": {"add", "remove", "install", "publish", "update"},
    "docker": {"run", "rm", "rmi", "stop", "kill", "build", "push", "prune"},
    "vercel": {"deploy", "rm", "env", "promote", "rollback", "--prod"},
    "netlify": {"deploy", "env:set", "unlink"},
    "gh": {"pr", "release", "repo", "issue", "secret", "workflow"},
}

#: Error signatures -> machine-readable cause used by RecoveryEngine.
ERROR_SIGNATURES: List[tuple] = [
    (r"ModuleNotFoundError: No module named '([\w\.\-]+)'", "missing_python_module"),
    (r"ImportError: cannot import name '([\w]+)'", "python_import_error"),
    (r"Cannot find module '([^']+)'", "missing_node_module"),
    (r"ERR_MODULE_NOT_FOUND", "missing_node_module"),
    (r"(?:command not found|is not recognized as an internal or external command)", "command_not_found"),
    (r"'([\w\.\-]+)' is not recognized", "command_not_found"),
    (r"(?:EACCES|Permission denied|Access is denied)", "permission_denied"),
    (r"(?:ENOENT|No such file or directory|cannot find the path)", "path_not_found"),
    (r"(?:ETIMEDOUT|ECONNREFUSED|ENOTFOUND|getaddrinfo|network is unreachable)", "network_error"),
    (r"npm ERR! code E(?:404|409)", "package_not_found"),
    (r"(?:SyntaxError|Unexpected token)", "syntax_error"),
    (r"TypeError:", "type_error"),
    (r"port \d+ is already in use|EADDRINUSE", "port_in_use"),
    (r"(?:fatal: not a git repository)", "not_a_git_repo"),
    (r"fatal: (?:Authentication failed|could not read Username)", "git_auth_required"),
    (r"(?:merge conflict|CONFLICT \()", "merge_conflict"),
    (r"nothing to commit, working tree clean", "nothing_to_commit"),
    (r"(?:rejected).*(?:non-fast-forward|fetch first)", "git_needs_pull"),
    (r"(?:no space left on device|ENOSPC)", "disk_full"),
    (r"(?:test.*failed|FAILED|AssertionError|\d+ failed)", "test_failure"),
    (r"(?:Build failed|build error|Compilation failed)", "build_failure"),
    (r"(?:401 Unauthorized|403 Forbidden|Invalid token|not authorized)", "auth_required"),
]

_SECRET_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|apikey|token|secret|password|passwd|bearer)"
                r"(\s*[:=]\s*|\s+)([^\s'\"]{8,})"), r"\1\2[REDACTED]"),
    (re.compile(r"(?i)(gsk_|sk-|ghp_|github_pat_|AIza)[A-Za-z0-9_\-]{10,}"), "[REDACTED_KEY]"),
]


def redact(text: str) -> str:
    """Strip secret-looking values from command output before logging."""
    if not text:
        return text
    result = str(text)
    for pattern, replacement in _SECRET_PATTERNS:
        try:
            result = pattern.sub(replacement, result)
        except re.error:
            continue
    return result


def classify_error(stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
    """
    Classify a failure into a machine-readable cause.

    Output is only pattern-matched, never interpreted as instructions.
    """
    combined = f"{stderr or ''}\n{stdout or ''}"
    causes: List[str] = []
    detail: Optional[str] = None

    for pattern, cause in ERROR_SIGNATURES:
        match = re.search(pattern, combined, re.IGNORECASE | re.MULTILINE)
        if match:
            if cause not in causes:
                causes.append(cause)
            if detail is None and match.groups():
                detail = match.group(1)

    transient = any(c in ("network_error",) for c in causes)
    return {
        "causes": causes,
        "primary_cause": causes[0] if causes else ("unknown_error" if exit_code else None),
        "detail": detail,
        "transient": transient,
        "exit_code": exit_code,
    }


@dataclass
class CommandResult:
    """Result of a real command execution."""

    command: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    timed_out: bool = False
    cancelled: bool = False
    cwd: str = ""
    truncated: bool = False
    diagnosis: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and not self.cancelled

    @property
    def output(self) -> str:
        parts = [p for p in (self.stdout.strip(), self.stderr.strip()) if p]
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "ok": self.ok,
            "timed_out": self.timed_out,
            "cancelled": self.cancelled,
            "duration_ms": self.duration_ms,
            "cwd": self.cwd,
            "diagnosis": self.diagnosis,
        }


class CommandExecutor:
    """Runs shell commands safely with cancellation support."""

    def __init__(self):
        self._active: Dict[int, subprocess.Popen] = {}
        self._lock = threading.RLock()
        self._cancel_all = threading.Event()

    # -- Risk assessment -------------------------------------------

    @staticmethod
    def assess(command: str) -> Dict[str, Any]:
        """
        Classify a command without running it.

        Returns dict with keys: risk ('blocked'|'safe'|'moderate'|'high'),
        reason, binary.
        """
        from agent.permissions import check_blocked

        text = (command or "").strip()
        if not text:
            return {"risk": "blocked", "reason": "empty command", "binary": ""}

        blocked = check_blocked(text)
        if blocked:
            return {"risk": "blocked", "reason": blocked, "binary": ""}

        try:
            tokens = shlex.split(text, posix=True)
        except ValueError:
            tokens = text.split()
        if not tokens:
            return {"risk": "blocked", "reason": "unparseable command", "binary": ""}

        binary = Path(tokens[0].strip('"').strip("'")).name.lower()
        binary = re.sub(r"\.(exe|cmd|bat|ps1)$", "", binary)
        rest = {t.lower().strip('"') for t in tokens[1:]}

        # Destructive verbs anywhere -> high risk.
        high_markers = ("del", "rm", "rmdir", "rd", "remove-item", "format",
                        "taskkill", "kill", "shutdown", "restart-computer",
                        "reg", "netsh", "sc", "icacls", "takeown")
        if binary in high_markers:
            return {"risk": "high", "reason": f"'{binary}' can destroy data or change the system",
                    "binary": binary}

        if binary in MUTATING_SUBCOMMANDS and rest & MUTATING_SUBCOMMANDS[binary]:
            hit = sorted(rest & MUTATING_SUBCOMMANDS[binary])[0]
            level = "high" if hit in ("reset", "clean", "push", "rm", "prune", "rmi") else "moderate"
            return {"risk": level, "reason": f"'{binary} {hit}' modifies state", "binary": binary}

        if binary in SAFE_COMMANDS:
            return {"risk": "safe", "reason": "read-only inspection", "binary": binary}

        return {"risk": "moderate", "reason": f"'{binary}' is not a known read-only command",
                "binary": binary}

    # -- Execution -------------------------------------------------

    def run(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        env: Optional[Dict[str, str]] = None,
        shell: bool = False,
        on_output: Optional[Callable[[str], None]] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> CommandResult:
        """
        Execute a command and capture the real result.

        Raises nothing: transport failures become CommandResults.
        """
        started = time.time()
        workdir = self._resolve_cwd(cwd)

        blocked = None
        try:
            from agent.permissions import check_blocked

            blocked = check_blocked(command)
        except Exception:
            pass
        if blocked:
            return CommandResult(
                command=command, exit_code=-1, cwd=workdir,
                stderr=f"Blocked before execution: {blocked}",
                diagnosis={"primary_cause": "blocked", "causes": ["blocked"], "transient": False},
            )

        run_env = os.environ.copy()
        if env:
            run_env.update({str(k): str(v) for k, v in env.items()})
        # Make child tooling non-interactive so we never hang on a prompt.
        run_env.setdefault("PYTHONIOENCODING", "utf-8")
        run_env.setdefault("PYTHONUNBUFFERED", "1")
        run_env.setdefault("CI", "1")
        run_env.setdefault("GIT_TERMINAL_PROMPT", "0")
        run_env.setdefault("NO_COLOR", "1")

        popen_args: Any
        if shell:
            popen_args = command
        else:
            try:
                # Always tokenise in POSIX mode, even on Windows. With
                # posix=False shlex keeps the surrounding quotes attached
                # to the token (['-c', '"import x"']), which silently
                # changes the argument the child receives.
                popen_args = shlex.split(command, posix=True)
            except ValueError as exc:
                return CommandResult(
                    command=command, exit_code=-1, cwd=workdir,
                    stderr=f"Could not parse command: {exc}",
                    diagnosis={"primary_cause": "invalid_command", "causes": [], "transient": False},
                )

        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            # New process group so we can kill the whole tree.
            creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

        try:
            process = subprocess.Popen(
                popen_args,
                cwd=workdir,
                env=run_env,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
            )
        except FileNotFoundError:
            binary = command.split()[0] if command.split() else command
            return CommandResult(
                command=command, exit_code=127, cwd=workdir,
                stderr=f"'{binary}' was not found on this system.",
                duration_ms=int((time.time() - started) * 1000),
                diagnosis={"primary_cause": "command_not_found", "causes": ["command_not_found"],
                           "detail": binary, "transient": False},
            )
        except (OSError, ValueError) as exc:
            return CommandResult(
                command=command, exit_code=-1, cwd=workdir, stderr=str(exc),
                duration_ms=int((time.time() - started) * 1000),
                diagnosis={"primary_cause": "spawn_failed", "causes": [], "transient": False},
            )

        with self._lock:
            self._active[process.pid] = process

        stdout_parts: List[str] = []
        stderr_parts: List[str] = []
        timed_out = False
        cancelled = False

        def _pump(stream, sink: List[str], forward: bool) -> None:
            try:
                for line in iter(stream.readline, ""):
                    sink.append(line)
                    if forward and on_output:
                        try:
                            on_output(redact(line.rstrip()))
                        except Exception:
                            pass
            except (ValueError, OSError):
                pass
            finally:
                try:
                    stream.close()
                except Exception:
                    pass

        threads = [
            threading.Thread(target=_pump, args=(process.stdout, stdout_parts, True), daemon=True),
            threading.Thread(target=_pump, args=(process.stderr, stderr_parts, False), daemon=True),
        ]
        for thread in threads:
            thread.start()

        deadline = started + max(1, timeout)
        try:
            while True:
                try:
                    process.wait(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    pass

                if time.time() > deadline:
                    timed_out = True
                    self._terminate(process)
                    break
                if (cancel_event and cancel_event.is_set()) or self._cancel_all.is_set():
                    cancelled = True
                    self._terminate(process)
                    break
        finally:
            for thread in threads:
                thread.join(timeout=2)
            with self._lock:
                self._active.pop(process.pid, None)

        stdout = redact("".join(stdout_parts))
        stderr = redact("".join(stderr_parts))
        truncated = False
        if len(stdout) > MAX_OUTPUT_CHARS:
            stdout = stdout[:MAX_OUTPUT_CHARS] + "\n...[output truncated]"
            truncated = True
        if len(stderr) > MAX_OUTPUT_CHARS:
            stderr = stderr[:MAX_OUTPUT_CHARS] + "\n...[output truncated]"
            truncated = True

        exit_code = process.returncode if process.returncode is not None else -1
        if timed_out:
            exit_code = -9
            stderr = (stderr + f"\n[Timed out after {timeout}s and was terminated]").strip()
        if cancelled:
            exit_code = -2
            stderr = (stderr + "\n[Cancelled by user]").strip()

        result = CommandResult(
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=int((time.time() - started) * 1000),
            timed_out=timed_out,
            cancelled=cancelled,
            cwd=workdir,
            truncated=truncated,
        )
        if not result.ok:
            result.diagnosis = classify_error(stdout, stderr, exit_code)
            if timed_out:
                result.diagnosis["primary_cause"] = "timeout"
                result.diagnosis["transient"] = True
            if cancelled:
                result.diagnosis["primary_cause"] = "cancelled"
        return result

    # -- Process control -------------------------------------------

    def _terminate(self, process: subprocess.Popen) -> None:
        """Kill a process and its children."""
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            else:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        except Exception as exc:
            logger.debug("Terminate fallback for %s: %s", process.pid, exc)
        try:
            if process.poll() is None:
                process.kill()
        except Exception:
            pass

    def cancel_all(self) -> int:
        """Kill every running command. Backs the UI Stop button."""
        self._cancel_all.set()
        with self._lock:
            processes = list(self._active.values())
        for process in processes:
            self._terminate(process)
        count = len(processes)
        self._cancel_all.clear()
        return count

    def active_count(self) -> int:
        with self._lock:
            return len(self._active)

    def _resolve_cwd(self, cwd: Optional[str]) -> str:
        candidates = [cwd] if cwd else []
        candidates.append(os.getcwd())
        for candidate in candidates:
            try:
                if candidate and Path(candidate).is_dir():
                    return str(Path(candidate).resolve())
            except (OSError, ValueError):
                continue
        return str(Path.home())


_executor: Optional[CommandExecutor] = None


def get_executor() -> CommandExecutor:
    global _executor
    if _executor is None:
        _executor = CommandExecutor()
    return _executor


__all__ = [
    "CommandExecutor",
    "CommandResult",
    "get_executor",
    "classify_error",
    "redact",
    "SAFE_COMMANDS",
]
