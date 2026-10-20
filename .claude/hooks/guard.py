#!/usr/bin/env python3
"""Read-only guard for the ABOT code directory.

Claude Code runs this before every Edit/Write/NotebookEdit/Bash/PowerShell call
(``guard.py pretool``) and once per session (``guard.py session-start``), with
the hook payload as JSON on stdin. It stops sessions in this folder from
changing the code directory, wherever that directory lives on a machine.

Protected paths:
  * each path in $ABOT_CODE_DIR (os.pathsep-separated), which setup_machine.py
    writes into .claude/settings.local.json on each machine;
  * any directory named darwinV2, so stray copies stay protected and the guard
    still means something on a machine that has not been set up yet.

File tools are denied when their target is protected. Shell commands are
denied when they would write, delete, move or run something inside a protected
path; reading (cat, grep, ls, git log/diff, copying files *out* of the code
dir) is allowed. Python processes are also guarded at runtime by
.claude/pyguard/sitecustomize.py once setup_machine.py has run.
"""
from __future__ import annotations

import json
import os
import posixpath
import re
import shlex
import sys

FALLBACK_DIR = "darwinv2"
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(HERE))
PYGUARD_DIR = os.path.join(os.path.dirname(HERE), "pyguard")
SETUP_HINT = 'python .claude/hooks/setup_machine.py "<path to the code dir>"'

# ── paths ─────────────────────────────────────────────────────────────────────

_GITBASH_DRIVE = re.compile(r"^/(?:mnt/|cygdrive/)?([a-zA-Z])(?=/|$)")


def to_native(path: str, cwd: str | None = None) -> str:
    """Absolute OS path for ``path``, accepting Git Bash (/c/...) and WSL forms on Windows."""
    p = path.strip()
    if len(p) >= 2 and p[0] == p[-1] and p[0] in "\"'":
        p = p[1:-1]
    if p.startswith("~"):
        p = os.path.expanduser(p)
    if os.name == "nt":
        p = _GITBASH_DRIVE.sub(lambda m: m.group(1).upper() + ":", p.replace("\\", "/"), count=1)
    if not os.path.isabs(p) and cwd:
        p = os.path.join(to_native(cwd), p)
    return os.path.normpath(p) if p else p


def norm(path: str) -> str:
    """Comparison key: lower-case, forward slashes, drive as ``c:``."""
    p = path.replace("\\", "/").lower()
    p = _GITBASH_DRIVE.sub(lambda m: m.group(1) + ":", p, count=1)
    p = posixpath.normpath(p) if p else p
    return "/" + p.lstrip("/") if p.startswith("//") else p


def candidates(token: str, cwd: str | None) -> set[str]:
    """Comparison keys for a path token: as written, and with symlinks resolved."""
    native = to_native(token, cwd)
    keys = {norm(native)}
    try:
        keys.add(norm(os.path.realpath(native)))
    except (OSError, ValueError):
        pass
    return keys


def under(key: str, root: str) -> bool:
    return key == root or key.startswith(root.rstrip("/") + "/")


def load_roots() -> list[str]:
    raw = os.environ.get("ABOT_CODE_DIR", "")
    if not raw.strip():
        try:
            with open(os.path.join(PROJECT_DIR, ".claude", "settings.local.json"), encoding="utf-8") as f:
                raw = json.load(f).get("env", {}).get("ABOT_CODE_DIR", "")
        except (OSError, ValueError, AttributeError):
            raw = ""
    roots = []
    for part in raw.split(os.pathsep):
        if part.strip():
            native = to_native(part)
            roots.append(norm(native))
            try:
                roots.append(norm(os.path.realpath(native)))
            except (OSError, ValueError):
                pass
    return sorted(set(roots))


ROOTS: list[str] = []


def protected_key(key: str) -> bool:
    return any(under(key, r) for r in ROOTS) or FALLBACK_DIR in key.split("/")


def protected(token: str, cwd: str | None) -> bool:
    return any(protected_key(k) for k in candidates(token, cwd))


def root_label() -> str:
    return ", ".join(ROOTS) if ROOTS else "any darwinV2 directory (ABOT_CODE_DIR is not set on this machine)"


# ── command text helpers ──────────────────────────────────────────────────────

NULL_TARGETS = {"/dev/null", "nul", "$null", "/dev/stdout", "/dev/stderr", "con"}


def text_key(text: str) -> str:
    """Lower-case command text with path separators normalised, for substring checks."""
    t = text.lower().replace("\\ ", " ").replace("\\", "/")
    t = re.sub(r"/{2,}", "/", t)
    return re.sub(r"(?<![\w.:-])/(?:mnt/|cygdrive/)?([a-z])(?=/)", r"\1:", t)


