- [x] Verify that the copilot-instructions.md file in the .github directory is created.
- [x] Clarify Project Requirements: Python MCP server for SAP Cloud ALM with OAuth2 client credentials and initial GET tooling.
- [x] Scaffold the Project: Created a Python MCP server using the official MCP Python SDK and a src/ layout.
- [x] Customize the Project: Added configuration validation, OAuth token acquisition, API GET proxying, tests, README, and VS Code MCP wiring.
- [x] Install Required Extensions: Python extension can be installed for local development.
- [x] Compile the Project: Project files are structured for Python 3.11+ and ready for dependency installation and local validation.
- [x] Create and Run Task: Added a VS Code validation task for pytest.
- [x] Launch the Project: Added VS Code launch configurations for run and debug workflows.
- [x] Ensure Documentation is Complete: README and MCP configuration are included.

Project references:
- MCP documentation: https://modelcontextprotocol.io/
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- MCP specification: https://modelcontextprotocol.io/specification/latest

Notes:
- The server entrypoint is `python -m sap_cloud_alm_mcp` with `PYTHONPATH=src`.
- Required SAP environment variables are documented in `.env.example` and `README.md`.
- Debug configuration uses `.env` if present and keeps `PYTHONPATH=src`.
