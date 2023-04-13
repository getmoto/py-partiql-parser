import json
from py_partiql_parser import Parser

input_object1 = {"id": "msg1", "body": "some text"}
input_object2 = {"id": "msg2", "body": "other text", "nested": {"item": "sth"}}

simple_doc = json.dumps(input_object1)
double_doc = simple_doc + "\n" + json.dumps(input_object2)


def test_table_with_single_row():
    query = "select * from msgs"
    assert Parser(source_data={"msgs": simple_doc}).parse(query) == [input_object1]


def test_table_with_multiple_rows():
    query = "select * from msgs where body = 'other text'"
    assert Parser(source_data={"msgs": double_doc}, query_has_table_prefix=False).parse(
        query
    ) == [input_object2]


def test_nested_where():
    query = "select * from table where nested.item = 'sth'"
    assert Parser(
        source_data={"table": double_doc}, query_has_table_prefix=False
    ).parse(query) == [input_object2]


def test_nested_where__no_results():
    query = "select * from table where nested.item = 'other'"
    assert (
        Parser(source_data={"table": double_doc}, query_has_table_prefix=False).parse(
            query
        )
        == []
    )
