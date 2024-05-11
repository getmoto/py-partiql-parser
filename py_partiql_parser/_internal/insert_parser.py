from typing import Any, Dict, Tuple

from .json_parser import JsonParser
from .clause_tokenizer import ClauseTokenizer
from .utils import serializer


class InsertParser:
    def parse(self, query: str) -> Tuple[str, Dict[str, Any]]:
        tokenizer = ClauseTokenizer(query)

        section = "START"
        current_phrase = ""

        table_name = ""
        attr = {}

        while True:
            c = tokenizer.next()
            if c is None:
                break

            if c == " ":
                if section == "START":
                    assert (
                        current_phrase.upper() == "INSERT"
                    ), f"{current_phrase} should be INSERT"
                    current_phrase = ""
                    section = "INSERT_FROM"
                    continue
                if section == "INSERT_FROM":
                    assert (
                        current_phrase.upper() == "INTO"
                    ), f"{current_phrase} should be INTO"
                    current_phrase = ""
                    section = "TABLE_NAME"
                    continue
                if section == "SECTION_VALUE":
                    assert current_phrase.upper() in ["VALUE"]
                    tokenizer.skip_white_space()
                    attr = next(JsonParser.parse(tokenizer.give_remaining()))
                    for key, value in attr.items():
                        attr[key] = serializer.serialize(value)
                if section == "TABLE_NAME":
                    table_name = current_phrase
                    current_phrase = ""
                    tokenizer.skip_white_space()
                    section = "SECTION_VALUE"
                continue
            elif c in ["'", '"']:
                if section == "TABLE_NAME":
                    table_name = tokenizer.next_until([c])
                    tokenizer.skip_white_space()
                    section = "SECTION_VALUE"
                continue
            else:
                current_phrase += c
                continue

        return table_name, attr
