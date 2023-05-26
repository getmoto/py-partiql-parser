from typing import Dict, Any

from .clause_tokenizer import ClauseTokenizer
from .json_parser import JsonParser


class FromParser:
    def __init__(self):
        self.clauses = None

    def parse(self, from_clause) -> Dict[str, str]:
        """
        Parse a FROM-clause in a PARTIQL query
        :param from_clause: a string of format `a AS b, x AS y` where `a` and `x` can contain commas
        :return: a dictionary of format `[b:a, y:x]`
        """
        clauses: Dict[str, Any] = dict()
        section = None  # NAME/AS/ALIAS
        current_phrase = ""
        name = alias = None
        from_clause_parser = ClauseTokenizer(from_clause)
        while True:
            c = from_clause_parser.next()
            if c is None:
                break
            if c == "[":
                if section is None:
                    # Beginning of the FROM-clause - probably a document in its own right, instead of a name
                    current_phrase = "[" + from_clause_parser.next_until(["]"]) + "]"
                    section = "NAME"
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
                    alias = current_phrase  # noqa
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
                # new phrase
                section = None
                continue

            if section is None:
                section = "NAME"

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
        self.clauses = clauses
        return clauses

    def get_source_data(self, documents: Dict[str, str]):
        source_data = documents
        for key in list(self.clauses.values())[0].lower().split("."):
            if key in source_data:
                source_data = JsonParser().parse(source_data[key])
            elif key.endswith("[*]"):
                if isinstance(source_data, dict):
                    source_data = JsonParser().parse(source_data[key[0:-3]])
                elif isinstance(source_data, list):
                    new_source = []
                    for row in source_data:
                        if isinstance(row[key[0:-3]], list):
                            new_source.extend(row[key[0:-3]])
                    source_data = new_source

        return source_data