def text_touches(text: str) -> bool:
    t = text_key(text)
    return (
        any(r in t for r in ROOTS)
        or "abot_code_dir" in t
        or re.search(r"(^|[/\s\"'=(])darwinv2(/|$|[\s\"')])", t) is not None
    )


def extract_heredocs(cmd: str) -> tuple[str, dict[str, str]]:
    """Replace each heredoc with a placeholder word and return the bodies."""
    lines = cmd.split("\n")
    out, bodies, i = [], {}, 0
    marker = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][\w.-]*)\2")
    while i < len(lines):
        line = lines[i]
        pending = []

        def repl(m):
            key = f"__HEREDOC{len(bodies) + len(pending)}__"
            pending.append((key, m.group(3), m.group(1) == "-"))
            return " " + key + " "

        line = marker.sub(lambda m: m.group(0) if m.string[max(0, m.start() - 1):m.start()] == "<" else repl(m), line)
        out.append(line)
        i += 1
        for key, delim, strip_tabs in pending:
            body = []
            while i < len(lines):
                cand = lines[i].lstrip("\t") if strip_tabs else lines[i]
                i += 1
                if cand.strip() == delim:
                    break
                body.append(lines[i - 1])
            bodies[key] = "\n".join(body)
    return "\n".join(out), bodies


def read_word(cmd: str, i: int) -> tuple[str, int]:
    """Read one shell word starting at i (quotes stripped); return it and the end index."""
    n, buf, quote = len(cmd), [], None
    while i < n:
        c = cmd[i]
        if quote:
            if c == quote:
                quote = None
            else:
                buf.append(c)
        elif c in "'\"":
            quote = c
        elif c.isspace() or c in ";|&<>()":
            break
        else:
            buf.append(c)
        i += 1
    return "".join(buf), i


def scan(cmd: str, mode: str) -> tuple[list[str], list[tuple[int, str]]]:
    """Split ``cmd`` into simple commands outside quotes and collect output redirections.

    mode is "bash", "ps" (PowerShell) or "cmd". Returns (segments, [(segment_index, target)]).
    """
    segs, cur, redirects = [], [], []
    i, n, quote = 0, len(cmd), None
    esc = {"bash": "\\", "ps": "`", "cmd": "^"}[mode]
    while i < n:
        c = cmd[i]
        if quote:
            cur.append(c)
            if quote in ("@'", '@"'):
                if c == "\n" and cmd.startswith(quote[1] + "@", i + 1):
                    cur.append(cmd[i + 1 : i + 3])
                    i += 3
                    quote = None
                    continue
            elif c == quote:
                quote = None
            elif quote == '"' and c == esc and mode != "cmd" and i + 1 < n:
                cur.append(cmd[i + 1])
                i += 1
            i += 1
            continue
        if mode == "ps" and c == "@" and cmd[i + 1 : i + 2] in ("'", '"'):
            quote = "@" + cmd[i + 1]
            cur.append(cmd[i : i + 2])
            i += 2
            continue
        if c in "'\"":
            quote = c
            cur.append(c)
            i += 1
            continue
        if c == esc and i + 1 < n:
            cur.append(cmd[i : i + 2])
            i += 2
            continue
        if c == "#" and mode != "cmd" and (i == 0 or cmd[i - 1].isspace()):
            j = cmd.find("\n", i)
            i = n if j < 0 else j
            continue
        if mode == "ps" and c in "{}":
            segs.append("".join(cur))
            cur = []
            i += 1
            continue
        if c in ";\n|&":
            if c == "&" and ((cur and cur[-1][-1:] in ("<", ">")) or cmd[i + 1 : i + 2] == ">"):
                cur.append(c)
                i += 1
                continue
            segs.append("".join(cur))
            cur = []
            i += 2 if cmd[i : i + 2] in ("&&", "||") else 1
            continue
        if c == ">":
            j = i + 1
            if j < n and cmd[j] in ">|":
                j += 1
            if j < n and cmd[j] == "&":
                cur.append(cmd[i : j + 1])
                i = j + 1
                continue
            while j < n and cmd[j] in " \t":
                j += 1
            target, i = read_word(cmd, j)
            redirects.append((len(segs), target))
            cur.append(" ")
            continue
        cur.append(c)
        i += 1
    segs.append("".join(cur))
    return segs, redirects


def substitutions(text: str) -> list[str]:
    """Inner commands of $(...) and `...` (non-nested), analysed as extra segments."""
    inner = re.findall(r"\$\(([^()]*)\)", text)
    inner += re.findall(r"`([^`]*)`", text) if "`" in text else []
    return inner


def tokens_of(seg: str, mode: str) -> list[str]:
    seg = seg.strip().lstrip("({").rstrip(")}").strip()
    if not seg:
        return []
    try:
        toks = shlex.split(seg, posix=(mode == "bash"))
    except ValueError:
        toks = seg.split()
    if mode != "bash":
        toks = [t[1:-1] if len(t) >= 2 and t[0] == t[-1] and t[0] in "'\"" else t for t in toks]
    return toks


