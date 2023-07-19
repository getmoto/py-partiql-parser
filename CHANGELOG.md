CHANGELOG
=========

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
