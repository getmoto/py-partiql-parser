from typing import Dict, Any

from .clause_tokenizer import ClauseTokenizer


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
