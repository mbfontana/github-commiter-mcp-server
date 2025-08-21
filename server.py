import os
import uuid
from typing import Optional, TypedDict

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.helpers import run_git, Session, sessions

load_dotenv()

mcp = FastMCP("git-committer")


class OpenRepoResult(TypedDict):
    session_id: str
    dir: str
    branch: Optional[str]


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
