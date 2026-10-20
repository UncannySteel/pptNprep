#!/usr/bin/env python3
"""Point this machine's Claude Code sessions at its copy of the ABOT code directory.

Run once per machine from the pptNprep folder (and again if the code dir moves):

    python .claude/hooks/setup_machine.py "<path to the code dir>" [more paths]
    python .claude/hooks/setup_machine.py --show

Merges the machine-specific half of the read-only guard into
.claude/settings.local.json, which is git-ignored:

  env.ABOT_CODE_DIR                  protected path(s), read by guard.py and pyguard
  env.PYTHONPATH                     .claude/pyguard, so Python refuses writes there at runtime
  env.PYTHONDONTWRITEBYTECODE        no __pycache__ litter when a session imports the code
  permissions.additionalDirectories  sessions can read the code dir without prompts
  permissions.deny                   Edit(...) rules, a second hard stop for the file tools

Start a new Claude Code session afterwards so the settings load.
"""
import json
import os
import re
import sys

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOCAL = os.path.join(PROJECT, ".claude", "settings.local.json")
PYGUARD = os.path.join(PROJECT, ".claude", "pyguard")


def edit_rule(path: str) -> str:
    """Absolute-path permission rule: C:\\a\\b -> Edit(//c/a/b/**), /home/a -> Edit(//home/a/**)."""
    p = os.path.abspath(path)
    drive, rest = os.path.splitdrive(p)
    if re.match(r"^[A-Za-z]:$", drive):
        p = "/" + drive[0].lower() + rest
    p = p.replace("\\", "/").rstrip("/")
    return f"Edit(/{p}/**)"


def load() -> dict:
    try:
        with open(LOCAL, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def show(settings: dict) -> None:
    env = settings.get("env", {})
    print("settings file :", LOCAL)
    print("ABOT_CODE_DIR :", env.get("ABOT_CODE_DIR", "(not set)"))
    print("PYTHONPATH    :", env.get("PYTHONPATH", "(not set)"))
    print("deny rules    :", [r for r in settings.get("permissions", {}).get("deny", []) if r.startswith("Edit(")])


def main(argv: list) -> int:
    settings = load()
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 1
    if argv[0] == "--show":
        show(settings)
        return 0

    paths = [os.path.abspath(os.path.expanduser(a)) for a in argv]
    for p in paths:
        if not os.path.isdir(p):
            print(f"error: not a directory: {p}", file=sys.stderr)
            return 1
        has_code = os.path.isdir(os.path.join(p, "darwinV2")) or any(
            os.path.isdir(os.path.join(p, s, "darwinV2")) for s in os.listdir(p)
        )
        if not has_code:
            print(f"warning: no darwinV2/ found in or directly under {p}; is this the code dir?")

    env = settings.setdefault("env", {})
    perms = settings.setdefault("permissions", {})
    old = [p for p in env.get("ABOT_CODE_DIR", "").split(os.pathsep) if p]
    old_rules = {edit_rule(p) for p in old}

    env["ABOT_CODE_DIR"] = os.pathsep.join(paths)
    env["PYTHONPATH"] = PYGUARD
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    dirs = [d for d in perms.get("additionalDirectories", []) if d not in old]
    perms["additionalDirectories"] = dirs + [p for p in paths if p not in dirs]
    deny = [r for r in perms.get("deny", []) if r not in old_rules]
    perms["deny"] = deny + [r for r in map(edit_rule, paths) if r not in deny]

    os.makedirs(os.path.dirname(LOCAL), exist_ok=True)
    with open(LOCAL, "w", encoding="utf-8", newline="\n") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    show(settings)
    print("\nDone. Start a new Claude Code session in this folder for it to take effect.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
