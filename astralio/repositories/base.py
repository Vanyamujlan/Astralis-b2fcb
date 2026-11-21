"""Base repository exceptions and helper types."""

from __future__ import annotations


class RepositoryError(RuntimeError):
    """Raised when a persistence operation fails."""


class DuplicatePaymentError(RepositoryError):
    """Raised when a payment charge ID has already been processed."""
