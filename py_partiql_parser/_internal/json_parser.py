from json import JSONEncoder
from typing import Any, List, Optional

from .clause_tokenizer import ClauseTokenizer
from .utils import CaseInsensitiveDict, Variable

ACCEPTED_QUOTES = ["'", '"', "’"]
NEW_LINE = "\n"


class JsonParser:
    """
    Input can be a multiple documents, separated by a new-line (\n) characters
    So we can't use the builtin JSON parser
    """

    def parse(
        self,
        original: str,
        tokenizer: Optional[ClauseTokenizer] = None,
        only_parse_initial: bool = False,
    ) -> Any:
        if not (original.startswith("{") or original.startswith("[")):
            # Doesn't look like JSON - let's return as a variable
            return original if original.isnumeric() else Variable(original)
        section: Optional[str] = None  # DICT_KEY | KEY_TO_VALUE | DICT_VAL | OBJECT_END
        dict_key = ""
        current_phrase = ""
        result = CaseInsensitiveDict()
        tokenizer = tokenizer or ClauseTokenizer(original)
        while True:
            c = tokenizer.next()
            if not c:
                break
            elif c == "[" and (not section or section == "KEY_TO_VALUE"):
                # Start of a list
                if not section:
                    return self._parse_list(original, tokenizer)
                else:
                    result[dict_key] = self._parse_list(original, tokenizer)
                    section = None
                    current_phrase = ""
            elif c in ["{", ","] and (not section or section == "OBJECT_END"):
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
                # Start of a value with a new dictionary
                tokenizer.revert()  # Ensure we start the new parser with the initial {
                result[dict_key] = self.parse(original, tokenizer)
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
            elif section in ["OBJECT_END"]:
                next_documents = self.parse(original, tokenizer)
                if next_documents == {}:
                    return result
                elif isinstance(next_documents, list):
                    return [result] + next_documents
                else:
                    return [result, next_documents]
            elif c == "}" and section is None:
                section = "OBJECT_END"
                # We know whether we are at the end of an object at this point
                # But we don't know whether this is:
                # - end of the root object
                # - end of a nested object
                # - inbetween multiple objects (separated by new-line)
                tokenizer.skip_white_space()
                if tokenizer.current() == "{":
                    # we're inbetween multiple objects - continue parsing
                    tokenizer.revert()
                    pass
                else:
                    # we're at the end of the root object - next char is probably None. Break and return to the user
                    # we're at the end of a nested object - next char is probably }.    Break and let the parent processor takeover
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

    def _parse_list(self, original: str, tokenizer: ClauseTokenizer) -> Any:
        result: List[Any] = list()
        section = None
        current_phrase = ""
        while True:
            c = tokenizer.next()
            if not c:
                break
            if c == "{":
                tokenizer.revert()  # Ensure we start the new parser with the initial {
                result.append(self.parse(original, tokenizer, only_parse_initial=True))
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