# ── verb tables ───────────────────────────────────────────────────────────────

READONLY = set("""
ls dir cat type head tail less more grep egrep fgrep rg ag wc file stat du df tree diff cmp comm
md5sum sha1sum sha256sum sha512sum b2sum echo printf pwd which where whereis sort uniq cut tr column
nl od xxd hexdump strings basename dirname realpath readlink test [ [[ true false jq yq date sleep
seq whoami hostname uname id get-childitem gci get-content gc select-string sls get-item gi
get-itemproperty gp test-path resolve-path measure-object measure select-object select where-object
where ? foreach-object % sort-object sort group-object format-table ft format-list fl format-wide
out-string out-host write-output write write-host get-filehash compare-object convertfrom-json
convertto-json convertfrom-csv convertto-csv import-csv get-command gcm split-path join-path
get-location gl get-date get-help help man popd exit return break continue wait read cls clear
out-null start-sleep write-error write-verbose write-warning get-process get-variable set-variable
new-variable get-member gm export set local declare typeset readonly unset alias unalias shopt trap
""".split())

MUTATING = set("""
rm rmdir unlink del erase rd ri remove-item mv move move-item mi ren rename rename-item rni touch
mkdir md new-item ni truncate chmod chown chgrp chattr attrib icacls takeown shred ln mklink link
set-content sc add-content ac clear-content clc out-file export-csv export-clixml set-itemproperty
sp clear-item cli new-itemproperty remove-itemproperty set-acl expand-archive compress-archive dd
patch install-module
""".split())

