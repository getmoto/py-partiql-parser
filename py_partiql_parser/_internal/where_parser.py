from typing import Any, List, Optional, Tuple

from .clause_tokenizer import ClauseTokenizer
from .utils import find_value_in_document


class WhereParser:
    def __init__(self, source_data: Any, query_has_table_prefix: bool):
        self.source_data = source_data
        self.query_has_table_prefix = query_has_table_prefix

    def parse(self, where_clause: str) -> Any:
        filter_keys, filter_value = self.parse_where_clause(where_clause)

        return self.filter_rows(filter_keys, filter_value)

    def filter_rows(self, filter_keys, filter_value):
        def _filter(row):
            if self.query_has_table_prefix:
                actual_value = find_value_in_document(filter_keys[1:], row)
                return actual_value == filter_value
            else:
                return find_value_in_document(filter_keys, row) == filter_value

        return [row for row in self.source_data if _filter(row)]

    def parse_where_clause(self, where_clause: str) -> Tuple[List[str], str]:
        where_clause_parser = ClauseTokenizer(where_clause)
        keys: List[str] = []
        value = ""
        section: Optional[str] = "KEY"
        current_phrase = ""
        while True:
            c = where_clause_parser.next()
            if c is None:
                if section == "KEY":
                    keys.append(current_phrase)
                break
            if c == ".":
                if section == "KEY":
                    if current_phrase != "":
                        keys.append(current_phrase)
                    current_phrase = ""
                    continue
            if c in ['"', "'"]:
                if section == "KEY":
                    # collect everything between these quotes
                    keys.append(where_clause_parser.next_until([c]))
                    continue
                if section == "START_VALUE":
                    section = "VALUE"
                    continue
                if section == "VALUE":
                    section = None
                    value = current_phrase
                    current_phrase = ""
            if c in [" "] and section == "KEY":
                if current_phrase != "":
                    keys.append(current_phrase)
                current_phrase = ""
                where_clause_parser.skip_until(["="])
                where_clause_parser.skip_white_space()
                section = "START_VALUE"
            if current_phrase == "" and section == "START_KEY":
                section = "KEY"
            if section in ["KEY", "VALUE"]:
                current_phrase += c
        return keys, value
