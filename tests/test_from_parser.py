import sure  # noqa
from py_partiql_parser._internal.parser import FromParser
from py_partiql_parser._internal.json_parser import Variable


def test_split__single_source():
    _, result = FromParser().parse("x")
    result.should.equal([{"x": Variable("x")}])


def test_split__multiple_sources():
    _, result = FromParser().parse("x,y")
    result.should.equal([{"x": Variable("x")}, {"y": Variable("y")}])


def test_split__multiple_sources_with_aliases():
    _, result = FromParser().parse("x, y AS z")
    result.should.equal([{"x": Variable("x")}, {"z": Variable("y")}])

    _, result = FromParser().parse("x AS y,z")
    result.should.equal([{"y": Variable("x")}, {"z": Variable("z")}])

    _, result = FromParser().parse("a AS b, x AS y")
    result.should.equal([{"b": Variable("a")}, {"y": Variable("x")}])


def test_split__single_source_with_alias():
    _, result = FromParser().parse("x AS y")
    result.should.equal([{"y": Variable("x")}])


def test_split__clauses_with_arrays():
    _, result = FromParser().parse("[1, 2, 3] AS y")
    result.should.equal([{"y": [1, 2, 3]}])

    _, result = FromParser().parse("a AS b, [1, 2, 3] AS y")
    result.should.equal([{"b": Variable("a")}, {"y": [1, 2, 3]}])


def test_multiple_rows():
    clause = """[{'a':'legit', 'b':1}, {'a':400, 'b':2}] AS v"""
    expected = [{"v": {"a": "legit", "b": 1}}, {"v": {"a": 400, "b": 2}}]
    _, result = FromParser().parse(clause)
    result.should.equal(expected)
