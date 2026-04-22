"""Client for Databricks Vector Search index operations."""

from databricks.sdk import WorkspaceClient

from BE.settings import get_settings
from BE.utils.logger import get_logger

logger = get_logger(__name__)


class VectorSearchClient:
    """Wraps the Databricks SDK to query and manage the Vector Search index."""

    def __init__(self, settings=None) -> None:
        self._settings = settings or get_settings()
        # Inside Databricks Apps, OAuth credentials are auto-injected.
        self._workspace_client = WorkspaceClient()

    def _get_index(self):
        """Return a handle to the configured Vector Search index."""
        return self._workspace_client.vector_search_indexes

    def search(
        self,
        query_embedding: list[float],
        chat_id: str,
        top_k: int = 5,
    ) -> list[dict]:
        """Query the vector search index for chunks related to *chat_id*.

        Filters by chat_id (via document relationship) and is_active=True.
        Returns a list of dicts with chunk_id, chunk_text, document_id,
        page_number, section_name, chunk_type, and score.
        """
        index_name = self._settings.vector_search_index

        filters = {"chat_id": chat_id, "is_active": True}
        columns = [
            "chunk_id",
            "chunk_text",
            "document_id",
            "page_number",
            "section_name",
            "chunk_type",
        ]

        result = self._get_index().query_index(
            index_name=index_name,
            query_vector=query_embedding,
            columns=columns,
            filters=filters,
            num_results=top_k,
        )

        results_data = result.get("result", {}).get("data_array", [])
        column_names = [*columns, "score"]

        return [dict(zip(column_names, row)) for row in results_data]

    def delete_by_document(self, document_id: str) -> None:
        """Remove all embeddings for *document_id* from the vector search index.

        For Delta sync indexes, direct deletion is not supported — the index
        syncs automatically from the source table. We log a warning and skip.
        """
        index_name = self._settings.vector_search_index

        logger.info(
            "Deleting embeddings for document %s from index %s",
            document_id,
            index_name,
            extra={"document_id": document_id},
        )

        try:
            self._get_index().delete_data_vector_index(
                index_name=index_name,
                primary_keys=[document_id],
            )
        except Exception as e:
            # Delta sync indexes don't support direct deletion — the index
            # will sync automatically when the source table rows are soft-deleted.
            logger.warning(
                "Vector search deletion skipped for document %s (index may be Delta sync): %s",
                document_id,
                str(e),
            )

    def sync_index(self) -> None:
        """Trigger a sync of the vector search index from the Delta table.

        Required for triggered pipeline_type indexes. Call after inserting
        or deleting chunks to make changes searchable.
        """
        index_name = self._settings.vector_search_index
        logger.info("Triggering vector search index sync for %s", index_name)
        self._get_index().sync_index(index_name=index_name)
