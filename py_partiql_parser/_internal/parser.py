import re

from typing import Dict, Any, Union, List, AnyStr

from .from_parser import FromParser
from .json_parser import JsonParser
from .select_parser import SelectParser
from .where_parser import WhereParser
from .utils import is_dict


class Parser:
    RETURN_TYPE = Union[Dict[AnyStr, Any], List]

    def __init__(self, source_data: Dict[str, str], query_has_table_prefix=True):
        # Source data is in the format: {source: json}
        # Where 'json' is one or more json documents separated by a newline
        self.documents = source_data
        self.query_has_table_prefix = query_has_table_prefix

    def parse(self, query: str) -> List[Dict[str, Any]]:
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
            source_data = WhereParser(source_data, self.query_has_table_prefix).parse(
                where_clause
            )

        # SELECT
        select_clause = clauses[1]
        return SelectParser().parse(select_clause, from_clauses, source_data)
