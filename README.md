# py-partiql-parser
A tokenizer/parser/executor for the PartiQL-language, in Python.

Much beta, such wow. Feel free to raise any issues you encounter.

## S3 Usage
```python
import json
from py_partiql_parser import S3SelectParser

original_json = json.dumps({"a1": "b1", "a2": "b2"})
parser = S3SelectParser(source_data={"s3object": original_json})
result = parser.parse("SELECT * FROM s3object")
```
## DynamoDB Usage
```python
import json
from py_partiql_parser import DynamoDBStatementParser

original_json = json.dumps({"a1": "b1", "a2": "b2"})
parser = DynamoDBStatementParser(source_data={"table1", original_json})
result = parser.parse("SELECT * from table1 WHERE a1 = ?", parameters=[{"S": "b1"}])
```


## Meat
The important logic of this library can be found here: https://github.com/bblommers/py-partiql-parser/blob/main/py_partiql_parser/_internal/parser.py

It is implemented as a naive, dependency-free, TDD-first tokenizer.

## Outstanding
 - Support for functions such as `count(*)`
 - Support for CSV conversion. A start has been made in `_internal/csv_converter.py`
 - .. and I'm sure many other things.

## Notes
The first iteration of this library was based on the spec, found here: https://partiql.org/assets/PartiQL-Specification.pdf

AWS doesn't follow its own spec though, most notably:
 - a file containing a list (with multiple JSON documents) cannot be queried normally (`select *` returns everything, but you cannot `select key` for each document in the list)
 - `select values` is not supported