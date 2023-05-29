from json import JSONEncoder
from typing import Dict, Any, List, Union

from .clause_tokenizer import ClauseTokenizer
from .case_insensitive_dict import CaseInsensitiveDict

ACCEPTED_QUOTES = ["'", '"', "’"]
NEW_LINE = "\n"


class Variable:
    def __init__(self, value: Any) -> None:
        self.value = value
        if value == "null":
            self.value = None
        elif isinstance(value, str) and value.lower() in ["true", "false"]:
            self.value = bool(value)

    def __repr__(self) -> str:
        return f"<{self.value}>"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other) -> bool:
        return other and isinstance(other, Variable) and self.value == other.value

    def apply(self, value) -> Any:
        if isinstance(value, dict):
            split_value = (
                self.value.split(".") if isinstance(self.value, str) else [self.value]
            )
            current_key = split_value[0]
            if current_key not in value:
                return MissingVariable()
            remaining_keys = ".".join(split_value[1:])
            return Variable(remaining_keys).apply(value[current_key])
        else:
            return value


class MissingVariable(Variable):
    def __init__(self) -> None:
        super().__init__(value=None)


class JsonParser:
    def parse(self, original, tokenizer=None, only_parse_initial=False) -> Any:
        if not (original.startswith("{") or original.startswith("[")):
            # Doesn't look like JSON - let's return as a variable
            return original if original.isnumeric() else Variable(original)
        section = None  # DICT_KEY | KEY_TO_VALUE | DICT_VAL | OBJECT_END
        dict_key = None
        current_phrase = ""
        result: Dict[Any, Any] = CaseInsensitiveDict()
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
                result[dict_key] = (
                    int(current_phrase)
                    if section == "INT_VALUE"
                    else Variable(current_phrase)
                )
                section = None
                current_phrase = ""
                if c == "}" and only_parse_initial:
                    break
            elif c in [","] and section in ["VAR_VALUE", "INT_VALUE"]:
                result[dict_key] = (
                    int(current_phrase)
                    if section == "INT_VALUE"
                    else Variable(current_phrase)
                )
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

    def _parse_list(self, original, tokenizer) -> Any:
        result: List[Union[Any, Dict]] = list()
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
            elif c.isnumeric() and section is None:
                result.append(int(c + tokenizer.next_until([",", "]"])))
                current_phrase = ""
                section = None
                # Skip the comma, and any whitespace
                tokenizer.next()
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
                result.append(Variable(current_phrase))
                return result
            elif c == "," and section == "VAR_VALUE":
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
    def default(self, o):
        if isinstance(o, Variable) and o.value is None:
            return None
        if isinstance(o, CaseInsensitiveDict):
            return dict(o.items())
        return JSONEncoder.default(self, o)
