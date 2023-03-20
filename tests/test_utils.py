from py_partiql_parser._internal.utils import find_value_in_document


class TestSingleObject:
    def test_single_level(self):
        doc = {"l1": "a"}
        assert find_value_in_document(["l1"], doc) == "a"

    def test_nested(self):
        doc = {"l1": {"l2": "a"}}
        assert find_value_in_document(["l1", "l2"], doc) == "a"

    def test_nonexisting_path(self):
        doc = {"l1": {"l2": "a"}}
        assert find_value_in_document(["l1", "l3"], doc) is None

    def test_deep_nonexisting_path(self):
        doc = {"l1": "a"}
        assert find_value_in_document(["l1", "l2", "l3"], doc) is None
