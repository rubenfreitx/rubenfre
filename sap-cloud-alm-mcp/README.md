# SAP Cloud ALM MCP

Minimal Python MCP server for SAP Cloud ALM.

## Included tools

- `health_summary`: Reports server status and sanitized configuration.
- `validate_environment`: Validates required SAP Cloud ALM environment variables.
- `get_access_token`: Requests an OAuth2 access token using client credentials.
- `api_get`: Executes a GET request against SAP Cloud ALM.

## Requirements

- Python 3.11+
- SAP Cloud ALM OAuth client credentials

## Configuration

Copy `.env.example` values into your preferred environment source and set:

- `SAP_ALM_TOKEN_URL`
- `SAP_ALM_API_BASE_URL`
- `SAP_ALM_CLIENT_ID`
- `SAP_ALM_CLIENT_SECRET`
- `SAP_ALM_SCOPES` (optional)
- `SAP_ALM_TIMEOUT_SECONDS` (optional)

## Install

```bash
python -m pip install -e .
python -m pip install -e .[dev]
```

## Run locally

```bash
PYTHONPATH=src python -m sap_cloud_alm_mcp
```

## Debug in VS Code

- Create a `.env` file from `.env.example` and fill in your SAP Cloud ALM credentials.
- Use the `Debug SAP Cloud ALM MCP` launch configuration to start the server with breakpoints.
- Use the `Run SAP Cloud ALM MCP` launch configuration to launch it without the debugger attached.

## VS Code MCP configuration

The project includes `.vscode/mcp.json` so the server can be attached in a compatible MCP-enabled client configuration.

## Notes

- `get_access_token` returns the raw token response. Treat it as sensitive output.
- `api_get` accepts either a relative API path such as `/operations/v1/events` or a fully qualified HTTPS URL.
