CHANGELOG
=========

0.5.5
-----
 - Add JsonParser to public API
 - Improve performance for JsonParser when parsing a source with many documents


0.5.3 & 0.5.4
-----
 - Fix project build


0.5.2
-----

 - Add json_to_csv converter


0.5.1
-----

 - Support INSERT/DELETE/UPDATE queries:

   - that contain a table name without quotes
   - that contain parameters
   - when calling get_query_metadata()


0.5.0
-----
 - Improved typing support
 - Support for INSERT/UPDATE/DELETE statements

0.4.2
-----
 - Support for Python 3.12

0.4.1
-----
 - Increased support for WHERE-clauses:
   1. Nested clauses
   2. OR-clauses
   3. Functions: attribute_type, IF (NOT) MISSING, comparison operators (<, >)

0.4.0
-----
 - The DynamoDBStatementParser now expects a document in the DynamoDB format:
{"a1": {"S": "b1"}, "a2": {"S": "b2"}}

  - Adds validation for tables that start with a number
  - Adds support for queries that have a table name surrounded by quotes

0.3.8
-----
 - Support JSON documents containing (lists of) BOOLeans

0.3.6
-----
 -  Allow where-clauses for lists, such as `where a[1] = '..'`

0.3.5
-----
 - Packaging improvements: Include source-files in the release, and update the version nr

0.3.4
-----
 - Packaging improvements: Include `tests/__init__.py` in the release and add project links to PyPi

0.3.3
-----
 - S3: Fix behaviour for nested FROM-queries (s3object[*].name)

0.3.2
-----
 - Improves the SelectEncoder behaviour to also encode CaseInsensitiveDict's
 - Ensure FROM-queries such as `s3object[*]` do not fail (NOTE: the correct behaviour is not correct yet)

0.3.1
-----
 - Expose a custom JSON encoder, `SelectEncoder`, in order to encode custom objects returned by our API such as `Variable`
   `json.dumps(x, indent=None, separators=(",", ":"), cls=SelectEncoder)`

0.3.0
-----
 - Support for multiple WHERE-clauses
 - Additional API: `DynamoDBStatementParser.get_query_metadata`

0.2.1
-----
 - Minor bugfix - `s3object` should be case-insensitive.

0.2.0
-----
 - Support for DynamoDB Statements.
 - Removed print-statements and some warnings.


0.1.0
-----
 - Initial release with support for S3Select queries.
