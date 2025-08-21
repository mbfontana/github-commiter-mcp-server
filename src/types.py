from typing import Optional, TypedDict, List, Literal


class OpenRepoResult(TypedDict):
    session_id: str
    dir: str
    branch: Optional[str]


class ListChangesResult(TypedDict):
    files: List[str]
    scope: Literal["working", "staged"]
    diff: Optional[str]
    diff_truncated: bool


class FileDiffResult(TypedDict):
    path: str
    diff: Optional[str]
    diff_truncated: bool


class CommitItem(TypedDict):
    files: List[str]
    message: str


class CommitChangesResult(TypedDict):
    commits: List[str]
