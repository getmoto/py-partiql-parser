import re
import sys
from collections import OrderedDict
from copy import copy
from typing import Any, Dict, List, Iterator, Optional, Tuple, Union, TYPE_CHECKING

if sys.version_info[:2] > (3, 8):
    from collections.abc import Mapping, MutableMapping
else:
    from typing import Mapping, MutableMapping

if TYPE_CHECKING:
    from .where_parser import AbstractWhereClause

from .._packages.boto3.types import TypeDeserializer, TypeSerializer


deserializer = TypeDeserializer()
serializer = TypeSerializer()


def is_dict(dct: Any) -> bool:
    return isinstance(dct, dict) or isinstance(dct, CaseInsensitiveDict)


def find_nested_data(
    select_clause: str, data_source: List["CaseInsensitiveDict"]
) -> List[Dict[str, Any]]:
    """
    Iterate over a list of JSON objects, and return only the keys specified
    :param select_clause: Key of the data source, in dot-notation: a.b
    :param data_source: List of JSON documents as dictionary
    :return: A list of JSON keys as dictionary
    """

    results: List[Dict[str, Any]] = []

    for row in data_source:
        # Run the select-clause over each row
        result = find_nested_data_in_object(select_clause=select_clause, json_doc=row)
        results.append(result)
    return results


def find_nested_data_in_object(
    select_clause: str, json_doc: Union[str, "CaseInsensitiveDict"]
) -> Any:
    if select_clause == "*":
        return json_doc

    current_key = select_clause.split(".")[0]
    remaining_keys = ".".join(select_clause.split(".")[1:])
    if isinstance(json_doc, list):  # type: ignore[unreachable]
        result = []  # type: ignore[unreachable]
        for row in json_doc:
            if current_key not in row:
                result.append(MissingVariable())
            else:
                result.append(
                    find_nested_data_in_object(
                        json_doc=row[current_key], select_clause=remaining_keys
                    )
                )
        return result
    elif is_dict(json_doc):
        if current_key not in json_doc:
            return MissingVariable()
        if remaining_keys:
            return find_nested_data_in_object(
                json_doc=json_doc[current_key], select_clause=remaining_keys  # type: ignore[index]
            )
        return json_doc.get_original(current_key)  # type: ignore[union-attr]


def find_value_in_document(keys: List[str], json_doc: Any) -> Any:
    if not is_dict(json_doc):
        return None
    key_is_array = re.search(r"(.+)\[(\d+)\]$", keys[0])
    if key_is_array:
        key_name = key_is_array.group(1)
        array_index = int(key_is_array.group(2))
        try:
            requested_list = json_doc.get(key_name, [])
            assert isinstance(requested_list, list)
            doc_one_layer_down = requested_list[array_index]
        except IndexError:
            # Array exists, but does not have enough values
            doc_one_layer_down = {}
        except AssertionError:
            # Requested key is not an array - fail silently just like AWS does
            doc_one_layer_down = {}
        return find_value_in_document(keys[1:], doc_one_layer_down)
    if len(keys) == 1:
        return json_doc.get(keys[0])
    return find_value_in_document(keys[1:], json_doc.get(keys[0], {}))


def find_value_in_dynamodb_document(keys: List[str], json_doc: Any) -> Any:
    if not is_dict(json_doc):
        return None
    key_is_array = re.search(r"(.+)\[(\d+)\]$", keys[0])
    if key_is_array:
        key_name = key_is_array.group(1)
        array_index = int(key_is_array.group(2))
        try:
            requested_list = json_doc.get(key_name, {})
            assert "L" in requested_list
            doc_one_layer_down = requested_list["L"][array_index]
            if "M" in doc_one_layer_down:
                doc_one_layer_down = doc_one_layer_down["M"]
        except IndexError:
            # Array exists, but does not have enough values
            doc_one_layer_down = {}
        except AssertionError:
            # Requested key is not a list - fail silently just like AWS does
            doc_one_layer_down = {}
        return find_value_in_dynamodb_document(keys[1:], doc_one_layer_down)
    if len(keys) == 1:
        if "M" in json_doc:
            return json_doc["M"].get(keys[0])
        else:
            return json_doc.get(keys[0])
    nested_doc = json_doc.get(keys[0], {})
    if "M" in nested_doc:
        return find_value_in_dynamodb_document(keys[1:], nested_doc["M"])
    # Key is not a map
    # Or does not exist
    return None


class QueryMetadata:
    def __init__(
        self,
        tables: Dict[str, str],
        where_clause: Optional["AbstractWhereClause"] = None,
        is_select_query: bool = False,
    ):
        self._tables = tables
        self._where_clause = where_clause
        self._is_select_query = is_select_query

    def get_table_names(self) -> List[str]:
        return list(self._tables.values())

    def get_filter_names(self) -> List[str]:
        if self._where_clause:
            return self._where_clause.get_filter_names()
        return []

    def is_select_query(self) -> bool:
        return self._is_select_query


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

    def __eq__(self, other: Any) -> bool:
        return other and isinstance(other, Variable) and self.value == other.value

    def apply(self, value: Any) -> Any:
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

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, MissingVariable)


class CaseInsensitiveDict(MutableMapping[str, Any]):
    # Taken from https://raw.githubusercontent.com/kennethreitz/requests/v2.25.1/requests/structures.py

    def __init__(self, data: Optional[Mapping[str, Any]] = None):
        self._store: Dict[str, Any] = OrderedDict()
        if data:
            self.update(
                {
                    key: CaseInsensitiveDict(val) if is_dict(val) else val
                    for key, val in data.items()
                }
            )

    def __setitem__(self, key: str, value: Any) -> None:
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key: str) -> Any:
        return self._store[key.lower()][1]

    def __delitem__(self, key: str) -> None:
        del self._store[key.lower()]

    def __iter__(self) -> Iterator[str]:
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def lower_items(self) -> Iterator[Tuple[str, Any]]:
        """Like iteritems(), but with all lowercase keys."""
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    def get_regular(self) -> Dict[str, Any]:
        dct = {}
        for key, val in self.items():
            if isinstance(val, CaseInsensitiveDict):
                dct[key] = val.get_regular()
            else:
                dct[key] = val
        return dct

    def get_original(self, key: str) -> "CaseInsensitiveDict":
        original_key, original_value = self._store[key.lower()]
        return CaseInsensitiveDict({original_key: original_value})

    # Copy is required
    def copy(self) -> "CaseInsensitiveDict":
        _new = CaseInsensitiveDict()
        for key, value in self._store.values():
            _new[key] = copy(value)
        return _new

    def __repr__(self) -> str:
        return str(dict(self.items()))
