"""
hana-multidb-mcp — FastMCP server entrypoint.

Tools exposed:
  list_connections    — list all aliases from the loaded catalog (no credentials)
  get_connection      — metadata for one alias
  refresh_catalog     — reload catalog from GitHub without restart
  ping_connection     — test connectivity for an alias
  list_schemas        — list schemas in a connection
  list_tables         — list tables in a schema
  execute_query       — run a read-only SELECT/WITH query

Environment variables (all required unless marked optional):
  GITHUB_TOKEN        — PAT with Contents read on the catalog repo
  GITHUB_OWNER        — GitHub organisation or user owning the catalog repo
  GITHUB_REPO         — Catalog repository name
  GITHUB_REF          — Branch / tag / commit SHA (optional, default: main)
  CATALOG_PATH        — Path to profiles directory inside repo (optional, default: db-profiles)
  LOG_LEVEL           — Logging level (optional, default: INFO)
"""

import logging
import sys
import time

from mcp.server.fastmcp import FastMCP

from .config import Config
from .github_loader import GitHubLoader
from .guards.sql_readonly import assert_readonly
from .registry import ConnectionRegistry

logging.basicConfig(
    stream=sys.stderr,
    level=getattr(logging, Config.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

mcp = FastMCP("hana-multidb")

# ── Lazy singletons ───────────────────────────────────────────────────────────

_loader: GitHubLoader | None = None
_registry: ConnectionRegistry | None = None


def _get_loader() -> GitHubLoader:
    global _loader
    if _loader is None:
        _loader = GitHubLoader(
            token=Config.github_token,
            owner=Config.github_owner,
            repo=Config.github_repo,
            ref=Config.github_ref,
            catalog_path=Config.catalog_path,
        )
    return _loader


def _get_registry() -> ConnectionRegistry:
    global _registry
    if _registry is None:
        _registry = ConnectionRegistry()
        loader = _get_loader()
        profiles = loader.load_catalog()
        _registry.set_profiles(profiles)
    return _registry


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sanitize(profile: dict) -> dict:
    """Strip credentials — return only safe metadata."""
    conn = profile.get("connection", {})
    return {
        "alias": profile.get("alias"),
        "db_type": profile.get("db_type"),
        "host": conn.get("host"),
        "port": conn.get("port"),
        "schema": conn.get("schema"),
        "tags": profile.get("tags", {}),
        "limits": profile.get("limits", {}),
    }


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_connections() -> list[dict]:
    """
    List all database connections available in the catalog.
    Returns connection metadata only — credentials are never included.
    Use refresh_catalog() to pick up changes made in the GitHub repo.
    """
    registry = _get_registry()
    return [_sanitize(p) for p in _get_loader().get_profiles().values()]


@mcp.tool()
def get_connection(alias: str) -> dict:
    """
    Return metadata for a single connection alias.
    Raises an error if the alias is not found.
    """
    profiles = _get_registry()  # ensure catalog is loaded
    all_profiles = _get_loader().get_profiles()
    if alias not in all_profiles:
        available = ", ".join(sorted(all_profiles)) or "(none)"
        raise ValueError(f"Unknown alias '{alias}'. Available: {available}")
    return _sanitize(all_profiles[alias])


@mcp.tool()
def refresh_catalog() -> dict:
    """
    Reload the connection catalog from GitHub without restarting the server.
    Useful after adding, modifying, or removing connection profiles in the repo.
    """
    registry = _get_registry()
    loader = _get_loader()
    profiles = loader.load_catalog()
    registry.set_profiles(profiles)
    return {
        "status": "ok",
        "loaded": len(profiles),
        "aliases": sorted(profiles.keys()),
        "index_sha": loader.index_sha,
    }


@mcp.tool()
def ping_connection(alias: str) -> dict:
    """
    Test connectivity for a named database connection.
    Returns the connection status and round-trip latency in milliseconds.
    """
    registry = _get_registry()
    start = time.monotonic()
    try:
        driver = registry.get_or_connect(alias)
        alive = driver.ping()
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        return {
            "alias": alias,
            "status": "ok" if alive else "error",
            "latency_ms": elapsed_ms,
        }
    except Exception as exc:
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        logger.warning("ping_connection(%s) failed: %s", alias, exc)
        return {
            "alias": alias,
            "status": "error",
            "latency_ms": elapsed_ms,
            "error": str(exc),
        }


@mcp.tool()
def list_schemas(alias: str) -> dict:
    """
    List all schemas visible to the configured user in the given connection.
    """
    registry = _get_registry()
    driver = registry.get_or_connect(alias)
    schemas = driver.list_schemas()
    return {"alias": alias, "schemas": schemas, "count": len(schemas)}


@mcp.tool()
def list_tables(alias: str, schema: str) -> dict:
    """
    List tables (name, type, comment) in a specific schema of the given connection.
    """
    registry = _get_registry()
    driver = registry.get_or_connect(alias)
    tables = driver.list_tables(schema)
    return {"alias": alias, "schema": schema, "tables": tables, "count": len(tables)}


@mcp.tool()
def execute_query(alias: str, sql: str, max_rows: int = 200) -> dict:
    """
    Execute a read-only SQL query against the named database connection.

    Rules:
    - Only SELECT and WITH statements are permitted.
    - DML (INSERT / UPDATE / DELETE), DDL, CALL and multi-statement inputs are blocked.
    - Results are capped at max_rows rows (default 200, hard cap 1000).
    - The profile's query_timeout_sec limit applies at connection level.

    Returns columns, rows (as a list of dicts), row_count, and a truncated flag.
    """
    assert_readonly(sql)

    max_rows = max(1, min(max_rows, 1000))

    registry = _get_registry()
    profile = _get_loader().get_profiles().get(alias, {})
    limits = profile.get("limits", {})
    effective_max_rows = min(max_rows, int(limits.get("max_rows", 200)))
    timeout_sec = int(limits.get("query_timeout_sec", 30))

    driver = registry.get_or_connect(alias)
    result = driver.execute_read_query(
        sql, max_rows=effective_max_rows, timeout_sec=timeout_sec
    )
    result["alias"] = alias
    return result


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
