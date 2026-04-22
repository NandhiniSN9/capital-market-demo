"""Genie MCP data retrieval repository — async implementation."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from settings import get_settings
from utils.exceptions import ERR_DATA_RETRIEVAL, DataRetrievalError
from utils.logger import logger

_GENIE_START_PATH = "/api/2.0/genie/spaces/{space_id}/start-conversation"
_GENIE_MESSAGE_PATH = "/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages"
_GENIE_RESULT_PATH = (
    "/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}"
    "/messages/{message_id}/attachments/{attachment_id}/query-result"
)
_POLL_INTERVAL_S = 2.0
_MAX_POLL_ATTEMPTS = 30


class GenieRepository:
    """Wraps the Databricks Genie REST API — all I/O is async."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._base_url = self._settings.databricks_host.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {self._settings.databricks_token}",
            "Content-Type": "application/json",
        }

    async def query(self, natural_language_query: str) -> list[dict[str, Any]]:
        """Send a natural-language query to Genie and return result rows."""
        space_id = self._settings.rfq_intelligence_genie_space_id
        if not space_id:
            raise DataRetrievalError(
                "RFQ_INTELLIGENCE_GENIE_SPACE_ID is not configured",
                error_code=ERR_DATA_RETRIEVAL,
            )
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._settings.llm_timeout) as client:
                conv_id, msg_id = await self._start_conversation(
                    client, space_id, natural_language_query
                )
                rows = await self._poll_for_result(client, space_id, conv_id, msg_id)
            logger.info("Genie query completed", extra={
                "rows": len(rows),
                "elapsed_ms": round((time.monotonic() - start) * 1000, 2),
            })
            return rows
        except DataRetrievalError:
            raise
        except Exception as exc:
            raise DataRetrievalError(
                f"Genie query failed: {exc}", error_code=ERR_DATA_RETRIEVAL
            ) from exc

    async def _start_conversation(
        self, client: httpx.AsyncClient, space_id: str, query: str
    ) -> tuple[str, str]:
        url = self._base_url + _GENIE_START_PATH.format(space_id=space_id)
        resp = await client.post(url, headers=self._headers, json={"content": query})
        resp.raise_for_status()
        data = resp.json()
        # Response may nest IDs inside "conversation"/"message" objects or at top level
        conv_id = data.get("conversation_id") or data.get("conversation", {}).get("id", "")
        msg_id = data.get("message_id") or data.get("message", {}).get("id", "")
        if not conv_id or not msg_id:
            raise DataRetrievalError(
                f"Genie start-conversation returned unexpected structure: {list(data.keys())}",
                error_code=ERR_DATA_RETRIEVAL,
            )
        return conv_id, msg_id

    async def _poll_for_result(
        self, client: httpx.AsyncClient, space_id: str, conv_id: str, msg_id: str,
    ) -> list[dict[str, Any]]:
        msg_url = self._base_url + _GENIE_MESSAGE_PATH.format(
            space_id=space_id, conversation_id=conv_id
        ) + f"/{msg_id}"
        for _ in range(_MAX_POLL_ATTEMPTS):
            resp = await client.get(msg_url, headers=self._headers)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "")
            if status in ("COMPLETED", "completed"):
                break
            if status in ("FAILED", "failed"):
                raise DataRetrievalError(
                    f"Genie query failed: {data}", error_code=ERR_DATA_RETRIEVAL
                )
            await asyncio.sleep(_POLL_INTERVAL_S)
        else:
            raise DataRetrievalError("Genie query timed out", error_code=ERR_DATA_RETRIEVAL)

        # Extract attachment_id from the completed message's attachments.
        # The Genie API nests attachments under the "attachments" key.
        # Each attachment with a SQL query has an "attachment_id" and a
        # nested "query" dict.  Some API versions use "attachment.query"
        # while others place "query" at the top level of the attachment
        # object.  We also fall back to any attachment that carries an id
        # when no "query" key is found, since the result endpoint will
        # still return the data.
        attachments = data.get("attachments") or []
        attachment_id = None

        logger.debug("Genie message attachments payload", extra={
            "conversation_id": conv_id,
            "message_id": msg_id,
            "attachment_keys": [
                {k: type(v).__name__ for k, v in att.items()} for att in attachments
            ] if attachments else "empty",
        })

        for att in attachments:
            # Primary: look for a "query" dict (contains the SQL statement)
            if att.get("query"):
                attachment_id = att.get("attachment_id") or att.get("id")
                break
            # Some API versions nest under "attachment" → "query"
            inner = att.get("attachment", {})
            if isinstance(inner, dict) and inner.get("query"):
                attachment_id = att.get("attachment_id") or att.get("id")
                break

        # Fallback: if no "query" key was found but attachments exist,
        # pick the first attachment that has an id — the query-result
        # endpoint can still return data for it.
        if not attachment_id and attachments:
            for att in attachments:
                candidate = att.get("attachment_id") or att.get("id")
                if candidate:
                    attachment_id = candidate
                    logger.info("Using fallback attachment_id (no 'query' key found)", extra={
                        "attachment_id": attachment_id,
                        "conversation_id": conv_id,
                        "message_id": msg_id,
                    })
                    break

        if not attachment_id:
            # No query attachment — Genie responded with text only, no SQL result
            logger.info("Genie returned no query attachment", extra={
                "conversation_id": conv_id, "message_id": msg_id,
                "num_attachments": len(attachments),
                "raw_attachment_keys": [list(a.keys()) for a in attachments],
            })
            return []

        result_url = self._base_url + _GENIE_RESULT_PATH.format(
            space_id=space_id, conversation_id=conv_id,
            message_id=msg_id, attachment_id=attachment_id,
        )
        resp = await client.get(result_url, headers=self._headers)
        resp.raise_for_status()
        result = resp.json()

        logger.debug("Genie query-result payload keys", extra={
            "top_keys": list(result.keys()),
            "conversation_id": conv_id,
        })

        # The result schema can vary across Genie API versions:
        #   v1: manifest.schema.columns + result.data_array
        #   v2: statement_response.manifest.schema.columns +
        #       statement_response.result.data_array
        manifest = result.get("manifest") or {}
        data_result = result.get("result") or {}

        # Check for nested statement_response wrapper
        stmt = result.get("statement_response") or {}
        if not manifest and stmt:
            manifest = stmt.get("manifest") or {}
        if not data_result.get("data_array") and stmt:
            data_result = stmt.get("result") or {}

        columns = manifest.get("schema", {}).get("columns", [])
        col_names = [c.get("name", f"col_{i}") for i, c in enumerate(columns)]
        data_array = data_result.get("data_array") or data_result.get("data", [])

        if not data_array:
            logger.info("Genie query-result returned empty data_array", extra={
                "conversation_id": conv_id,
                "result_keys": list(result.keys()),
                "manifest_found": bool(columns),
            })

        return [dict(zip(col_names, row)) for row in data_array]
