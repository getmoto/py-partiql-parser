import re

from typing import Dict, Any, Union, List, AnyStr

from .from_parser import FromParser
from .json_parser import JsonParser
from .select_parser import SelectParser
from .where_parser import WhereParser


class Parser:
    RETURN_TYPE = Union[Dict[AnyStr, Any], List]

    def __init__(self, source_data: Dict[str, str]):
        self.source_data = source_data
        # Source data is in the format: {source: json}
        # Where 'json' is one or more json documents separated by a newline
        self.documents = {key: value for key, value in source_data.items()}

    def parse(self, query: str) -> List[Dict[str, Any]]:
        query = query.replace("\n", " ")
        clauses = re.split("SELECT | FROM | WHERE ", query, flags=re.IGNORECASE)
        # First clause is whatever comes in front of SELECT - which should be nothing
        _ = clauses[0]
        # FROM
        from_clauses = FromParser().parse(clauses[2])
        # WHERE
        if len(clauses) > 3:
            where_clause = clauses[3]
            self.documents = WhereParser(self.source_data).parse(
                from_clauses, where_clause
            )
        else:
            for key, value in self.documents.items():
                self.documents[key] = JsonParser().parse(value)
                if isinstance(self.documents[key], dict):
                    self.documents[key] = [self.documents[key]]  # type: ignore

        # SELECT
        select_clause = clauses[1]
        return SelectParser().parse(select_clause, from_clauses, self.documents)
