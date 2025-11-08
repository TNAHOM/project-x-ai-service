"""
One-time OAuth bootstrap for Google Calendar MCP server.

Run this on a machine with a browser to generate token.json, then copy the
resulting token.json to the server machine (or set GOOGLE_TOKEN_JSON[_PATH]).

Usage:
  .venv/bin/python app/mcp/google_calendar_mcp/auth_bootstrap.py

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
from dotenv import load_dotenv
from app.core.logger import get_logger

logger = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

# get path from enviroment variable
load_dotenv(".env")


def main() -> int:
    logger.info("Google Calendar MCP OAuth Bootstrap")
    cred_path_env = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    if not cred_path_env:
        raise ValueError("GOOGLE_CREDENTIALS_PATH environment variable not set.")
    cred_path = Path(cred_path_env).expanduser()

    if not cred_path.exists():
        logger.error("ERROR: credentials file not found.")
        logger.error(f"Looked for cred_path:  {cred_path}")
        logger.error("Set GOOGLE_CREDENTIALS_PATH to your OAuth client secrets JSON path, or place")
        logger.error(f"a 'credentials.json' next to this script: {cred_path}")
        return 1

    logger.info("Starting OAuth flow in your browser...")
    flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
    # run_local_server may return different credential implementations; cast for type checkers
    creds = cast(Any, flow.run_local_server(port=0))

    TOKEN_PATH = os.environ.get("GOOGLE_TOKEN_JSON_PATH")
    if not TOKEN_PATH:
      raise ValueError("GOOGLE_TOKEN_JSON_PATH environment variable not set.")
    
    TOKEN_PATH = Path(TOKEN_PATH).expanduser()
    with open(TOKEN_PATH, "w") as f:
        f.write(cast(Any, creds).to_json())

    logger.info("✅ OAuth complete. Saved: %s", TOKEN_PATH)
    logger.info("You can now:")
    logger.info("  - Copy this token.json to your server machine next to server.py, or")
    logger.info("  - Set GOOGLE_TOKEN_JSON_PATH to its absolute path, or")
    logger.info("  - Set GOOGLE_TOKEN_JSON to its file contents (ensure secure storage)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
