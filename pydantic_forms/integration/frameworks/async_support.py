"""Compat shim: re-export async helper used by legacy imports."""

from __future__ import annotations

from ..async_support import handle_async_form

__all__ = ["handle_async_form"]
