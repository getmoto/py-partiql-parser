import sure  # noqa
from py_partiql_parser._internal.parser import FromParser
from py_partiql_parser._internal.json_parser import Variable


def test_split__single_source():
    FromParser().parse("x").should.equal([{"x": Variable("x")}])


def test_split__multiple_sources():
    FromParser().parse("x,y").should.equal([{"x": Variable("x")}, {"y": Variable("y")}])


def test_split__multiple_sources_with_aliases():
    FromParser().parse("x, y AS z").should.equal(
        [{"x": Variable("x")}, {"z": Variable("y")}]
    )
    FromParser().parse("x AS y,z").should.equal(
        [{"y": Variable("x")}, {"z": Variable("z")}]
    )
    FromParser().parse("a AS b, x AS y").should.equal(
        [{"b": Variable("a")}, {"y": Variable("x")}]
    )


def test_split__single_source_with_alias():
    FromParser().parse("x AS y").should.equal([{"y": Variable("x")}])


def test_split__clauses_with_arrays():
    FromParser().parse("[1, 2, 3] AS y").should.equal([{"y": [1, 2, 3]}])
    FromParser().parse("a AS b, [1, 2, 3] AS y").should.equal(
        [{"b": Variable("a")}, {"y": [1, 2, 3]}]
    )


def test_multiple_rows():
    clause = """[{'a':'legit', 'b':1}, {'a':400, 'b':2}] AS v"""
    expected = [{"v": {"a": "legit", "b": "1"}}, {"v": {"a": "400", "b": "2"}}]
    FromParser().parse(clause).should.equal(expected)
