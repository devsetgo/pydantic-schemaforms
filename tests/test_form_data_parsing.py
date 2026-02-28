from pydantic_schemaforms.form_data import (
    _assign_list_token,
    _assign_mapping_token,
    _assign_nested,
    _coerce_to_list,
    _ensure_list_index,
    _new_container,
    parse_nested_form_data,
)


def test_coerce_form_value_non_string_is_returned_unchanged() -> None:
    parsed = parse_nested_form_data({"count": 5})
    assert parsed == {"count": 5}


def test_coerce_form_value_unknown_string_is_preserved() -> None:
    parsed = parse_nested_form_data({"note": "not-a-bool"})
    assert parsed == {"note": "not-a-bool"}


def test_coerce_form_value_false_like_strings() -> None:
    parsed = parse_nested_form_data({"enabled": "off"})
    assert parsed == {"enabled": False}


def test_parse_nested_form_data_nested_and_boolean_coercion() -> None:
    form_data = {
        "owner": "Casey",
        "pets[0].name": "Fido",
        "pets[0].is_active": "true",
        "pets[1].name": "Mochi",
    }

    parsed = parse_nested_form_data(form_data)

    assert parsed == {
        "owner": "Casey",
        "pets": [
            {"name": "Fido", "is_active": True},
            {"name": "Mochi"},
        ],
    }


def test_parse_nested_form_data_can_disable_value_coercion() -> None:
    parsed = parse_nested_form_data({"enabled": "true"}, coerce_values=False)
    assert parsed == {"enabled": "true"}


def test_parse_nested_form_data_handles_keys_without_path_tokens() -> None:
    parsed = parse_nested_form_data({"[]": "raw"}, coerce_values=False)
    assert parsed == {"[]": "raw"}


def test_assign_nested_expands_list_for_direct_index_assignment() -> None:
    container: dict[str, object] = {"items": []}

    _assign_nested(container, ["items", 2], "third")

    assert container == {"items": [None, None, "third"]}


def test_assign_nested_replaces_none_with_expected_container() -> None:
    dict_container: dict[str, object] = {"profile": None}
    list_container: dict[str, object] = {"pets": None}

    _assign_nested(dict_container, ["profile", "name"], "Ada")
    _assign_nested(list_container, ["pets", 0, "name"], "Milo")

    assert dict_container == {"profile": {"name": "Ada"}}
    assert list_container == {"pets": [{"name": "Milo"}]}


def test_new_container_returns_expected_types() -> None:
    assert _new_container(0) == []
    assert _new_container("name") == {}
    assert _new_container(None) == {}


def test_assign_mapping_token_last_and_non_last_paths() -> None:
    mapping: dict[str, object] = {}

    next_current = _assign_mapping_token(
        mapping,
        "users",
        is_last=False,
        next_token=0,
        value="unused",
    )
    assert mapping == {"users": []}
    assert next_current is mapping["users"]

    end = _assign_mapping_token(
        mapping,
        "status",
        is_last=True,
        next_token=None,
        value="ok",
    )
    assert mapping["status"] == "ok"
    assert end is None


def test_coerce_to_list_returns_existing_list_unchanged() -> None:
    current = [1, 2]
    result = _coerce_to_list(current, ["ignored", 0], 1)
    assert result is current


def test_coerce_to_list_with_idx_zero_does_not_reparent() -> None:
    current = {"x": 1}
    result = _coerce_to_list(current, [0], 0)

    assert result == []
    assert current == {"x": 1}


def test_coerce_to_list_reparents_when_previous_token_is_string() -> None:
    current = {"node": {}}
    result = _coerce_to_list(current, ["node", 0], 1)

    assert result == []
    assert current["node"] == []


def test_ensure_list_index_extends_with_none() -> None:
    values = ["a"]
    _ensure_list_index(values, 3)
    assert values == ["a", None, None, None]


def test_assign_list_token_last_and_non_last_paths() -> None:
    current = []

    next_current = _assign_list_token(
        current,
        0,
        tokens=["items", 0, "name"],
        idx=1,
        is_last=False,
        next_token="name",
        value="unused",
    )
    assert current == [{}]
    assert next_current == {}

    end = _assign_list_token(
        current,
        1,
        tokens=["items", 1],
        idx=1,
        is_last=True,
        next_token=None,
        value="done",
    )
    assert current[1] == "done"
    assert end is None


def test_assign_list_token_uses_reparented_list_for_non_list_current() -> None:
    container = {"node": {"node": {}}}

    _assign_nested(container, ["node", 0, "name"], "Neo")

    assert container == {"node": {"node": [{"name": "Neo"}]}}
