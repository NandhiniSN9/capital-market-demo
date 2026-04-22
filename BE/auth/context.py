"""Authentication context for populating audit columns.

This module provides a placeholder for user identity resolution. The
``get_current_user`` function currently returns a static default value
("system") and is designed to be replaced with a real authentication
mechanism (JWT, OAuth, Databricks workspace identity, etc.) when the
project integrates an auth layer.

All repository operations use this function to populate the ``created_by``
and ``updated_by`` audit columns, so swapping the implementation here will
automatically propagate the authenticated identity across the entire data
layer.
"""


def get_current_user() -> str:
    """Return the identifier of the current authenticated user.

    This is a placeholder that returns ``"system"`` for every call.
    Replace the body of this function with real token / session
    extraction logic (e.g. FastAPI ``Depends`` with a JWT decoder)
    when authentication is integrated.

    Returns:
        A string representing the current user identity.
    """
    return "system"
