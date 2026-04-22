"""Shared auth helper — PAT for local dev, OAuth for Databricks Apps."""

from __future__ import annotations

import os
import time

_token_cache = {"token": "", "expires_at": 0.0}
_TOKEN_REFRESH_BUFFER = 300


def get_auth_token() -> str:
    """Get a valid Databricks auth token.

    Uses PAT (DATABRICKS_TOKEN env var) if available.
    Falls back to OAuth via service principal (DATABRICKS_CLIENT_ID + SECRET).
    Caches the OAuth token and auto-refreshes before expiry.
    """
    # PAT mode
    pat = os.environ.get("DATABRICKS_TOKEN", "")
    if pat:
        return pat

    # OAuth mode — check cache
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - _TOKEN_REFRESH_BUFFER:
        return _token_cache["token"]

    # Refresh OAuth token
    try:
        from databricks.sdk import WorkspaceClient
        host = os.environ.get("DATABRICKS_HOST", "")
        client_id = os.environ.get("DATABRICKS_CLIENT_ID", "")
        client_secret = os.environ.get("DATABRICKS_CLIENT_SECRET", "")
        wc = WorkspaceClient(host=host, client_id=client_id, client_secret=client_secret)
        token_obj = wc.config.oauth_token()
        token = token_obj.access_token if hasattr(token_obj, "access_token") else str(token_obj)
        expiry = getattr(token_obj, "expiry", None)
        if expiry and hasattr(expiry, "timestamp"):
            _token_cache["expires_at"] = expiry.timestamp()
        else:
            _token_cache["expires_at"] = now + 3600
        _token_cache["token"] = token
        return token
    except Exception:
        return _token_cache["token"] or ""
