import json

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


input_with_lists = [
    {
        "staff": [
            {
                "name": "Janelyn M",
                "date": "2020-02-23T00:00:00",
                "city": "Chicago",
                "kids": 2,
            },
            {
                "name": "Stacy P",
                "date": "2020-02-28T00:00:00",
                "city": "Seattle",
                "kids": 1,
            },
        ],
        "country": "USA",
    }
]
