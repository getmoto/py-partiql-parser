import sure  # noqa
from py_partiql_parser._internal.parser import FromParser


def test_split__single_source():
    FromParser().parse("x").should.equal({"x": "x"})


def test_split__multiple_sources():
    FromParser().parse("x,y").should.equal({"x": "x", "y": "y"})


def test_split__multiple_sources_with_aliases():
    FromParser().parse("x, y AS z").should.equal({"x": "x", "z": "y"})
    FromParser().parse("x AS y,z").should.equal({"y": "x", "z": "z"})
    FromParser().parse("a AS b, x AS y").should.equal({"b": "a", "y": "x"})


def test_split__single_source_with_alias():
    FromParser().parse("x AS y").should.equal({"y": "x"})


def test_split__nonliteral_clauses():
    FromParser().parse("[1, 2, 3] AS y").should.equal({"y": "[1, 2, 3]"})
    FromParser().parse("a AS b, [1, 2, 3] AS y").should.equal(
        {"b": "a", "y": "[1, 2, 3]"}
    )
