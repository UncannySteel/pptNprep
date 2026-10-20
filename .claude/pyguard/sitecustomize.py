"""Python runtime half of the read-only guard for the ABOT code directory.

setup_machine.py puts this directory on PYTHONPATH for Claude Code sessions in
pptNprep, so every Python process they start imports this module first. It
installs an audit hook that refuses to write, create, delete, rename or chmod
anything under the paths in $ABOT_CODE_DIR, or under any directory named
darwinV2. Reading is unaffected. Any other sitecustomize on the path still runs.
"""
import os
import sys


def _install() -> None:
    raw = os.environ.get("ABOT_CODE_DIR", "")
    roots = []
    for part in raw.split(os.pathsep):
        if part.strip():
            p = os.path.abspath(part.strip())
            roots += [os.path.normcase(p), os.path.normcase(os.path.realpath(p))]
    roots = sorted(set(roots))
    write_flags = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC

    def is_protected(path) -> bool:
        if path is None or isinstance(path, int):
            return False
        try:
            p = os.path.normcase(os.path.realpath(os.fsdecode(os.fspath(path))))
        except (TypeError, ValueError, OSError):
            return False
        if any(p == r or p.startswith(r.rstrip(os.sep) + os.sep) for r in roots):
            return True
        return "darwinv2" in p.lower().replace("\\", "/").split("/")

    # audit event -> positions of the path arguments that get modified
    path_events = {
        "os.remove": (0,), "os.rmdir": (0,), "os.mkdir": (0,), "os.chmod": (0,), "os.chown": (0,),
        "os.truncate": (0,), "os.utime": (0,), "os.chflags": (0,), "os.lchflags": (0,),
        "os.setxattr": (0,), "os.removexattr": (0,), "os.mkfifo": (0,), "os.mknod": (0,),
        "os.rename": (0, 1), "os.link": (1,), "os.symlink": (1,),
        "shutil.rmtree": (0,), "shutil.copyfile": (1,), "shutil.copymode": (1,),
        "shutil.copystat": (1,), "shutil.move": (0, 1), "shutil.chown": (0,),
        "shutil.make_archive": (0,), "shutil.unpack_archive": (1,),
    }

    def deny(path) -> None:
        raise PermissionError(
            f"pptNprep read-only guard: refusing to modify '{os.fsdecode(os.fspath(path))}' "
            "inside the ABOT code directory. Write outputs into the pptNprep project instead."
        )

    def hook(event, args) -> None:
        if event == "open":
            path, mode, flags = (tuple(args) + (None, None, None))[:3]
            if isinstance(mode, str):
                writing = any(c in mode for c in "wax+")
            else:
                writing = bool((flags or 0) & write_flags)
            if writing and is_protected(path):
                deny(path)
        elif event in path_events:
            for idx in path_events[event]:
                if idx < len(args) and is_protected(args[idx]):
                    deny(args[idx])

    sys.addaudithook(hook)


def _chain_next_sitecustomize() -> None:
    """Run the sitecustomize this one shadows (e.g. a distro's), if there is one."""
    import importlib.machinery
    import importlib.util

    here = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
    rest = [p for p in sys.path if os.path.normcase(os.path.abspath(p or os.curdir)) != here]
    spec = importlib.machinery.PathFinder.find_spec("sitecustomize", rest)
    if spec and spec.origin and os.path.normcase(os.path.abspath(spec.origin)) != os.path.normcase(os.path.abspath(__file__)):
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)


_install()
try:
    _chain_next_sitecustomize()
except Exception:
    pass
