import re

from typing import Dict, Any, Union, List, AnyStr, Optional

from .from_parser import DynamoDBFromParser, S3FromParser, FromParser
from .select_parser import SelectParser
from .where_parser import DynamoDBWhereParser, S3WhereParser, WhereParser
from .utils import is_dict, QueryMetadata


class Parser:
    RETURN_TYPE = Union[Dict[AnyStr, Any], List]

    def __init__(
        self,
        source_data: Dict[str, str],
        table_prefix: Optional[str],
        from_parser: FromParser,
        where_parser: WhereParser,
    ):
        # Source data is in the format: {source: json}
        # Where 'json' is one or more json documents separated by a newline
        self.documents = source_data
        self.table_prefix = table_prefix
        self.from_parser = from_parser
        self.where_parser = where_parser

    def parse(self, query: str, parameters=None) -> List[Dict[str, Any]]:
        query = query.replace("\n", " ")
        clauses = re.split("SELECT | FROM | WHERE ", query, flags=re.IGNORECASE)
        # First clause is whatever comes in front of SELECT - which should be nothing
        _ = clauses[0]
        # FROM
        from_parser = self.from_parser()
        from_clauses = from_parser.parse(clauses[2])
        source_data = from_parser.get_source_data(self.documents)
        if is_dict(source_data):
            source_data = [source_data]  # type: ignore

        # WHERE
        if len(clauses) > 3:
            where_clause = clauses[3]
            source_data = self.where_parser(source_data).parse(where_clause, parameters)

        # SELECT
        select_clause = clauses[1]
        table_prefix = self.table_prefix
        for alias_key, alias_value in from_clauses.items():
            if table_prefix == alias_value:
                table_prefix = alias_key
        return SelectParser(table_prefix).parse(
            select_clause, from_clauses, source_data
        )


class S3SelectParser(Parser):
    def __init__(self, source_data: Dict[str, str]):
        super().__init__(
            source_data,
            table_prefix="s3object",
            from_parser=S3FromParser,
            where_parser=S3WhereParser,
        )


class DynamoDBStatementParser(Parser):
    def __init__(self, source_data: Dict[str, str]):
        super().__init__(
            source_data,
            table_prefix=None,
            from_parser=DynamoDBFromParser,
            where_parser=DynamoDBWhereParser,
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
