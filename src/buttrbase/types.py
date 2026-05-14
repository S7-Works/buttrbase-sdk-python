"""Type definitions for the ButtrBase SDK."""
from __future__ import annotations

from typing import Optional

try:
    from typing import TypedDict
except ImportError:  # Python 3.7
    from typing_extensions import TypedDict


class Credential(TypedDict):
    """A credential object returned by the credentials endpoints.

    Note: ``client_secret`` is **not** present on GET responses; it is only
    included in the create (``CreateCredentialResponse``) and rotate-secret
    (``RotateSecretResponse``) responses.
    """

    credentials_id: str
    client_id: str
    name: str
    description: Optional[str]
    created_at: str


class CreateCredentialResponse(TypedDict):
    """Response from POST /credentials (HTTP 201)."""

    credentials_id: str
    client_id: str
    client_secret: str
    name: str
    description: Optional[str]
    created_at: str


class RotateSecretResponse(TypedDict):
    """Response from POST /credentials/:id/rotate-secret."""

    credentials_id: str
    client_id: str
    client_secret: str


class SandboxResetResponse(TypedDict):
    """Response from POST /api/sandbox/reset."""

    status: str
