# SAP Cloud ALM MCP

Minimal Python MCP server for SAP Cloud ALM.

## What This Project Does

This project exposes SAP Cloud ALM access through an MCP server using stdio transport.
It includes OAuth2 client-credentials authentication and a generic GET tool for SAP Cloud ALM APIs.

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

## Validate

```bash
PYTHONPATH=src python -m pytest -q
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

## MCP Documentation

Use these sources as the official baseline for MCP behavior and compatibility:

- MCP documentation portal: https://modelcontextprotocol.io/
- MCP specification (protocol contracts): https://modelcontextprotocol.io/specification/latest
- MCP Python SDK (server/client implementation): https://github.com/modelcontextprotocol/python-sdk
- MCP maintained servers catalog: https://github.com/modelcontextprotocol/servers
- MCP registry: https://github.com/modelcontextprotocol/registry
- MCP Inspector (manual test and debugging): https://github.com/modelcontextprotocol/inspector

### MCP Concepts To Review

- Transport model: stdio and client-server lifecycle.
- Server primitives: tools, resources, and prompts.
- Tool design: explicit input schema, stable outputs, actionable errors.
- Authentication boundaries: never leak secrets in logs or tool results.
- Compatibility: keep SDK version aligned with spec and client capabilities.

### How This Repository Maps To MCP

- Server entrypoint: `src/sap_cloud_alm_mcp/server.py`
- Tool registration: `@mcp.tool()` functions in `server.py`
- SAP API client logic: `src/sap_cloud_alm_mcp/client.py`
- Runtime config and validation: `src/sap_cloud_alm_mcp/config.py`
- VS Code MCP wiring: `.vscode/mcp.json`

## SAP Cloud ALM Notes

- OAuth flow is `client_credentials`.
- Access token is obtained via `SAP_ALM_TOKEN_URL`.
- API base URL is `SAP_ALM_API_BASE_URL`.
- If your tenant requires a scope, set `SAP_ALM_SCOPES`.
- Keep credentials only in environment variables, never hardcoded.

## Next Steps (Remote Checklist)

When you come back to continue this project, follow this order:

1. Clone and open the repository/folder in VS Code.
2. Copy `.env.example` to `.env`.
3. Fill real values for:
   - `SAP_ALM_TOKEN_URL`
   - `SAP_ALM_API_BASE_URL`
   - `SAP_ALM_CLIENT_ID`
   - `SAP_ALM_CLIENT_SECRET`
   - `SAP_ALM_SCOPES` (if required)
4. Install dependencies:
   - `python -m pip install -e .`
   - `python -m pip install -e .[dev]`
5. Run tests: `PYTHONPATH=src python -m pytest -q`.
6. Start MCP server:
   - VS Code launch: `Debug SAP Cloud ALM MCP` or `Run SAP Cloud ALM MCP`
   - or terminal: `PYTHONPATH=src python -m sap_cloud_alm_mcp`
7. Validate basic tools in this order:
   - `health_summary`
   - `validate_environment`
   - `get_access_token`
   - `api_get`
8. Test one real SAP Cloud ALM endpoint and capture expected response contract.
9. Create specific MCP tools for your top endpoints (instead of generic `api_get`).
10. Add tests for each new tool and keep `pytest` green.

## Next Steps (Implementation Backlog)

- Add support for custom headers required by specific SAP Cloud ALM APIs.
- Add optional proxy and custom CA certificate settings for corporate networks.
- Add pagination helpers for list endpoints.
- Add endpoint-specific typed tools (alerts, events, deployments, etc.).
- Add structured error mapping (401/403/404/429/5xx).
- Add integration tests with mocked SAP responses.

## Notes

- `get_access_token` returns the raw token response. Treat it as sensitive output.
- `api_get` accepts either a relative API path such as `/operations/v1/events` or a fully qualified HTTPS URL.
