"""Errors for the ButtrBase SDK."""
from __future__ import annotations

from typing import Any, Optional


class ButtrbaseError(Exception):
    """Raised when the ButtrBase API returns a non-2xx response."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        detail: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.detail = detail

    def __repr__(self) -> str:
        return (
            f"ButtrbaseError(status_code={self.status_code!r}, "
            f"code={self.code!r}, detail={self.detail!r})"
        )
