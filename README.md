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
There are two classes of tests:
 - Tests based on the examples in the spec (https://partiql.org/assets/PartiQL-Specification.pdf)
 - Tests based on real-world examples from users/AWS

## Outstanding
 - Support for functions such as `count(*)`
 - There is no CSV support at the moment. We'll have to decide how/if to implement that. We could force users to convert their data into JSON first, so we don't have to worry about that..
 - .. and I'm sure many other things.
