import pytest
from py_partiql_parser._internal.select_parser import SelectParser
from py_partiql_parser._internal.select_parser import SelectClause, FunctionClause


def test_select_all_clause():
    result = SelectParser(table_prefix=None).parse_clauses("*")
    assert result == [SelectClause("*")]


def test_parse_simple_clause():
    result = SelectParser(table_prefix=None).parse_clauses("s.name")
    assert result == [SelectClause("s.name")]


def test_parse_multiple_clauses():
    result = SelectParser(table_prefix=None).parse_clauses("s.name, s.city")
    assert result == [SelectClause("s.name"), SelectClause("s.city")]


def test_parse_function_clause():
    result = SelectParser(table_prefix=None).parse_clauses("count(*)")
    assert result == [FunctionClause(function_name="count", value="*")]


@pytest.mark.xfail(message="Not yet implemented")
def test_parse_function_alias_clause():
    result = SelectParser(table_prefix=None).parse_clauses("count(*) as cnt")
    assert result == [FunctionClause(function_name="count", value="*")]


def test_parse_mix_of_function_and_regular_clauses():
    result = SelectParser(table_prefix=None).parse_clauses(
        "count(*), s.city, max(s.citizens)"
    )
    assert len(result) == 3
    assert FunctionClause(function_name="count", value="*") in result
    assert FunctionClause(function_name="max", value="s.citizens") in result
    assert SelectClause(value="s.city") in result
