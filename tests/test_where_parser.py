import pytest
from py_partiql_parser._internal.parser import WhereParser


class TestWhereClause:
    def test_single_key(self):
        where_clause = "s3object.city = 'Chicago'"
        assert WhereParser().parse_where_clause(where_clause) == (
            ["s3object", "city"],
            "Chicago",
        )

    def test_nested_key(self):
        where_clause = "s3object.city.street = 'Chicago'"
        assert WhereParser().parse_where_clause(where_clause) == (
            ["s3object", "city", "street"],
            "Chicago",
        )

    def test_quoted_key(self):
        where_clause = "s3object.\"city\" = 'Chicago'"
        assert WhereParser().parse_where_clause(where_clause) == (
            ["s3object", "city"],
            "Chicago",
        )

    def test_quoted_nested_key(self):
        where_clause = "s3object.\"city details\".street = 'Chicago'"
        assert WhereParser().parse_where_clause(where_clause) == (
            ["s3object", "city details", "street"],
            "Chicago",
        )

    @pytest.mark.xfail(
        message="Multiple clauses are not yet supported - this just returns the first clause at the moment"
    )
    def test_multiple_keys(self):
        where_clause = "s3object.city = 'Chicago', s3object.name = 'Tommy'"
        assert WhereParser().parse_where_clause(where_clause) == (
            ["s3object", "city"],
            "Chicago",
        )


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
        aliases = {"s3object": "s3object"}
        filter_keys = ["s3object", "city"]
        filter_value = "Los Angeles"
        data_key = "s3object"
        assert WhereParser().filter_rows(
            aliases=aliases,
            filter_keys=filter_keys,
            filter_value=filter_value,
            data_key=data_key,
            all_rows=TestFilter.all_rows,
        ) == [{"Name": "Vinod", "city": "Los Angeles"}]

    def test_alias(self):
        aliases = {"s": "s3object"}
        filter_keys = ["s", "city"]
        filter_value = "Los Angeles"
        data_key = "s3object"
        assert WhereParser().filter_rows(
            aliases=aliases,
            filter_keys=filter_keys,
            filter_value=filter_value,
            data_key=data_key,
            all_rows=TestFilter.all_rows,
        ) == [{"Name": "Vinod", "city": "Los Angeles"}]

    def test_alias_nested_key(self):
        aliases = {"s3object": "s3object"}
        filter_keys = ["s3object", "notes", "extra"]
        filter_value = "y"
        data_key = "s3object"
        assert WhereParser().filter_rows(
            aliases=aliases,
            filter_keys=filter_keys,
            filter_value=filter_value,
            data_key=data_key,
            all_rows=TestFilter.all_rows,
        ) == [{"Name": "Mary", "city": "Chicago", "notes": {"extra": "y"}}]

    @pytest.mark.xfail(message="Not yet implemented")
    def test_case_insensitivity(self):
        aliases = {"s3object": "s3object"}
        # Filter by lower case "city"
        filter_keys = ["s3object", "city"]
        filter_value = "Chicago"
        data_key = "s3object"
        # Data has upper case CITY
        all_rows = [
            {"Name": "Sam", "CITY": "Irvine"},
            {"Name": "Vinod", "City": "Los Angeles"},
        ]
        assert WhereParser().filter_rows(
            aliases=aliases,
            filter_keys=filter_keys,
            filter_value=filter_value,
            data_key=data_key,
            all_rows=all_rows,
        ) == [{"Name": "Jane", "City": "Chicago"}]