COPYLIKE = {"cp", "copy", "copy-item", "cpi", "xcopy", "robocopy", "rsync", "scp", "install"}
TEE = {"tee", "tee-object"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish", "git-bash"}
POWERSHELLS = {"powershell", "pwsh"}
PREFIXES = {"sudo", "nohup", "time", "nice", "stdbuf", "exec", "command", "builtin", "&", "doas"}
KEYWORDS_DROP = {"if", "elif", "while", "until", "then", "do", "else", "!", "{", "}"}
KEYWORDS_SKIP = {"for", "case", "select", "in", "done", "fi", "esac", "function", "foreach"}
PY_VERB = re.compile(r"^(python(\d+(\.\d+)*)?w?|py|pypy3?)$")
PIPS = {"pip", "pip3", "uv", "conda", "mamba", "poetry", "pipx"}
PYTESTS = {"pytest", "py.test"}

GIT_READONLY = set("""
log show diff status blame grep ls-files ls-tree ls-remote rev-parse rev-list describe shortlog
cat-file for-each-ref show-ref name-rev count-objects help version whatchanged annotate cherry
merge-base range-diff var check-ignore check-attr verify-commit verify-tag difftool --version
""".split())

PY_WRITE = re.compile(
    r"""open\([^)]*,\s*(?:mode\s*=\s*)?['"][rbt]*[wax+][rbtwax+]*['"]|\.write_(?:text|bytes)\(|\.to_(?:csv|excel|json|parquet|pickle|"""
    r"""feather|html|latex|markdown|hdf|sql)\(|savefig\(|\.save\(|np\.save|json\.dump\(|pickle\.dump\("""
    r"""|os\.(?:remove|unlink|rename|replace|rmdir|removedirs|mkdir|makedirs|chmod|truncate|system|popen)"""
    r"""|shutil\.|\.unlink\(|\.rmdir\(|\.mkdir\(|\.touch\(|\.rename\(|subprocess|copyfile|"""
    r"""(?<!stdout)(?<!stderr)\.write\(""",
    re.I,
)
NET_IO_WRITE = re.compile(
    r"\[(?:system\.)?io\.(?:file|directory)\]::(?:write|append|delete|move|copy|create|replace|set|"
    r"open(?!read|text))|streamwriter|filestream",
    re.I,
)


class Blocked(Exception):
    pass


# ── per-command analysis ──────────────────────────────────────────────────────


class Analyzer:
    def __init__(self, cwd: str, mode: str, env_overrides: dict[str, str] | None = None):
        self.cwd = cwd
        self.mode = mode
        self.vars = {k.lower(): v for k, v in os.environ.items()}
        if env_overrides:
            self.vars.update(env_overrides)
        self.touches = False
        self.pythonpath_overridden = False

    # helpers
    def expand(self, tok: str) -> str:
        def rep(m):
            name = next(g for g in m.groups() if g)
            val = self.vars.get(name.lower())
            return val if val is not None else m.group(0)

        tok = re.sub(r"\$\{(\w+)\}|\$env:(\w+)|\$(\w+)|%(\w+)%", rep, tok, flags=re.I)
        if tok == "~" or tok.startswith(("~/", "~\\")):
            tok = os.path.expanduser(tok)
        return tok

    @staticmethod
    def unresolved(tok: str) -> bool:
        return re.search(r"\$[\w{(_]|%\w+%|\{\}", tok) is not None

    def path_args(self, toks: list[str]) -> list[str]:
        out = []
        for t in toks:
            if not t or "://" in t:
                continue
            if t.startswith("--") and "=" in t:
                t = t.split("=", 1)[1]
            elif t.startswith("-") and t != "-":
                continue
            elif re.match(r"^[A-Za-z]\w*=", t):
                t = t.split("=", 1)[1]
            if t:
                out.append(t)
        return out

    def check_target(self, tok: str, cwd: str, what: str) -> None:
        if tok.lower() in NULL_TARGETS or tok.startswith("&"):
            return
        if self.unresolved(tok):
            if self.touches:
                raise Blocked(f"{what} writes to '{tok}', which can't be resolved, in a command that touches the code dir")
            return
        if protected(tok, cwd):
            raise Blocked(f"{what} would write to '{tok}'")

    def check_all(self, toks: list[str], cwd: str, what: str) -> None:
        for t in self.path_args(toks):
            self.check_target(t, cwd, what)

    # main entry
    def run(self, cmd: str) -> None:
        body, heredocs = extract_heredocs(cmd)
        segs, redirects = scan(body, self.mode)
        segs = segs + [s for seg in list(segs) for s in substitutions(seg)]
        self.collect_assignments(segs)
        if self.mode == "ps":
            segs = [self.ps_assignment_rhs(s) for s in segs]
        tokens = [[self.expand(t) for t in tokens_of(s, self.mode)] for s in segs]

        self.touches = text_touches(body) or protected_key(norm(to_native(self.cwd)))
        if not self.touches:
            self.touches = any(protected(t, self.cwd) for ts in tokens for t in self.path_args(ts) if not self.unresolved(t))
        if self.touches and NET_IO_WRITE.search(body):
            raise Blocked("a .NET file-write call in a command that touches the code dir")

        cwd = self.cwd
        cwds = []
        stack = []
        for toks in tokens:
            cwds.append(cwd)
            cwd = self.segment(toks, cwd, stack, heredocs)
        for seg_idx, target in redirects:
            seg_cwd = cwds[seg_idx] if seg_idx < len(cwds) else cwd
            self.check_target(self.expand(target), seg_cwd, "an output redirection")

    @staticmethod
    def ps_assignment_rhs(seg: str) -> str:
        """``$x = <expr>``: keep the right-hand side only if it is a command, not a value."""
        m = re.match(r"^\s*\$[\w:]+\s*[+]?=\s*(.*)$", seg, re.S)
        if not m:
            return seg
        rhs = m.group(1).strip()
        return rhs if rhs and rhs[0] not in "\"'$@([0123456789-" else ""

    def collect_assignments(self, segs: list[str]) -> None:
        for s in segs:
            for m in re.finditer(r"(?:^|\s)(?:export\s+|set\s+|local\s+)?([A-Za-z_]\w*)=(\"[^\"]*\"|'[^']*'|\S*)", s):
                self.vars[m.group(1).lower()] = m.group(2).strip("\"'")
                if m.group(1).upper() == "PYTHONPATH":
                    self.pythonpath_overridden = True
            for m in re.finditer(r"\$(?:env:)?([A-Za-z_]\w*)\s*=\s*(\"[^\"]*\"|'[^']*')", s, re.I):
                self.vars[m.group(1).lower()] = m.group(2).strip("\"'")
                if m.group(1).upper() == "PYTHONPATH":
                    self.pythonpath_overridden = True

    def segment(self, toks: list[str], cwd: str, stack: list[str], heredocs: dict[str, str]) -> str:
        """Check one simple command; return the working directory after it."""
        while toks and (re.match(r"^[A-Za-z_]\w*=", toks[0]) or toks[0].lower() in KEYWORDS_DROP):
            toks = toks[1:]
        if not toks:
            return cwd
        stdin = next((heredocs[t] for t in toks if t in heredocs), None)
        toks = [t for t in toks if t not in heredocs]
        if not toks:
            return cwd
        raw_verb = toks[0]
        verb = os.path.basename(raw_verb.replace("\\", "/")).lower()
        verb = verb[:-4] if verb.endswith(".exe") else verb
        args = toks[1:]

        if verb in KEYWORDS_SKIP or verb.startswith("__heredoc"):
            return cwd
        if verb in PREFIXES:
            rest = args
            if verb == "nice" and rest[:1] == ["-n"]:
                rest = rest[2:]
            return self.segment(rest, cwd, stack, heredocs)
        if verb == "timeout":
            rest = list(args)
            while rest and rest[0].startswith("-"):
                rest = rest[2:] if rest[0] in ("-s", "-k", "--signal", "--kill-after") else rest[1:]
            return self.segment(rest[1:], cwd, stack, heredocs)
        if verb == "command" and args[:1] in (["-v"], ["-V"]):
            return cwd
        if verb.startswith("$"):
            if self.touches and re.search(r"\.(delete|moveto|copyto|create|write|append|replace|encrypt)", verb):
                raise Blocked(f"a PowerShell method call ('{raw_verb}') in a command that touches the code dir")
            return cwd
        if verb == "env":
            rest = list(args)
            while rest and (rest[0].startswith("-") or "=" in rest[0]):
                if rest[0] in ("-u", "--unset") and len(rest) > 1:
                    if rest[1].upper() == "PYTHONPATH":
                        self.pythonpath_overridden = True
                    rest = rest[2:]
                    continue
                if rest[0] in ("-C", "--chdir") and len(rest) > 1:
                    cwd = to_native(rest[1], cwd)
                    rest = rest[2:]
                    continue
                if rest[0].upper().startswith("PYTHONPATH="):
                    self.pythonpath_overridden = True
                rest = rest[1:]
            return self.segment(rest, cwd, stack, heredocs)

        # directory changes
        if verb in ("cd", "chdir", "pushd", "set-location", "sl", "push-location"):
            dests = self.path_args(args)
            if verb in ("pushd", "push-location"):
                stack.append(cwd)
            if not dests:
                return os.path.expanduser("~") if verb in ("cd", "chdir") else cwd
            return cwd if dests[0] == "-" or self.unresolved(dests[0]) else to_native(dests[0], cwd)
        if verb in ("popd", "pop-location"):
            return stack.pop() if stack else cwd

        # running something that lives inside the code dir
        if ("/" in raw_verb or "\\" in raw_verb) and protected(raw_verb, cwd):
            raise Blocked(f"running '{raw_verb}' from the code dir")

        if verb == "git":
            self.git(args, cwd)
        elif PY_VERB.match(verb):
            self.python(args, cwd, stdin)
        elif verb in PYTESTS:
            if protected_key(norm(to_native(cwd))) or any(protected(a, cwd) for a in self.path_args(args)):
                raise Blocked("running the code dir's tests (pytest writes caches there)")
        elif verb in PIPS:
            self.pip(args, cwd)
        elif verb in SHELLS:
            self.shell(args, cwd, stdin, "bash")
        elif verb in ("cmd",):
            inner = next((i for i, a in enumerate(args) if a.lower() in ("/c", "/k")), None)
            if inner is not None:
                Analyzer(cwd, "cmd", self.vars).run(" ".join(args[inner + 1 :]))
        elif verb in POWERSHELLS:
            self.powershell(args, cwd)
        elif verb in (".", "source"):
            if args and protected(args[0], cwd):
                raise Blocked(f"sourcing '{args[0]}' from the code dir")
        elif verb == "xargs":
            self.xargs(args, cwd, stack, heredocs)
        elif verb == "find":
            self.find(args, cwd, stack, heredocs)
        elif verb in ("sed", "perl", "awk", "gawk"):
            self.inplace(verb, args, cwd)
        elif verb in TEE:
            self.check_all([a for a in args if a.lower() not in ("-filepath", "-path", "-literalpath")], cwd, verb)
        elif verb in COPYLIKE:
            self.copy(verb, args, cwd)
        elif verb in ("tar", "zip", "unzip"):
            self.archive(verb, args, cwd)
        elif verb in MUTATING:
            self.check_all(args, cwd, f"'{verb}'")
        elif verb in READONLY:
            pass
        else:
            self.unknown(verb, raw_verb, args, cwd)
        return cwd

    # verb handlers
    def git(self, args: list[str], cwd: str) -> None:
        repo, i, extra_paths = cwd, 0, []
        while i < len(args) and args[i].startswith("-"):
            a = args[i]
            if a == "-C" and i + 1 < len(args):
                repo = to_native(args[i + 1], repo)
                i += 2
                continue
            if a.startswith(("--git-dir=", "--work-tree=")):
                extra_paths.append(a.split("=", 1)[1])
            if a in ("-c", "--git-dir", "--work-tree", "--namespace") and i + 1 < len(args):
                if a != "-c":
                    extra_paths.append(args[i + 1])
                i += 2
                continue
            if a in ("--version", "--help"):
                return
            i += 1
        if i >= len(args):
            return
        sub, rest = args[i].lower(), args[i + 1 :]
        if self.git_readonly(sub, rest):
            return
        targets = [repo] + [to_native(p, cwd) for p in extra_paths]
        if sub == "clone":
            pos = [a for a in rest if not a.startswith("-")]
            targets = [to_native(pos[1], repo)] if len(pos) > 1 else [repo]
        if any(protected_key(norm(t)) for t in targets):
            raise Blocked(f"'git {sub}' would change the code dir's repository")

    @staticmethod
    def git_readonly(sub: str, rest: list[str]) -> bool:
        flags = {a for a in rest if a.startswith("-")}
        pos = [a for a in rest if not a.startswith("-")]
        first = pos[0].lower() if pos else ""
        if sub in GIT_READONLY:
            return True
        if sub == "branch":
            bad = {"-d", "-D", "-m", "-M", "-c", "-C", "-f", "--delete", "--move", "--copy", "--force",
                   "-u", "--set-upstream-to", "--unset-upstream", "--edit-description", "-t", "--track"}
            listing = flags & {"-l", "--list", "--contains", "--merged", "--no-merged", "--points-at", "--no-contains"}
            return not (flags & bad) and (not pos or bool(listing))
        if sub == "tag":
            bad = {"-d", "--delete", "-a", "-s", "-f", "--force", "-m", "-F", "-u"}
            return not (flags & bad) and (not pos or bool(flags & {"-l", "--list"}))
        if sub == "remote":
            return not pos or first in ("show", "get-url")
        if sub == "stash":
            return first in ("list", "show")
        if sub == "config":
            reads = {"--get", "--get-all", "--get-regexp", "--list", "-l", "--get-urlmatch"}
            writes = {"--unset", "--unset-all", "--add", "--replace-all", "--rename-section",
                      "--remove-section", "-e", "--edit"}
            return bool(flags & reads) or (not (flags & writes) and len(pos) <= 1)
        if sub == "reflog":
            return first not in ("expire", "delete")
        if sub in ("worktree", "notes"):
            return first in ("list", "show")
        if sub == "submodule":
            return first in ("status", "summary")
        if sub == "lfs":
            return first in ("ls-files", "status", "env", "version")
        return False

    def python(self, args: list[str], cwd: str, stdin: str | None) -> None:
        i, inline, isolated = 0, None, False
        while i < len(args):
            a = args[i]
            if a == "-c" and i + 1 < len(args):
                inline = args[i + 1]
                break
            if a == "-m" and i + 1 < len(args):
                mod, margs = args[i + 1], args[i + 2 :]
                if mod.startswith("pytest"):
                    if protected_key(norm(to_native(cwd))) or any(protected(x, cwd) for x in self.path_args(margs)):
                        raise Blocked("running the code dir's tests (pytest writes caches there)")
                elif mod == "pip":
                    self.pip(margs, cwd)
                elif protected_key(norm(to_native(cwd))):
                    raise Blocked(f"running module '{mod}' with the code dir as working directory")
                return
            if a == "-":
                inline = stdin or ""
                break
            if a.startswith("-"):
                if any(f in a[1:] for f in "IES") and not a.startswith("--"):
                    isolated = True
                if a in ("-X", "-W", "--check-hash-based-pycs") and i + 1 < len(args):
                    i += 1
                i += 1
                continue
            if protected(a, cwd):
                raise Blocked(f"running the code dir's script '{a}'")
            return
        if inline is None:
            inline = stdin or ""
        if not inline:
            return
        runtime_guarded = (
            not isolated
            and not self.pythonpath_overridden
            and bool(ROOTS)
            and os.path.normcase(os.path.abspath(PYGUARD_DIR))
            in [os.path.normcase(os.path.abspath(p)) for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
        )
        if runtime_guarded:
            return
        if (text_touches(inline) or protected_key(norm(to_native(cwd)))) and PY_WRITE.search(inline):
            raise Blocked("inline Python that writes files and references the code dir (runtime guard not active)")

    def pip(self, args: list[str], cwd: str) -> None:
        skip_next = False
        for a in args:
            if skip_next:
                skip_next = False
                continue
            if a in ("-r", "--requirement", "-c", "--constraint"):
                skip_next = True
                continue
            if a.startswith("-"):
                continue
            if protected(a, cwd):
                raise Blocked(f"pip/env tooling would write into the code dir ('{a}')")

    def shell(self, args: list[str], cwd: str, stdin: str | None, mode: str) -> None:
        for i, a in enumerate(args):
            if a in ("-c", "-lc", "-ic") and i + 1 < len(args):
                Analyzer(cwd, mode, self.vars).run(args[i + 1])
                return
            if not a.startswith("-"):
                if protected(a, cwd):
                    raise Blocked(f"running the code dir's script '{a}'")
                return
        if stdin:
            Analyzer(cwd, mode, self.vars).run(stdin)

    def powershell(self, args: list[str], cwd: str) -> None:
        for i, a in enumerate(args):
            al = a.lower()
            if al in ("-command", "-c") and i + 1 < len(args):
                Analyzer(cwd, "ps", self.vars).run(" ".join(args[i + 1 :]))
                return
            if al in ("-encodedcommand", "-enc", "-e", "-ec"):
                if self.touches:
                    raise Blocked("an encoded PowerShell command in a command that touches the code dir")
                return
            if al in ("-file", "-f") and i + 1 < len(args):
                if protected(args[i + 1], cwd):
                    raise Blocked(f"running the code dir's script '{args[i + 1]}'")
                return
            if not a.startswith("-"):
                Analyzer(cwd, "ps", self.vars).run(" ".join(args[i:]))
                return

    def xargs(self, args: list[str], cwd: str, stack: list[str], heredocs: dict[str, str]) -> None:
        i, with_value = 0, {"-I", "-n", "-P", "-d", "-L", "-s", "-E", "-a", "--delimiter", "--max-args"}
        while i < len(args) and args[i].startswith("-"):
            i += 2 if args[i] in with_value else 1
        inner = args[i:]
        if not inner:
            return
        verb = os.path.basename(inner[0]).lower()
        if self.touches and verb not in READONLY:
            raise Blocked(f"'xargs {verb}' on input that comes from the code dir")
        self.segment(inner, cwd, stack, heredocs)

    def find(self, args: list[str], cwd: str, stack: list[str], heredocs: dict[str, str]) -> None:
        paths = []
        for a in args:
            if a.startswith(("-", "(", "!")):
                break
            paths.append(a)
        roots_hit = any(protected(p, cwd) for p in paths) or (not paths and protected_key(norm(to_native(cwd))))
        if not roots_hit:
            return
        lowered = [a.lower() for a in args]
        if any(a in lowered for a in ("-delete", "-fprint", "-fprint0", "-fprintf", "-fls")):
            raise Blocked("'find -delete/-fprint' inside the code dir")
        for i, a in enumerate(lowered):
            if a in ("-exec", "-execdir", "-ok", "-okdir"):
                inner = []
                for b in args[i + 1 :]:
                    if b in (";", "+", "\\;"):
                        break
                    inner.append(b)
                verb = os.path.basename(inner[0]).lower() if inner else ""
                if verb not in READONLY:
                    raise Blocked(f"'find -exec {verb}' on files inside the code dir")

    def inplace(self, verb: str, args: list[str], cwd: str) -> None:
        if verb == "sed":
            inpl = any(a.startswith("--in-place") or re.match(r"^-[a-zA-Z]*i", a) for a in args)
        elif verb == "perl":
            inpl = any(re.match(r"^-[a-zA-Z]*i", a) for a in args)
        else:
            inpl = "inplace" in " ".join(args).lower()
        if inpl:
            self.check_all(args, cwd, f"in-place '{verb}'")

    def copy(self, verb: str, args: list[str], cwd: str) -> None:
        lowered = [a.lower() for a in args]
        for flag in ("-destination", "-t", "--target-directory"):
            if flag in lowered:
                idx = lowered.index(flag)
                if idx + 1 < len(args):
                    self.check_target(args[idx + 1], cwd, f"'{verb}'")
                return
        for a in args:
            if a.startswith("--target-directory="):
                self.check_target(a.split("=", 1)[1], cwd, f"'{verb}'")
                return
        pos = self.path_args(args)
        if verb in ("xcopy", "robocopy"):
            pos = [a for a in pos if not re.match(r"^/[A-Za-z]+(:\S*)?$", a)]
        if verb in ("robocopy", "xcopy", "copy-item", "cpi", "copy"):
            dest = pos[1] if len(pos) > 1 else None
            if dest is None:
                dest = cwd
        else:
            dest = pos[-1] if len(pos) > 1 else None
        if dest is not None:
            self.check_target(dest, cwd, f"'{verb}'")

    def archive(self, verb: str, args: list[str], cwd: str) -> None:
        lowered = " ".join(args)
        if verb == "tar":
            first = args[0] if args else ""
            creating = "--create" in lowered or ("c" in first.lstrip("-") and not first.startswith("--"))
            extracting = "--extract" in lowered or ("x" in first.lstrip("-") and not first.startswith("--"))
            if creating:
                for i, a in enumerate(args):
                    if a.startswith("--file="):
                        self.check_target(a.split("=", 1)[1], cwd, "'tar'")
                    elif (a == "-f" or (a.startswith("-") and not a.startswith("--") and a.endswith("f")) or (i == 0 and a.endswith("f"))) and i + 1 < len(args):
                        self.check_target(args[i + 1], cwd, "'tar'")
            if extracting:
                dest = next((args[i + 1] for i, a in enumerate(args) if a in ("-C", "--directory") and i + 1 < len(args)), None)
                self.check_target(dest or cwd, cwd, "'tar' extraction")
        elif verb == "zip":
            pos = self.path_args(args)
            if pos:
                self.check_target(pos[0], cwd, "'zip'")
        elif verb == "unzip":
            if "-l" in args or "-v" in args or "-t" in args or "-p" in args:
                return
            dest = next((args[i + 1] for i, a in enumerate(args) if a == "-d" and i + 1 < len(args)), None)
            self.check_target(dest or cwd, cwd, "'unzip'")

    def unknown(self, verb: str, raw_verb: str, args: list[str], cwd: str) -> None:
        if protected_key(norm(to_native(cwd))):
            raise Blocked(f"running '{verb}' with the code dir as working directory")
        for a in self.path_args(args):
            if not self.unresolved(a) and protected(a, cwd):
                raise Blocked(f"'{verb}' given a path inside the code dir ('{a}'); copy the file out first")


# ── hook entry points ─────────────────────────────────────────────────────────


def deny(reason: str) -> None:
    msg = (
        f"Blocked by the pptNprep read-only guard: {reason}. The ABOT code directory "
        f"({root_label()}) is read-only for sessions in this folder. Read it, or copy files "
        "out of it into this project, but don't modify it or run its scripts. Code changes "
        "belong in a session opened in the code directory itself."
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": msg,
    }}))


