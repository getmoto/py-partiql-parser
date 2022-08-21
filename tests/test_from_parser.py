import sure  # noqa
from py_partiql_parser._internal.parser import FromParser


def test_split__single_source():
    FromParser().split_clauses("x").should.equal({"x": "x"})


def test_split__multiple_sources():
    FromParser().split_clauses("x,y").should.equal({"x": "x", "y": "y"})


def test_split__multiple_sources_with_aliases():
    FromParser().split_clauses("x, y AS z").should.equal({"x": "x", "z": "y"})
    FromParser().split_clauses("x AS y,z").should.equal({"y": "x", "z": "z"})
    FromParser().split_clauses("a AS b, x AS y").should.equal({"b": "a", "y": "x"})


def test_split__single_source_with_alias():
    FromParser().split_clauses("x AS y").should.equal({"y": "x"})


def test_split__nonliteral_clauses():
    FromParser().split_clauses("[1, 2, 3] AS y").should.equal({"y": "[1, 2, 3]"})
    FromParser().split_clauses("a AS b, [1, 2, 3] AS y").should.equal(
        {"b": "a", "y": "[1, 2, 3]"}
    )
