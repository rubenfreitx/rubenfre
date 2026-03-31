import os


class Config:
    github_token: str = os.environ.get("GITHUB_TOKEN", "")
    github_owner: str = os.environ.get("GITHUB_OWNER", "")
    github_repo: str = os.environ.get("GITHUB_REPO", "")
    github_ref: str = os.environ.get("GITHUB_REF", "main")
    catalog_path: str = os.environ.get("CATALOG_PATH", "db-profiles")
    log_level: str = os.environ.get("LOG_LEVEL", "INFO").upper()
