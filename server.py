import os
import uuid
from typing import List, Literal, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.helpers import run_git, ensure_session, Session, sessions
from src.types import OpenRepoResult, ListChangesResult, FileDiffResult, CommitItem, CommitChangesResult

load_dotenv()

mcp = FastMCP("git-committer")


@mcp.tool()
def open_repo(
        repo_name: str,
        branch: Optional[str] = None,
) -> OpenRepoResult:
    """
    Open a local repository by **name** under the repos root directory.

    Args:
      repo_name: Folder name of the repository inside the repos root (env: MCP_REPOS_DIR | REPOS_DIR | REPOS_ROOT)
      branch: Branch to checkout; defaults to 'main' if not provided. If 'main' doesn't exist and branch isn't provided, falls back to 'master'.

    Returns:
        OpenRepoResult:
            sessionI_i: str
            dir: str
            branch: str
    """

    root = os.environ.get("REPOS_DIR")
    if not root:
        raise RuntimeError("Set MCP_REPOS_DIR (or REPOS_DIR/REPOS_ROOT) to your repos directory")
    root_abs = os.path.abspath(root)

    target = os.path.abspath(os.path.join(root_abs, repo_name))
    if not (target == root_abs or target.startswith(root_abs + os.sep)):
        raise RuntimeError("Invalid repo_name path; must be inside repos root")

    if not os.path.isdir(target):
        raise RuntimeError(f"Repository folder not found: {target}")
    if not os.path.isdir(os.path.join(target, ".git")):
        raise RuntimeError("Target folder is not a git repository (.git missing)")

    run_git(["checkout", branch], cwd=target)

    sid = str(uuid.uuid4())
    sessions[sid] = Session(id=sid, dir=target, branch=branch)
    return OpenRepoResult(session_id=sid, dir=target, branch=branch)


@mcp.tool()
def list_changes(
        session_id: str,
        scope: Literal["working", "staged"] = "working",
        include_diff: bool = True,
        max_bytes: int = 120_000,
) -> ListChangesResult:
    """
    List changed files and (optionally) a trimmed unified diff for reasoning.

    Args:
        session_id: Session ID
        scope: Working or staged changes
        include_diff: Include diff for diff
        max_bytes: Maximum number of bytes to return

    Returns:
        ListChangesResult:
            files: List[str]
            scope: Literal["working", "staged"]
            diff: Optional[str]
            diff_truncated: bool
    """

    sess = ensure_session(session_id)

    porcelain = run_git(["status", "--porcelain=v1", "--renames"], cwd=sess.dir)
    files: List[str] = []
    for line in porcelain.splitlines():
        # format: XY <path> [-> <newpath>]
        parts = line.strip().split()
        if not parts:
            continue

        path = parts[-1]
        if path not in files:
            files.append(path)

    diff_text: Optional[str] = None
    truncated = False
    if include_diff and files:
        args = ["diff", "--unified=3"]
        if scope == "staged":
            args.append("--staged")
        diff = run_git(args, cwd=sess.dir)
        if len(diff.encode("utf-8")) > max_bytes:
            enc = diff.encode("utf-8")[:max_bytes]
            diff_text = enc.decode("utf-8", errors="ignore") + "\n[diff truncated]"
            truncated = True
        else:
            diff_text = diff

    return ListChangesResult(files=files, scope=scope, diff=diff_text, diff_truncated=truncated)


@mcp.tool()
def get_file_diff(
        session_id: str,
        path: str,
        staged: bool = False,
        max_bytes: int = 60_000,
) -> FileDiffResult:
    """
    Return a unified diff for a single file. Useful when the full diff was truncated.

    Args:
        session_id: Session ID
        path: Path to file
        staged: Staged or staged diff
        max_bytes: Maximum number of bytes to return

    Returns:
        FileDiffResult:
            path: str
            diff: Optional[str]
            diff_truncated: bool
    """

    sess = ensure_session(session_id)
    args = ["diff", "--unified=3"] + (["--staged"] if staged else []) + ["--", path]
    try:
        diff = run_git(args, cwd=sess.dir)
    except RuntimeError as e:
        # For brand-new untracked files, plain diff won’t show; try no-index against /dev/null
        if "is outside repository" in str(e) or "fatal: ambiguous argument" in str(e):
            diff = run_git(["diff", "--no-index", "/dev/null", path], cwd=sess.dir)
        else:
            raise

    truncated = False
    if len(diff.encode("utf-8")) > max_bytes:
        enc = diff.encode("utf-8")[:max_bytes]
        diff = enc.decode("utf-8", errors="ignore") + "\n[diff truncated]"
        truncated = True

    return FileDiffResult(path=path, diff=diff, diff_truncated=truncated)


@mcp.tool()
def commit_changes(
        session_id: str,
        commits: List[CommitItem],
        signoff: bool = False,
) -> CommitChangesResult:
    """
    Create one or multiple commits. The model should group files logically and craft messages.

    Each commit item: { files: [paths], message: str }

    Args:
        session_id: Session ID
        commits: List[CommitItem]
        signoff: bool

    Returns:
        CommitChangesResult:
            commits: List[CommitItem]
    """

    sess = ensure_session(session_id)
    shas: List[str] = []
    for item in commits:
        files = item.get("files", [])
        message = item.get("message", "")
        if not message.strip():
            raise ValueError("Commit message cannot be empty")
        if files:
            run_git(["add", "--", *files], cwd=sess.dir)

        args = ["commit", "-m", message]
        if signoff:
            args.append("-s")
        run_git(args, cwd=sess.dir)
        sha = run_git(["rev-parse", "HEAD"], cwd=sess.dir).strip()
        shas.append(sha)
    return CommitChangesResult(commits=shas)
