"""Databricks Model Serving client — fire-and-forget trigger."""

import os
import threading
import time

import httpx

from BE.settings import get_settings
from BE.utils.logger import logger

TRIGGER_TIMEOUT_SECONDS = 120

# Cached token with expiry
_token_cache = {"token": "", "expires_at": 0.0}
_TOKEN_REFRESH_BUFFER = 300  # refresh 5 min before expiry


def _get_auth_token() -> str:
    """Get auth token — PAT for local dev, OAuth with caching for Databricks Apps."""
    settings = get_settings()
    if settings.DATABRICKS_TOKEN:
        return settings.DATABRICKS_TOKEN

    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - _TOKEN_REFRESH_BUFFER:
        return _token_cache["token"]

    try:
        from databricks.sdk import WorkspaceClient
        wc = WorkspaceClient(
            host=settings.DATABRICKS_HOST,
            client_id=os.environ.get("DATABRICKS_CLIENT_ID"),
            client_secret=os.environ.get("DATABRICKS_CLIENT_SECRET"),
        )
        token_obj = wc.config.oauth_token()
        token = token_obj.access_token if hasattr(token_obj, "access_token") else str(token_obj)

        expiry = getattr(token_obj, "expiry", None)
        if expiry and hasattr(expiry, "timestamp"):
            _token_cache["expires_at"] = expiry.timestamp()
        else:
            _token_cache["expires_at"] = now + 3600

        _token_cache["token"] = token
        return token
    except Exception as e:
        logger.error("Failed to get OAuth token for DatabricksClient: %s", str(e))
        return _token_cache["token"] or ""


class DatabricksClient:
    """Client for triggering the Databricks serving endpoint."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.DATABRICKS_HOST.rstrip("/")
        self.endpoint_name = settings.DATABRICKS_SERVING_ENDPOINT
        self.url = f"{self.base_url}/serving-endpoints/{self.endpoint_name}/invocations"

    def _do_trigger(self, payload: dict) -> None:
        """Actual HTTP call — runs in a background thread."""
        token = _get_auth_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=TRIGGER_TIMEOUT_SECONDS) as client:
                response = client.post(self.url, json=payload, headers=headers)

            if response.status_code in (200, 202):
                logger.info(
                    "Databricks endpoint triggered: endpoint=%s, status=%d",
                    self.endpoint_name, response.status_code
                )
            else:
                logger.error(
                    "Databricks endpoint error: endpoint=%s, status=%d, body=%s",
                    self.endpoint_name, response.status_code, response.text[:500]
                )

        except httpx.TimeoutException:
            logger.error("Databricks endpoint timed out: endpoint=%s", self.endpoint_name)
        except Exception:
            logger.exception("Databricks endpoint trigger failed: endpoint=%s", self.endpoint_name)

    def trigger(self, payload: dict) -> bool:
        """Fire-and-forget: dispatch to a background thread and return immediately."""
        thread = threading.Thread(target=self._do_trigger, args=(payload,), daemon=True)
        thread.start()
        logger.info(
            "Databricks endpoint trigger dispatched in background: endpoint=%s",
            self.endpoint_name,
        )
        return True
