import re

from typing import Dict, Any, List, Optional, Tuple

from ..exceptions import ParserException
from .delete_parser import DeleteParser
from .from_parser import DynamoDBFromParser, S3FromParser, FromParser
from .insert_parser import InsertParser
from .select_parser import SelectParser
from .update_parser import UpdateParser
from .where_parser import DynamoDBWhereParser, S3WhereParser, WhereParser
from .utils import is_dict, QueryMetadata, CaseInsensitiveDict


TYPE_RESPONSE = Tuple[
    List[Dict[str, Any]],
    Dict[str, List[Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]]],
]


class S3SelectParser:
    def __init__(self, source_data: Dict[str, str]):
        # Source data is in the format: {source: json}
        # Where 'json' is one or more json documents separated by a newline
        self.documents = source_data
        self.table_prefix = "s3object"

    def parse(self, query: str) -> List[Dict[str, Any]]:
        query = query.replace("\n", " ")
        clauses = re.split("SELECT | FROM | WHERE ", query, flags=re.IGNORECASE)
        # First clause is whatever comes in front of SELECT - which should be nothing
        _ = clauses[0]
        # FROM
        from_parser = S3FromParser(from_clause=clauses[2])

        source_data = from_parser.get_source_data(self.documents)
        if is_dict(source_data):
            source_data = [source_data]

        # WHERE
        if len(clauses) > 3:
            where_clause = clauses[3]
            source_data = S3WhereParser(source_data).parse(where_clause)

        # SELECT
        select_clause = clauses[1]
        table_prefix = self.table_prefix
        for alias_key, alias_value in from_parser.clauses.items():
            if table_prefix == alias_value:
                table_prefix = alias_key
        return SelectParser(table_prefix).parse(
            select_clause, from_parser.clauses, source_data
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
        self.documents = {
            key: [CaseInsensitiveDict(v) for v in val]
            for key, val in source_data.items()
        }

    def parse(  # type: ignore[return]
        self, query: str, parameters: Optional[List[Dict[str, Any]]] = None
    ) -> TYPE_RESPONSE:
        if query.lower().startswith("select"):
            return_data, updates = self._parse_select(query, parameters)
            for item in return_data:
                for key, val in item.items():
                    item[key] = val.get_regular()
            return return_data, updates

        if query.lower().startswith("update"):
            return self._parse_update(query, parameters)

        if query.lower().startswith("delete"):
            return self._parse_delete(query)

        if query.lower().startswith("insert"):
            return self._parse_insert(query)

    def _parse_select(
        self, query: str, parameters: Optional[List[Dict[str, Any]]] = None
    ) -> TYPE_RESPONSE:
        query = query.replace("\n", " ")
        clauses = re.split("SELECT | FROM | WHERE ", query, flags=re.IGNORECASE)
        # First clause is whatever comes in front of SELECT - which should be nothing
        _ = clauses[0]
        # FROM
        from_parser = DynamoDBFromParser(from_clause=clauses[2])

        source_data = self.documents[list(from_parser.clauses.values())[0]]

        # WHERE
        if len(clauses) > 3:
            where_clause = clauses[3]
            source_data = DynamoDBWhereParser(source_data).parse(
                where_clause, parameters
            )

        # SELECT
        select_clause = clauses[1]
        queried_data = SelectParser().parse(
            select_clause, from_parser.clauses, source_data
        )
        updates: Dict[
            str, List[Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]]
        ] = {}
        return queried_data, updates

    def _parse_update(
        self, query: str, parameters: Optional[List[Dict[str, Any]]] = None
    ) -> TYPE_RESPONSE:
        query = query.replace("\n", " ")

        table_name, attrs_to_update, attrs_to_filter = UpdateParser().parse(query)

        parameters_requested = len(
            [_ for _, val in attrs_to_update + attrs_to_filter if val == "?"]
        )
        if parameters_requested and len(parameters) != parameters_requested:  # type: ignore
            raise ParserException(
                name="ValidationError",
                message="Number of parameters in request and statement don't match.",
            )

        attrs_to_update = [
            (key, parameters.pop(0) if val == "?" else val)  # type: ignore
            for key, val in attrs_to_update
        ]
        attrs_to_filter = [
            (key, parameters.pop(0) if val == "?" else val)  # type: ignore
            for key, val in attrs_to_filter
        ]

        source_data = self.documents[table_name]
        updates_per_table: Dict[
            str, List[Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]]
        ] = {table_name: []}

        for item in source_data:
            if all([item.get(name) == val for name, val in attrs_to_filter]):
                new_item = item.copy()
                for attr_key, attr_value in attrs_to_update:
                    if attr_value is None:
                        new_item.pop(attr_key, None)
                    else:
                        new_item[attr_key] = attr_value
                updates_per_table[table_name].append(
                    (item.get_regular(), new_item.get_regular())
                )

        return [], updates_per_table

    def _parse_delete(self, query: str) -> TYPE_RESPONSE:
        query = query.replace("\n", " ")

        table_name, attrs_to_filter = DeleteParser().parse(query)

        source_data = self.documents[table_name]
        deletes_per_table: Dict[
            str, List[Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]]
        ] = {table_name: []}

        for item in source_data:
            if all([item.get(name) == val for name, val in attrs_to_filter]):
                deletes_per_table[table_name].append((item.get_regular(), None))

        return [], deletes_per_table

    def _parse_insert(self, query: str) -> TYPE_RESPONSE:
        query = query.replace("\n", " ")

        table_name, new_item = InsertParser().parse(query)
        return [], {table_name: [(None, new_item)]}

    @classmethod
    def get_query_metadata(cls, query: str) -> QueryMetadata:
        query = query.replace("\n", " ")
        if query.lower().startswith("select"):
            clauses = re.split("SELECT | FROM | WHERE ", query, flags=re.IGNORECASE)

            from_parser = FromParser(clauses[2])
            # WHERE
            if len(clauses) > 3:
                where_clause = clauses[3]
                where = WhereParser.parse_where_clause(where_clause)
            else:
                where = None

            return QueryMetadata(
                tables=from_parser.clauses, where_clause=where, is_select_query=True
            )
        elif query.lower().startswith("update"):
            table_name, attrs_to_update, attrs_to_filter = UpdateParser().parse(query)
            return QueryMetadata(tables={table_name: table_name}, where_clause=None)
        elif query.lower().startswith("delete"):
            query = query.replace("\n", " ")

            table_name, attrs_to_filter = DeleteParser().parse(query)
            return QueryMetadata(tables={table_name: table_name})
        elif query.lower().startswith("insert"):
            query = query.replace("\n", " ")

            table_name, new_item = InsertParser().parse(query)
            return QueryMetadata(tables={table_name: table_name})
        raise Exception
