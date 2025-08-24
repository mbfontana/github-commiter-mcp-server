# MCP Git Committer

Tiny **Model Context Protocol (MCP)** server I built to learn how MCP tools work with an AI client (e.g., Claude Desktop).
It exposes a few Git actions as tools so you can say things like:

> “Commit the changed files on repo `mcp-demo` with meaningful messages.”

The model reads the diff, drafts **Conventional Commit** messages, and the server runs `git` safely.

---

## What’s here

- Tools: `open_repo`, `list_changes`, `get_file_diff`, `commit_changes`, `push`, `validate_commit_message`
- Prompt: `commit_message_style` (teaches Conventional Commits)
- Repos are sandboxed to a root folder via `MCP_REPOS_DIR`
- Code split for clarity:

  ```
  mcp-git-committer/
  ├─ server.py
  └─ src/
     ├─ helpers.py   # run_git, ensure_session
     └─ types.py     # TypedDicts + Session
  ```

---

## Quick start

**Requirements:** Python 3.10+, `git` in PATH

```bash
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install "mcp[cli]" python-dotenv
echo 'MCP_REPOS_DIR=/ABS/PATH/TO/your/repos' > .env
```


Run locally (dev):

```bash
mcp dev server.py
# or
python server.py
```

---

## Use with Claude Desktop (simplest)

Add to the config file and restart Claude:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "git-committer": {
      "command": "/ABS/PATH/TO/repo/.venv/bin/python",
      "args": ["/ABS/PATH/TO/repo/server.py"],
      "env": { "MCP_REPOS_DIR": "/ABS/PATH/TO/your/repos" }
    }
  }
}
```

Then try in a chat:

- “List the changed files on repo **mcp-demo**.”
- “Commit the changed files on repo **mcp-demo** with meaningful messages.”
- “Push the branch.”