def pretool(payload: dict) -> None:
    tool = payload.get("tool_name", "")
    ti = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    if tool in ("Bash", "PowerShell"):
        cmd = ti.get("command") or ""
        try:
            Analyzer(cwd, "ps" if tool == "PowerShell" else "bash").run(cmd)
        except Blocked as b:
            deny(str(b))
        except Exception as exc:  # parsing failure: fail closed only when the code dir is involved
            if text_touches(cmd) or protected_key(norm(to_native(cwd))):
                deny(f"the guard could not analyse this command ({type(exc).__name__}) and it involves the code dir")
        return
    for key in ("file_path", "notebook_path", "path"):
        target = ti.get(key)
        if isinstance(target, str) and target and protected(target, cwd):
            deny(f"{tool} targets '{target}'")
            return


def find_content_roots() -> list[str]:
    """The folder(s) holding darwinV2/ inside each configured code dir (what context.md calls <CODE>)."""
    found = []
    raw = os.environ.get("ABOT_CODE_DIR", "")
    if not raw.strip():
        try:
            with open(os.path.join(PROJECT_DIR, ".claude", "settings.local.json"), encoding="utf-8") as f:
                raw = json.load(f).get("env", {}).get("ABOT_CODE_DIR", "")
        except (OSError, ValueError, AttributeError):
            raw = ""
    for part in [p for p in raw.split(os.pathsep) if p.strip()]:
        base = to_native(part)
        if os.path.isdir(os.path.join(base, "darwinV2")):
            found.append(base)
            continue
        try:
            subs = sorted(os.listdir(base))
        except OSError:
            subs = []
        hits = [os.path.join(base, s) for s in subs if os.path.isdir(os.path.join(base, s, "darwinV2"))]
        found.extend(hits or [base])
    return found


