"""The code behind an example page, for its "How it's built" tab.

Read from the running app, so it can't drift from what the page does: the
route functions registered for the example's URL, and the ``FormModel``
classes those functions (or the helpers they call) use, with their sub-forms.
"""

from __future__ import annotations

import inspect
import sys
import types
import typing
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from fastapi.routing import APIRoute
from pydantic import BaseModel

from examples.catalog import Example
from pydantic_schemaforms import FormModel

REPO_ROOT = Path(__file__).resolve().parent.parent
GITHUB = 'https://github.com/devsetgo/pydantic-schemaforms/blob/main'


@dataclass(frozen=True)
class SourceBlock:
    title: str
    code: str
    file: str
    url: str


def _routes(routes: list[Any]) -> Iterator[APIRoute]:
    for route in routes:
        if isinstance(route, APIRoute):
            yield route
        elif hasattr(route, 'original_router'):  # an included router
            yield from _routes(route.original_router.routes)


def _endpoints(app: Any, paths: set[str]) -> list[Callable[..., Any]]:
    found: list[Callable[..., Any]] = []
    for route in _routes(app.router.routes):
        if route.path.rstrip('/') in paths and route.endpoint not in found:
            found.append(route.endpoint)
    return found


def _names(code: types.CodeType) -> Iterator[str]:
    yield from code.co_names
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            yield from _names(const)


def _imported_inside(name: str) -> Any:
    """A name a function imports in its body, found in the example modules."""

    for module_name, module in list(sys.modules.items()):
        if module_name.startswith('examples.') and isinstance(module, types.ModuleType):
            value = getattr(module, name, None)
            if isinstance(value, type) and issubclass(value, FormModel):
                return value
    return None


def _models_used(function: Callable[..., Any], depth: int = 2) -> list[type[FormModel]]:
    """FormModel classes a function names, looking one helper deep in its own module."""

    found: list[type[FormModel]] = []
    module_globals = getattr(function, '__globals__', {})
    for name in _names(function.__code__):
        value = module_globals.get(name, _imported_inside(name))
        if isinstance(value, type) and issubclass(value, FormModel) and value is not FormModel:
            found.append(value)
        elif (
            depth > 1
            and inspect.isfunction(value)
            and value.__module__ == function.__module__
            and value is not function
        ):
            found.extend(_models_used(value, depth - 1))
    return found


def _sub_forms(model: type[BaseModel]) -> Iterator[type[BaseModel]]:
    for info in model.model_fields.values():
        stack = [info.annotation]
        while stack:
            annotation = stack.pop()
            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                yield annotation
            stack.extend(typing.get_args(annotation))


def _with_sub_forms(models: list[type[BaseModel]]) -> list[type[BaseModel]]:
    ordered: list[type[BaseModel]] = []
    queue = list(models)
    while queue:
        model = queue.pop(0)
        if model in ordered or not model.__module__.startswith('examples'):
            continue
        ordered.append(model)
        queue.extend(_sub_forms(model))
    return ordered


def _block(title: str, obj: Any) -> SourceBlock:
    code = inspect.getsource(obj)
    path = Path(inspect.getsourcefile(obj) or '').resolve()
    line = inspect.getsourcelines(obj)[1]
    relative = path.relative_to(REPO_ROOT).as_posix()
    return SourceBlock(
        title,
        inspect.cleandoc(code) if code.startswith(' ') else code,
        relative,
        f'{GITHUB}/{relative}#L{line}',
    )


@cache
def _sources(
    app_id: int, example: Example, app: Any
) -> tuple[tuple[SourceBlock, ...], tuple[SourceBlock, ...]]:
    paths = {example.path.rstrip('/'), *(page.rstrip('/') for page in example.pages)}
    endpoints = _endpoints(app, paths)
    models = list(example.models)
    for endpoint in endpoints:
        models.extend(_models_used(endpoint))
    model_blocks = tuple(_block(model.__name__, model) for model in _with_sub_forms(models))
    route_blocks = tuple(_block(f'{endpoint.__name__}()', endpoint) for endpoint in endpoints)
    return model_blocks, route_blocks


def example_sources(
    request: Any, example: Example
) -> tuple[tuple[SourceBlock, ...], tuple[SourceBlock, ...]]:
    """The model and route source for an example page: (models, routes)."""

    return _sources(id(request.app), example, request.app)
