import datetime
import decimal
import logging

from .base import BaseDriver

logger = logging.getLogger(__name__)


class HanaDriver(BaseDriver):

    def __init__(self) -> None:
        self._conn = None

    def connect(self, profile: dict) -> None:
        try:
            from hdbcli import dbapi
        except ImportError as exc:
            raise RuntimeError(
                "hdbcli is required for HANA connections. "
                "Add hdbcli>=2.19 to your dependencies."
            ) from exc

        conn_cfg = profile["connection"]
        limits = profile.get("limits", {})
        timeout_ms = int(limits.get("query_timeout_sec", 30)) * 1000

        kwargs: dict = {
            "address": conn_cfg["host"],
            "port": int(conn_cfg["port"]),
            "user": conn_cfg["user"],
            "password": conn_cfg["password"],
            "statementTimeout": timeout_ms,
        }

        if conn_cfg.get("ssl", False):
            kwargs["encrypt"] = conn_cfg.get("encrypt", True)
            kwargs["sslValidateCertificate"] = conn_cfg.get("validate_cert", False)

        if conn_cfg.get("database_name"):
            kwargs["databaseName"] = conn_cfg["database_name"]

        if conn_cfg.get("connection_type"):
            kwargs["connectionType"] = conn_cfg["connection_type"]

        self._conn = dbapi.connect(**kwargs)
        logger.debug("HANA connected: %s:%s", conn_cfg["host"], conn_cfg["port"])

    def _require_conn(self) -> object:
        if self._conn is None:
            raise RuntimeError("Driver is not connected. Call connect() first.")
        return self._conn

    def ping(self) -> bool:
        try:
            cursor = self._require_conn().cursor()
            cursor.execute("SELECT 1 AS OK FROM DUMMY")
            cursor.close()
            return True
        except Exception:
            return False

    def list_schemas(self) -> list[str]:
        cursor = self._require_conn().cursor()
        cursor.execute(
            "SELECT SCHEMA_NAME FROM SYS.SCHEMAS ORDER BY SCHEMA_NAME"
        )
        rows = cursor.fetchall()
        cursor.close()
        return [r[0] for r in rows]

    def list_tables(self, schema: str) -> list[dict]:
        cursor = self._require_conn().cursor()
        cursor.execute(
            "SELECT TABLE_NAME, TABLE_TYPE, COMMENTS "
            "FROM SYS.TABLES "
            "WHERE SCHEMA_NAME = ? "
            "ORDER BY TABLE_NAME",
            (schema,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [
            {"table_name": r[0], "table_type": r[1], "comment": r[2]}
            for r in rows
        ]

    def execute_read_query(
        self, sql: str, max_rows: int = 200, timeout_sec: int = 30
    ) -> dict:
        cursor = self._require_conn().cursor()
        cursor.execute(sql)

        cols = [desc[0] for desc in cursor.description] if cursor.description else []
        raw_rows = cursor.fetchmany(max_rows)
        cursor.close()

        rows = []
        for raw_row in raw_rows:
            row: dict = {}
            for i, col in enumerate(cols):
                val = raw_row[i]
                if isinstance(val, decimal.Decimal):
                    val = float(val)
                elif isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
                    val = val.isoformat()
                elif isinstance(val, bytes):
                    val = val.hex()
                elif val is not None and not isinstance(val, (str, int, float, bool)):
                    val = str(val)
                row[col] = val
            rows.append(row)

        return {
            "columns": cols,
            "rows": rows,
            "row_count": len(rows),
            "truncated": len(raw_rows) == max_rows,
        }

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            finally:
                self._conn = None
