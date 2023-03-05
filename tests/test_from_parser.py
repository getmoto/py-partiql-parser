import sure  # noqa
from py_partiql_parser._internal.parser import FromParser
from py_partiql_parser._internal.json_parser import Variable


def test_split__single_source():
    result = FromParser().parse("x")
    result.should.equal({"x": "x"})


def test_split__multiple_sources():
    result = FromParser().parse("x,y")
    result.should.equal({"x": "x", "y": "y"})


def test_split__multiple_sources_with_aliases():
    result = FromParser().parse("x, y AS z")
    result.should.equal({"x": "x", "z": "y"})

    result = FromParser().parse("x AS y,z")
    result.should.equal({"y": "x", "z": "z"})

    result = FromParser().parse("a AS b, x AS y")
    result.should.equal({"b": "a", "y": "x"})


def test_split__single_source_with_alias():
    result = FromParser().parse("x AS y")
    result.should.equal({"y": "x"})


def test_split__clauses_with_arrays():
    result = FromParser().parse("[1, 2, 3] AS y")
    result.should.equal({"y": "[1, 2, 3]"})

    result = FromParser().parse("a AS b, [1, 2, 3] AS y")
    result.should.equal({"b": "a", "y": "[1, 2, 3]"})


def test_multiple_rows():
    clause = """[{'a':'legit', 'b':1}, {'a':400, 'b':2}] AS v"""
    expected = {"v": "[{'a':'legit', 'b':1}, {'a':400, 'b':2}]"}
    result = FromParser().parse(clause)
    result.should.equal(expected)
