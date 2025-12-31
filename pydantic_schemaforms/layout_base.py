"""Shared layout primitives used by both general and form-aware layout systems."""

from __future__ import annotations

from string import Template
from typing import Any, Callable, Dict, Iterable, Optional, Sequence, Union

try:  # pragma: no cover - optional import for typing only
    from typing import TYPE_CHECKING
except ImportError:  # pragma: no cover
    TYPE_CHECKING = False

if TYPE_CHECKING:  # pragma: no cover
    from .enhanced_renderer import EnhancedFormRenderer

RenderableContent = Union[str, "BaseLayout", Sequence[Union[str, "BaseLayout"]]]
ContentCallable = Callable[[Dict[str, Any], Dict[str, Any], Optional["EnhancedFormRenderer"], str], str]


class BaseLayout:
    """Minimal building block for layout components.

    The class focuses on content orchestration and attribute merging so that both the
    lightweight layout DSL (``pydantic_schemaforms.layouts``) and the form-composition
    helpers (``pydantic_schemaforms.form_layouts``) can share a single abstraction.
    """

    template: str = '<div class="${class_}" style="${style}">${content}</div>'

    def __init__(self, content: Optional[Union[RenderableContent, ContentCallable]] = None, **attributes: Any) -> None:
        self.content = content
        self.attributes = attributes
        self.template_renderer = Template(self.template)

    # ------------------------------------------------------------------
    # Core rendering API shared across layout stacks
    # ------------------------------------------------------------------
    def render(
        self,
        *,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        renderer: Optional["EnhancedFormRenderer"] = None,
        framework: str = "bootstrap",
        **kwargs: Any,
    ) -> str:
        """Render the layout by combining template attributes and content."""

        attrs: Dict[str, Any] = {**self.attributes, **kwargs}
        class_attr = self._merge_classes(attrs)
        style_attr = self._merge_styles(attrs)

        template_data: Dict[str, Any] = {
            "content": self._render_content(
                data=data or {},
                errors=errors or {},
                renderer=renderer,
                framework=framework,
            ),
            "class_": class_attr,
            "style": style_attr,
            **attrs,
        }

        # Use safe_substitute so optional attributes do not raise key errors.
        return self.template_renderer.safe_substitute(**template_data)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _render_content(
        self,
        *,
        data: Dict[str, Any],
        errors: Dict[str, Any],
        renderer: Optional["EnhancedFormRenderer"],
        framework: str,
    ) -> str:
        """Render nested content recursively."""

        if self.content is None:
            return ""

        if callable(self.content):
            return self.content(data, errors, renderer, framework)

        if isinstance(self.content, BaseLayout):
            return self.content.render(
                data=data,
                errors=errors,
                renderer=renderer,
                framework=framework,
            )

        if isinstance(self.content, (list, tuple)):
            rendered_parts = [
                self._render_nested(item, data=data, errors=errors, renderer=renderer, framework=framework)
                for item in self.content
            ]
            return "".join(rendered_parts)

        return str(self.content)

    def _render_nested(
        self,
        item: Union[str, "BaseLayout"],
        *,
        data: Dict[str, Any],
        errors: Dict[str, Any],
        renderer: Optional["EnhancedFormRenderer"],
        framework: str,
    ) -> str:
        if isinstance(item, BaseLayout):
            return item.render(data=data, errors=errors, renderer=renderer, framework=framework)
        return str(item)

    @staticmethod
    def _merge_classes(attrs: Dict[str, Any]) -> str:
        classes: Iterable[str] = filter(None, [attrs.pop("class_", ""), attrs.pop("css_class", "")])
        return " ".join(cls for cls in classes if cls)

    @staticmethod
    def _merge_styles(attrs: Dict[str, Any]) -> str:
        styles: Iterable[str] = filter(None, [attrs.pop("style", ""), attrs.pop("css_style", "")])
        return "; ".join(s for s in styles if s)
