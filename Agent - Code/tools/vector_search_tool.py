"""RAG retrieval tool — searches vector index for chunks similar to user query."""

from __future__ import annotations

import httpx
from databricks.sdk import WorkspaceClient

from settings import get_settings

_ws_client: WorkspaceClient | None = None


def _get_ws_client() -> WorkspaceClient:
    """Return a cached WorkspaceClient singleton."""
    global _ws_client
    if _ws_client is None:
        import os
        host = os.environ.get("DATABRICKS_HOST", "")
        if os.environ.get("DATABRICKS_CLIENT_ID") and os.environ.get("DATABRICKS_CLIENT_SECRET"):
            _ws_client = WorkspaceClient(
                host=host,
                client_id=os.environ.get("DATABRICKS_CLIENT_ID"),
                client_secret=os.environ.get("DATABRICKS_CLIENT_SECRET"),
            )
        else:
            settings = get_settings()
            _ws_client = WorkspaceClient(host=settings.databricks_host, token=settings.databricks_token)
    return _ws_client


def vector_search(query: str, chat_id: str, top_k: int | None = None) -> list[dict]:
    """Retrieve document chunks similar to the query, scoped to a chat.

    Fetches extra results and re-ranks with a recency boost based on
    document_year stored in chunk metadata.
    """
    settings = get_settings()
    top_k = top_k or settings.vector_search_top_k
    # Fetch more than needed so recency re-ranking has room to promote newer docs
    fetch_k = top_k * 2
    embedding = _generate_embedding(query, settings)
    ws = _get_ws_client()
    import json as _json
    result = ws.vector_search_indexes.query_index(
        index_name=settings.vector_search_index,
        query_vector=embedding,
        columns=[
            "chunk_id", "chunk_text", "document_id",
            "page_number", "section_name", "chunk_type", "metadata",
        ],
        filters_json=_json.dumps({"chat_id": chat_id, "is_active": True}),
        num_results=fetch_k,
    )
    try:
        data_array = result.result.data_array if result.result else []
    except AttributeError:
        try:
            data_array = result.as_dict().get("result", {}).get("data_array", [])
        except Exception:
            data_array = []
    if not data_array:
        return []
    column_names = [
        "chunk_id", "chunk_text", "document_id",
        "page_number", "section_name", "chunk_type", "metadata", "score",
    ]
    chunks = [dict(zip(column_names, row)) for row in data_array]

    # Apply recency boost: newer document_year gets a score bonus
    chunks = _apply_recency_boost(chunks)

    return chunks[:top_k]


def _apply_recency_boost(chunks: list[dict], boost_weight: float = 0.15) -> list[dict]:
    """Re-rank chunks by boosting scores for more recent documents.

    Parses document_period (e.g., "Q3 2024", "FY 2024") from the metadata
    field and converts to a numeric score for ranking. Q4 2024 > Q3 2024 > Q2 2024 > Q1 2024.
    Falls back to document_year if document_period is not available.
    """
    import json as _json
    import re as _re

    def _period_to_numeric(period_str: str) -> float | None:
        """Convert a period string to a numeric value for comparison.
        Q3 2024 -> 2024.75, Q1 2024 -> 2024.25, FY 2024 -> 2024.0
        """
        if not period_str or period_str == "UNKNOWN":
            return None
        # Try quarterly: Q3 2024
        q_match = _re.search(r'Q([1-4])\s*((?:19|20)\d{2})', str(period_str))
        if q_match:
            quarter = int(q_match.group(1))
            year = int(q_match.group(2))
            return year + (quarter * 0.25)
        # Try annual: FY 2024
        fy_match = _re.search(r'FY\s*((?:19|20)\d{2})', str(period_str))
        if fy_match:
            return float(fy_match.group(1))
        # Try bare year
        year_match = _re.search(r'\b(19|20)\d{2}\b', str(period_str))
        if year_match:
            return float(year_match.group(0))
        return None

    for chunk in chunks:
        meta = chunk.get("metadata") or ""
        numeric = None
        if meta:
            try:
                parsed = _json.loads(meta) if isinstance(meta, str) else meta
                # Try document_period first, fall back to document_year
                period = parsed.get("document_period") or parsed.get("document_year", "")
                numeric = _period_to_numeric(str(period))
            except Exception:
                # Try regex on raw string
                match = _re.search(r'document_period.*?Q([1-4])\s*((?:19|20)\d{2})', str(meta))
                if match:
                    numeric = int(match.group(2)) + (int(match.group(1)) * 0.25)
                else:
                    match = _re.search(r'document_year.*?((?:19|20)\d{2})', str(meta))
                    if match:
                        numeric = float(match.group(1))
        chunk["_doc_numeric"] = numeric

    # Find range for normalization
    values = [c["_doc_numeric"] for c in chunks if c["_doc_numeric"] is not None]
    if not values or max(values) == min(values):
        for c in chunks:
            c.pop("_doc_numeric", None)
        return chunks

    min_val, max_val = min(values), max(values)
    val_range = max_val - min_val

    for chunk in chunks:
        score = chunk.get("score", 0) or 0
        val = chunk["_doc_numeric"]
        if val is not None:
            recency_factor = (val - min_val) / val_range
            chunk["score"] = score + (boost_weight * recency_factor)
        chunk.pop("_doc_numeric", None)

    chunks.sort(key=lambda c: c.get("score", 0), reverse=True)
    return chunks


def _generate_embedding(text: str, settings) -> list[float]:
    from utils.auth import get_auth_token
    host = settings.databricks_host.rstrip("/")
    url = f"{host}/serving-endpoints/{settings.embedding_endpoint}/invocations"
    headers = {
        "Authorization": f"Bearer {get_auth_token()}",
        "Content-Type": "application/json",
    }
    response = httpx.post(url, json={"input": text}, headers=headers, timeout=60.0)
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]
