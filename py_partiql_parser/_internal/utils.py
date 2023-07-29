import re

from .case_insensitive_dict import CaseInsensitiveDict
from .json_parser import MissingVariable, Variable
from typing import Any, Dict, List, Tuple, Union


def is_dict(dct):
    return isinstance(dct, dict) or isinstance(dct, CaseInsensitiveDict)


def find_nested_data(
    select_clause: str, data_source: List[Dict[str, Any]]
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
    select_clause: Union[None, str, Variable], json_doc: Any
) -> Any:
    if isinstance(select_clause, str):
        if select_clause == "*":
            return json_doc
        select_clause = Variable(select_clause)
    if isinstance(select_clause, Variable):
        if not select_clause.value:
            return json_doc
        current_key = select_clause.value.split(".")[0]
        remaining_keys = ".".join(select_clause.value.split(".")[1:])
        if isinstance(json_doc, list):
            result = []
            for row in json_doc:
                if current_key not in row:
                    result.append(MissingVariable())
                else:
                    result.append(
                        find_nested_data_in_object(
                            row[current_key], Variable(remaining_keys)
                        )
                    )
            return result
        elif isinstance(json_doc, CaseInsensitiveDict):
            if current_key not in json_doc:
                return MissingVariable()
            if remaining_keys:
                return find_nested_data_in_object(
                    json_doc[current_key], Variable(remaining_keys)
                )
            return json_doc.get_original(current_key)
    if isinstance(select_clause, CaseInsensitiveDict):
        result = [
            {k: v.apply(row) for k, v in select_clause.items()} for row in json_doc
        ]
        return [
            {k: v for k, v in row.items() if not isinstance(v, MissingVariable)}
            for row in result
        ]
    if isinstance(select_clause, list):
        return [
            [find_nested_data_in_object(data_row, x) for x in select_clause]
            for data_row in json_doc
        ]
    return []


def find_value_in_document(keys: List[str], json_doc):
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


class QueryMetadata:
    def __init__(
        self, tables: Dict[str, str], where_clauses: List[Tuple[List[str], str]] = None
    ):
        self._tables = tables
        self._where_clauses = where_clauses or []

    def get_table_names(self) -> List[str]:
        return list(self._tables.values())

    def get_filter_names(self) -> List[str]:
        return [".".join(keys) for keys, _ in self._where_clauses]
