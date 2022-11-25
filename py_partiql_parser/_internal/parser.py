import re

from typing import Dict, Any, Union, List, AnyStr

from .clause_tokenizer import ClauseTokenizer
from .json_parser import JsonParser, Variable


class Parser:

    RETURN_TYPE = Union[Dict[AnyStr, Any], List]

    def parse(self, query) -> RETURN_TYPE:
        clauses = re.split("SELECT | FROM | WHERE ", query)
        # First clause is whatever comes in front of SELECT - which should be nothing
        _ = clauses[0]
        # FROM
        from_clause = clauses[2]
        data_source = FromParser().parse(from_clause)
        # WHERE
        where_clause = clauses[3] if len(clauses) > 3 else None
        # SELECT
        select_clause = clauses[1]
        select_clause = SelectParser().parse(select_clause)
        return self._select_data(data_source, select_clause)

    def _select_data(self, data_source, select_clause) -> List[Any]:
        """
        Find a key in a dictionary
        :param data_source: Dictionary such as {"a: {"b": "asdf"}}
        :param key: Key of the data source, in dot-notation: a.b
        :return: "asdf"
        """
        if not select_clause:
            return data_source
        if isinstance(select_clause, Variable):
            if not select_clause.value:
                return data_source
            current_key = select_clause.value.split(".")[0]
            remaining_keys = ".".join(select_clause.value.split(".")[1:])
            if isinstance(data_source, list):
                return [
                    self._select_data(row[current_key], Variable(remaining_keys))
                    for row in data_source
                ]
            elif isinstance(data_source, dict):
                return self._select_data(
                    data_source[current_key], Variable(remaining_keys)
                )
        if isinstance(select_clause, dict):
            return [
                {k: v.apply(row) for k, v in select_clause.items()}
                for row in data_source
            ]
        if isinstance(select_clause, list):
            return [
                [self._select_data(data_row, x) for x in select_clause]
                for data_row in data_source
            ]
        return []


class SelectParser:
    def parse(self, select_clause) -> Any:
        if select_clause.startswith("VALUE "):
            select_clause = select_clause[6:].strip()
            return JsonParser().parse(select_clause)


class FromParser:
    def parse(self, from_clause) -> Any:
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
        result = []
        for alias, data in clauses.items():
            data = JsonParser().parse(data)
            if isinstance(data, list) and all([isinstance(row, dict) for row in data]):
                result.extend([{alias: row} for row in data])
            else:
                result.append({alias: data})
        return result
