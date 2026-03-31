"""
Loads the connection catalog from a GitHub repository.

Catalog layout expected in the repo:
  {catalog_path}/
    index.yml          — lists all profiles with alias + path + enabled flag
    hana-pyd.yml       — full connection profile for alias "hana-pyd"
    hana-hqp.yml       — ...

Index schema (index.yml):
  version: "1"
  profiles:
    - alias: hana-pyd
      path: db-profiles/hana-pyd.yml
      db_type: hana
      enabled: true
"""

import base64
import logging
from typing import Optional

import httpx
import yaml

logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com"


class GitHubLoader:

    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
        ref: str = "main",
        catalog_path: str = "db-profiles",
    ) -> None:
        self._token = token
        self._owner = owner
        self._repo = repo
        self._ref = ref
        self._catalog_path = catalog_path.rstrip("/")
        self._profiles: dict[str, dict] = {}
        self._index_sha: Optional[str] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _fetch_file(self, path: str) -> tuple[str, str]:
        """Fetch a single file from the repo. Returns (decoded_content, sha)."""
        url = (
            f"{_GITHUB_API}/repos/{self._owner}/{self._repo}"
            f"/contents/{path}"
        )
        params = {"ref": self._ref}
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, headers=self._headers(), params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("encoding") != "base64":
            raise ValueError(
                f"Unexpected encoding '{data.get('encoding')}' for {path}. "
                "Only base64-encoded files are supported."
            )

        content = base64.b64decode(data["content"]).decode("utf-8")
        return content, data["sha"]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_catalog(self) -> dict[str, dict]:
        """
        Fetch the index and all enabled profiles from GitHub.
        Returns a dict keyed by alias.
        Replaces any previously cached profiles.
        """
        index_path = f"{self._catalog_path}/index.yml"
        logger.info("Loading catalog index from %s@%s:%s", self._owner + "/" + self._repo, self._ref, index_path)

        index_content, index_sha = self._fetch_file(index_path)
        index = yaml.safe_load(index_content)

        profiles: dict[str, dict] = {}
        for entry in index.get("profiles", []):
            if not entry.get("enabled", True):
                logger.debug("Skipping disabled profile: %s", entry.get("alias"))
                continue

            alias = entry["alias"]
            profile_path = entry["path"]

            profile_content, profile_sha = self._fetch_file(profile_path)
            profile = yaml.safe_load(profile_content)
            profiles[alias] = profile
            logger.info("Loaded profile: %s (sha=%s)", alias, profile_sha[:8])

        self._profiles = profiles
        self._index_sha = index_sha
        logger.info("Catalog loaded: %d profiles", len(profiles))
        return profiles

    def get_profiles(self) -> dict[str, dict]:
        """Return the currently cached profiles (may be empty before first load)."""
        return self._profiles

    @property
    def index_sha(self) -> Optional[str]:
        return self._index_sha
