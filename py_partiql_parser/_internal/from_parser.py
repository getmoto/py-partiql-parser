from typing import Any, Dict, List, Union

from .clause_tokenizer import ClauseTokenizer
from .utils import CaseInsensitiveDict

from ..exceptions import ParserException


class FromParser:
    def __init__(self, from_clause: str):
        """
        Parse a FROM-clause in a PARTIQL query
        :param from_clause: a string of format `a AS b, x AS y` where `a` and `x` can contain commas
        :return: a dictionary of format `[b:a, y:x]`
        """
        clauses: Dict[str, Any] = dict()
        section = None  # NAME/AS/ALIAS
        current_phrase = ""
        name = None
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


class S3FromParser(FromParser):
    def get_source_data(
        self, document: Union[CaseInsensitiveDict, List[CaseInsensitiveDict]]
    ) -> Any:
        from_query = list(self.clauses.values())[0].lower()
        if "." in from_query:
            return self._get_nested_source_data(document)

        if isinstance(document, list):
            return {"_1": document}
        else:
            return document

    def _get_nested_source_data(
        self, document: Union[CaseInsensitiveDict, List[CaseInsensitiveDict]]
    ) -> Any:
        """
        Our FROM-clauses are nested, meaning we need to dig into the provided document to return the key that we need
           --> FROM s3object.name as name
        """
        entire_key = list(self.clauses.values())[0].lower().split(".")
        if entire_key[0].lower() in ["s3object[*]"]:
            entire_key = entire_key[1:]
        alias = list(self.clauses.keys())[0]
        if alias.endswith("[*]"):
            alias = alias[0:-3]
        key_so_far = []
        for key in entire_key:
            key_so_far.append(key)

            if key in document:
                document = document[key]
                if isinstance(document, list):
                    # AWS behaviour when the root-document is a list
                    document = CaseInsensitiveDict({"_1": document[0]})
                elif key_so_far == entire_key:
                    if list(self.clauses.keys()) == list(self.clauses.values()):
                        # self.clauses contains the same from_clause if no alias is provided
                        # FROM s3object.a
                        pass
                    else:
                        # An alias has been provided, and the subsequent WHERE/SELECT clauses should use it
                        # FROM s3object as s WHERE s.x = '..'
                        document = CaseInsensitiveDict({alias: document})
            else:
                document = CaseInsensitiveDict()

        return document


class DynamoDBFromParser(FromParser):
    def __init__(self, from_clause: str):
        super().__init__(from_clause)

        for alias, table_name in list(self.clauses.items()):
            if table_name[0].isnumeric():
                raise ParserException(
                    "ValidationException", "Aliasing is not supported"
                )

            if table_name[0] == '"' and table_name[-1] == '"':
                self.clauses[alias] = table_name[1:-1]

            if table_name[0] == "'" and table_name[-1] == "'":
                self.clauses[alias] = table_name[1:-1]
