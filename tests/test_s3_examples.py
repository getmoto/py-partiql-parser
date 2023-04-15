import json
import pytest
import sure  # noqa
from py_partiql_parser import S3SelectParser
from . import input_json_list, json_as_lines


# https://aws.amazon.com/blogs/storage/querying-data-without-servers-or-databases-using-amazon-s3-select/


input_data_csv = """Name,PhoneNumber,City,Occupation
Sam,(949) 555-6701,Irvine,Solutions Architect
Vinod,(949) 555-6702,Los Angeles,Solutions Architect
Jeff,(949) 555-6703,Seattle,AWS Evangelist
Jane,(949) 555-6704,Chicago,Developer
Sean,(949) 555-6705,Chicago,Developer
Mary,(949) 555-6706,Chicago,Developer
Kate,(949) 555-6707,Chicago,Developer"""

input_json_object = {"a1": "b1", "a2": "b2"}


@pytest.mark.xfail(reason="CSV functionality not yet implemented")
def test_aws_sample__csv():
    query = "SELECT * FROM s3object s where s.\"Name\" = 'Jane'"
    x = S3SelectParser(source_data={"s3object": input_data_csv}).parse(query)


@pytest.mark.xfail(
    reason="this shouldn't work, as it doesn't work against AWS. Input should be a string where line is a document, not a list"
)
def test_aws_sample__json__search_by_name():
    query = "SELECT * FROM s3object s where s.\"Name\" = 'Jane'"
    result = S3SelectParser(source_data={"s3object": input_json_list}).parse(query)
    result.should.equal(
        [
            {
                "Name": "Jane",
                "PhoneNumber": "(949) 555-6704",
                "City": "Chicago",
                "Occuption": "Developer",
            }
        ]
    )


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM s3object s where s.City = 'Chicago'",
        "SELECT * FROM s3object s where s.\"City\" = 'Chicago'",
    ],
)
def test_aws_sample__json__search_by_city(query):
    result = S3SelectParser(source_data={"s3object": json_as_lines}).parse(query)
    result.should.have.length_of(4)
    result.should.contain(
        {
            "Name": "Jane",
            "PhoneNumber": "(949) 555-6704",
            "City": "Chicago",
            "Occuption": "Developer",
        }
    )
    result.should.contain(
        {
            "Name": "Sean",
            "PhoneNumber": "(949) 555-6705",
            "City": "Chicago",
            "Occuption": "Developer",
        }
    )
    result.should.contain(
        {
            "Name": "Mary",
            "PhoneNumber": "(949) 555-6706",
            "City": "Chicago",
            "Occuption": "Developer",
        }
    )
    result.should.contain(
        {
            "Name": "Kate",
            "PhoneNumber": "(949) 555-6707",
            "City": "Chicago",
            "Occuption": "Developer",
        }
    )


def test_aws_sample__json_select_multiple_attrs__search_by_city():
    query = "SELECT s.name, s.city FROM s3object s where s.\"City\" = 'Chicago'"
    result = S3SelectParser(source_data={"s3object": json_as_lines}).parse(query)
    result.should.have.length_of(4)
    result.should.contain(
        {
            "Name": "Jane",
            "City": "Chicago",
        }
    )
    result.should.contain(
        {
            "Name": "Sean",
            "City": "Chicago",
        }
    )
    result.should.contain(
        {
            "Name": "Mary",
            "City": "Chicago",
        }
    )
    result.should.contain(
        {
            "Name": "Kate",
            "City": "Chicago",
        }
    )


def test_aws_sample__object_select_all():
    query = "SELECT * FROM s3object"
    result = S3SelectParser(
        source_data={"s3object": json.dumps(input_json_object)}
    ).parse(query)
    result.should.equal([input_json_object])


def test_aws_sample__s3object_is_case_insensitive():
    query = "SELECT * FROM s3obJEct"
    result = S3SelectParser(
        source_data={"s3object": json.dumps(input_json_object)}
    ).parse(query)
    result.should.equal([input_json_object])


def test_aws_sample__object_select_everything():
    query = "SELECT s FROM s3object AS s"
    result = S3SelectParser(
        source_data={"s3object": json.dumps(input_json_object)}
    ).parse(query)
    result.should.equal([input_json_object])


def test_aws_sample__object_select_attr():
    query = "SELECT s.a1 FROM s3object AS s"
    result = S3SelectParser(
        source_data={"s3object": json.dumps(input_json_object)}
    ).parse(query)
    result.should.equal([{"a1": "b1"}])


def test_case_insensitivity():
    # Filter by lower case "city"
    query = "SELECT * from s3object where s3object.city = 'Los Angeles'"
    # Data has upper case CITY
    all_rows = (
        json.dumps({"Name": "Sam", "CITY": "Irvine"})
        + "\n"
        + json.dumps({"Name": "Vinod", "City": "Los Angeles"})
    )
    parser = S3SelectParser(source_data={"s3object": all_rows})
    assert parser.parse(query, parameters=None) == [
        {"Name": "Vinod", "City": "Los Angeles"}
    ]
