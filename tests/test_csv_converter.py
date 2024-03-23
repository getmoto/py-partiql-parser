from py_partiql_parser import csv_to_json, json_to_csv
import json


input_csv = """Sam,(949) 555-6701,Irvine,Solutions Architect
Vinod,(949) 555-6702,Los Angeles,Solutions Architect
Jeff,(949) 555-6703,Seattle,AWS Evangelist
Jane,(949) 555-6704,Chicago,Developer
Sean,(949) 555-6705,Chicago,Developer
Mary,(949) 555-6706,Chicago,Developer
Kate,(949) 555-6707,Chicago,Developer"""


input_with_header = (
    """Name,PhoneNumber,City,Occupation
"""
    + input_csv
)


def test_csv_to_json() -> None:
    result = csv_to_json(input_csv)
    lines = result.split("\n")
    assert len(lines) == 7

    line0 = json.loads(lines[0])
    assert line0["_1"] == "Sam"


def test_csv_to_json_with_headers() -> None:
    result = csv_to_json(input_with_header, headers_included=True)
    lines = result.split("\n")
    assert len(lines) == 7

    line0 = json.loads(lines[0])
    assert line0["Name"] == "Sam"

    line2 = json.loads(lines[2])
    assert line2["City"] == "Seattle"


def test_json_to_csv() -> None:
    json_result = csv_to_json(input_csv)
    lines = json_result.split("\n")

    csv_result = json_to_csv(
        [json.loads(lines[0])], field_delimiter=",", record_delimiter="\n"
    )
    assert csv_result == "Sam,(949) 555-6701,Irvine,Solutions Architect\n"

    csv_result = json_to_csv(
        [json.loads(lines[4])], field_delimiter=",", record_delimiter="\n"
    )
    assert csv_result == "Sean,(949) 555-6705,Chicago,Developer\n"
