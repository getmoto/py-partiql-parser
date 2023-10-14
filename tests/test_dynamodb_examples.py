import pytest
from py_partiql_parser import DynamoDBStatementParser
from py_partiql_parser.exceptions import ParserException
from py_partiql_parser._packages.boto3.types import TypeSerializer, TypeDeserializer

serializer = TypeSerializer()
deserializer = TypeDeserializer()


input_object1 = {"id": {"S": "msg1"}, "k2": {"S": "v2"}, "body": {"S": "some text"}}
input_object2 = {
    "id": {"S": "msg2"},
    "k2": {"S": "v2"},
    "body": {"S": "other text"},
    "catchup": {"BOOL": True},
    "not_catchup": {"BOOL": False},
    "list_of_bools": {"L": [{"BOOL": True}, {"BOOL": False}]},
    "list_of_ints": {"L": [{"N": "42"}, {"N": "7"}]},
    "nested": {"M": {"item": {"S": "sth"}}},
    "bool_at_end": {"BOOL": False},
}
input_object3 = {"id": {"S": "msg3"}, "body": {"S": "irrelevant"}}

simple_doc = [input_object1]
double_doc = [input_object1, input_object2, input_object3]


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
    assert result == [
        {"id": {"S": "msg1"}},
        {"id": {"S": "msg2"}},
        {"id": {"S": "msg3"}},
    ]


def test_select_multiple_keys():
    query = "select id, body from table"
    result = DynamoDBStatementParser(source_data={"table": double_doc}).parse(query)
    assert result == [
        {"id": {"S": "msg1"}, "body": {"S": "some text"}},
        {"id": {"S": "msg2"}, "body": {"S": "other text"}},
        {"id": {"S": "msg3"}, "body": {"S": "irrelevant"}},
    ]


def test_select_missing_key():
    query = "select id, nested from table"
    result = DynamoDBStatementParser(source_data={"table": double_doc}).parse(query)
    assert result == [
        {"id": {"S": "msg1"}},
        {"id": {"S": "msg2"}, "nested": {"M": {"item": {"S": "sth"}}}},
        {"id": {"S": "msg3"}},
    ]


def test_multiple_where_clauses():
    query = "SELECT * from table WHERE k2 = 'v2' and body = 'some text'"
    result = DynamoDBStatementParser(source_data={"table": double_doc}).parse(query)
    assert result == [input_object1]


def test_search_object_inside_a_list():
    # TODO: try sets as well
    # StringSets, NumberSets, BinarySets

    # L -> M
    obj = [
        {
            "a1": serializer.serialize([{"name": "lvyan"}]),
            "a2": serializer.serialize("b2"),
        }
    ]
    print(obj)
    query = "select * from table where a1[0].name = 'lvyan'"
    assert DynamoDBStatementParser(source_data={"table": obj}).parse(query) == obj

    # L -> M -> M
    obj = [{"a1": serializer.serialize([{"name": {"first_name": "lvyan"}}])}]
    query = "select * from table where a1[0].name.first_name = 'lvyan'"
    assert DynamoDBStatementParser(source_data={"table": obj}).parse(query) == obj

    # M -> L -> M
    obj = [{"a1": serializer.serialize({"names": [{"first_name": "lvyan"}]})}]
    query = "select * from table where a1.names[0].first_name = 'lvyan'"
    assert DynamoDBStatementParser(source_data={"table": obj}).parse(query) == obj

    # L -> L
    obj = [{"a1": serializer.serialize([{"b1": [{"name": "lvyan"}]}])}]
    query = "select * from table where a1[0].b1[0].name = 'lvyan'"
    assert DynamoDBStatementParser(source_data={"table": obj}).parse(query) == obj

    # Search name, but the where-clause is not a list
    query = "select * from table where a2[0].name = 'lvyan'"
    result = DynamoDBStatementParser(source_data={"table": obj}).parse(query)
    assert result == []

    # Search name, but the where-clause wants a list-item that does not exist
    query = "select * from table where a1[5].name = 'lvyan'"
    result = DynamoDBStatementParser(source_data={"table": obj}).parse(query)
    assert result == []


def test_table_starting_with_number():
    query = "SELECT * from 0table"
    with pytest.raises(ParserException) as exc:
        DynamoDBStatementParser(source_data={"table": double_doc}).parse(query)
    assert exc.value.message == "Aliasing is not supported"
    assert exc.value.name == "ValidationException"

    query = 'SELECT * FROM "0table"'
    assert (
        DynamoDBStatementParser(source_data={"0table": double_doc}).parse(query)
        == double_doc
    )
