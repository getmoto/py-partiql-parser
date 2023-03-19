import pytest
from py_partiql_parser import Parser
from . import json_as_lines


class TestCount:
    def setup_method(self):
        print("setup")

    def test_count(self):
        query = "select count(*) from s3object"
        result = Parser(source_data={"s3object": json_as_lines}).parse(query)
        assert result == {"_1": 7}

    @pytest.mark.xfail(message="Verify this works against AWS")
    def test_count_with_alias(self):
        query = "select count(s) from s3object as s"
        result = Parser(source_data={"s3object": json_as_lines}).parse(query)
        assert result == {"_1": 7}

    @pytest.mark.xfail(message="Verify this works against AWS")
    def test_count_with_select(self):
        query = "select count(*) from s3object as s where Name = 'Jean'"
        result = Parser(source_data={"s3object": json_as_lines}).parse(query)
        assert result == {"_1": 1}
