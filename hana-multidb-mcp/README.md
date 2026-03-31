# hana-multidb-mcp

Python MCP server that reads HANA connection profiles from a private GitHub repository and exposes them as **read-only** tools inside VS Code Copilot Chat.

A single server instance can manage any number of HANA connections simultaneously. Each connection is identified by an **alias** defined in the GitHub catalog repo — no credentials ever appear in the MCP configuration.

---

## Table of contents

- [Architecture overview](#architecture-overview)
- [Project structure](#project-structure)
- [MCP tools](#mcp-tools)
- [Connection catalog (GitHub repo)](#connection-catalog-github-repo)
- [Local setup](#local-setup)
- [VS Code integration](#vs-code-integration)
- [Security guardrails](#security-guardrails)
- [Running tests](#running-tests)
- [Next steps to continue](#next-steps-to-continue)

---

## Architecture overview

```
VS Code Copilot Chat
        │  JSON-RPC (stdio)
        ▼
  server.py  ──►  github_loader.py  ──►  GitHub Contents API
        │                                  (private catalog repo)
        ▼
  registry.py  ──►  drivers/hana.py  ──►  SAP HANA (hdbcli)
        │
        ▼
  guards/sql_readonly.py  (blocks DML / DDL / CALL / multi-statement)
```

1. On first tool call the server fetches `db-profiles/index.yml` from the catalog repo, then loads every enabled profile.
2. Connections are opened **lazily**: the driver connects only when the alias is first used.
3. `refresh_catalog` reloads profiles from GitHub without restarting VS Code.

---

## Project structure

```
hana-multidb-mcp/
├── pyproject.toml                  # uv project, dependencies, script entrypoint
├── catalog-example/
│   └── db-profiles/
│       ├── index.yml               # catalog index template
│       └── hana-pyd.yml            # connection profile template
├── src/
│   ├── config.py                   # reads env vars
│   ├── server.py                   # FastMCP entrypoint — all 7 tools defined here
│   ├── github_loader.py            # fetches catalog from GitHub Contents API
│   ├── registry.py                 # lazy connection pool keyed by alias
│   ├── drivers/
│   │   ├── base.py                 # abstract driver interface
│   │   └── hana.py                 # hdbcli driver (JSON-safe type conversion)
│   └── guards/
│       └── sql_readonly.py         # SQL guardrail (allowlist + blocklist)
└── tests/
    ├── test_sql_readonly.py        # 35 tests for the guardrail
    ├── test_registry.py            # 14 tests for the connection registry
    └── test_github_loader.py       # 8 tests for the GitHub catalog loader
```

---

## MCP tools

| Tool | Parameters | Description |
|---|---|---|
| `list_connections` | — | List all aliases with metadata. **No credentials exposed.** |
| `get_connection` | `alias` | Metadata for a single alias. |
| `refresh_catalog` | — | Hot-reload catalog from GitHub without restarting. |
| `ping_connection` | `alias` | Test connectivity and measure round-trip latency. |
| `list_schemas` | `alias` | List schemas visible to the configured user. |
| `list_tables` | `alias`, `schema` | List tables (name, type, comment) in a schema. |
| `execute_query` | `alias`, `sql`, `max_rows` | Run a `SELECT` / `WITH` query. DML/DDL blocked. |

---

## Connection catalog (GitHub repo)

The server reads connection profiles from a **separate private GitHub repo**. The catalog has two levels:

### `db-profiles/index.yml` — lightweight index

```yaml
version: "1"
profiles:
  - alias: hana-pyd
    path: db-profiles/hana-pyd.yml
    db_type: hana
    enabled: true
  - alias: hana-hqp
    path: db-profiles/hana-hqp.yml
    db_type: hana
    enabled: false   # set true to activate
```

### `db-profiles/<alias>.yml` — full connection profile

```yaml
alias: hana-pyd
db_type: hana

connection:
  host: axdeslthana1.central.inditex.grp
  port: 30015
  user: SAPHANADB
  password: "your-password-here"   # ⚠️ see security section
  schema: PYD
  ssl: true
  encrypt: true
  validate_cert: false
  connection_type: auto            # optional

limits:
  max_rows: 200          # hard cap on rows returned
  max_cols: 50
  query_timeout_sec: 30

tags:
  environment: des
  team: your-team
```

Template files are provided in [`catalog-example/db-profiles/`](catalog-example/db-profiles/).

---

## Local setup

### Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) installed
- Access to the private catalog GitHub repo

### Install

```bash
cd hana-multidb-mcp
uv sync --group dev
```

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GITHUB_TOKEN` | ✅ | — | GitHub PAT with `Contents: read` on the catalog repo |
| `GITHUB_OWNER` | ✅ | — | GitHub org or user owning the catalog repo |
| `GITHUB_REPO` | ✅ | — | Catalog repository name |
| `GITHUB_REF` | — | `main` | Branch, tag, or commit SHA |
| `CATALOG_PATH` | — | `db-profiles` | Directory inside the repo containing `index.yml` |
| `LOG_LEVEL` | — | `INFO` | Python log level (`DEBUG`, `INFO`, `WARNING`) |

### Run manually (for debugging)

```bash
GITHUB_TOKEN=ghp_xxx \
GITHUB_OWNER=my-org \
GITHUB_REPO=my-db-catalog \
uv run hana-multidb-mcp
```

Logs are written to **stderr**. stdout is reserved exclusively for MCP JSON-RPC messages.

---

## VS Code integration

The server entry is already added to your user-level `mcp.json` at:
`~/Library/Application Support/Code/User/mcp.json`

```json
"hana-multidb": {
  "type": "stdio",
  "command": "/Users/rubenfre/.asdf/installs/ivm-uv/0.9.7/bin/uv",
  "args": [
    "run",
    "--directory",
    "/Users/rubenfre/rubenfre/hana-multidb-mcp",
    "hana-multidb-mcp"
  ],
  "env": {
    "GITHUB_TOKEN": "${input:HANA_CATALOG_GITHUB_TOKEN}",
    "GITHUB_OWNER": "REPLACE_WITH_ORG",
    "GITHUB_REPO": "REPLACE_WITH_CATALOG_REPO",
    "GITHUB_REF": "main",
    "CATALOG_PATH": "db-profiles",
    "LOG_LEVEL": "INFO",
    "SSL_CERT_FILE": "/Users/rubenfre/.config/inditex/lde-wizard/certificate-bundle.pem"
  }
}
```

VS Code will prompt for `HANA_CATALOG_GITHUB_TOKEN` (stored securely as a session input, never written to disk).

---

## Security guardrails

### Read-only SQL enforcement

The `sql_readonly` guard runs on every `execute_query` call **before** the query reaches the database:

- **Allowed**: `SELECT`, `WITH` (CTEs), `EXPLAIN`, `SHOW`
- **Blocked**: `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `UPSERT`, all DDL (`CREATE` / `ALTER` / `DROP` / `TRUNCATE`), stored procedures (`CALL` / `EXECUTE`), privilege changes (`GRANT` / `REVOKE`), transactions (`COMMIT` / `ROLLBACK`)
- **Multi-statement protection**: any input containing `;` between statements is rejected
- **Comment injection**: SQL comments are stripped before token inspection

### Credentials in the catalog repo

Storing passwords in a git repo is a high-risk practice. If you choose to do so:

| Rule | Why |
|---|---|
| Keep the catalog repo **private** | Prevents public exposure |
| Use a **read-only fine-grained PAT** (`Contents: read`) | Limits blast radius if the token is leaked |
| Never commit the catalog repo to a public location | One accidental push exposes all passwords |
| Rotate passwords regularly | Limits the window of exposure |
| Prefer `secretRef` (env var injection) over plaintext | Recommended long-term approach |

The `list_connections` and `get_connection` tools **redact credentials** — only host, port, schema and tags are returned.

---

## Running tests

```bash
uv run pytest tests/ -v
```

Expected output: **51 passed** in < 2 seconds. No network or HANA connection required — all external calls are mocked.

---

## Next steps to continue

### 1. Create the private catalog repo (required to use the server)

```bash
# On GitHub, create a new private repo, e.g.: my-org/hana-db-catalog
# Then push the template files:
mkdir hana-db-catalog && cd hana-db-catalog
git init
cp -r /path/to/hana-multidb-mcp/catalog-example/* .
git add . && git commit -m "chore: initial catalog"
git remote add origin https://github.com/my-org/hana-db-catalog.git
git push -u origin main
```

Fill in the real password in `db-profiles/hana-pyd.yml` before pushing.

### 2. Create the GitHub PAT

1. Go to **GitHub → Settings → Developer settings → Fine-grained personal access tokens**
2. Create a token scoped to the catalog repo only
3. Permission needed: **Repository contents → Read-only**
4. Copy the token value (you will paste it when VS Code prompts for `HANA_CATALOG_GITHUB_TOKEN`)

### 3. Update `mcp.json` with the real repo coordinates

Open `~/Library/Application Support/Code/User/mcp.json` and replace:

```json
"GITHUB_OWNER": "REPLACE_WITH_ORG",
"GITHUB_REPO": "REPLACE_WITH_CATALOG_REPO",
```

with your actual GitHub org/user and repo name.

### 4. Reload the MCP server in VS Code

Open the Command Palette (`Cmd+Shift+P`) → **MCP: Restart Server** → select `hana-multidb`.

VS Code will prompt for the GitHub PAT the first time.

### 5. Verify end-to-end

In Copilot Chat, run these tool calls in sequence:

```
list_connections
→ should return your aliases with host/port metadata

ping_connection alias="hana-pyd"
→ should return {"status": "ok", "latency_ms": ...}

execute_query alias="hana-pyd" sql="SELECT 1 AS OK FROM DUMMY"
→ should return {"rows": [{"OK": 1}], "row_count": 1}

execute_query alias="hana-pyd" sql="DELETE FROM t"
→ should return an error: "DELETE is not permitted"
```

### 6. Add more connections (optional)

For each new HANA instance:

1. Create `db-profiles/<alias>.yml` in the catalog repo using the template.
2. Add an entry to `db-profiles/index.yml`.
3. Push to GitHub.
4. Call `refresh_catalog` in Copilot Chat — no restart needed.

### 7. Consider moving passwords out of git (recommended)

Replace the `password` field in each profile with a reference to a secret manager or env var injection. The long-term recommended pattern:

```yaml
connection:
  host: ...
  user: SAPHANADB
  password: "${env:HANA_PYD_PASSWORD}"   # resolved at runtime from env
```

This requires a small change to `github_loader.py` to expand `${env:VAR}` references after YAML parsing.
