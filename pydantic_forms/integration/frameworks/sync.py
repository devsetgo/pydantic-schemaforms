"""Compat shim: re-export sync helpers used by legacy imports."""

from __future__ import annotations

from ..sync import handle_sync_form, normalize_form_data

__all__ = ["handle_sync_form", "normalize_form_data"]
