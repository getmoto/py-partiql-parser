from .json_parser import Variable
from typing import Any, Dict, Optional, Union


def find_nested_data(
    data_source: Dict[str, Any], select_clause: Union[None, str, Variable]
) -> Any:
    """
    Find a key in a dictionary
    :param data_source: Dictionary such as {"a: {"b": "asdf"}}
    :param select_clause: Key of the data source, in dot-notation: a.b
    :return: "asdf"
    """
    if not select_clause:
        return data_source
    if isinstance(select_clause, str):
        select_clause = Variable(select_clause)
    if isinstance(select_clause, Variable):
        if not select_clause.value:
            return data_source
        current_key = select_clause.value.split(".")[0]
        remaining_keys = ".".join(select_clause.value.split(".")[1:])
        if isinstance(data_source, list):
            return [
                find_nested_data(row[current_key], Variable(remaining_keys))
                for row in data_source
            ]
        elif isinstance(data_source, dict):
            return find_nested_data(data_source[current_key], Variable(remaining_keys))
    if isinstance(select_clause, dict):
        return [
            {k: v.apply(row) for k, v in select_clause.items()} for row in data_source
        ]
    if isinstance(select_clause, list):
        return [
            [find_nested_data(data_row, x) for x in select_clause]
            for data_row in data_source
        ]
    return []
