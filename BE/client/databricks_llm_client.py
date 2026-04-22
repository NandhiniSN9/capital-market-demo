"""Async client for Databricks Foundation Model endpoints (Sonnet, Haiku, Embeddings)."""
 
import asyncio
import base64
 
import httpx
 
from BE.settings import get_settings
from BE.utils.exceptions import ProcessingException
from BE.utils.logger import get_logger
 
logger = get_logger(__name__)
 
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
_cached_llm_token: str = ""
_cached_llm_token_expires_at: float = 0.0
_LLM_TOKEN_REFRESH_BUFFER = 300  # refresh 5 min before expiry


def _get_llm_token(settings) -> str:
    """Get OAuth token for LLM calls, cached with expiry."""
    global _cached_llm_token, _cached_llm_token_expires_at
    import time

    now = time.time()
    if _cached_llm_token and now < _cached_llm_token_expires_at - _LLM_TOKEN_REFRESH_BUFFER:
        return _cached_llm_token

    token = settings.DATABRICKS_TOKEN or settings.databricks_token
    if not token:
        try:
            import os
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
                _cached_llm_token_expires_at = expiry.timestamp()
            else:
                _cached_llm_token_expires_at = now + 3600
        except Exception as e:
            logger.error("Failed to get OAuth token for LLM client: %s", str(e))
            return _cached_llm_token or ""
    else:
        # PAT token — never expires in this context
        _cached_llm_token_expires_at = now + 86400

    _cached_llm_token = token
    return token

 
 
class DatabricksLLMClient:
    """Async wrapper around Databricks serving endpoints for LLM and embedding calls."""
 
    def __init__(self, settings=None) -> None:
        self._settings = settings or get_settings()
 
    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
 
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {_get_llm_token(self._settings)}",
            "Content-Type": "application/json",
        }
 
    def _endpoint_url(self, endpoint_name: str) -> str:
        host = self._settings.databricks_host.rstrip("/")
        return f"{host}/serving-endpoints/{endpoint_name}/invocations"
 
    async def _post_with_retry(
        self,
        url: str,
        payload: dict,
        trace_id: str = "",
    ) -> dict:
        """POST *payload* to *url* with retry logic (3 attempts, exponential backoff)."""
 
        last_exc: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=self._headers(),
                        timeout=120.0,
                    )
                    response.raise_for_status()
                    return response.json()
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                logger.warning(
                    "Request attempt %d/%d failed: %s",
                    attempt,
                    MAX_RETRIES,
                    str(exc),
                    extra={"trace_id": trace_id},
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1)))
 
        logger.error(
            "All %d retry attempts exhausted for %s",
            MAX_RETRIES,
            url,
            extra={"trace_id": trace_id},
        )
        raise ProcessingException(
            detail=f"LLM endpoint request failed after {MAX_RETRIES} retries: {last_exc}",
        )
 
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
 
    async def invoke_sonnet(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 4096,
        trace_id: str = "",
    ) -> dict:
        """Call Claude Sonnet via the Databricks serving endpoint.
 
        Returns the parsed JSON response dict from the endpoint.
        """
        url = self._endpoint_url(self._settings.llm_endpoint_sonnet)
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": max_tokens,
        }
        return await self._post_with_retry(url, payload, trace_id=trace_id)
 
    async def invoke_sonnet_with_image(
        self,
        system_prompt: str,
        image_bytes: bytes,
        media_type: str = "image/png",
        text_prompt: str = "",
        max_tokens: int = 4096,
        trace_id: str = "",
    ) -> dict:
        """Call Claude Sonnet with a base64-encoded image for vision/multimodal analysis.
 
        Sends image bytes alongside an optional text prompt using the Anthropic
        multimodal message format (content array with image_url or base64 blocks).
 
        Args:
            system_prompt: System-level instruction for the model.
            image_bytes: Raw image bytes to analyse.
            media_type: MIME type of the image (e.g. image/png, image/jpeg).
            text_prompt: Optional text to accompany the image.
            max_tokens: Maximum tokens in the response.
            trace_id: Optional trace identifier for logging.
 
        Returns:
            Parsed JSON response dict from the endpoint.
        """
        url = self._endpoint_url(self._settings.llm_endpoint_sonnet)
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
 
        # Anthropic multimodal content format
        user_content: list[dict] = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{b64_image}"},
            }
        ]
        if text_prompt:
            user_content.append({"type": "text", "text": text_prompt})
 
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": max_tokens,
        }
        return await self._post_with_retry(url, payload, trace_id=trace_id)
 
    async def invoke_haiku(
        self,
        prompt: str,
        max_tokens: int = 1024,
        trace_id: str = "",
    ) -> str:
        """Call Claude Haiku via the Databricks serving endpoint.
 
        Returns the text content from the response.
        """
        url = self._endpoint_url(self._settings.llm_endpoint_haiku)
        payload = {
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
        }
        result = await self._post_with_retry(url, payload, trace_id=trace_id)
        # Extract text from Anthropic-style response
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return str(result)
 
    async def generate_embedding(
        self,
        text: str,
        trace_id: str = "",
    ) -> list[float]:
        """Generate an embedding vector via the Databricks embedding endpoint.
 
        Returns a list of floats representing the embedding.
        """
        url = self._endpoint_url(self._settings.embedding_endpoint)
        payload = {"input": text}
        result = await self._post_with_retry(url, payload, trace_id=trace_id)
        try:
            return result["data"][0]["embedding"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.error(
                "Failed to parse embedding response: %s",
                str(exc),
                extra={"trace_id": trace_id},
            )
            raise ProcessingException(
                detail=f"Failed to parse embedding response: {exc}",
            ) from exc
