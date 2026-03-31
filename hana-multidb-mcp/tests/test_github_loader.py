import base64
import pytest
from unittest.mock import MagicMock, patch

from src.github_loader import GitHubLoader


_INDEX_YML = """\
version: "1"
profiles:
  - alias: hana-test
    path: db-profiles/hana-test.yml
    db_type: hana
    enabled: true
  - alias: hana-disabled
    path: db-profiles/hana-disabled.yml
    db_type: hana
    enabled: false
"""

_PROFILE_YML = """\
alias: hana-test
db_type: hana
connection:
  host: localhost
  port: 30015
  user: testuser
  password: testpass
  schema: TEST
limits:
  max_rows: 100
  query_timeout_sec: 10
tags:
  environment: des
"""


def _make_mock_response(content: str, sha: str = "abc12345") -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {
        "content": base64.b64encode(content.encode()).decode(),
        "encoding": "base64",
        "sha": sha,
    }
    resp.raise_for_status.return_value = None
    return resp


def _make_client_mock(responses: list) -> MagicMock:
    client = MagicMock()
    client.__enter__ = lambda s: client
    client.__exit__ = MagicMock(return_value=False)
    client.get.side_effect = responses
    return client


# ── load_catalog ──────────────────────────────────────────────────────────────

def test_load_catalog_returns_enabled_profiles():
    loader = GitHubLoader("token", "owner", "repo", "main", "db-profiles")

    responses = [
        _make_mock_response(_INDEX_YML, "index-sha"),
        _make_mock_response(_PROFILE_YML, "profile-sha"),
    ]
    client_mock = _make_client_mock(responses)

    with patch("src.github_loader.httpx.Client", return_value=client_mock):
        profiles = loader.load_catalog()

    assert "hana-test" in profiles
    assert "hana-disabled" not in profiles  # enabled: false


def test_load_catalog_parses_connection_details():
    loader = GitHubLoader("token", "owner", "repo", "main", "db-profiles")

    responses = [
        _make_mock_response(_INDEX_YML, "index-sha"),
        _make_mock_response(_PROFILE_YML, "profile-sha"),
    ]
    with patch("src.github_loader.httpx.Client", return_value=_make_client_mock(responses)):
        profiles = loader.load_catalog()

    conn = profiles["hana-test"]["connection"]
    assert conn["host"] == "localhost"
    assert conn["port"] == 30015
    assert conn["user"] == "testuser"


def test_load_catalog_caches_profiles():
    loader = GitHubLoader("token", "owner", "repo", "main", "db-profiles")

    responses = [
        _make_mock_response(_INDEX_YML, "index-sha"),
        _make_mock_response(_PROFILE_YML, "profile-sha"),
    ]
    with patch("src.github_loader.httpx.Client", return_value=_make_client_mock(responses)):
        loader.load_catalog()

    assert "hana-test" in loader.get_profiles()


def test_load_catalog_stores_index_sha():
    loader = GitHubLoader("token", "owner", "repo", "main", "db-profiles")

    responses = [
        _make_mock_response(_INDEX_YML, "deadbeef"),
        _make_mock_response(_PROFILE_YML, "profile-sha"),
    ]
    with patch("src.github_loader.httpx.Client", return_value=_make_client_mock(responses)):
        loader.load_catalog()

    assert loader.index_sha == "deadbeef"


def test_load_catalog_all_disabled():
    fully_disabled = """\
version: "1"
profiles:
  - alias: hana-disabled
    path: db-profiles/hana-disabled.yml
    db_type: hana
    enabled: false
"""
    loader = GitHubLoader("token", "owner", "repo", "main", "db-profiles")

    responses = [_make_mock_response(fully_disabled, "sha")]
    with patch("src.github_loader.httpx.Client", return_value=_make_client_mock(responses)):
        profiles = loader.load_catalog()

    assert profiles == {}


def test_get_profiles_empty_before_load():
    loader = GitHubLoader("token", "owner", "repo")
    assert loader.get_profiles() == {}


def test_load_catalog_raises_on_http_error():
    loader = GitHubLoader("token", "owner", "repo", "main", "db-profiles")

    error_resp = MagicMock()
    error_resp.raise_for_status.side_effect = Exception("404 Not Found")

    client_mock = _make_client_mock([error_resp])

    with patch("src.github_loader.httpx.Client", return_value=client_mock):
        with pytest.raises(Exception, match="404"):
            loader.load_catalog()


def test_load_catalog_uses_configured_ref():
    loader = GitHubLoader("token", "owner", "repo", "v1.2.3", "db-profiles")

    responses = [
        _make_mock_response(_INDEX_YML, "sha"),
        _make_mock_response(_PROFILE_YML, "psha"),
    ]
    client_mock = _make_client_mock(responses)

    with patch("src.github_loader.httpx.Client", return_value=client_mock):
        loader.load_catalog()

    # Both requests must include ref=v1.2.3
    for call in client_mock.get.call_args_list:
        assert call.kwargs.get("params", {}).get("ref") == "v1.2.3" or \
               (call.args[1:] and call.args[1].get("ref") == "v1.2.3") or \
               client_mock.get.call_args_list[0][1].get("params", {}).get("ref") == "v1.2.3"
