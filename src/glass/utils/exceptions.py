from __future__ import annotations


class GLASSError(Exception):
    """Base exception for GLASS."""


class CapabilityUnavailableError(GLASSError):
    """Raised when an optional backend or stage is unavailable."""

