import re

from typing import Dict, Any, Union, List, AnyStr, Optional, Tuple

from .clause_tokenizer import ClauseTokenizer
from .json_parser import JsonParser, Variable
from .utils import find_nested_data


class Parser:
    RETURN_TYPE = Union[Dict[AnyStr, Any], List]

    def __init__(self, source_data: Dict[str, str]):
        self.source_data = source_data
        # Source data is in the format: {source: json}
        # Where 'json' is one or more json documents separated by a newline
        self.documents = {key: value for key, value in source_data.items()}

    def parse(self, query: str) -> List[str]:
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
                    self.documents[key] = [self.documents[key]]
        # SELECT
        select_clause = clauses[1]
        key, data = SelectParser().parse(select_clause, from_clauses, self.documents)
        return find_nested_data(select_clause=key, data_source=data)


class SelectParser:
    def parse(
        self,
        select_clause: str,
        from_clauses: Dict[str, Any],
        data: Dict[str, List[str]],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        aliased_data = from_clauses
        for key, value in aliased_data.items():
            if value in data:
                aliased_data[key] = data[value]
        # TODO: deal with multiple select clauses
        if "." in select_clause:
            key, remaining = select_clause.split(".", maxsplit=1)
            return remaining, aliased_data[key]
        else:
            return select_clause, aliased_data[key]


class FromParser:
    def parse(self, from_clause) -> Dict[str, str]:
        """
        Parse a FROM-clause in a PARTIQL query
        :param from_clause: a string of format `a AS b, x AS y` where `a` and `x` can contain commas
        :return: a dictionary of format `[b:a, y:x]`
        """
        clauses: Dict[str, Any] = dict()
        section = "NAME"  # NAME/AS/ALIAS
        current_phrase = ""
        name = alias = None
        from_clause_parser = ClauseTokenizer(from_clause)
        while True:
            c = from_clause_parser.next()
            if c is None:
                break
            if c == "[":
                current_phrase = "[" + from_clause_parser.next_until(["]"]) + "]"
                continue
            if c == " ":
                if section == "AS" and current_phrase.upper() == "AS":
                    current_phrase = ""
                    section = "ALIAS"
                elif section == "NAME":
                    name = current_phrase
                    current_phrase = ""
                    section = "AS"
                elif section == "ALIAS":
                    alias = current_phrase
                    current_phrase = ""
                    section = "NAME"
                continue
            if c == ",":
                if section == "NAME":
                    clauses[current_phrase] = current_phrase
                elif section == "ALIAS":
                    clauses[current_phrase] = name
                    section = "NAME"
                current_phrase = ""
                from_clause_parser.skip_white_space()
                continue
            current_phrase += c
        if section == "NAME":
            clauses[current_phrase] = current_phrase
        else:
            clauses[current_phrase] = name
        #
        # One FROM clause may point to the alias of another
        # {'s': 'sensors', 'r': 's.readings'} --> {'s': 'sensors', 'r': 'sensors.readings'}
        aliases = [(f"{key}.", f"{value}.") for key, value in clauses.items()]
        for key, value in clauses.items():
            for short, long in aliases:
                if value.startswith(short):
                    clauses[key] = value.replace(short, long)
        # {alias: full_name_of_table_or_file}
        return clauses


class WhereParser:
    def __init__(self, partially_prepped_data: Any = None):
        self.partially_prepped_data = partially_prepped_data or {}

    def parse(self, from_clauses: Dict[str, str], where_clause: str) -> Any:
        return_all = where_clause == "TRUE"
        if return_all:
            alias, key, value = ("", "", "")
        else:
            alias, key, value = self._parse_where_clause(where_clause)
        #
        # Let's assume the following:
        #  - We only have one data source, denoted by the alias
        #  - Our partially prepped data is from that data source
        data_as_string = self.partially_prepped_data.get(from_clauses.get(alias, alias))
        data_as_json = JsonParser().parse(data_as_string)
        return {
            from_clauses.get(alias, alias): [
                row for row in data_as_json if return_all or row_filter(row, key, value)
            ]
        }

    def _parse_where_clause(self, where_clause: str) -> Tuple[str, str, str]:
        where_clause_parser = ClauseTokenizer(where_clause)
        alias = ""
        key = ""
        value = ""
        section: Optional[str] = "ALIAS"
        current_phrase = ""
        while True:
            c = where_clause_parser.next()
            if c is None:
                if section == "KEY":
                    key = current_phrase
                break
            if c == ".":
                if section == "ALIAS":
                    alias = current_phrase
                    current_phrase = ""
                    section = "START_KEY"
                    continue
            if c in ['"', "'"]:
                if section == "START_KEY":
                    section = "KEY"
                    continue
                if section == "KEY":
                    key = current_phrase
                    current_phrase = ""
                    where_clause_parser.skip_until(["="])
                    where_clause_parser.skip_white_space()
                    section = "START_VALUE"
                    continue
                if section == "START_VALUE":
                    section = "VALUE"
                    continue
                if section == "VALUE":
                    section = None
                    value = current_phrase
                    current_phrase = ""
            if current_phrase == "" and section == "START_KEY":
                section = "KEY"
            if section in ["ALIAS", "KEY", "VALUE"]:
                current_phrase += c
        return alias, key, value


def row_filter(row: Dict[str, Any], key: str, value: Optional[str]) -> bool:
    if value is None:
        return key in row and not_none(row[key])
    else:
        return key in row and row[key] == value


def not_none(x: Optional[Variable]) -> bool:
    if x is None:
        return False
    if isinstance(x, Variable):
        return x.value is not None
    return True
