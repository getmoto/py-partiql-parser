import json
import pytest
from typing import Any
from uuid import uuid4
from py_partiql_parser._internal.json_parser import JsonParser, Variable


def test_static_value() -> None:
    assert next(JsonParser.parse("a")) == Variable("a")


def test_dict() -> None:
    assert next(JsonParser.parse(json.dumps({"a": "b"}))) == {"a": "b"}
    assert next(JsonParser.parse("{'a': 'b'}")) == {"a": "b"}
    assert next(JsonParser.parse('{"a": "b"}')) == {"a": "b"}


def test_dict_with_spaces_in_keys_and_values() -> None:
    assert next(JsonParser.parse(json.dumps({"a sth": "b sth"}))) == {"a sth": "b sth"}


def test_dict_with_multiple_entries() -> None:
    assert next(JsonParser.parse(json.dumps({"a": "b", "c": "d"}))) == {
        "a": "b",
        "c": "d",
    }


def test_dict_with_nested_entries() -> None:
    original = {"a": {"b1": {"b1.1": "b1.2"}}, "c": "d"}
    assert next(JsonParser.parse(json.dumps(original))) == original


def test_dict_with_list() -> None:
    assert next(JsonParser.parse(json.dumps({"a": ["b1", "b2"], "c": "d"}))) == {
        "a": ["b1", "b2"],
        "c": "d",
    }


def test_list() -> None:
    assert next(JsonParser.parse(json.dumps(["a", "b", "asdfasdf"]))) == [
        "a",
        "b",
        "asdfasdf",
    ]


def test_list_with_only_numbers() -> None:
    assert next(JsonParser.parse(json.dumps([1, 1234, 12341234]))) == [
        1,
        1234,
        12341234,
    ]


def test_list_with_numbers_and_strings() -> None:
    assert next(JsonParser.parse(json.dumps(["x", 1324, "y"]))) == ["x", 1324, "y"]


def test_list_with_variables() -> None:
    assert next(JsonParser.parse("[v.a, v.b]")) == [Variable("v.a"), Variable("v.b")]


def test_dict_with_key_containing_a_special_char() -> None:
    assert next(JsonParser.parse(json.dumps({"a:a": "b"}))) == {"a:a": "b"}


def test_dict_with_value_containing_a_special_char() -> None:
    assert next(JsonParser.parse(json.dumps({"a": "b:b"}))) == {"a": "b:b"}


@pytest.mark.parametrize(
    "original",
    [[{"a": "legit", "b": 1}, {"a": 400, "b": 2}], {"a": "legit", "b": {"nr": 25}}],
)
def test_dict_containing_a_number(original: str) -> None:
    assert next(JsonParser.parse(json.dumps(original))) == original


def test_dict_containing_a_variable() -> None:
    original = "[{'a':'legit', 'b':1}, {'a':qwer, 'b':'2'}]"
    assert next(JsonParser.parse(original)) == [
        {"a": "legit", "b": 1},
        {"a": Variable("qwer"), "b": "2"},
    ]


def test_unusual_quotes() -> None:
    original = "[{’a’:1, ’b’:true}, {’a’:2, ’b’:null}, {’a’:3}]"
    assert next(JsonParser.parse(original)) == [
        {"a": 1, "b": True},
        {"a": 2, "b": Variable(None)},
        {"a": 3},
    ]


def test_parse_multiple_objects() -> None:
    """
    An input of multiple objects, separated by a new-line, should result in a list of objects
    """
    multi_object_string = """{"a1": "v1", "a1": "v2"}
    {"a2": "w1",
     "a2": "w2"
    }
{"a3": "z"
}
    
    """
    assert list(JsonParser.parse(multi_object_string)) == [
        {"a1": "v1", "a1": "v2"},
        {"a2": "w1", "a2": "w2"},
        {"a3": "z"},
    ]


@pytest.mark.parametrize(
    "source",
    [
        [{"staff": [{"name": "J M"}], "country": "USA"}],
        {"staff": [{"name": "J M"}], "country": "USA"},
        [{"staff": [{"name": "J M"}, {"name": "M, J"}], "country": "USA"}],
    ],
)
def test_list_and_string_are_siblings(source: Any) -> None:  # type: ignore[misc]
    assert next(JsonParser.parse(json.dumps(source))) == source


def test_bool_parser() -> None:
    assert next(JsonParser.parse(json.dumps({"sth": False}))) == {"sth": False}


def test_multiline_bool_parser() -> None:
    obj1 = {"sth": False}
    obj2 = {"k1": "v1"}
    combined = json.dumps(obj1) + "\n" + json.dumps(obj2)
    assert list(JsonParser.parse(combined)) == [obj1, obj2]


@pytest.mark.parametrize("nr_of_docs", [1, 25, 2500])
def test_large_object(nr_of_docs: int) -> None:
    data = "".join(
        [json.dumps({"pk": f"pk{i}", "data": str(uuid4())}) for i in range(nr_of_docs)]
    )

    res = list(JsonParser.parse(data))
    assert len(res) == nr_of_docs