def session_start() -> None:
    contents = find_content_roots()
    pyguard_on = os.path.normcase(os.path.abspath(PYGUARD_DIR)) in [
        os.path.normcase(os.path.abspath(p)) for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p
    ]
    if not ROOTS:
        ctx = (
            "ABOT code directory: NOT CONFIGURED on this machine. context.md refers to it as <CODE>. "
            f"Ask the user for its path and have them run: {SETUP_HINT} — then start a new session. "
            "Until then, writes into any darwinV2 directory are still blocked, but other files in the "
            "code dir are only protected by the CLAUDE.md rule."
        )
        out = {"systemMessage": f"ABOT code dir not configured on this machine. Run: {SETUP_HINT}",
               "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}
    else:
        missing = [c for c in contents if not os.path.isdir(c)]
        ctx = (
            f"ABOT code directory on this machine (<CODE> in context.md): {' | '.join(contents)}. "
            "It is READ-ONLY for this session: read and copy out only. "
            f"Guard status: hook active; Python runtime guard {'active' if pyguard_on else 'NOT active (re-run setup_machine.py, then restart)'}."
        )
        out = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}
        if missing or not pyguard_on:
            out["systemMessage"] = (
                f"ABOT guard: code dir path not found ({', '.join(missing)})" if missing
                else "ABOT guard: Python runtime guard inactive; re-run setup_machine.py"
            ) + f" — {SETUP_HINT}"
    print(json.dumps(out))


def main() -> None:
    global ROOTS
    ROOTS = load_roots()
    event = sys.argv[1] if len(sys.argv) > 1 else "pretool"
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except ValueError:
        payload = {}
    if event == "session-start":
        session_start()
    else:
        pretool(payload)


if __name__ == "__main__":
    main()
