# py-partiql-parser
A tokenizer/parser/executor for the PartiQL-language, in Python.

Much beta, such wow. Feel free to raise any issues you encounter.

## Usage
```
original_json = {"a1": "b1", "a2": "b2"}
from py_partiql_parser import Parser
parser = Parser(source_data={"s3object": original_json})
result = parser.parse("SELECT * FROM s3object")
```

## Meat
The important logic of this library can be found here: https://github.com/bblommers/py-partiql-parser/blob/main/py_partiql_parser/_internal/parser.py

It is implemented as a naive, dependency-free, TDD-first tokenizer.

## Tests
Tests based on real-world examples from users/AWS, and can be found here:
https://github.com/getmoto/py-partiql-parser/blob/main/tests/test_aws_examples.py

## Outstanding
 - Support for functions such as `count(*)`
 - There is no CSV support at the moment. We'll have to decide how/if to implement that. We could force users to convert their data into JSON first, so we don't have to worry about that..
 - .. and I'm sure many other things.

## Notes
The first iteration of this library was based on the spec, found here: https://partiql.org/assets/PartiQL-Specification.pdf

AWS doesn't follow its own spec though, most notably:
 - a file containing a list (with multiple JSON documents) cannot be queried normally (`select *` returns everything, but you cannot `select key` for each document in the list)
 - `select values` is not supported