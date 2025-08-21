import shlex
import subprocess
from typing import Dict, Optional, List


class Session:
    def __init__(self, id: str, dir: str, branch: Optional[str] = None):
        self.id = id
        self.dir = dir
        self.branch = branch


sessions: Dict[str, Session] = {}


def ensure_session(session_id: str) -> Session:
    sess = sessions.get(session_id)
    if not sess:
        raise RuntimeError("Invalid sessionId; call open_repo first")
    return sess


def run_git(args: List[str], cwd: Optional[str] = None) -> str:
    cmd = ["git", *args]
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(shlex.quote(a) for a in args)} failed (code {proc.returncode})\nSTDERR:\n{proc.stderr.strip()}"
        )
    return proc.stdout
