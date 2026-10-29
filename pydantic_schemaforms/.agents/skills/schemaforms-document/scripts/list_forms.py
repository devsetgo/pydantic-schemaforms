"""List the pydantic-schemaforms FormModel classes in an app, with their fields.

Usage:
    python list_forms.py app.forms app/other_forms.py [--json]

Each argument is a module name or a .py file. The modules are imported, so run this only in the
app's own environment and only with the user's agreement. Prints Markdown, or JSON with --json.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from pydantic_core import PydanticUndefined

from pydantic_schemaforms import FormModel


def load(target: str) -> ModuleType:
    path = Path(target)
    if path.suffix == '.py':
        sys.path.insert(0, str(path.resolve().parent))
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise SystemExit(f'Cannot load {target}')
        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)
        return module
    sys.path.insert(0, str(Path.cwd()))
    return importlib.import_module(target)


def forms_in(module: ModuleType) -> list[type[FormModel]]:
    return [
        obj
        for obj in vars(module).values()
        if inspect.isclass(obj)
        and issubclass(obj, FormModel)
        and obj is not FormModel
        and obj.__module__ == module.__name__
    ]


def _type_name(annotation: Any) -> str:
    if inspect.isclass(annotation):
        return annotation.__name__
    return str(annotation).replace('typing.', '')


_RULES = ('min_length', 'max_length', 'ge', 'gt', 'le', 'lt', 'multiple_of', 'pattern')


def _rules(info: Any) -> str:
    found = []
    for item in info.metadata:
        found += [
            f'{rule} {getattr(item, rule)}'
            for rule in _RULES
            if getattr(item, rule, None) is not None
        ]
    return ', '.join(found)


def describe(model: type[FormModel]) -> dict[str, Any]:
    fields = []
    for name, info in model.model_fields.items():
        extra = info.json_schema_extra if isinstance(info.json_schema_extra, dict) else {}
        default = info.default
        if info.default_factory is not None:
            default = '(factory)'
        fields.append(
            {
                'name': name,
                'label': info.title or name.replace('_', ' ').title(),
                'type': _type_name(info.annotation),
                'input': extra.get('ui_element') or extra.get('input_type') or '(from type)',
                'required': info.is_required(),
                'default': None if default is PydanticUndefined else repr(default),
                'rules': _rules(info),
                'help': info.description or extra.get('ui_help_text') or '',
            }
        )
    decorators = model.__pydantic_decorators__
    return {
        'name': model.__name__,
        'module': model.__module__,
        'doc': inspect.getdoc(model) if model.__doc__ else '',
        'title': model.model_config.get('title'),
        'fields': fields,
        'field_validators': sorted(decorators.field_validators),
        'model_validators': sorted(decorators.model_validators),
    }


def to_markdown(forms: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for form in forms:
        lines += [f'## {form["name"]}', '', f'`{form["module"]}`', '']
        if form['doc']:
            lines += [form['doc'], '']
        lines += [
            '| Field | Label | Type | Input | Required | Default | Rules | Help |',
            '|---|---|---|---|---|---|---|---|',
        ]
        for f in form['fields']:
            cells = [
                f'`{f["name"]}`',
                f['label'],
                f'`{f["type"]}`',
                f['input'],
                'yes' if f['required'] else 'no',
                f'`{f["default"]}`' if f['default'] is not None else '',
                f['rules'],
                f['help'],
            ]
            lines.append('| ' + ' | '.join(str(c).replace('|', '\\|') for c in cells) + ' |')
        validators = form['field_validators'] + form['model_validators']
        if validators:
            lines += ['', 'Validators: ' + ', '.join(f'`{v}`' for v in validators)]
        lines.append('')
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='List the FormModel classes in an app.')
    parser.add_argument('targets', nargs='+', help='module names or .py files')
    parser.add_argument('--json', action='store_true', help='print JSON instead of Markdown')
    args = parser.parse_args(argv)
    forms = [describe(model) for target in args.targets for model in forms_in(load(target))]
    print(json.dumps(forms, indent=2) if args.json else to_markdown(forms))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
