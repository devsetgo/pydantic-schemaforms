"""Material icon rendering helpers.

The self-contained Material renderer cannot rely on external icon fonts.
This module provides a small inline-SVG fallback for the subset of Material
icon names used by the library demos.

If an icon name is not recognized, we fall back to the Material Icons
ligature markup (which requires the font to be available).
"""

from __future__ import annotations

from html import escape
from typing import Final, Optional


# Minimal set of SVG paths for common Material icon names used by the demo.
# Paths are 24x24 viewBox and render via currentColor.
_MATERIAL_ICON_PATHS: Final[dict[str, str]] = {

    "add": "M19 13H13v6h-2v-6H5v-2h6V5h2v6h6v2z",
    "delete": "M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z",
    "person": "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z",
    "email": "M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4-8 5-8-5V6l8 5 8-5v2z",
    "lock": "M12 17a2 2 0 0 0 2-2v-2a2 2 0 0 0-4 0v2a2 2 0 0 0 2 2zm6-7h-1V8a5 5 0 0 0-10 0v2H6c-1.1 0-2 .9-2 2v8c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-8c0-1.1-.9-2-2-2zm-3 0H9V8a3 3 0 0 1 6 0v2z",
    "calendar_today": "M19 4h-1V2h-2v2H8V2H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11zm0-13H5V6h14v1z",
    "shield": "M12 1 3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z",
    "verified_user": "M12 1 3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-1 17-4-4 1.41-1.41L11 14.17l5.59-5.59L18 10l-7 8z",
    "security": "M12 1 3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 5c1.66 0 3 1.34 3 3 0 1.31-.84 2.42-2 2.83V14h1c1.1 0 2 .9 2 2v2H8v-2c0-1.1.9-2 2-2h1v-2.17c-1.16-.41-2-1.52-2-2.83 0-1.66 1.34-3 3-3z",
    "warning": "M1 21h22L12 2 1 21zm12-3h-2v2h2v-2zm0-8h-2v6h2V10z",
    "description": "M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 18H6V4h7v5h5v11zm-2-4H8v2h6v-2zm2-4H8v2h8v-2zm0-4H8v2h8V8z",
}


def render_material_icon(

    icon_name: str,
    *,
    classes: str = "",
    aria_hidden: bool = True,
    title: Optional[str] = None,
) -> str:

    """Render a Material icon by name.

	For known names, this returns inline SVG (no external dependencies).
	For unknown names, it falls back to ligature markup.
	"""


    safe_name = escape(icon_name)
    class_attr = " ".join(part for part in ["material-icons", classes.strip()] if part).strip()
    safe_class = escape(class_attr, quote=True)


    path_d = _MATERIAL_ICON_PATHS.get(icon_name)
    if not path_d:
        return f'<span class="{safe_class}">{safe_name}</span>'


    aria = ' aria-hidden="true"' if aria_hidden else ""
    title_tag = f"<title>{escape(title)}</title>" if title else ""


    return (
        f'<svg class="{safe_class}" viewBox="0 0 24 24" focusable="false"{aria}>'
        f"{title_tag}<path d=\"{escape(path_d, quote=True)}\" /></svg>"
    )
