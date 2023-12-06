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
