"""
In-memory connection registry.

Maintains one live driver instance per alias. Connections are created lazily
on first use. Connections whose aliases have been removed from the catalog are
closed automatically on the next set_profiles() call.
"""

import logging

from .drivers.base import BaseDriver

logger = logging.getLogger(__name__)


class ConnectionRegistry:

    def __init__(self) -> None:
        self._profiles: dict[str, dict] = {}
        self._connections: dict[str, BaseDriver] = {}

    # ------------------------------------------------------------------
    # Catalog management
    # ------------------------------------------------------------------

    def set_profiles(self, profiles: dict[str, dict]) -> None:
        """
        Update the registry with a new set of profiles.
        Closes any open connections whose aliases are no longer present.
        """
        removed = set(self._profiles.keys()) - set(profiles.keys())
        for alias in removed:
            logger.info("Profile removed; closing connection: %s", alias)
            self._close_one(alias)
        self._profiles = profiles

    # ------------------------------------------------------------------
    # Connection access
    # ------------------------------------------------------------------

    def get_or_connect(self, alias: str) -> BaseDriver:
        """
        Return a live driver for *alias*, creating the connection if needed.
        Raises KeyError for unknown aliases.
        Raises RuntimeError / connection errors from the driver on failure.
        """
        if alias not in self._profiles:
            available = ", ".join(sorted(self._profiles)) or "(none)"
            raise KeyError(
                f"Unknown connection alias '{alias}'. "
                f"Available: {available}"
            )

        if alias not in self._connections:
            profile = self._profiles[alias]
            driver = self._create_driver(profile)
            driver.connect(profile)
            self._connections[alias] = driver
            logger.info("Connection established: %s", alias)

        return self._connections[alias]

    def reconnect(self, alias: str) -> BaseDriver:
        """Force-close and re-open the connection for *alias*."""
        self._close_one(alias)
        return self.get_or_connect(alias)

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    def close(self, alias: str) -> None:
        self._close_one(alias)

    def close_all(self) -> None:
        for alias in list(self._connections.keys()):
            self._close_one(alias)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _close_one(self, alias: str) -> None:
        driver = self._connections.pop(alias, None)
        if driver is not None:
            try:
                driver.close()
            except Exception as exc:
                logger.warning("Error closing connection '%s': %s", alias, exc)
            logger.debug("Connection closed: %s", alias)

    @staticmethod
    def _create_driver(profile: dict) -> BaseDriver:
        db_type = profile.get("db_type", "hana").lower()
        if db_type == "hana":
            from .drivers.hana import HanaDriver
            return HanaDriver()
        raise ValueError(
            f"Unsupported db_type '{db_type}'. "
            "Currently supported: hana"
        )
