import json
from py_partiql_parser import Parser

input_object1 = {"id": {"S": "msg1"}, "body": {"S": "some text"}}
input_object2 = {"id": {"S": "msg2"}, "body": {"S": "other text"}}

simple_doc = json.dumps(input_object1)
double_doc = simple_doc + "\n" + json.dumps(input_object2)


def test_table_with_single_row():
    assert Parser(source_data={"msgs": simple_doc}).parse("select * from msgs") == [
        input_object1
    ]


def test_table_with_multiple_rows():
    assert Parser(source_data={"msgs": double_doc}).parse("select * from msgs") == [
        input_object1,
        input_object2,
    ]
