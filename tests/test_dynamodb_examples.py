import pytest
from typing import Any, Dict, List

from py_partiql_parser import DynamoDBStatementParser
from py_partiql_parser.exceptions import ParserException
from py_partiql_parser._packages.boto3.types import TypeSerializer, TypeDeserializer

serializer = TypeSerializer()
deserializer = TypeDeserializer()


input_object1: Dict[str, Any] = {
    "id": {"S": "msg1"},
    "k2": {"S": "v2"},
    "body": {"S": "some text"},
}
input_object2: Dict[str, Any] = {
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
input_object3: Dict[str, Any] = {"id": {"S": "msg3"}, "body": {"S": "irrelevant"}}

simple_doc = [input_object1]
double_doc = [input_object1, input_object2, input_object3]


def test_table_with_single_row() -> None:
    query = "select * from msgs"
    source = {"msgs": simple_doc}
    assert _get_result(query, source) == [input_object1]


def test_table_with_multiple_rows() -> None:
    query = "select * from msgs where body = 'other text'"
    assert _get_result(query, source={"msgs": double_doc}) == [input_object2]


def test_nested_where() -> None:
    query = "select * from table where nested.item = 'sth'"
    assert _get_result(query, source={"table": double_doc}) == [input_object2]


def test_nested_where__no_results() -> None:
    query = "select * from table where nested.item = 'other'"
    assert _get_result(query, source={"table": double_doc}) == []


def test_select_single_key() -> None:
    query = "select id from table"
    assert _get_result(query, source={"table": double_doc}) == [
        {"id": {"S": "msg1"}},
        {"id": {"S": "msg2"}},
        {"id": {"S": "msg3"}},
    ]


def test_select_multiple_keys() -> None:
    query = "select id, body from table"
    assert _get_result(query, source={"table": double_doc}) == [
        {"id": {"S": "msg1"}, "body": {"S": "some text"}},
        {"id": {"S": "msg2"}, "body": {"S": "other text"}},
        {"id": {"S": "msg3"}, "body": {"S": "irrelevant"}},
    ]


def test_select_missing_key() -> None:
    query = "select id, nested from table"
    assert _get_result(query, source={"table": double_doc}) == [
        {"id": {"S": "msg1"}},
        {"id": {"S": "msg2"}, "nested": {"M": {"item": {"S": "sth"}}}},
        {"id": {"S": "msg3"}},
    ]


def test_multiple_where_clauses() -> None:
    query = "SELECT * from table WHERE k2 = 'v2' and body = 'some text'"
    assert _get_result(query, source={"table": double_doc}) == [input_object1]


def test_search_object_inside_a_list() -> None:
    # TODO: try sets as well
    # StringSets, NumberSets, BinarySets

    # L -> M
    obj = [
        {
            "A1": serializer.serialize([{"name": "lvyan"}]),
            "a2": serializer.serialize("b2"),
        }
    ]
    query = "select * from table where a1[0].name = 'lvyan'"
    assert _get_result(query, source={"table": obj}) == obj

    # L -> M -> M
    obj = [{"a1": serializer.serialize([{"name": {"first_name": "lvyan"}}])}]
    query = "select * from table where a1[0].name.first_name = 'lvyan'"
    assert _get_result(query, source={"table": obj}) == obj

    # M -> L -> M
    obj = [{"a1": serializer.serialize({"names": [{"first_name": "lvyan"}]})}]
    query = "select * from table where a1.names[0].first_name = 'lvyan'"
    assert _get_result(query, source={"table": obj}) == obj

    # L -> L
    obj = [{"a1": serializer.serialize([{"b1": [{"name": "lvyan"}]}])}]
    query = "select * from table where a1[0].b1[0].name = 'lvyan'"
    assert _get_result(query, source={"table": obj}) == obj

    # Search name, but the where-clause is not a list
    query = "select * from table where a2[0].name = 'lvyan'"
    assert _get_result(query, source={"table": obj}) == []

    # Search name, but the where-clause wants a list-item that does not exist
    query = "select * from table where a1[5].name = 'lvyan'"
    assert _get_result(query, source={"table": obj}) == []


def test_table_starting_with_number() -> None:
    query = "SELECT * from 0table"
    with pytest.raises(ParserException) as exc:
        DynamoDBStatementParser(source_data={"table": double_doc}).parse(query)
    assert exc.value.message == "Aliasing is not supported"
    assert exc.value.name == "ValidationException"

    query = 'SELECT * FROM "0table"'
    assert _get_result(query, source={"0table": double_doc}) == double_doc


items: List[Dict[str, Any]] = [
    {
        "Id": {"S": "0"},
        "Name": {"S": "Lambda"},
        "NameLower": {"S": "lambda"},
        "Description": {"S": "Run code in under 15 minutes"},
        "DescriptionLower": {"S": "run code in under 15 minutes"},
        "Price": {"N": "2E-7"},
        "Unit": {"S": "invocation"},
        "Category": {"S": "free"},
        "FreeTier": {"N": "1E+6"},
    },
    {
        "Id": {"S": "1"},
        "Name": {"S": "Auto Scaling"},
        "NameLower": {"S": "auto scaling"},
        "Description": {
            "S": "Automatically scale the number of EC2 instances with demand"
        },
        "DescriptionLower": {
            "S": "automatically scale the number of ec2 instances with demand"
        },
        "Price": {"N": "0"},
        "Unit": {"S": "group"},
        "Category": {"S": "free"},
        "FreeTier": {"NULL": True},
    },
    {
        "Id": {"S": "2"},
        "Name": {"S": "EC2"},
        "NameLower": {"S": "ec2"},
        "Description": {"S": "Servers in the cloud"},
        "DescriptionLower": {"S": "servers in the cloud"},
        "Price": {"N": "7.2"},
        "Unit": {"S": "instance"},
        "Category": {"S": "trial"},
    },
    {
        "Id": {"S": "3"},
        "Name": {"S": "Config"},
        "NameLower": {"S": "config"},
        "Description": {"S": "Audit the configuration of AWS resources"},
        "DescriptionLower": {"S": "audit the configuration of aws resources"},
        "Price": {"N": "0.003"},
        "Unit": {"S": "configuration item"},
        "Category": {"S": "paid"},
    },
]


def test_complex_where_clauses() -> None:
    # IS MISSING
    query = "SELECT Id from table where FreeTier IS MISSING"
    assert _get_result(query, {"table": items}) == [
        {"Id": {"S": "2"}},
        {"Id": {"S": "3"}},
    ]

    # IS NOT MISSING
    query = "SELECT Id from table where FreeTier IS NOT MISSING"
    assert _get_result(query, {"table": items}) == [
        {"Id": {"S": "0"}},
        {"Id": {"S": "1"}},
    ]

    # CONTAINS
    query = "SELECT Id from table where contains(\"DescriptionLower\", 'cloud')"
    assert _get_result(query, {"table": items}) == [{"Id": {"S": "2"}}]

    # <
    query = "SELECT Id from table where Price < 1"
    assert _get_result(query, {"table": items}) == [
        {"Id": {"S": "0"}},
        {"Id": {"S": "1"}},
        {"Id": {"S": "3"}},
    ]

    # >=
    query = "SELECT Id from table where Price >= 7.2"
    assert _get_result(query, source={"table": items}) == [{"Id": {"S": "2"}}]

    # attribute_type
    query = "SELECT Id from table where attribute_type(\"FreeTier\", 'N')"
    assert _get_result(query, source={"table": items}) == [{"Id": {"S": "0"}}]

    # FULL
    query = f"SELECT Id FROM \"table\" WHERE (contains(\"NameLower\", 'code') OR contains(\"DescriptionLower\", 'code')) AND Category = 'free' AND Price >= 0 AND Price <= 1 AND FreeTier IS NOT MISSING AND attribute_type(\"FreeTier\", 'N')"
    assert _get_result(query, source={"table": items}) == [{"Id": {"S": "0"}}]


def _get_result(query: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
    return_value, updates = DynamoDBStatementParser(source_data=source).parse(query)
    return return_value


def test_update_non_existing_attr() -> None:
    query = "UPDATE 'table' SET attr='updated' WHERE Id='2'"
    return_value, updates = DynamoDBStatementParser(source_data={"table": items}).parse(
        query
    )

    item_to_update = items[2]
    updated_item = items[2].copy()
    updated_item["attr"] = {"S": "updated"}

    assert return_value == []
    assert updates == {"table": [(item_to_update, updated_item)]}


def test_update_with_multiple_keys() -> None:
    query = "UPDATE 'table' SET attr='updated' WHERE Id='id1' AND Sk='oth'"
    items = [
        {"id": {"S": "id1"}, "Sk": {"S": "sth"}},
        {"id": {"S": "id1"}, "Sk": {"S": "oth"}},
        {"id": {"S": "id1"}},  # missing field
    ]
    return_value, updates = DynamoDBStatementParser(source_data={"table": items}).parse(
        query
    )

    assert return_value == []
    updated_item = items[1].copy()
    updated_item["attr"] = {"S": "updated"}
    assert updates == {"table": [(items[1], updated_item)]}


def test_update_with_quoted_attributes_and_parameters() -> None:
    # Note that the table is without parameters
    query = 'UPDATE users SET "first_name" = ?, "last_name" = ? WHERE "id"= ?'
    items = [
        {"id": {"S": "yes"}, "first_name": {"S": "old"}, "last_name": {"S": "old"}},
        {"id": {"S": "no"}, "first_name": {"S": "old"}, "last_name": {"S": "old"}},
    ]
    return_value, updates = DynamoDBStatementParser(source_data={"users": items}).parse(
        query, parameters=[{"S": "fn"}, {"S": "ln"}, {"S": "yes"}]
    )

    assert return_value == []
    assert len(updates["users"]) == 1
    old, new = updates["users"][0]
    assert old == {
        "id": {"S": "yes"},
        "first_name": {"S": "old"},
        "last_name": {"S": "old"},
    }
    assert new == {
        "id": {"S": "yes"},
        "first_name": {"S": "fn"},
        "last_name": {"S": "ln"},
    }


def test_update_remove() -> None:
    query = "UPDATE 'table' REMOVE attr WHERE Id='id1'"
    items = [
        {"id": {"S": "id1"}, "attr": {"S": "sth"}},
        {"id": {"S": "id2"}, "attr": {"S": "oth"}},
        {"id": {"S": "id3"}},  # missing field
    ]
    return_value, updates = DynamoDBStatementParser(source_data={"table": items}).parse(
        query
    )

    assert return_value == []
    updated_item = items[0].copy()
    updated_item.pop("attr")
    assert updates == {"table": [(items[0], updated_item)]}


@pytest.mark.parametrize(
    "query",
    ["DELETE FROM 'tablename' WHERE Id='id1'", "DELETE FROM tablename WHERE Id='id1'"],
)
def test_delete(query: str) -> None:
    items = [
        {"id": {"S": "id1"}, "attr": {"S": "sth"}},
        {"id": {"S": "id2"}, "attr": {"S": "oth"}},
        {"id": {"S": "id3"}},  # missing field
    ]
    return_value, updates = DynamoDBStatementParser(
        source_data={"tablename": items}
    ).parse(query)

    assert return_value == []
    assert updates == {"tablename": [(items[0], None)]}


def test_delete_with_multiple_keys() -> None:
    query = "DELETE FROM 'tablename' WHERE Id='id1' AND attr='sth'"
    items = [
        {"id": {"S": "id1"}, "attr": {"S": "sth"}},
        {"id": {"S": "id1"}, "attr": {"S": "oth"}},
        {"id": {"S": "id1"}},  # missing field
    ]
    return_value, updates = DynamoDBStatementParser(
        source_data={"tablename": items}
    ).parse(query)

    assert return_value == []
    assert updates == {"tablename": [(items[0], None)]}


def test_delete_with_no_hits() -> None:
    query = "DELETE FROM 'tablename' WHERE Id='id1'"
    items = [{"id": {"S": "asdf"}}]
    return_value, updates = DynamoDBStatementParser(
        source_data={"tablename": items}
    ).parse(query)

    assert return_value == []
    assert updates == {"tablename": []}


@pytest.mark.parametrize(
    "query",
    [
        "INSERT INTO 'mytable' value {'id': 'id1'}",
        "INSERT INTO mytable value {'id': 'id1'}",
    ],
)
def test_insert(query: str) -> None:
    items = [{"id": {"S": "asdf"}}]
    return_value, updates = DynamoDBStatementParser(
        source_data={"mytable": items}
    ).parse(query)

    assert return_value == []
    assert updates == {"mytable": [(None, {"id": {"S": "id1"}})]}


def test_insert_complex_item() -> None:
    # driving the point home - the source data does not matter
    query = "INSERT INTO 'mytable' value {'id': 'id1', 'attr': {'some': ['datas']}}"
    return_value, updates = DynamoDBStatementParser(source_data={"mytable": []}).parse(
        query
    )

    assert return_value == []
    assert updates == {
        "mytable": [
            (
                None,
                {"id": {"S": "id1"}, "attr": {"M": {"some": {"L": [{"S": "datas"}]}}}},
            )
        ]
    }
