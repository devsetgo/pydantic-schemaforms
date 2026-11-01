"""Conditional fields: ``Field(ui_show_when={"field": "kind", "equals": "other"})``.

The same rules decide what the browser shows (``SHOW_WHEN_SCRIPT``) and what the
server keeps (``prune``), so a value hidden on the page is never validated, even
in a hand-written request. ``rule_matches`` and the script must agree.

``field`` is relative to the model declaring the rule, and may go down into a
sub-form (``"address.country"``). It can't reach up to a parent model: put the
rule on the sub-form field itself instead.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from .form_data import _tokenize_form_path
from .tstring import SafeHTML, html

SHOW_WHEN_KEY = 'show_when'
GROUP_RULE_KEY = 'ui_group_show_when'
_OPERATORS = ('equals', 'in', 'truthy', 'not_empty')
_FALSE_STRINGS = frozenset({'', '0', 'false', 'off', 'no'})


def _plain(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def check_rule(rule: Any) -> dict[str, Any]:
    """Validate a ``ui_show_when`` rule and return it in JSON-safe form."""

    if not isinstance(rule, dict) or not isinstance(rule.get('field'), str) or not rule['field']:
        raise ValueError('ui_show_when needs a "field" naming the field it depends on')
    unknown = set(rule) - {'field', 'required', *_OPERATORS}
    operators = [name for name in _OPERATORS if name in rule]
    if unknown or len(operators) != 1:
        raise ValueError(
            f'ui_show_when needs "field" and exactly one of {list(_OPERATORS)}, '
            f'plus an optional "required"; got {sorted(rule)}'
        )
    operator = operators[0]
    expected = rule[operator]
    if operator in ('truthy', 'not_empty') and not isinstance(expected, bool):
        raise ValueError(f'ui_show_when "{operator}" must be True or False')
    if operator == 'in' and not isinstance(expected, (list, tuple, set)):
        raise ValueError('ui_show_when "in" must be a list of values')
    if operator == 'equals' and expected is None:
        raise ValueError('ui_show_when "equals" needs a value; use "not_empty": False for empty')
    checked = {'field': rule['field'], operator: _plain(expected)}
    if operator == 'in':
        checked['in'] = [_plain(item) for item in rule['in']]
    if rule.get('required'):
        checked['required'] = True
    return checked


def check_field_options(
    *,
    has_default: bool,
    ui_show_when: Any,
    ui_group: Any,
    ui_cols: Any,
    ui_group_show_when: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Validate the rule and layout options shared by ``Field()`` and ``FormField()``,
    and return both rules in JSON-safe form."""

    if ui_cols is not None and (
        not isinstance(ui_cols, int) or isinstance(ui_cols, bool) or not 1 <= ui_cols <= 12
    ):
        raise ValueError(f'ui_cols must be a whole number from 1 to 12, not {ui_cols!r}')
    if ui_group is not None and (not isinstance(ui_group, str) or not ui_group.strip()):
        raise ValueError('ui_group must be a non-empty title')
    if ui_group_show_when is not None:
        if ui_group is None:
            raise ValueError('ui_group_show_when needs ui_group on the same field')
        ui_group_show_when = check_rule(ui_group_show_when)
        if ui_group_show_when.get('required'):
            raise ValueError(
                'ui_group_show_when can\'t say "required"; put it on the field\'s own ui_show_when'
            )
    if ui_show_when is not None:
        ui_show_when = check_rule(ui_show_when)
        if not has_default:
            raise ValueError(
                'A field with ui_show_when needs a default, since it submits nothing while '
                'hidden. For a value required only while shown, add "required": True to the rule.'
            )
    return ui_show_when, ui_group_show_when


def _is_truthy(value: Any) -> bool:
    value = _plain(value)
    if isinstance(value, str):
        return value.strip().lower() not in _FALSE_STRINGS
    return bool(value)


def _is_empty(value: Any) -> bool:
    return value is None or value == '' or value == [] or value == {}


def _same(value: Any, expected: Any) -> bool:
    if isinstance(expected, bool):
        return _is_truthy(value) == expected
    if value is None:
        return False
    return str(_plain(value)) == str(expected)


def rule_matches(rule: dict[str, Any], value: Any) -> bool:
    """Whether a rule shows its field, given the current value of the field it names."""

    if 'truthy' in rule:
        return _is_truthy(value) == rule['truthy']
    if 'not_empty' in rule:
        return (not _is_empty(value)) == rule['not_empty']
    values = value if isinstance(value, (list, tuple, set)) else [value]
    expected = rule['in'] if 'in' in rule else [rule['equals']]
    return any(_same(item, option) for item in values for option in expected)


def lookup(scope: Any, path: str) -> Any:
    current = scope
    for segment in path.split('.'):
        current = current.get(segment) if isinstance(current, dict) else None
    return current


