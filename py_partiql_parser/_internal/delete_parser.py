from typing import Any, Dict, List, Tuple

from .clause_tokenizer import ClauseTokenizer
from .utils import serializer


class DeleteParser:
    def parse(self, query: str) -> Tuple[str, List[Tuple[str, Dict[str, Any]]]]:
        tokenizer = ClauseTokenizer(query)

        section = "START"
        current_phrase = ""

        table_name = ""
        attr_filters: List[Tuple[str, Dict[str, Any]]] = []

        while True:
            c = tokenizer.next()
            if c is None:
                break

            if c == " ":
                if section == "START":
                    assert (
                        current_phrase.upper() == "DELETE"
                    ), f"{current_phrase} should be DELETE"
                    current_phrase = ""
                    section = "DELETE_FROM"
                    continue
                if section == "DELETE_FROM":
                    assert (
                        current_phrase.upper() == "FROM"
                    ), f"{current_phrase} should be FROM"
                    current_phrase = ""
                    section = "TABLE_NAME"
                    continue
                if section == "ACTION":
                    assert current_phrase.upper() in ["SET", "REMOVE"]
                    section = f"ACTION_{current_phrase.upper()}"
                    current_phrase = ""
                    continue
                if section == "SECTION_WHERE":
                    assert current_phrase.upper() == "WHERE"
                    section = "WHERE"
                    current_phrase = ""
                    continue
                if section == "WHERE_AND":
                    assert current_phrase.upper() == "AND"
                    section = "WHERE"
                    current_phrase = ""
                if section == "TABLE_NAME":
                    table_name = current_phrase
                    current_phrase = ""
                    tokenizer.skip_white_space()
                    section = "SECTION_WHERE"
                continue
            elif c in ["'", '"']:
                if section == "TABLE_NAME":
                    table_name = tokenizer.next_until([c])
                    tokenizer.skip_white_space()
                    section = "SECTION_WHERE"
                continue
            elif c == "=":
                if section == "WHERE":
                    attr_name = current_phrase
                    tokenizer.skip_white_space()
                    quote_type = tokenizer.current()
                    assert quote_type in ["'", '"']

                    tokenizer.next()
                    attr_value = tokenizer.next_until([quote_type])
                    attr_filters.append((attr_name, serializer.serialize(attr_value)))

                    tokenizer.skip_white_space()
                    current_phrase = ""
                    section = "WHERE_AND"
                continue
            else:
                current_phrase += c
                continue

        return table_name, attr_filters
