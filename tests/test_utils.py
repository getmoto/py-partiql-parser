from typing import Dict, Any

import pytest

from py_partiql_parser._internal.utils import find_value_in_document
from py_partiql_parser._internal.utils import find_nested_data_in_object
from py_partiql_parser._internal.utils import CaseInsensitiveDict, MissingVariable


class TestSingleObject:
    def test_single_level(self) -> None:
        doc = {"l1": "a"}
        assert find_value_in_document(["l1"], doc) == "a"

    def test_nested(self) -> None:
        doc = {"l1": {"l2": "a"}}
        assert find_value_in_document(["l1", "l2"], doc) == "a"

    def test_nonexisting_path(self) -> None:
        doc = {"l1": {"l2": "a"}}
        assert find_value_in_document(["l1", "l3"], doc) is None

    def test_deep_nonexisting_path(self) -> None:
        doc = {"l1": "a"}
        assert find_value_in_document(["l1", "l2", "l3"], doc) is None


class TestNestedDataInObject:
    def test_single_level(self) -> None:
        doc = CaseInsensitiveDict({"l1": "a"})
        assert find_nested_data_in_object("l1", doc) == {"l1": "a"}

    def test_nested(self) -> None:
        doc = CaseInsensitiveDict({"l1": {"l2": "a"}})
        assert find_nested_data_in_object("l1.l2", doc) == {"l2": "a"}

    def test_nonexisting_path(self) -> None:
        doc = CaseInsensitiveDict({"l1": {"l2": "a"}})
        assert find_nested_data_in_object("l1.l3", doc) == MissingVariable()

    def test_deep_nonexisting_path(self) -> None:
        doc = CaseInsensitiveDict({"l1": "a"})
        assert find_nested_data_in_object("l1.l2.l3", doc) is None


@pytest.mark.parametrize(
    "values",
    [
        {"key": "value"},
        {"key": ["value"]},
        {"key": {"key1": "value1"}},
    ],
)
def test_copy(values: Dict[str, Any]) -> None:  # type: ignore[misc]
    assert CaseInsensitiveDict(values).copy() == CaseInsensitiveDict(values)


def test_copy_is_different() -> None:
    original = CaseInsensitiveDict({"key": "value"})
    copy = original.copy()
    copy["key"] = "updated"

    assert original == {"key": "value"}
    assert copy == {"key": "updated"}


def test_get_original() -> None:
    original = CaseInsensitiveDict({"kEy": "value"})
    assert "key" in original
    assert "kEy" in original

    regular = original.get_regular()
    assert regular == original
    assert "key" not in regular
    assert "kEy" in regular