def _rules(field_schema: dict[str, Any]) -> list[dict[str, Any]]:
    """A field's own rule and its group's; schema_parser copies the latter to each field."""

    # A dynamically registered field keeps its ui_* keys under 'ui', unprefixed.
    nested = field_schema.get('ui') or {}
    candidates = (
        field_schema.get('ui_show_when') or nested.get(SHOW_WHEN_KEY),
        field_schema.get(GROUP_RULE_KEY) or nested.get('group_show_when'),
    )
    return [rule for rule in candidates if rule]


def is_shown(field_schema: dict[str, Any], scope: Any) -> bool:
    """Whether a field shows, given the (already pruned) values of its own model."""

    return all(rule_matches(rule, lookup(scope, rule['field'])) for rule in _rules(field_schema))


def _ref(node: Any) -> str | None:
    ref = node.get('$ref') if isinstance(node, dict) else None
    return ref.split('/')[-1] if isinstance(ref, str) else None


def _sub_definition(
    field_schema: dict[str, Any], schema_defs: dict[str, Any]
) -> tuple[dict[str, Any] | None, bool]:
    """The model a property holds and whether it holds a list of them."""

    for candidate in [field_schema, *(field_schema.get('anyOf') or [])]:
        definition = schema_defs.get(_ref(candidate) or '')
        if definition:
            return definition, False
        if isinstance(candidate, dict) and candidate.get('type') == 'array':
            definition = schema_defs.get(_ref(candidate.get('items')) or '')
            if definition:
                return definition, True
    return None, False


def _check_target(
    name: str, rule: dict[str, Any], properties: dict[str, Any], schema_defs: dict[str, Any]
) -> None:
    current = properties
    for segment in rule['field'].split('.'):
        target = current.get(segment)
        if not isinstance(target, dict):
            raise ValueError(
                f'ui_show_when on {name!r} names {rule["field"]!r}, which is not a field of '
                f'its model; expected one of {sorted(properties)}'
            )
        definition, _is_list = _sub_definition(target, schema_defs)
        current = (definition or {}).get('properties') or {}


