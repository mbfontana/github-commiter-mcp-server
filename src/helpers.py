from typing import Dict, Optional


class Session:
    def __init__(self, id: str, dir: str, branch: Optional[str] = None):
        self.id = id
        self.dir = dir
        self.branch = branch


_sessions: Dict[str, Session] = {}


def _ensure_session(session_id: str) -> Session:
    sess = _sessions.get(session_id)
    if not sess:
        raise RuntimeError("Invalid sessionId; call open_repo first")
    return sess
