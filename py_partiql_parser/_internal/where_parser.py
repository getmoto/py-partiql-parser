from typing import Any, List, Optional, Tuple

from .clause_tokenizer import ClauseTokenizer
from .utils import find_value_in_document


class WhereParser:
    def __init__(self, source_data: Any):
        self.source_data = source_data

    @classmethod
    def parse_where_clause(cls, where_clause: str) -> Tuple[List[str], str]:
        where_clause_parser = ClauseTokenizer(where_clause)
        results = []
        keys: List[str] = []
        section: Optional[str] = "KEY"
        current_phrase = ""
        while True:
            c = where_clause_parser.next()
            if c is None:
                if section == "KEY" and current_phrase != "":
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
                    section = "END_VALUE"
                    results.append((keys.copy(), current_phrase))
                    keys.clear()
                    current_phrase = ""
                    where_clause_parser.skip_white_space()
                    continue
            if c in [" "] and section == "KEY":
                if current_phrase != "":
                    keys.append(current_phrase)
                current_phrase = ""
                where_clause_parser.skip_until(["="])
                where_clause_parser.skip_white_space()
                section = "START_VALUE"
                continue
            if c in [" "] and section == "END_VALUE":
                if current_phrase.upper() == "AND":
                    current_phrase = ""
                    section = "KEY"
                    where_clause_parser.skip_white_space()
                continue
            if c in ["?"] and section == "START_VALUE":
                # Most values have to be surrounded by quotes
                # Question marks are parameters, and are valid values on their own
                results.append((keys.copy(), "?"))
                keys.clear()
                section = "END_VALUE"  # Next step is to look for other key/value pairs
                continue
            if current_phrase == "" and section == "START_KEY":
                section = "KEY"
            if section in ["KEY", "VALUE", "END_VALUE"]:
                current_phrase += c
        return results


class DynamoDBWhereParser(WhereParser):
    def parse(self, where_clause: str, parameters) -> Any:
        _filters = WhereParser.parse_where_clause(where_clause)

        _filters = [
            (key, parameters.pop(0) if value == "?" else value)
            for key, value in _filters
        ]

        return self.filter_rows(_filters)

    def filter_rows(self, _filters):
        def _filter(row) -> bool:
            return all(
                [find_value_in_document(keys, row) == value for keys, value in _filters]
            )

        return [row for row in self.source_data if _filter(row)]


class S3WhereParser(WhereParser):
    def parse(self, where_clause: str, parameters) -> Any:
        # parameters argument is ignored - only relevant for DynamoDB
        _filters = WhereParser.parse_where_clause(where_clause)

        return self.filter_rows(_filters)

    def filter_rows(self, _filters):
        def _filter(row):
            return all(
                [find_value_in_document(keys, row) == value for keys, value in _filters]
            )

        return [row for row in self.source_data if _filter(row)]