def _prune_sub_forms(
    pruned: dict[str, Any],
    properties: dict[str, Any],
    schema_defs: dict[str, Any],
    path: tuple[Any, ...],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for name, field_schema in properties.items():
        definition, is_list = _sub_definition(field_schema, schema_defs)
        value = pruned.get(name)
        if not definition or not value:
            continue
        sub_properties = definition.get('properties') or {}
        if not is_list:
            pruned[name], sub_errors = prune(sub_properties, schema_defs, value, (*path, name))
            errors.extend(sub_errors)
        elif isinstance(value, list):
            items = [
                prune(sub_properties, schema_defs, item, (*path, name, index))
                for index, item in enumerate(value)
            ]
            pruned[name] = [item for item, _errors in items]
            errors.extend(error for _item, item_errors in items for error in item_errors)
    return errors


def _drop_hidden(pruned: dict[str, Any], ruled: dict[str, list[dict[str, Any]]]) -> set[str]:
    # A field can depend on one that is itself hidden, in any declaration order.
    hidden: set[str] = set()
    for _pass in range(len(ruled)):
        newly_hidden = {
            name
            for name, rules in ruled.items()
            if name not in hidden
            and not all(rule_matches(rule, lookup(pruned, rule['field'])) for rule in rules)
        }
        if not newly_hidden:
            break
        hidden |= newly_hidden
        for name in newly_hidden:
            pruned.pop(name, None)
    return hidden


def prune(
    properties: dict[str, Any],
    schema_defs: dict[str, Any],
    data: Any,
    path: tuple[Any, ...] = (),
) -> tuple[Any, list[dict[str, Any]]]:
    """Drop the values of fields hidden by a rule, at every depth.

    Returns the pruned copy, plus an error for each field whose rule says
    ``required`` that is shown and empty.
    """

    if not isinstance(data, dict):
        return data, []
    pruned = dict(data)
    sub_errors = _prune_sub_forms(pruned, properties, schema_defs, path)

    ruled = {name: rules for name, schema in properties.items() if (rules := _rules(schema))}
    for name, rules in ruled.items():
        for rule in rules:
            _check_target(name, rule, properties, schema_defs)
    hidden = _drop_hidden(pruned, ruled)

    depth = len(path)
    errors = [error for error in sub_errors if error['loc'][depth] not in hidden]
    for name, rules in ruled.items():
        value = pruned.get(name)
        required = any(rule.get('required') for rule in rules)
        if name not in hidden and required and (value is False or _is_empty(value)):
            message = properties[name].get('unchecked_message') or 'Field required'
            errors.append({'loc': (*path, name), 'msg': message, 'type': 'missing'})
    return pruned, errors


def show_when_wrapper(field_name: str, rule: dict[str, Any], markup: str, context: Any) -> SafeHTML:
    """Wrap markup that a rule hides. ``field_name`` places the rule among its siblings."""

    # A disabled fieldset disables everything inside it without touching each
    # control, so a field's own ui_disabled survives being shown again.
    prefix = field_name[: field_name.rfind('.') + 1]
    scope: Any = context.form_data if context.visible_data is None else context.visible_data
    for token in _tokenize_form_path(prefix.rstrip('.')):
        if isinstance(token, int):
            scope = scope[token] if isinstance(scope, list) and token < len(scope) else None
        else:
            scope = scope.get(token) if isinstance(scope, dict) else None
    shown = rule_matches(rule, lookup(scope, rule['field']))
    _state = SafeHTML('' if shown else ' hidden disabled')
    target = f'{prefix}{rule["field"]}'  # NOSONAR - read in the t-string below
    # The script only needs the test, not where it points.
    test = json.dumps({k: v for k, v in rule.items() if k not in ('field', 'required')})  # NOSONAR
    _markup = SafeHTML(str(markup))  # NOSONAR
    return html(
        t'<fieldset class="sf-show-when" data-show-when="{test}" '
        t'data-show-when-target="{target}" '
        t'style="border: 0; margin: 0; padding: 0; min-width: 0"{_state}>{_markup}</fieldset>'
    )


# Plain JavaScript in a Python string: a '#' comment here would kill the script.
SHOW_WHEN_SCRIPT = """<script data-schemaforms-show-when>
(function () {
    if (window.schemaFormsShowWhen) { window.schemaFormsShowWhen.refresh(); return; }
    var FALSE_STRINGS = ['', '0', 'false', 'off', 'no'];

    function currentValue(wrapper) {
        var root = wrapper.closest('form') || document;
        var name = CSS.escape(wrapper.getAttribute('data-show-when-target'));
        var controls = Array.prototype.slice.call(root.querySelectorAll('[name="' + name + '"]'))
            .filter(function (control) { return !control.matches(':disabled'); });
        if (!controls.length) { return null; }
        var first = controls[0];
        if (first.type === 'radio') {
            var picked = controls.filter(function (c) { return c.checked; })[0];
            return picked ? picked.value : null;
        }
        if (first.type === 'checkbox') {
            var ticked = controls.filter(function (c) { return c.checked; });
            if (controls.length === 1 && ['1', 'on', 'true'].indexOf(first.value) !== -1) {
                return ticked.length === 1;
            }
            return ticked.map(function (c) { return c.value; });
        }
        if (first.multiple && first.options) {
            return Array.prototype.slice.call(first.selectedOptions).map(function (o) { return o.value; });
        }
        return first.value;
    }

    function isTruthy(value) {
        if (Array.isArray(value)) { return value.length > 0; }
        if (typeof value === 'string') {
            return FALSE_STRINGS.indexOf(value.trim().toLowerCase()) === -1;
        }
        return Boolean(value);
    }

    function isEmpty(value) {
        return value === null || value === '' || (Array.isArray(value) && value.length === 0);
    }

    function same(value, expected) {
        if (typeof expected === 'boolean') { return isTruthy(value) === expected; }
        return value !== null && String(value) === String(expected);
    }

    function matches(rule, value) {
        if ('truthy' in rule) { return isTruthy(value) === rule.truthy; }
        if ('not_empty' in rule) { return !isEmpty(value) === rule.not_empty; }
        var values = Array.isArray(value) ? value : [value];
        var expected = 'in' in rule ? rule['in'] : [rule.equals];
        return values.some(function (item) {
            return expected.some(function (option) { return same(item, option); });
        });
    }

    function refresh() {
        var wrappers = document.querySelectorAll('[data-show-when]');
        var changed = true;
        for (var pass = 0; changed && pass <= wrappers.length; pass++) {
            changed = false;
            wrappers.forEach(function (wrapper) {
                var show = matches(JSON.parse(wrapper.getAttribute('data-show-when')), currentValue(wrapper));
                if (wrapper.hidden === show) {
                    wrapper.hidden = !show;
                    wrapper.disabled = !show;
                    changed = true;
                }
            });
        }
    }

    window.schemaFormsShowWhen = { refresh: refresh };
    document.addEventListener('change', refresh);
    document.addEventListener('input', refresh);
    if (window.MutationObserver) {
        new MutationObserver(function (mutations) {
            var added = mutations.some(function (m) { return m.addedNodes.length || m.removedNodes.length; });
            if (added) { refresh(); }
        }).observe(document.documentElement, { childList: true, subtree: true });
    }
    refresh();
})();
</script>"""
