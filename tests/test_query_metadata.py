from py_partiql_parser import DynamoDBStatementParser


def test_get_single_table_name() -> None:
    query = "SELECT * FROM table1"
    metadata = DynamoDBStatementParser.get_query_metadata(query)

    assert metadata.get_table_names() == ["table1"]


def test_get_multiple_table_names() -> None:
    query = "SELECT * FROM table1, table2"
    metadata = DynamoDBStatementParser.get_query_metadata(query)

    assert metadata.get_table_names() == ["table1", "table2"]


def test_get_multiple_table_names_with_aliases() -> None:
    query = "SELECT * FROM table1 as t1, table2"
    metadata = DynamoDBStatementParser.get_query_metadata(query)

    assert metadata.get_table_names() == ["table1", "table2"]


def test_nonexisting_filter_names() -> None:
    query = "SELECT * FROM table1"
    metadata = DynamoDBStatementParser.get_query_metadata(query)

    assert metadata.get_filter_names() == []


def test_filter_names() -> None:
    query = "SELECT * FROM table1 WHERE k1 = 'sth' AND k2 = 'else'"
    metadata = DynamoDBStatementParser.get_query_metadata(query)

    assert metadata.get_filter_names() == ["k1", "k2"]


def test_nested_filter_names() -> None:
    query = "SELECT * FROM table1 WHERE k1 = 'sth' AND k2.sth = 'else'"
    metadata = DynamoDBStatementParser.get_query_metadata(query)

    assert metadata.get_filter_names() == ["k1", "k2.sth"]
