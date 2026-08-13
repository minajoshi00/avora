"""
============================================================
AVORA Project Intelligence
============================================================

Finds and understands real projects on the user's machine so
AVORA never has to ask "where is your project?".

Provides:
- find_projects()      : discover projects in common dev locations
- detect_project()     : identify framework / package manager / scripts
- git_info()           : real Git state via the executor
- diagnose_deployment(): inspect Vercel / Netlify / Render config

Everything here is read-only inspection.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AgentProject")

#: Directories never worth scanning.
IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "out", "target", "bin", "obj",
    ".cache", ".pytest_cache", ".mypy_cache", "vendor", "coverage",
    ".idea", ".vscode", "AppData", "Windows", "Program Files",
    "Program Files (x86)", "$Recycle.Bin", "System Volume Information",
}

#: Marker file -> (framework, package manager)
PROJECT_MARKERS = {
    "package.json": "node",
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "setup.py": "python",
    "Pipfile": "python",
    "pom.xml": "java-maven",
    "build.gradle": "java-gradle",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "composer.json": "php",
    "Gemfile": "ruby",
    "CMakeLists.txt": "cmake",
    "Makefile": "make",
    "*.csproj": "dotnet",
    "*.sln": "dotnet",
}


@dataclass
class ProjectInfo:
    """Everything AVORA knows about a project directory."""

    path: str
    name: str = ""
    kind: str = "unknown"
    frameworks: List[str] = field(default_factory=list)
    package_manager: Optional[str] = None
    scripts: Dict[str, str] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)
    has_git: bool = False
    has_tests: bool = False
    test_command: Optional[str] = None
    build_command: Optional[str] = None
    dev_command: Optional[str] = None
    install_command: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    deployment_targets: List[str] = field(default_factory=list)
    env_files: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "kind": self.kind,
            "frameworks": self.frameworks,
            "package_manager": self.package_manager,
            "scripts": self.scripts,
            "has_git": self.has_git,
            "has_tests": self.has_tests,
            "test_command": self.test_command,
            "build_command": self.build_command,
            "dev_command": self.dev_command,
            "install_command": self.install_command,
            "deployment_targets": self.deployment_targets,
            "config_files": self.config_files,
            "env_files": self.env_files,
            "entry_points": self.entry_points,
            "notes": self.notes,
        }

    def summary(self) -> str:
        bits = [f"{self.name} ({self.kind}"]
        if self.frameworks:
            bits.append(", ".join(self.frameworks))
        bits.append(")")
        text = f"{bits[0]}" + (f" - {bits[1]}" if len(bits) > 2 else "") + ")"
        extras = []
        if self.has_git:
            extras.append("git")
        if self.has_tests:
            extras.append("tests")
        if self.deployment_targets:
            extras.append("deploy:" + "/".join(self.deployment_targets))
        if extras:
            text += " [" + ", ".join(extras) + "]"
        return text


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def search_roots() -> List[Path]:
    """Common locations for user projects. No hardcoded machine paths."""
    home = Path.home()
    candidates = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "source" / "repos",
        home / "Projects",
        home / "projects",
        home / "dev",
        home / "Dev",
        home / "code",
        home / "Code",
        home / "repos",
        home / "git",
        home / "workspace",
        home / "OneDrive" / "Desktop",
        home / "OneDrive" / "Documents",
        home,
    ]
    roots: List[Path] = []
    seen = set()
    for candidate in candidates:
        try:
            if candidate.is_dir():
                resolved = candidate.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    roots.append(candidate)
        except (OSError, ValueError):
            continue
    return roots


def _is_project_dir(path: Path) -> Optional[str]:
    """Return the project kind if this directory looks like a project root."""
    try:
        entries = {e.name for e in path.iterdir()}
    except (OSError, PermissionError):
        return None

    for marker, kind in PROJECT_MARKERS.items():
        if marker.startswith("*"):
            suffix = marker[1:]
            if any(name.endswith(suffix) for name in entries):
                return kind
        elif marker in entries:
            return kind
    if ".git" in entries:
        return "git"
    return None


def find_projects(
    query: Optional[str] = None,
    max_depth: int = 3,
    limit: int = 40,
) -> List[ProjectInfo]:
    """
    Discover projects on this machine, optionally filtered by name.

    Breadth-first, depth-limited, and ignores heavy directories so it
    stays fast enough to run inline during a conversation.
    """
    found: List[ProjectInfo] = []
    seen: set = set()
    needle = (query or "").strip().lower()

    for root in search_roots():
        queue: List[tuple] = [(root, 0)]
        while queue and len(found) < limit:
            current, depth = queue.pop(0)
            if depth > max_depth:
                continue
            try:
                resolved = current.resolve()
            except (OSError, ValueError):
                continue
            if resolved in seen:
                continue
            seen.add(resolved)

            if current.name in IGNORE_DIRS or current.name.startswith("."):
                if depth > 0:
                    continue

            kind = _is_project_dir(current)
            if kind:
                if not needle or needle in current.name.lower():
                    try:
                        found.append(detect_project(str(current), quick=True))
                    except Exception as exc:
                        logger.debug("detect failed for %s: %s", current, exc)
                # Don't descend into a detected project root.
                continue

            try:
                for child in current.iterdir():
                    if child.is_dir() and child.name not in IGNORE_DIRS:
                        queue.append((child, depth + 1))
            except (OSError, PermissionError):
                continue

    # Prefer name matches, then shallower paths.
    found.sort(key=lambda p: (0 if needle and needle == p.name.lower() else 1, len(p.path)))
    return found[:limit]


def detect_project(path: str, quick: bool = False) -> ProjectInfo:
    """Inspect a directory and identify what kind of project it is."""
    root = Path(path).expanduser()
    if not root.is_dir():
        root = root.parent
    root = root.resolve()

    info = ProjectInfo(path=str(root), name=root.name)
    try:
        entries = {e.name: e for e in root.iterdir()}
    except (OSError, PermissionError) as exc:
        info.notes.append(f"Could not read directory: {exc}")
        return info

    info.has_git = ".git" in entries

    # ---- Node / JS ecosystem ----
    pkg_path = entries.get("package.json")
    if pkg_path is not None:
        info.kind = "node"
        pkg = _read_json(Path(pkg_path)) or {}
        info.name = pkg.get("name") or info.name
        info.scripts = {k: str(v) for k, v in (pkg.get("scripts") or {}).items()}
        deps = dict(pkg.get("dependencies") or {})
        deps.update(pkg.get("devDependencies") or {})
        info.dependencies = sorted(deps.keys())

        if "pnpm-lock.yaml" in entries:
            info.package_manager = "pnpm"
        elif "yarn.lock" in entries:
            info.package_manager = "yarn"
        elif "bun.lockb" in entries:
            info.package_manager = "bun"
        else:
            info.package_manager = "npm"

        framework_map = {
            "next": "next.js", "react": "react", "vue": "vue", "nuxt": "nuxt",
            "svelte": "svelte", "@angular/core": "angular", "vite": "vite",
            "express": "express", "nestjs": "nestjs", "@nestjs/core": "nestjs",
            "astro": "astro", "remix": "remix", "gatsby": "gatsby",
            "electron": "electron", "typescript": "typescript",
            "tailwindcss": "tailwind", "jest": "jest", "vitest": "vitest",
        }
        for dep, label in framework_map.items():
            if dep in deps:
                info.frameworks.append(label)

        run = info.package_manager
        exec_prefix = f"{run} run " if run != "npm" else "npm run "
        if "test" in info.scripts:
            info.test_command = f"{exec_prefix}test"
            info.has_tests = True
        if "build" in info.scripts:
            info.build_command = f"{exec_prefix}build"
        for dev_key in ("dev", "start", "serve"):
            if dev_key in info.scripts:
                info.dev_command = f"{exec_prefix}{dev_key}"
                break
        info.install_command = f"{run} install"

    # ---- Python ecosystem ----
    py_markers = {"requirements.txt", "pyproject.toml", "setup.py", "Pipfile"}
    if py_markers & set(entries):
        info.kind = "python" if info.kind in ("unknown", "git") else f"{info.kind}+python"
        info.frameworks.append("python")

        if "requirements.txt" in entries:
            info.install_command = "pip install -r requirements.txt"
            try:
                text = Path(entries["requirements.txt"]).read_text(
                    encoding="utf-8", errors="replace"
                )
                for line in text.splitlines():
                    name = re.split(r"[<>=!\[;#]", line.strip())[0].strip()
                    if name and not name.startswith("#"):
                        info.dependencies.append(name)
            except Exception:
                pass
        elif "pyproject.toml" in entries:
            info.install_command = "pip install -e ."

        lowered = {d.lower() for d in info.dependencies}
        for dep, label in {
            "django": "django", "flask": "flask", "fastapi": "fastapi",
            "pyside6": "pyside6", "pyqt5": "pyqt5", "streamlit": "streamlit",
            "pytest": "pytest", "torch": "pytorch", "tensorflow": "tensorflow",
        }.items():
            if dep in lowered:
                info.frameworks.append(label)

        if "pytest" in lowered or "tests" in entries or "test" in entries:
            info.has_tests = True
            info.test_command = "python -m pytest -q"

        for entry_name in ("main.py", "app.py", "manage.py", "run.py", "__main__.py"):
            if entry_name in entries:
                info.entry_points.append(entry_name)

    # ---- Other ecosystems ----
    other = {
        "Cargo.toml": ("rust", "cargo build", "cargo test"),
        "go.mod": ("go", "go build ./...", "go test ./..."),
        "pom.xml": ("java-maven", "mvn -B package", "mvn -B test"),
        "build.gradle": ("java-gradle", "gradle build", "gradle test"),
        "composer.json": ("php", None, None),
        "Gemfile": ("ruby", None, None),
    }
    for marker, (kind, build, test) in other.items():
        if marker in entries:
            if info.kind in ("unknown", "git"):
                info.kind = kind
            info.frameworks.append(kind)
            info.build_command = info.build_command or build
            if test:
                info.test_command = info.test_command or test
                info.has_tests = True

    if info.kind in ("unknown", "git") and any(
        n.endswith((".html", ".css")) for n in entries
    ):
        info.kind = "static-web"
        info.frameworks.append("html/css")

    # ---- Config, env, deployment ----
    known_config = [
        "vercel.json", "netlify.toml", "render.yaml", "Dockerfile",
        "docker-compose.yml", "tsconfig.json", "vite.config.js",
        "vite.config.ts", "next.config.js", "next.config.mjs",
        "next.config.ts", "tailwind.config.js", "webpack.config.js",
        ".eslintrc.json", "eslint.config.js", "pytest.ini", "tox.ini",
        "Procfile", "app.yaml", "fly.toml", ".github",
    ]
    for name in known_config:
        if name in entries:
            info.config_files.append(name)

    for name in entries:
        if name == ".env" or name.startswith(".env."):
            info.env_files.append(name)

    if "vercel.json" in entries or ".vercel" in entries:
        info.deployment_targets.append("vercel")
    if "netlify.toml" in entries:
        info.deployment_targets.append("netlify")
    if "render.yaml" in entries:
        info.deployment_targets.append("render")
    if "Dockerfile" in entries:
        info.deployment_targets.append("docker")
    if "fly.toml" in entries:
        info.deployment_targets.append("fly.io")
    if "next.js" in info.frameworks and not info.deployment_targets:
        info.deployment_targets.append("vercel")

    info.frameworks = sorted(set(info.frameworks))
    info.dependencies = sorted(set(info.dependencies))[:200]
    return info


def git_info(path: str) -> Dict[str, Any]:
    """Collect real Git state for a repository (read-only)."""
    from agent.executor import get_executor

    executor = get_executor()
    root = str(Path(path).expanduser().resolve())
    result: Dict[str, Any] = {"path": root, "is_repo": False}

    check = executor.run("git rev-parse --show-toplevel", cwd=root, timeout=15)
    if not check.ok:
        result["error"] = check.output or "Not a Git repository"
        return result

    result["is_repo"] = True
    result["root"] = check.stdout.strip().splitlines()[0] if check.stdout.strip() else root
    repo = result["root"]

    def run(cmd: str) -> str:
        res = executor.run(cmd, cwd=repo, timeout=20)
        return res.stdout.strip() if res.ok else ""

    result["branch"] = run("git rev-parse --abbrev-ref HEAD")
    result["remote"] = run("git remote get-url origin")

    status = executor.run("git status --porcelain=v1", cwd=repo, timeout=25)
    changes: List[Dict[str, str]] = []
    staged = unstaged = untracked = conflicted = 0
    if status.ok:
        for line in status.stdout.splitlines():
            if len(line) < 3:
                continue
            code, filename = line[:2], line[3:]
            changes.append({"status": code.strip(), "file": filename})
            if code == "??":
                untracked += 1
            elif "U" in code or code in ("AA", "DD"):
                conflicted += 1
            else:
                if code[0] not in (" ", "?"):
                    staged += 1
                if code[1] not in (" ", "?"):
                    unstaged += 1

    result["changes"] = changes[:100]
    result["change_count"] = len(changes)
    result["staged"] = staged
    result["unstaged"] = unstaged
    result["untracked"] = untracked
    result["conflicted"] = conflicted
    result["clean"] = not changes

    log = run("git log --oneline -10")
    result["recent_commits"] = log.splitlines() if log else []

    upstream = run("git rev-list --left-right --count HEAD...@{u}")
    if upstream:
        parts = upstream.split()
        if len(parts) == 2:
            result["ahead"], result["behind"] = int(parts[0]), int(parts[1])
    else:
        result["upstream_tracking"] = False

    return result


def diagnose_deployment(path: str, platform: Optional[str] = None) -> Dict[str, Any]:
    """
    Inspect local deployment configuration and report concrete findings.

    This only reads local files. It never claims dashboard access;
    anything requiring the provider API is listed under
    `requires_user_action`.
    """
    root = Path(path).expanduser().resolve()
    project = detect_project(str(root))
    findings: List[str] = []
    problems: List[Dict[str, str]] = []
    requires_user: List[str] = []

    targets = [platform] if platform else (project.deployment_targets or ["vercel"])
    report: Dict[str, Any] = {
        "project": project.to_dict(),
        "platforms": targets,
        "findings": findings,
        "problems": problems,
        "requires_user_action": requires_user,
    }

    # -- Generic build sanity --------------------------------------
    if project.kind == "node":
        if not project.build_command:
            problems.append({
                "issue": "No build script found in package.json",
                "fix": "Add a \"build\" script so the platform knows how to build the project.",
            })
        else:
            findings.append(f"Build command: {project.build_command}")

        out_dirs = {
            "next.js": ".next", "vite": "dist", "react": "build",
            "astro": "dist", "nuxt": ".output", "svelte": "build",
        }
        for framework, out in out_dirs.items():
            if framework in project.frameworks:
                findings.append(f"Detected {framework}; expected output directory '{out}'")
                break

    if project.env_files:
        findings.append(
            f"Local env file(s) present: {', '.join(project.env_files)} "
            "(these are NOT uploaded automatically)"
        )
        requires_user.append(
            "Confirm the environment variables from your local .env are also set in the "
            "hosting dashboard - I can read the variable NAMES locally but will not send values."
        )

    # -- Vercel ----------------------------------------------------
    if "vercel" in targets:
        vercel_json = root / "vercel.json"
        if vercel_json.exists():
            config = _read_json(vercel_json)
            if config is None:
                problems.append({
                    "issue": "vercel.json exists but is not valid JSON",
                    "fix": "Fix the JSON syntax; Vercel ignores/errors on malformed config.",
                })
            else:
                findings.append("vercel.json is valid JSON")
                for key in ("buildCommand", "outputDirectory", "framework", "rootDirectory"):
                    if key in config:
                        findings.append(f"vercel.json {key} = {config[key]!r}")
        else:
            findings.append("No vercel.json (Vercel will auto-detect the framework)")

        linked = root / ".vercel" / "project.json"
        if linked.exists():
            data = _read_json(linked) or {}
            if data.get("projectId"):
                findings.append("Project is linked to a Vercel project locally (.vercel present)")
        else:
            requires_user.append(
                "This folder is not linked to a Vercel project locally. Running "
                "`vercel link` (needs your Vercel login) would let me inspect and deploy it."
            )

        # A very common real cause: monorepo root mismatch.
        if project.kind == "node":
            subdirs = [
                d.name for d in root.iterdir()
                if d.is_dir() and (d / "package.json").exists() and d.name not in IGNORE_DIRS
            ] if root.is_dir() else []
            if subdirs and not (root / "package.json").exists():
                problems.append({
                    "issue": f"No package.json at the repo root, but found one in: {', '.join(subdirs)}",
                    "fix": "Set the Vercel 'Root Directory' to the subfolder that contains package.json.",
                })

    # -- Netlify ---------------------------------------------------
    if "netlify" in targets:
        toml_path = root / "netlify.toml"
        if toml_path.exists():
            try:
                text = toml_path.read_text(encoding="utf-8", errors="replace")
                findings.append("netlify.toml found")
                if "publish" not in text:
                    problems.append({
                        "issue": "netlify.toml has no 'publish' directory",
                        "fix": "Add publish = \"dist\" (or your build output folder).",
                    })
                if "command" not in text:
                    problems.append({
                        "issue": "netlify.toml has no build 'command'",
                        "fix": "Add command = \"npm run build\".",
                    })
            except Exception as exc:
                problems.append({"issue": f"Could not read netlify.toml: {exc}", "fix": ""})
        else:
            findings.append("No netlify.toml (build settings come from the dashboard)")
            requires_user.append(
                "Netlify build settings live in the dashboard; I can't read them without your login."
            )

    # -- Render ----------------------------------------------------
    if "render" in targets:
        render_yaml = root / "render.yaml"
        if render_yaml.exists():
            findings.append("render.yaml found")
            try:
                text = render_yaml.read_text(encoding="utf-8", errors="replace")
                if "startCommand" not in text:
                    problems.append({
                        "issue": "render.yaml has no startCommand",
                        "fix": "Add a startCommand so Render knows how to run the service.",
                    })
            except Exception:
                pass
        else:
            findings.append("No render.yaml (settings come from the Render dashboard)")

    # -- Git state affects what gets deployed ----------------------
    if project.has_git:
        git = git_info(str(root))
        report["git"] = git
        if git.get("is_repo"):
            if git.get("change_count"):
                problems.append({
                    "issue": f"{git['change_count']} uncommitted change(s) locally",
                    "fix": "Deployments build from the pushed commit, so local-only changes "
                           "won't appear in production until committed and pushed.",
                })
            if git.get("ahead"):
                problems.append({
                    "issue": f"{git['ahead']} commit(s) not pushed to the remote",
                    "fix": "Push them so the hosting platform can build the latest code.",
                })
            findings.append(f"Git branch: {git.get('branch')}")

    return report


__all__ = [
    "ProjectInfo",
    "find_projects",
    "detect_project",
    "git_info",
    "diagnose_deployment",
    "search_roots",
]
