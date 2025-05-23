from typing import Any

from py_partiql_parser._internal.where_parser import WhereParser
from py_partiql_parser._internal.where_parser import S3WhereParser
from py_partiql_parser._internal.where_parser import DynamoDBWhereParser
from py_partiql_parser._internal.where_parser import (
    WhereClause,
    WhereAndClause,
    WhereOrClause,
)


class TestWhereClause:
    def test_single_key(self) -> None:
        where_clause = "s3object.city = 'Chicago'"
        assert WhereParser.parse_where_clause(where_clause) == WhereClause(
            fn="=", left=["s3object", "city"], right="Chicago"
        )

    def test_single_key_surrounded_by_parentheses(self) -> None:
        where_clause = "(city = 'Chicago')"
        assert WhereParser.parse_where_clause(where_clause) == WhereClause(
            fn="=", left=["city"], right="Chicago"
        )

    def test_nested_key(self) -> None:
        where_clause = "s3object.city.street = 'Chicago'"
        assert WhereParser.parse_where_clause(where_clause) == WhereClause(
            fn="=", left=["s3object", "city", "street"], right="Chicago"
        )

    def test_quoted_key(self) -> None:
        where_clause = "s3object.\"city\" = 'Chicago'"
        assert WhereParser.parse_where_clause(where_clause) == WhereClause(
            fn="=", left=["s3object", "city"], right="Chicago"
        )

    def test_quoted_nested_key(self) -> None:
        where_clause = "s3object.\"city details\".street = 'Chicago'"
        assert WhereParser.parse_where_clause(where_clause) == WhereClause(
            fn="=", left=["s3object", "city details", "street"], right="Chicago"
        )

    def test_multiple_keys__and(self) -> None:
        where_clause = "s3.city = 'Chicago' AND s3.name = 'Tommy'"
        expected = WhereAndClause(
            WhereClause(fn="=", left=["s3", "city"], right="Chicago")
        )
        expected.children.append(
            WhereClause(fn="=", left=["s3", "name"], right="Tommy")
        )
        assert WhereParser.parse_where_clause(where_clause) == expected

    def test_multiple_keys_with_question_marks(self) -> None:
        where_clause = "s3.city = ? AND s3.name = ?"
        expected = WhereAndClause(WhereClause(fn="=", left=["s3", "city"], right="?"))
        expected.children.append(WhereClause(fn="=", left=["s3", "name"], right="?"))
        assert WhereParser.parse_where_clause(where_clause) == expected

    def test_multiple_keys__or(self) -> None:
        where_clause = "s3.city = 'Chicago' OR s3.name = 'Tommy'"
        expected = WhereOrClause(
            WhereClause(fn="=", left=["s3", "city"], right="Chicago")
        )
        expected.children.append(
            WhereClause(fn="=", left=["s3", "name"], right="Tommy")
        )
        assert WhereParser.parse_where_clause(where_clause) == expected

    def test_multiple_keys__and_and_or(self) -> None:
        where_clause = "(city = 'Chicago' AND name = 'Tommy') OR stuff = 'sth'"
        left = WhereAndClause(WhereClause(fn="=", left=["city"], right="Chicago"))
        left.children.append(WhereClause(fn="=", left=["name"], right="Tommy"))
        expected = WhereOrClause(left)
        expected.children.append(WhereClause(fn="=", left=["stuff"], right="sth"))
        assert WhereParser.parse_where_clause(where_clause) == expected

    def test_multiple_keys__or_and_and(self) -> None:
        where_clause = "stuff = 'sth' or (city = 'Chicago' AND name = 'Tommy')"
        right = WhereAndClause(WhereClause(fn="=", left=["city"], right="Chicago"))
        right.children.append(WhereClause(fn="=", left=["name"], right="Tommy"))
        expected = WhereAndClause(WhereClause(fn="=", left=["stuff"], right="sth"))
        expected.children.append(right)
        assert WhereParser.parse_where_clause(where_clause) == expected

    def test_number_operators_and_is_not_missing(self) -> None:
        where_clause = "Price >= 0 AND Price <= 1 AND FreeTier IS NOT MISSING AND attribute_type(\"FreeTier\", 'N')"
        result = WhereParser.parse_where_clause(where_clause)

        flat_results = []

        def _get_root_clause(clause: Any) -> None:
            if isinstance(clause, WhereAndClause):
                for c in clause.children:
                    if isinstance(c, WhereAndClause):
                        _get_root_clause(c)
                flat_results.extend(
                    [c for c in clause.children if not isinstance(c, WhereAndClause)]
                )
            else:
                flat_results.append(clause)

        _get_root_clause(result)
        assert len(flat_results) == 4

        assert WhereClause(left=["Price"], fn=">=", right="0") in flat_results
        assert WhereClause(left=["Price"], fn="<=", right="1") in flat_results
        assert (
            WhereClause(left=["FreeTier"], fn="is", right="NOT MISSING") in flat_results
        )
        assert (
            WhereClause(left=["FreeTier"], fn="attribute_type", right="N")
            in flat_results
        )

    def test_contains(self) -> None:
        where_clause = "(contains(\"city\", 'dam'))"
        expected = WhereClause(fn="contains", left=["city"], right="dam")
        assert WhereParser.parse_where_clause(where_clause) == expected

    def test_multiple_contains(self) -> None:
        where_clause = "(contains(\"city\", 'dam') and contains(\"find\", 'things'))"
        left = WhereClause(fn="contains", left=["city"], right="dam")
        right = WhereClause(fn="contains", left=["find"], right="things")
        expected = WhereAndClause(left)
        expected.children.append(right)
        assert WhereParser.parse_where_clause(where_clause) == expected

    def test_comparisons(self) -> None:
        where_clause = "size >= 20"
        expected = WhereClause(fn=">=", left=["size"], right="20")
        assert WhereParser.parse_where_clause(where_clause) == expected

    def test_missing(self) -> None:
        where_clause = "size IS MISSING"
        expected = WhereClause(fn="IS", left=["size"], right="MISSING")
        assert WhereParser.parse_where_clause(where_clause) == expected

    def test_not_missing(self) -> None:
        where_clause = "size IS NOT MISSING"
        expected = WhereClause(fn="IS", left=["size"], right="NOT MISSING")
        assert WhereParser.parse_where_clause(where_clause) == expected

    def test_attribute_type(self) -> None:
        # This is only applicable for DynamoDB
        # Parsing is the same though - it's just a function like any other
        where_clause = "attribute_type(\"FreeTier\", 'N')"
        expected = WhereClause(fn="attribute_type", left=["FreeTier"], right="N")
        assert WhereParser.parse_where_clause(where_clause) == expected

    def test_where_values_contain_parentheses(self) -> None:
        # Parentheses are a special case in case of nested clauses
        # But should be processed correctly when they are part of a value
        where_clause = "sth = 's(meth)ng'"
        expected = WhereClause(fn="=", left=["sth"], right="s(meth)ng")
        assert WhereParser.parse_where_clause(where_clause) == expected


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

    def test_simple(self) -> None:
        query = "s3.city = 'Los Angeles'"
        assert not S3WhereParser.applies(
            doc={"Name": "Sam", "city": "Irvine"},
            table_prefix="s3",
            _where_clause=query,
        )
        assert not S3WhereParser.applies(
            doc={"Name": "Sam", "city": "Seattle"},
            table_prefix="s3",
            _where_clause=query,
        )
        assert not S3WhereParser.applies(
            doc={"Name": "Sam", "city": "Chicago"},
            table_prefix="s3",
            _where_clause=query,
        )
        assert not S3WhereParser.applies(
            doc={"Name": "Sam"}, table_prefix="s3", _where_clause=query
        )

        assert S3WhereParser.applies(
            doc={"Name": "Sam", "city": "Los Angeles"},
            table_prefix="s3",
            _where_clause=query,
        )

    def test_alias_nested_key(self) -> None:
        query = "s3.notes.extra = 'y'"
        assert not S3WhereParser.applies(
            doc={"Name": "Sam", "city": "Chicago"},
            table_prefix="s3",
            _where_clause=query,
        )
        assert not S3WhereParser.applies(
            doc={"Name": "Sam"}, table_prefix="s3", _where_clause=query
        )

        assert S3WhereParser.applies(
            doc={"Name": "Sam", "notes": {"extra": "y"}},
            table_prefix="s3",
            _where_clause=query,
        )


class TestDynamoDBParse:
    def test_parameters(self) -> None:
        data = [
            {
                "id": {"S": "msg1"},
                "k2": {"S": "v2"},
                "body": {"M": {"data": {"S": "some text"}}},
            }
        ]
        parser = DynamoDBWhereParser(source_data=data)  # type: ignore[arg-type]
        resp = parser.parse(
            "body = ?", parameters=[{"M": {"data": {"S": "some text"}}}]
        )
        assert resp == data
