"""
Read-only SQL guardrail.

Permits: SELECT, WITH, EXPLAIN, SHOW
Blocks:  All DML (INSERT / UPDATE / DELETE / MERGE / UPSERT),
         DDL (CREATE / ALTER / DROP / TRUNCATE),
         stored procedures (CALL / EXECUTE / EXEC),
         privilege changes (GRANT / REVOKE),
         transactions (COMMIT / ROLLBACK / SET),
         and multi-statement inputs (;).
"""

import re

_ALLOWED_FIRST_TOKENS = {"SELECT", "WITH", "EXPLAIN", "SHOW"}

_BLOCKED_FIRST_TOKENS = {
    "INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT",
    "CREATE", "ALTER", "DROP", "TRUNCATE",
    "CALL", "EXECUTE", "EXEC",
    "GRANT", "REVOKE",
    "COMMIT", "ROLLBACK", "SET",
}


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", "", sql)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql.strip()


def assert_readonly(sql: str) -> None:
    """Raise ValueError if *sql* is not a safe read-only statement."""
    cleaned = _strip_comments(sql)

    if not cleaned:
        raise ValueError("Empty SQL statement.")

    # Strip a single trailing semicolon, then reject any remaining semicolons.
    stripped = cleaned.rstrip(";").rstrip()
    if ";" in stripped:
        raise ValueError(
            "Multiple statements are not allowed. "
            "Submit one query at a time."
        )

    tokens = re.split(r"\s+", stripped, maxsplit=1)
    first = tokens[0].upper()

    if first in _BLOCKED_FIRST_TOKENS:
        raise ValueError(
            f"Statement type '{first}' is not permitted. "
            "Only read-only SELECT / WITH / EXPLAIN / SHOW queries are allowed."
        )

    if first not in _ALLOWED_FIRST_TOKENS:
        raise ValueError(
            f"Unrecognised statement type '{first}'. "
            "Only SELECT, WITH, EXPLAIN and SHOW are permitted."
        )
