"""Base repository providing common CRUD helpers with audit trail support.

Every repository in the application should inherit from ``BaseRepository``
to get consistent insert, update, soft-delete, and active-query behaviour
with automatic audit column population.
"""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from BE.auth.context import get_current_user


class BaseRepository:
    """Provides shared data-access helpers for all repositories.

    Parameters:
        session: An active SQLAlchemy ``Session`` bound to the database.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Insert
    # ------------------------------------------------------------------

    def insert_record(self, model_instance: object) -> None:
        """Insert a new record, populating audit columns and generating a UUID PK.

        The primary-key column is detected from the model's ``__table__``
        metadata so that child repositories do not need to hard-code the
        column name.

        Args:
            model_instance: A SQLAlchemy ORM model instance to persist.
        """
        now = datetime.utcnow()
        user = get_current_user()

        # Detect PK column name and assign a UUID v4 string only if not already set
        pk_columns = model_instance.__table__.primary_key.columns
        for pk_col in pk_columns:
            if not getattr(model_instance, pk_col.name, None):
                setattr(model_instance, pk_col.name, str(uuid.uuid4()))

        model_instance.created_by = user
        model_instance.created_at = now
        model_instance.updated_by = user
        model_instance.updated_at = now
        model_instance.is_active = True

        self.session.add(model_instance)
        self.session.flush()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_record(self, model_instance: object) -> None:
        """Update an existing record's audit columns and flush.

        Args:
            model_instance: The ORM instance with modified fields.
        """
        model_instance.updated_by = get_current_user()
        model_instance.updated_at = datetime.utcnow()

        self.session.flush()

    # ------------------------------------------------------------------
    # Soft delete
    # ------------------------------------------------------------------

    def soft_delete_record(self, model_instance: object) -> None:
        """Mark a record as inactive (soft-delete) and flush.

        Args:
            model_instance: The ORM instance to deactivate.
        """
        model_instance.is_active = False
        model_instance.updated_by = get_current_user()
        model_instance.updated_at = datetime.utcnow()

        self.session.flush()

    # ------------------------------------------------------------------
    # Query helper
    # ------------------------------------------------------------------

    def active_query(self, model_class: type):
        """Return a query pre-filtered to only active (non-deleted) records.

        Args:
            model_class: The SQLAlchemy ORM model class to query.

        Returns:
            A ``Query`` object with ``is_active == True`` already applied.
        """
        return self.session.query(model_class).filter(model_class.is_active == True)  # noqa: E712
