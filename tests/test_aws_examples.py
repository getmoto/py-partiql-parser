import json
import pytest
import sure  # noqa
from py_partiql_parser import Parser


# https://aws.amazon.com/blogs/storage/querying-data-without-servers-or-databases-using-amazon-s3-select/


input_data_csv = """Name,PhoneNumber,City,Occupation
Sam,(949) 555-6701,Irvine,Solutions Architect
Vinod,(949) 555-6702,Los Angeles,Solutions Architect
Jeff,(949) 555-6703,Seattle,AWS Evangelist
Jane,(949) 555-6704,Chicago,Developer
Sean,(949) 555-6705,Chicago,Developer
Mary,(949) 555-6706,Chicago,Developer
Kate,(949) 555-6707,Chicago,Developer"""


input_json_list = [
    {
        "Name": "Sam",
        "PhoneNumber": "(949) 555-6701",
        "City": "Irvine",
        "Occuption": "Solutions Architect",
    },
    {
        "Name": "Vinod",
        "PhoneNumber": "(949) 555-6702",
        "City": "Los Angeles",
        "Occuption": "Solutions Architect",
    },
    {
        "Name": "Jeff",
        "PhoneNumber": "(949) 555-6703",
        "City": "Seattle",
        "Occuption": "AWS Evangelist",
    },
    {
        "Name": "Jane",
        "PhoneNumber": "(949) 555-6704",
        "City": "Chicago",
        "Occuption": "Developer",
    },
    {
        "Name": "Sean",
        "PhoneNumber": "(949) 555-6705",
        "City": "Chicago",
        "Occuption": "Developer",
    },
    {
        "Name": "Mary",
        "PhoneNumber": "(949) 555-6706",
        "City": "Chicago",
        "Occuption": "Developer",
    },
    {
        "Name": "Kate",
        "PhoneNumber": "(949) 555-6707",
        "City": "Chicago",
        "Occuption": "Developer",
    },
]
json_as_lines = "\n".join([json.dumps(x) for x in input_json_list])

input_json_object = {"a1": "b1", "a2": "b2"}


@pytest.mark.xfail(reason="CSV functionality not yet implemented")
def test_aws_sample__csv():
    query = "SELECT * FROM s3object s where s.\"Name\" = 'Jane'"
    x = Parser(source_data={"s3object": input_data_csv}).parse(query)


@pytest.mark.xfail(
    reason="this shouldn't work, as it doesn't work against AWS. Input should be a string where line is a document, not a list"
)
def test_aws_sample__json__search_by_name():
    query = "SELECT * FROM s3object s where s.\"Name\" = 'Jane'"
    result = Parser(source_data={"s3object": input_json_list}).parse(query)
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


def test_aws_sample__json__search_by_city():
    query = "SELECT * FROM s3object s where s.\"City\" = 'Chicago'"
    result = Parser(source_data={"s3object": json_as_lines}).parse(query)
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


def test_aws_sample__object_select_all():
    query = "SELECT * FROM s3object"
    result = Parser(source_data={"s3object": json.dumps(input_json_object)}).parse(
        query
    )
    result.should.equal([input_json_object])


def test_aws_sample__object_select_attr():
    query = "SELECT s.a1 FROM s3object AS s"
    result = Parser(source_data={"s3object": json.dumps(input_json_object)}).parse(
        query
    )
    result.should.equal([{"a1": "b1"}])
