import json
from . import input_with_lists
from py_partiql_parser import S3SelectParser, SelectEncoder


def test_json_output_can_be_dumped():
    query = "select * from s3object s"
    input_with_none = json.dumps(
        {
            "name": "Janelyn M",
            "date": "2020-02-23T00:00:00",
            "city": "Chicago",
            "kids": None,
        }
    )
    result = S3SelectParser(source_data={"s3object": input_with_none}).parse(query)
    assert f"[{input_with_none}]" == json.dumps(result, cls=SelectEncoder)


def test_json_with_lists_can_be_dumped():
    query = "select * from s3object s"
    input_with_none = json.dumps(input_with_lists[0])
    result = S3SelectParser(source_data={"s3object": input_with_none}).parse(query)
    assert f"[{input_with_none}]" == json.dumps(result, cls=SelectEncoder)
