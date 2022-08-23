import sure  # noqa
from py_partiql_parser._internal.parser import SelectParser
from py_partiql_parser._internal.json_parser import Variable


def test_parse_simple():
    SelectParser().parse("VALUE v").should.equal(Variable("v"))


def test_parse_dict():
    SelectParser().parse("VALUE {'x': 'y'}").should.equal({"x": "y"})


def test_parse_dict_with_variable():
    res = SelectParser().parse("VALUE {'x': y.z}")
    str(res).should.equal("{'x': <y.z>}")
