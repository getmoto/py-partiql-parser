import json
import pytest
from py_partiql_parser._internal.json_parser import JsonParser, Variable


def test_static_value():
    assert JsonParser().parse("a") == Variable("a")


def test_dict():
    assert JsonParser().parse(json.dumps({"a": "b"})) == {"a": "b"}
    assert JsonParser().parse("{'a': 'b'}") == {"a": "b"}
    assert JsonParser().parse('{"a": "b"}') == {"a": "b"}


def test_dict_with_spaces_in_keys_and_values():
    assert JsonParser().parse(json.dumps({"a sth": "b sth"})) == {"a sth": "b sth"}


def test_dict_with_multiple_entries():
    assert JsonParser().parse(json.dumps({"a": "b", "c": "d"})) == {"a": "b", "c": "d"}


def test_dict_with_nested_entries():
    original = {"a": {"b1": {"b1.1": "b1.2"}}, "c": "d"}
    assert JsonParser().parse(json.dumps(original)) == original


def test_dict_with_list():
    assert JsonParser().parse(json.dumps({"a": ["b1", "b2"], "c": "d"})) == {
        "a": ["b1", "b2"],
        "c": "d",
    }


def test_list():
    assert JsonParser().parse(json.dumps(["a", "b", "asdfasdf"])) == [
        "a",
        "b",
        "asdfasdf",
    ]


def test_list_with_only_numbers():
    assert JsonParser().parse(json.dumps([1, 1234, 12341234])) == [1, 1234, 12341234]


def test_list_with_numbers_and_strings():
    assert JsonParser().parse(json.dumps(["x", 1324, "y"])) == ["x", 1324, "y"]


def test_list_with_variables():
    assert JsonParser().parse("[v.a, v.b]") == [Variable("v.a"), Variable("v.b")]


def test_dict_with_key_containing_a_special_char():
    assert JsonParser().parse(json.dumps({"a:a": "b"})) == {"a:a": "b"}


def test_dict_with_value_containing_a_special_char():
    assert JsonParser().parse(json.dumps({"a": "b:b"})) == {"a": "b:b"}


def test_dict_containing_a_number():
    original = "[{'a':'legit', 'b':1}, {'a':400, 'b':2}]"
    assert JsonParser().parse(original) == [{"a": "legit", "b": 1}, {"a": 400, "b": 2}]


def test_dict_containing_a_variable():
    original = "[{'a':'legit', 'b':1}, {'a':qwer, 'b':'2'}]"
    assert JsonParser().parse(original) == [
        {"a": "legit", "b": 1},
        {"a": Variable("qwer"), "b": "2"},
    ]


def test_unusual_quotes():
    original = "[{’a’:1, ’b’:true}, {’a’:2, ’b’:null}, {’a’:3}]"
    assert JsonParser().parse(original) == [
        {"a": 1, "b": Variable(True)},
        {"a": 2, "b": Variable(None)},
        {"a": 3},
    ]


def test_parse_multiple_objects():
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
    assert JsonParser().parse(multi_object_string) == [
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
def test_list_and_string_are_siblings(source):
    assert JsonParser().parse(json.dumps(source)) == source
