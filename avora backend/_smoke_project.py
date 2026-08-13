import json
from agent.project import detect_project, git_info, diagnose_deployment, find_projects

p = detect_project(".")
print("=== backend detect ===")
print(json.dumps(p.to_dict(), indent=2)[:1400])

print("\n=== frontend detect ===")
f = detect_project("../avora frontend")
d = f.to_dict()
print("kind:", d["kind"], "| pm:", d["package_manager"])
print("frameworks:", d["frameworks"])
print("build:", d["build_command"], "| dev:", d["dev_command"], "| test:", d["test_command"])
print("deploy:", d["deployment_targets"], "| config:", d["config_files"][:8])

print("\n=== git ===")
g = git_info(".")
print({k: g[k] for k in ("is_repo", "branch", "change_count", "clean", "conflicted") if k in g})
print("commits:", g.get("recent_commits", [])[:3])

print("\n=== find projects 'avora' ===")
for proj in find_projects("avora", max_depth=2, limit=8):
    print(" -", proj.path, "|", proj.kind, proj.frameworks[:4])
