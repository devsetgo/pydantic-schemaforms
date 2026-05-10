"""
Backward-compatibility shim for SimpleMaterialRenderer.

Material Design rendering is now handled natively by
EnhancedFormRenderer(framework="material"). This module keeps
the old import paths working so existing code doesn't break.
"""

from .enhanced_renderer import EnhancedFormRenderer


class SimpleMaterialRenderer(EnhancedFormRenderer):
    """Thin alias for EnhancedFormRenderer(framework='material').

    Kept for backward compatibility. New code should use::

        EnhancedFormRenderer(framework="material")

    or the top-level helpers::

        render_form_html(..., framework="material")
        render_form_html_async(..., framework="material")
    """

    def __init__(self) -> None:
        super().__init__(framework='material')


# Legacy alias
MaterialDesign3Renderer = SimpleMaterialRenderer
