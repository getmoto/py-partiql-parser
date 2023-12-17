from typing import Any, Dict, List, Tuple, Optional

from .clause_tokenizer import ClauseTokenizer
from .utils import serializer


class UpdateParser:
    def parse(
        self, query: str
    ) -> Tuple[
        str,
        List[Tuple[str, Optional[Dict[str, Any]]]],
        List[Tuple[str, Dict[str, Any]]],
    ]:
        tokenizer = ClauseTokenizer(query)

        section = "START"
        current_phrase = ""

        table_name = ""
        attrs_to_update: List[Tuple[str, Optional[Dict[str, Any]]]] = []
        attr_filters = []

        while True:
            c = tokenizer.next()
            if c is None:
                break

            if c == " ":
                if section == "START":
                    assert (
                        current_phrase.upper() == "UPDATE"
                    ), f"{current_phrase} should be UPDATE"
                    current_phrase = ""
                    section = "TABLE_NAME"
                if section == "ACTION":
                    assert current_phrase.upper() in ["SET", "REMOVE"]
                    section = f"ACTION_{current_phrase.upper()}"
                    current_phrase = ""
                    continue
                if section == "SECTION_WHERE":
                    assert current_phrase.upper() == "WHERE"
                    section = "WHERE"
                    current_phrase = ""
                if section == "WHERE_AND":
                    assert current_phrase.upper() == "AND"
                    section = "WHERE"
                    current_phrase = ""
                if section == "ACTION_REMOVE":
                    attr_name = current_phrase

                    attrs_to_update.append((attr_name, None))
                    current_phrase = ""

                    tokenizer.skip_white_space()
                    section = "SECTION_WHERE"
                continue
            elif c in ["'", '"']:
                if section == "TABLE_NAME":
                    table_name = tokenizer.next_until([c])
                    tokenizer.skip_white_space()
                    section = "ACTION"
                continue
            elif c == "=":
                if section == "ACTION_SET":
                    attr_name = current_phrase
                    tokenizer.skip_white_space()
                    quote_type = tokenizer.current()
                    assert quote_type in ["'", '"']

                    tokenizer.next()
                    attr_value = tokenizer.next_until([quote_type])
                    attrs_to_update.append(
                        (attr_name, serializer.serialize(attr_value))
                    )
                    current_phrase = ""

                    tokenizer.skip_white_space()
                    section = "SECTION_WHERE"
                elif section == "WHERE":
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

        return table_name, attrs_to_update, attr_filters
