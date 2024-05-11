from typing import Any, Dict

from .clause_tokenizer import ClauseTokenizer
from .json_parser import JsonParser
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
    def get_source_data(self, documents: Dict[str, str]) -> Any:
        from_alias = list(self.clauses.keys())[0].lower()
        from_query = list(self.clauses.values())[0].lower()
        if "." in from_query:
            return self._get_nested_source_data(documents)

        key_has_asterix = from_query.endswith("[*]")
        from_query = from_query[0:-3] if key_has_asterix else from_query
        from_alias = from_alias[0:-3] if from_alias.endswith("[*]") else from_alias
        doc_is_list = documents[from_query].startswith("[") and documents[
            from_query
        ].endswith("]")

        source_data = list(JsonParser.parse(documents[from_query]))

        if doc_is_list:
            return {"_1": source_data[0]}
        elif from_alias:
            return [CaseInsensitiveDict({from_alias: doc}) for doc in source_data]
        else:
            return source_data

    def _get_nested_source_data(self, documents: Dict[str, Any]) -> Any:
        """
        Our FROM-clauses are nested, meaning we need to dig into the provided document to return the key that we need
           --> FROM s3object.name as name
        """
        root_doc = True
        source_data = documents
        iterate_over_docs = False
        entire_key = list(self.clauses.values())[0].lower().split(".")
        alias = list(self.clauses.keys())[0]
        if alias.endswith("[*]"):
            alias = alias[0:-3]
        key_so_far = []
        for key in entire_key:
            key_so_far.append(key)
            key_has_asterix = key.endswith("[*]") and key[0:-3] in source_data
            new_key = key[0:-3] if key_has_asterix else key
            if iterate_over_docs and isinstance(source_data, list):  # type: ignore[unreachable]
                # The previous key ended in [*]
                # Iterate over all docs in the result, and only return the requested source key
                if key_so_far == entire_key:  # type: ignore[unreachable]
                    # If we have an alias, we have to use that instead of the original name
                    source_data = [{alias: doc.get(new_key, {})} for doc in source_data]
                else:
                    source_data = [
                        doc.get_original(new_key) or CaseInsensitiveDict({})
                        for doc in source_data
                    ]
            else:
                # The previous key was a regular key
                # Assume that the result consists of a singular JSON document
                if new_key in source_data:
                    doc_is_list = source_data[new_key].startswith("[") and source_data[
                        new_key
                    ].endswith("]")
                    source_data = list(JsonParser.parse(source_data[new_key]))  # type: ignore
                    if root_doc and doc_is_list:
                        # AWS behaviour when the root-document is a list
                        source_data = {"_1": source_data[0]}  # type: ignore
                    elif key_so_far == entire_key:
                        if isinstance(source_data, list):  # type: ignore[unreachable]
                            source_data = [{alias: doc} for doc in source_data]  # type: ignore[unreachable]
                        else:
                            source_data = {alias: source_data}
                else:
                    source_data = {}

            iterate_over_docs = key_has_asterix
            root_doc = False

        return source_data


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
