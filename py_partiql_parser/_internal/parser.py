import re

from typing import Dict, Any, Union, List, AnyStr, Optional

from .from_parser import FromParser
from .json_parser import JsonParser
from .select_parser import SelectParser
from .where_parser import DynamoDBWhereParser, S3WhereParser, WhereParser
from .utils import is_dict, QueryMetadata


class Parser:
    RETURN_TYPE = Union[Dict[AnyStr, Any], List]

    def __init__(
        self,
        source_data: Dict[str, str],
        table_prefix: Optional[str],
        where_parser,
    ):
        # Source data is in the format: {source: json}
        # Where 'json' is one or more json documents separated by a newline
        self.documents = source_data
        self.table_prefix = table_prefix
        self.where_parser = where_parser

    def parse(self, query: str, parameters=None) -> List[Dict[str, Any]]:
        query = query.replace("\n", " ")
        clauses = re.split("SELECT | FROM | WHERE ", query, flags=re.IGNORECASE)
        # First clause is whatever comes in front of SELECT - which should be nothing
        _ = clauses[0]
        # FROM
        from_clauses = FromParser().parse(clauses[2])
        source_data = self.documents[list(from_clauses.values())[0].lower()]
        source_data = JsonParser().parse(source_data)
        if is_dict(source_data):
            source_data = [source_data]  # type: ignore

        # WHERE
        if len(clauses) > 3:
            where_clause = clauses[3]
            source_data = self.where_parser(source_data).parse(where_clause, parameters)

        # SELECT
        select_clause = clauses[1]
        return SelectParser(self.table_prefix).parse(
            select_clause, from_clauses, source_data
        )


class S3SelectParser(Parser):
    def __init__(self, source_data: Dict[str, str]):
        super().__init__(
            source_data, table_prefix="s3object", where_parser=S3WhereParser
        )


class DynamoDBStatementParser(Parser):
    def __init__(self, source_data: Dict[str, str]):
        super().__init__(
            source_data, table_prefix=None, where_parser=DynamoDBWhereParser
        )

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

        return QueryMetadata(tables=from_clauses, where_clauses=where)
