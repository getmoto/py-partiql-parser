from py_partiql_parser._internal.parser import FromParser


def test_split__single_source() -> None:
    parser = FromParser("x")
    assert parser.clauses == {"x": "x"}


def test_split__multiple_sources() -> None:
    parser = FromParser("x,y")
    assert parser.clauses == {"x": "x", "y": "y"}


def test_split__multiple_sources_with_aliases() -> None:
    parser = FromParser("x, y AS z")
    assert parser.clauses == {"x": "x", "z": "y"}

    parser = FromParser("x AS y,z")
    assert parser.clauses == {"y": "x", "z": "z"}

    parser = FromParser("a AS b, x AS y")
    assert parser.clauses == {"b": "a", "y": "x"}


def test_split__single_source_with_alias() -> None:
    parser = FromParser("x AS y")
    assert parser.clauses == {"y": "x"}


def test_split__clauses_with_arrays() -> None:
    parser = FromParser("[1, 2, 3] AS y")
    assert parser.clauses == {"y": "[1, 2, 3]"}

    parser = FromParser("a AS b, [1, 2, 3] AS y")
    assert parser.clauses == {"b": "a", "y": "[1, 2, 3]"}


def test_multiple_rows() -> None:
    clause = """[{'a':'legit', 'b':1}, {'a':400, 'b':2}] AS v"""
    expected = {"v": "[{'a':'legit', 'b':1}, {'a':400, 'b':2}]"}
    parser = FromParser(clause)
    assert parser.clauses == expected
