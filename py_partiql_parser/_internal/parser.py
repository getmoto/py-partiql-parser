import re

from typing import Dict, Any, Union, List, AnyStr, Optional

from .clause_tokenizer import ClauseTokenizer
from .json_parser import JsonParser, Variable
from .utils import find_nested_data


class Parser:

    RETURN_TYPE = Union[Dict[AnyStr, Any], List]

    def __init__(self, source_data: Optional[Dict[str, str]] = None):
        self.source_data = source_data or {}

    def parse(self, query: str) -> RETURN_TYPE:
        query = query.replace("\n", " ")
        clauses = re.split("SELECT | FROM | WHERE ", query, flags=re.IGNORECASE)
        # First clause is whatever comes in front of SELECT - which should be nothing
        _ = clauses[0]
        # FROM
        from_clause = clauses[2]
        from_clauses, partially_prepped_data = FromParser(self.source_data).parse(
            from_clause
        )
        # WHERE
        if len(clauses) > 3:
            where_clause = clauses[3]
            partially_prepped_data = WhereParser(partially_prepped_data).parse(
                from_clauses, where_clause
            )
        # SELECT
        select_clause = clauses[1]
        return SelectParser().parse(select_clause, partially_prepped_data)


class SelectParser:
    def parse(self, select_clause, data=None) -> Any:
        if select_clause.startswith("VALUE "):
            select_clause = select_clause[6:].strip()
            select_clause = JsonParser().parse(select_clause)
            return find_nested_data(data, select_clause)
        if select_clause.startswith("VALUES "):
            return set(find_nested_data(data, Variable(select_clause[7:])))
        return find_nested_data(data, None)


class FromParser:
    def __init__(self, source_data: Optional[Dict[str, str]] = None):
        self.source_data = source_data or {}

    def parse(self, from_clause) -> Any:
        """
        Parse a FROM-clause in a PARTIQL query
        :param from_clause: a string of format `a AS b, x AS y` where `a` and `x` can contain commas
        :return: a dictionary of format `[b:a, y:x]`
        """
        if from_clause.lower().startswith("from "):
            from_clause = from_clause[5:]
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
                if section == "AS" and current_phrase == "AS":
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
        #
        # Substitute the FROM-clause with the appropriate data
        # TODO: when we have multiple clauses, we should create a cartesian product
        result = []
        for alias, data in clauses.items():
            data = JsonParser().parse(data)
            if isinstance(data, list) and all([isinstance(row, dict) for row in data]):
                result.extend([{alias: row} for row in data])
            elif isinstance(data, Variable) and self.source_data:
                result.extend(find_nested_data(self.source_data, data))
            else:
                result.append({alias: data})
        return clauses, result


class WhereParser:
    def __init__(self, partially_prepped_data: Any = None):
        self.partially_prepped_data = partially_prepped_data or {}

    def parse(self, from_clauses, where_clause) -> Any:
        where_clause_parser = ClauseTokenizer(where_clause)
        alias: Optional[str] = None
        key: Optional[str] = None
        value: Optional[str] = None
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
        #
        # Let's assume the following:
        #  - We only have one data source, denoted by the alias
        #  - Our partially prepped data is from that data source
        return [
            row
            for row in self.partially_prepped_data
            if row_filter(row, alias, key, value)
        ]


def row_filter(
    row: Dict[str, Any], alias: Optional[str], key: Optional[str], value: Optional[str]
):
    if alias in row:
        row = row[alias]
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
