"""
One-time OAuth bootstrap for Google Calendar MCP server.

Run this on a machine with a browser to generate token.json, then copy the
resulting token.json to the server machine (or set GOOGLE_TOKEN_JSON[_PATH]).

Usage:
  .venv/bin/python app/mcp/google-calendar-mcp/auth_bootstrap.py

Respects:
  - GOOGLE_CREDENTIALS_PATH: path to OAuth client secrets (defaults to credentials.json in this folder)

Writes:
  - token.json in this folder
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from google_auth_oauthlib.flow import InstalledAppFlow
from typing import cast


SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

HERE = Path(__file__).resolve().parent
DEFAULT_CREDENTIALS = HERE / "credentials.json"
TOKEN_PATH = HERE / "token.json"


def main() -> int:
    cred_path_env = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    cred_path = Path(cred_path_env).expanduser() if cred_path_env else DEFAULT_CREDENTIALS

    if not cred_path.exists():
        print("ERROR: credentials file not found.")
        print(f"Looked for: {cred_path}")
        print("Set GOOGLE_CREDENTIALS_PATH to your OAuth client secrets JSON path, or place")
        print(f"a 'credentials.json' next to this script: {DEFAULT_CREDENTIALS}")
        return 1

    print("Starting OAuth flow in your browser...")
    flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
    # run_local_server may return different credential implementations; cast for type checkers
    creds = cast(Any, flow.run_local_server(port=0))

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_PATH, "w") as f:
        f.write(cast(Any, creds).to_json())

    print()
    print("✅ OAuth complete. Saved:", TOKEN_PATH)
    print("You can now:")
    print("  - Copy this token.json to your server machine next to server.py, or")
    print("  - Set GOOGLE_TOKEN_JSON_PATH to its absolute path, or")
    print("  - Set GOOGLE_TOKEN_JSON to its file contents (ensure secure storage)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
