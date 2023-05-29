from py_partiql_parser._internal.where_parser import WhereParser
from py_partiql_parser._internal.where_parser import S3WhereParser
from py_partiql_parser._internal.where_parser import DynamoDBWhereParser


class TestWhereClause:
    def test_single_key(self):
        where_clause = "s3object.city = 'Chicago'"
        assert WhereParser.parse_where_clause(where_clause) == [
            (
                ["s3object", "city"],
                "Chicago",
            )
        ]

    def test_nested_key(self):
        where_clause = "s3object.city.street = 'Chicago'"
        assert WhereParser.parse_where_clause(where_clause) == [
            (
                ["s3object", "city", "street"],
                "Chicago",
            )
        ]

    def test_quoted_key(self):
        where_clause = "s3object.\"city\" = 'Chicago'"
        assert WhereParser.parse_where_clause(where_clause) == [
            (
                ["s3object", "city"],
                "Chicago",
            )
        ]

    def test_quoted_nested_key(self):
        where_clause = "s3object.\"city details\".street = 'Chicago'"
        assert WhereParser.parse_where_clause(where_clause) == [
            (
                ["s3object", "city details", "street"],
                "Chicago",
            )
        ]

    def test_multiple_keys(self):
        where_clause = "s3.city = 'Chicago' AND s3.name = 'Tommy'"
        assert WhereParser.parse_where_clause(where_clause) == [
            (
                ["s3", "city"],
                "Chicago",
            ),
            (["s3", "name"], "Tommy"),
        ]

    def test_multiple_keys_with_question_marks(self):
        where_clause = "s3.city = ? AND s3.name = ?"
        assert WhereParser.parse_where_clause(where_clause) == [
            (
                ["s3", "city"],
                "?",
            ),
            (["s3", "name"], "?"),
        ]


class TestFilter:
    all_rows = [
        {"Name": "Sam", "city": "Irvine"},
        {"Name": "Vinod", "city": "Los Angeles"},
        {"Name": "Jeff", "city": "Seattle"},
        {"Name": "Jane", "city": "Chicago"},
        {"Name": "Sean", "city": "Chicago"},
        {"Name": "Mary", "city": "Chicago", "notes": {"extra": "y"}},
        {"Name": "Kate", "city": "Chicago", "notes": {"extra": "n"}},
    ]

    def test_simple(self):
        filter_keys = ["city"]
        filter_value = "Los Angeles"
        assert S3WhereParser(TestFilter.all_rows).filter_rows(
            _filters=[(filter_keys, filter_value)]
        ) == [{"Name": "Vinod", "city": "Los Angeles"}]

    def test_without_prefix(self):
        filter_keys = ["city"]
        filter_value = "Los Angeles"
        assert DynamoDBWhereParser(TestFilter.all_rows).filter_rows(
            _filters=[(filter_keys, filter_value)]
        ) == [{"Name": "Vinod", "city": "Los Angeles"}]

    def test_alias(self):
        filter_keys = ["city"]
        filter_value = "Los Angeles"
        assert S3WhereParser(TestFilter.all_rows).filter_rows(
            _filters=[(filter_keys, filter_value)]
        ) == [{"Name": "Vinod", "city": "Los Angeles"}]

    def test_alias_nested_key(self):
        filter_keys = ["notes", "extra"]
        filter_value = "y"
        assert S3WhereParser(TestFilter.all_rows).filter_rows(
            _filters=[(filter_keys, filter_value)]
        ) == [{"Name": "Mary", "city": "Chicago", "notes": {"extra": "y"}}]


class TestDynamoDBParse:
    def test_parameters(self):
        parser = DynamoDBWhereParser(source_data=TestFilter.all_rows)
        resp = parser.parse("notes = ?", parameters=[{"extra": "n"}])
        assert resp == [{"Name": "Kate", "city": "Chicago", "notes": {"extra": "n"}}]
