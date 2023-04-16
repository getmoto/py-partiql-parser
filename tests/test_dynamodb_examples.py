import json
from py_partiql_parser import DynamoDBStatementParser

input_object1 = {"id": "msg1", "k2": "v2", "body": "some text"}
input_object2 = {
    "id": "msg2",
    "k2": "v2",
    "body": "other text",
    "nested": {"item": "sth"},
}

simple_doc = json.dumps(input_object1)
double_doc = simple_doc + "\n" + json.dumps(input_object2)


def test_table_with_single_row():
    query = "select * from msgs"
    assert DynamoDBStatementParser(source_data={"msgs": simple_doc}).parse(query) == [
        input_object1
    ]


def test_table_with_multiple_rows():
    query = "select * from msgs where body = 'other text'"
    assert DynamoDBStatementParser(source_data={"msgs": double_doc}).parse(
        query, parameters=[]
    ) == [input_object2]


def test_nested_where():
    query = "select * from table where nested.item = 'sth'"
    assert DynamoDBStatementParser(source_data={"table": double_doc}).parse(
        query, parameters=[]
    ) == [input_object2]


def test_nested_where__no_results():
    query = "select * from table where nested.item = 'other'"
    assert (
        DynamoDBStatementParser(source_data={"table": double_doc}).parse(
            query, parameters=[]
        )
        == []
    )


def test_select_single_key():
    query = "select id from table"
    result = DynamoDBStatementParser(source_data={"table": double_doc}).parse(query)
    assert result == [{"id": "msg1"}, {"id": "msg2"}]


def test_select_multiple_keys():
    query = "select id, body from table"
    result = DynamoDBStatementParser(source_data={"table": double_doc}).parse(query)
    assert result == [
        {"id": "msg1", "body": "some text"},
        {"id": "msg2", "body": "other text"},
    ]


def test_select_missing_key():
    query = "select id, nested from table"
    result = DynamoDBStatementParser(source_data={"table": double_doc}).parse(query)
    assert result == [{"id": "msg1"}, {"id": "msg2", "nested": {"item": "sth"}}]


def test_multiple_where_clauses():
    query = "SELECT * from table WHERE k2 = 'v2' and body = 'some text'"
    result = DynamoDBStatementParser(source_data={"table": double_doc}).parse(query)
    assert result == [input_object1]
