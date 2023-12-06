import re

from typing import Dict, Any, List

from .from_parser import DynamoDBFromParser, S3FromParser, FromParser
from .select_parser import SelectParser
from .where_parser import DynamoDBWhereParser, S3WhereParser, WhereParser
from .utils import is_dict, QueryMetadata


class S3SelectParser:
    def __init__(self, source_data: Dict[str, str]):
        # Source data is in the format: {source: json}
        # Where 'json' is one or more json documents separated by a newline
        self.documents = source_data
        self.table_prefix = "s3object"

    def parse(self, query: str, parameters=None) -> List[Dict[str, Any]]:
        query = query.replace("\n", " ")
        clauses = re.split("SELECT | FROM | WHERE ", query, flags=re.IGNORECASE)
        # First clause is whatever comes in front of SELECT - which should be nothing
        _ = clauses[0]
        # FROM
        from_parser = S3FromParser()
        from_clauses = from_parser.parse(clauses[2])

        source_data = from_parser.get_source_data(self.documents)
        if is_dict(source_data):
            source_data = [source_data]  # type: ignore

        # WHERE
        if len(clauses) > 3:
            where_clause = clauses[3]
            source_data = S3WhereParser(source_data).parse(where_clause, parameters)

        # SELECT
        select_clause = clauses[1]
        table_prefix = self.table_prefix
        for alias_key, alias_value in from_clauses.items():
            if table_prefix == alias_value:
                table_prefix = alias_key
        return SelectParser(table_prefix).parse(
            select_clause, from_clauses, source_data
        )


class DynamoDBStatementParser:
    def __init__(self, source_data: Dict[str, List[Dict[str, Any]]]):
        """
        Source Data should be a list of DynamoDB documents, mapped to the table name
        {
          "table_name": [
             {
               "hash_key": "..",
               "other_item": {"S": ".."},
               ..
             },
             ..
          ],
          ..
        }
        """
        # Source data is in the format: {source: json}
        # Where 'json' is one or more json documents separated by a newline
        self.documents = source_data

    def parse(self, query: str, parameters=None) -> List[Dict[str, Any]]:
        query = query.replace("\n", " ")
        clauses = re.split("SELECT | FROM | WHERE ", query, flags=re.IGNORECASE)
        # First clause is whatever comes in front of SELECT - which should be nothing
        _ = clauses[0]
        # FROM
        from_parser = DynamoDBFromParser()
        from_clauses = from_parser.parse(clauses[2])

        source_data = from_parser.get_source_data(self.documents)

        # WHERE
        if len(clauses) > 3:
            where_clause = clauses[3]
            source_data = DynamoDBWhereParser(source_data).parse(
                where_clause, parameters
            )

        # SELECT
        select_clause = clauses[1]
        return SelectParser().parse(select_clause, from_clauses, source_data)

    @classmethod
    def get_query_metadata(cls, query: str):
        query = query.replace("\n", " ")
        clauses = re.split("SELECT | FROM | WHERE ", query, flags=re.IGNORECASE)

        from_clauses = FromParser().parse(clauses[2])

        # WHERE
        if len(clauses) > 3:
            where_clause = clauses[3]
            where = WhereParser.parse_where_clause(where_clause)
        else:
            where = None

        return QueryMetadata(tables=from_clauses, where_clause=where)
