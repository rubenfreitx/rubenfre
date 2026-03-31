from sap_cloud_alm_mcp.config import Settings, mask_secret


def test_mask_secret_keeps_edges() -> None:
    assert mask_secret("abcdefghi") == "abc***ghi"


def test_settings_reports_missing_fields() -> None:
    settings = Settings(
        token_url="",
        api_base_url="https://example.sap",
        client_id="",
        client_secret="",
        scopes="",
        timeout_seconds=30,
    )

    assert settings.missing_fields() == [
        "SAP_ALM_TOKEN_URL",
        "SAP_ALM_CLIENT_ID",
        "SAP_ALM_CLIENT_SECRET",
    ]
