import pytest
from py_partiql_parser import S3SelectParser
from . import json_as_lines


class TestCount:
    def setup_method(self) -> None:
        self.parser = S3SelectParser(source_data={"s3object": json_as_lines})

    @pytest.mark.parametrize(
        "query,key,result",
        [
            ["select count(*) from s3object", "_1", 7],
            ["select count(s) from s3object s", "_1", 7],
            ["select count(s) from s3object as s", "_1", 7],
            ["select count(*) from s3object where s3object.Name = 'Jane'", "_1", 1],
        ],
    )
    def test_count(self, query: str, key: str, result: int) -> None:
        assert self.parser.parse(query) == [{key: result}]

    @pytest.mark.xfail(reason="Not yet implemented")
    @pytest.mark.parametrize(
        "query,key,result",
        [
            ["select count(*) as cnt from s3object", "cnt", 7],
        ],
    )
    def test_count_failures(self, query: str, key: str, result: int) -> None:
        assert self.parser.parse(query) == [{key: result}]
