from json import JSONEncoder
from typing import Any, List, Iterator, Optional

from .clause_tokenizer import ClauseTokenizer
from .utils import CaseInsensitiveDict, Variable

ACCEPTED_QUOTES = ["'", '"', "’"]
NEW_LINE = "\n"


class JsonParser:
    """
    Input can be a multiple documents, separated by a new-line (\n) characters
    So we can't use the builtin JSON parser
    """

    @staticmethod
    def parse(original: str) -> Iterator[Any]:  # type: ignore[misc]
        if not (original.startswith("{") or original.startswith("[")):
            # Doesn't look like JSON - let's return as a variable
            yield original if original.isnumeric() else Variable(original)
        tokenizer = ClauseTokenizer(original)
        while tokenizer.current() is not None:
            result = JsonParser._get_next_document(original, tokenizer)
            if result is not None:
                yield result

    @staticmethod
    def _get_next_document(  # type: ignore[misc]
        original: str,
        tokenizer: ClauseTokenizer,
        only_parse_initial: bool = False,
    ) -> Any:
        section: Optional[str] = None  # DICT_KEY | KEY_TO_VALUE | DICT_VAL | OBJECT_END
        dict_key = ""
        current_phrase = ""
        result = CaseInsensitiveDict()
        level = 0
        while True:
            c = tokenizer.next()
            if not c:
                return None
            elif c == "[" and (not section or section == "KEY_TO_VALUE"):
                level += 1
                # Start of a list
                if not section:
                    return JsonParser._parse_list(original, tokenizer)
                else:
                    result[dict_key] = JsonParser._parse_list(original, tokenizer)
                    section = None
                    current_phrase = ""
            elif c in ["{", ","] and (not section or section == "OBJECT_END"):
                if c == "{":
                    level += 1
                # Start of a key
                section = "DICT_KEY"
                tokenizer.skip_until(ACCEPTED_QUOTES)
                current_phrase = ""
            elif c in ACCEPTED_QUOTES and section == "DICT_KEY":
                # End of a key
                dict_key = current_phrase
                tokenizer.skip_until([":"])
                section = "KEY_TO_VALUE"
                current_phrase = ""
            elif c in ["{"] and section == "KEY_TO_VALUE":
                level += 1
                # Start of a value with a new dictionary
                tokenizer.revert()  # Ensure we start the new parser with the initial {
                result[dict_key] = JsonParser._get_next_document(original, tokenizer)
                section = None
                current_phrase = ""
            elif c in ACCEPTED_QUOTES and section == "KEY_TO_VALUE":
                # Start of a value
                section = "DICT_VAL"
                current_phrase = ""
            elif c in ACCEPTED_QUOTES and section == "DICT_VAL":
                # End of a value
                result[dict_key] = current_phrase
                section = None
                current_phrase = ""
            elif c in ["}"] and section in ["VAR_VALUE", "INT_VALUE"]:
                level -= 1
                # End of a variable/number
                if section == "INT_VALUE":
                    result[dict_key] = int(current_phrase)
                elif current_phrase.lower() in ["true", "false"]:
                    result[dict_key] = current_phrase.lower() == "true"
                else:
                    result[dict_key] = Variable(current_phrase)
                section = None
                current_phrase = ""
                if only_parse_initial:
                    break
                else:
                    tokenizer.revert()
            elif c in [","] and section in ["VAR_VALUE", "INT_VALUE"]:
                if section == "INT_VALUE":
                    result[dict_key] = int(current_phrase)
                elif current_phrase.lower() in ["true", "false"]:
                    result[dict_key] = current_phrase.lower() == "true"
                else:
                    result[dict_key] = Variable(current_phrase)
                tokenizer.revert()
                section = None
                current_phrase = ""
            elif c == "}" and section is None:
                level -= 1
                if level == 0:
                    return result
                else:
                    break
            elif c in [" ", NEW_LINE] and section not in ["DICT_KEY", "DICT_VAL"]:
                pass
            else:
                if section == "KEY_TO_VALUE":
                    # We found a value directly after the key, unquoted
                    # That means it's either a variable, or a number
                    if c.isnumeric():
                        section = "INT_VALUE"
                    else:
                        section = "VAR_VALUE"
                if section in ["DICT_KEY", "DICT_VAL", "INT_VALUE", "VAR_VALUE"]:
                    current_phrase += c
        return result

    @staticmethod
    def _parse_list(original: str, tokenizer: ClauseTokenizer) -> List[Any]:  # type: ignore
        result: List[Any] = list()
        section = None
        current_phrase = ""
        while True:
            c = tokenizer.next()
            if not c:
                break
            if c == "{":
                tokenizer.revert()  # Ensure we start the new parser with the initial {
                result.append(
                    JsonParser._get_next_document(
                        original, tokenizer, only_parse_initial=True
                    )
                )
                if tokenizer.current() == "]":
                    break
                tokenizer.skip_until([","])
                tokenizer.skip_white_space()
            elif c in ACCEPTED_QUOTES and section is None:
                section = "VALUE"
            elif c in ACCEPTED_QUOTES and section == "VALUE":
                result.append(current_phrase)
                current_phrase = ""
                section = None
            elif c == "]" and not section:
                return result
            elif c == "]" and section == "VAR_VALUE":
                if current_phrase.isnumeric():
                    result.append(int(current_phrase))
                elif current_phrase.lower() in ["true", "false"]:
                    result.append(current_phrase.lower() == "true")
                else:
                    result.append(Variable(current_phrase))
                return result
            elif c == "," and section == "VAR_VALUE":
                if current_phrase.isnumeric():
                    result.append(int(current_phrase))
                elif current_phrase.lower() in ["true", "false"]:
                    result.append(current_phrase.lower() == "true")
                else:
                    result.append(Variable(current_phrase))
                current_phrase = ""
                section = None
                tokenizer.skip_white_space()
            elif c == "," and not section:
                tokenizer.skip_white_space()
            elif not section:
                current_phrase += c
                section = "VAR_VALUE"
            elif section in ["VALUE", "VAR_VALUE"]:
                current_phrase += c
        return result


class SelectEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Variable) and o.value is None:
            return None
        if isinstance(o, CaseInsensitiveDict):
            return dict(o.items())
        return JSONEncoder.default(self, o)
