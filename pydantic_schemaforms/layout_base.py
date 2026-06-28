"""Shared layout primitives used by both general and form-aware layout systems."""

from __future__ import annotations

from typing import Any, Optional, Union
from collections.abc import Callable, Iterable, Sequence

from .tstring import substitute

try:  # pragma: no cover - optional import for typing only
    from typing import TYPE_CHECKING
except ImportError:  # pragma: no cover
    TYPE_CHECKING = False

if TYPE_CHECKING:  # pragma: no cover
    from .enhanced_renderer import EnhancedFormRenderer

RenderableContent = Union[str, 'BaseLayout', Sequence[Union[str, 'BaseLayout']]]
ContentCallable = Callable[
    [dict[str, Any], dict[str, Any], Optional['EnhancedFormRenderer'], str], str
]


class BaseLayout:
    """Minimal building block for layout components.

    The class focuses on content orchestration and attribute merging so that both the
    lightweight layout DSL (``pydantic_schemaforms.layouts``) and the form-composition
    helpers (``pydantic_schemaforms.form_layouts``) can share a single abstraction.
    """

    template: str = '<div class="${class_}" style="${style}">${content}</div>'

    def __init__(
        self, content: RenderableContent | ContentCallable | None = None, **attributes: Any
    ) -> None:
        self.content = content
        self.attributes = attributes

    def render(
        self,
        *,
        data: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = None,
        renderer: EnhancedFormRenderer | None = None,
        framework: str = 'bootstrap',
        **kwargs: Any,
    ) -> str:
        attrs: dict[str, Any] = {**self.attributes, **kwargs}
        class_attr = self._merge_classes(attrs)
        style_attr = self._merge_styles(attrs)

        template_data: dict[str, Any] = {
            'content': self._render_content(
                data=data or {},
                errors=errors or {},
                renderer=renderer,
                framework=framework,
            ),
            'class_': class_attr,
            'style': style_attr,
            **attrs,
        }

        return substitute(self.template, **template_data)

    def _render_content(
        self,
        *,
        data: dict[str, Any],
        errors: dict[str, Any],
        renderer: EnhancedFormRenderer | None,
        framework: str,
    ) -> str:
        if self.content is None:
            return ''

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
                self._render_nested(
                    item, data=data, errors=errors, renderer=renderer, framework=framework
                )
                for item in self.content
            ]
            return ''.join(rendered_parts)

        return str(self.content)

    def _render_nested(
        self,
        item: str | BaseLayout,
        *,
        data: dict[str, Any],
        errors: dict[str, Any],
        renderer: EnhancedFormRenderer | None,
        framework: str,
    ) -> str:
        if isinstance(item, BaseLayout):
            return item.render(data=data, errors=errors, renderer=renderer, framework=framework)
        return str(item)

    @staticmethod
    def _merge_classes(attrs: dict[str, Any]) -> str:
        classes: Iterable[str] = filter(None, [attrs.pop('class_', ''), attrs.pop('css_class', '')])
        return ' '.join(cls for cls in classes if cls)

    @staticmethod
    def _merge_styles(attrs: dict[str, Any]) -> str:
        styles: Iterable[str] = filter(None, [attrs.pop('style', ''), attrs.pop('css_style', '')])
        return '; '.join(s for s in styles if s)
