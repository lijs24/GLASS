from __future__ import annotations


class GPWBPPError(Exception):
    """Base exception for GPWBPP."""


class CapabilityUnavailableError(GPWBPPError):
    """Raised when an optional backend or stage is unavailable."""

