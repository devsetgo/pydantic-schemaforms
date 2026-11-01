"""Conditional fields: ``Field(ui_show_when={"field": "kind", "equals": "other"})``.

The same rules decide what the browser shows (``SHOW_WHEN_SCRIPT``) and what the
server keeps (``prune``), so a value hidden on the page is never validated, even
in a hand-written request. ``rule_matches`` and the script must agree.

``field`` is relative to the model declaring the rule, and may go down into a
sub-form (``"address.country"``). It can't reach up to a parent model: put the
rule on the sub-form field itself instead.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

SHOW_WHEN_KEY = 'show_when'
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


def _rule(field_schema: dict[str, Any]) -> dict[str, Any] | None:
    # A dynamically registered field keeps its ui_* keys under 'ui', unprefixed.
    return field_schema.get('ui_show_when') or (field_schema.get('ui') or {}).get(SHOW_WHEN_KEY)


def is_shown(field_schema: dict[str, Any], scope: Any) -> bool:
    """Whether a field shows, given the (already pruned) values of its own model."""

    rule = _rule(field_schema)
    return rule is None or rule_matches(rule, lookup(scope, rule['field']))


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
    errors: list[dict[str, Any]] = []

    for name, field_schema in properties.items():
        definition, is_list = _sub_definition(field_schema, schema_defs)
        value = pruned.get(name)
        if not definition or not value:
            continue
        sub_properties = definition.get('properties') or {}
        if is_list and isinstance(value, list):
            items = [
                prune(sub_properties, schema_defs, item, (*path, name, index))
                for index, item in enumerate(value)
            ]
            pruned[name] = [item for item, _errors in items]
            errors.extend(error for _item, item_errors in items for error in item_errors)
        elif not is_list:
            pruned[name], sub_errors = prune(sub_properties, schema_defs, value, (*path, name))
            errors.extend(sub_errors)

    ruled = {name: rule for name, schema in properties.items() if (rule := _rule(schema))}
    for name, rule in ruled.items():
        _check_target(name, rule, properties, schema_defs)

    # A field can depend on one that is itself hidden, in any declaration order.
    hidden: set[str] = set()
    for _pass in range(len(ruled)):
        newly_hidden = {
            name
            for name, rule in ruled.items()
            if name not in hidden and not rule_matches(rule, lookup(pruned, rule['field']))
        }
        if not newly_hidden:
            break
        hidden |= newly_hidden
        for name in newly_hidden:
            pruned.pop(name, None)

    shown_and_nested = {name for name in ruled if name not in hidden}
    errors = [
        error
        for error in errors
        if len(error['loc']) <= len(path) or error['loc'][len(path)] not in hidden
    ]
    for name in shown_and_nested:
        value = pruned.get(name)
        if ruled[name].get('required') and (value is False or _is_empty(value)):
            message = properties[name].get('unchecked_message') or 'Field required'
            errors.append({'loc': (*path, name), 'msg': message, 'type': 'missing'})
    return pruned, errors


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
