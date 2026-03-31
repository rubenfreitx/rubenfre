from abc import ABC, abstractmethod


class BaseDriver(ABC):

    @abstractmethod
    def connect(self, profile: dict) -> None:
        """Establish a connection using the given connection profile."""

    @abstractmethod
    def ping(self) -> bool:
        """Return True if the connection is alive."""

    @abstractmethod
    def list_schemas(self) -> list[str]:
        """Return all schema names available to the connected user."""

    @abstractmethod
    def list_tables(self, schema: str) -> list[dict]:
        """Return table metadata for the given schema."""

    @abstractmethod
    def execute_read_query(self, sql: str, max_rows: int, timeout_sec: int) -> dict:
        """Execute a read-only SQL statement and return rows as a dict."""

    @abstractmethod
    def close(self) -> None:
        """Release the database connection."""
