"""Databricks SQL repository — async wrapper for conversation persistence."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import databricks.sql as dbsql  # type: ignore[import-untyped]

from settings import STATUS_COMPLETED, STATUS_INPROGRESS, get_settings
from utils.exceptions import ERR_CONVERSATION_PERSIST, ERR_DATA_RETRIEVAL, ConversationPersistError, DataRetrievalError
from utils.logger import logger


class DatabricksRepository:
    """Async wrapper around the Databricks SQL connector."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._conn: Any = None

    def _get_connection(self) -> Any:
        if self._conn is None:
            from utils.auth import get_auth_token
            self._conn = dbsql.connect(
                server_hostname=self._settings.databricks_host.replace("https://", ""),
                http_path=self._settings.databricks_http_path,
                access_token=get_auth_token(),
            )
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None

    def _execute_write_sync(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        start = time.monotonic()
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
            logger.info("DB write executed", extra={
                "elapsed_ms": round((time.monotonic() - start) * 1000, 2),
            })
        except Exception as exc:
            raise ConversationPersistError(
                f"Write failed: {exc}", error_code=ERR_CONVERSATION_PERSIST
            ) from exc

    async def _execute_write(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        await asyncio.to_thread(self._execute_write_sync, sql, params)

    async def insert_conversation(self, conversation_id: str, session_id: str, user_message: str) -> None:
        cat, sch = self._settings.databricks_catalog, self._settings.databricks_schema
        sql = f"""
            INSERT INTO {cat}.{sch}.conversations
                (conversation_id, session_id, user_message, agent_response,
                 response_status, is_active, created_at, updated_at)
            VALUES (?, ?, ?, '', ?, true, current_timestamp(), current_timestamp())
        """
        await self._execute_write(sql, (conversation_id, session_id, user_message, STATUS_INPROGRESS))

    async def update_conversation_response(self, conversation_id: str, agent_response: str) -> None:
        cat, sch = self._settings.databricks_catalog, self._settings.databricks_schema
        sql = f"""
            UPDATE {cat}.{sch}.conversations
            SET agent_response = ?, response_status = ?, updated_at = current_timestamp()
            WHERE conversation_id = ?
        """
        logger.info("Updating conversation response", extra={
            "conversation_id": conversation_id,
            "response_length": len(agent_response),
        })
        await self._execute_write(sql, (agent_response, STATUS_COMPLETED, conversation_id))

    async def insert_token_consumption(
        self, token_id: str, conversation_id: str, session_id: str,
        usage_type: str, model_name: str, input_tokens: int, output_tokens: int,
    ) -> None:
        cat, sch = self._settings.databricks_catalog, self._settings.databricks_schema
        sql = f"""
            INSERT INTO {cat}.{sch}.token_consumption
                (token_id, conversation_id, session_id, usage_type, model_name,
                 input_tokens, output_tokens, total_tokens, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, current_timestamp())
        """
        await self._execute_write(sql, (
            token_id, conversation_id, session_id, usage_type, model_name,
            input_tokens, output_tokens, input_tokens + output_tokens,
        ))

    async def insert_error_log(
        self, error_id: str, user_id: str, error_code: str, error_type: str, error_message: str,
    ) -> None:
        cat, sch = self._settings.databricks_catalog, self._settings.databricks_schema
        sql = f"""
            INSERT INTO {cat}.{sch}.error_logs
                (error_id, user_id, error_code, error_type, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, current_timestamp())
        """
        await self._execute_write(sql, (error_id, user_id, error_code, error_type, error_message))

    def fetch_conversation_history_sync(self, session_id: str, limit: int = 6) -> list[dict]:
        """Fetch recent messages for a session from deal_session_messages.

        Returns up to *limit* user+assistant pairs (limit * 2 messages),
        ordered oldest-first for LLM context.
        """
        logger.info("fetch_conversation_history_sync called — session_id=%s, limit=%d", session_id, limit)
        cat, sch = self._settings.databricks_catalog, self._settings.databricks_schema
        sql = f"""
            SELECT role, content
            FROM (
                SELECT role, content, created_at
                FROM {cat}.{sch}.deal_session_messages
                WHERE session_id = ?
                  AND is_active = true
                  AND role IN ('user', 'assistant')
                ORDER BY created_at DESC
                LIMIT ?
            ) recent
            ORDER BY recent.created_at ASC
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (session_id, limit * 2))
                rows = cursor.fetchall()
            logger.info("fetch_conversation_history_sync returned %d rows for session %s", len(rows), session_id)
        except Exception as exc:
            logger.warning("fetch_conversation_history_sync failed for session %s: %s", session_id, str(exc))
            return []

        messages = [{"role": row[0], "content": row[1]} for row in rows if row[1]]
        logger.info("fetch_conversation_history_sync built %d messages for session %s", len(messages), session_id)
        return messages


    def fetch_rfq_conversation_history_sync(self, session_id: str, limit: int = 2) -> list[dict[str, str]]:
        """Fetch the latest *limit* completed conversations for an RFQ session.

        Returns list of dicts with 'user_message' and 'agent_response',
        ordered oldest-first so they can be injected as context.
        """
        cat, sch = self._settings.databricks_catalog, self._settings.databricks_schema
        sql = f"""
            SELECT user_message, agent_response
            FROM (
                SELECT user_message, agent_response, created_at
                FROM {cat}.{sch}.conversations
                WHERE session_id = ?
                  AND is_active = true
                  AND response_status = 'completed'
                  AND agent_response IS NOT NULL
                  AND agent_response != ''
                ORDER BY created_at DESC
                LIMIT ?
            ) recent
            ORDER BY recent.created_at ASC
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (session_id, limit))
                rows = cursor.fetchall()
            logger.info("fetch_rfq_conversation_history_sync returned %d rows for session %s", len(rows), session_id)
        except Exception as exc:
            logger.warning("fetch_rfq_conversation_history_sync failed for session %s: %s", session_id, str(exc))
            return []

        return [{"user_message": row[0], "agent_response": row[1]} for row in rows if row[0]]

    async def fetch_rfq_conversation_history(self, session_id: str, limit: int = 2) -> list[dict[str, str]]:
        """Async wrapper for fetch_rfq_conversation_history_sync."""
        return await asyncio.to_thread(self.fetch_rfq_conversation_history_sync, session_id, limit)

