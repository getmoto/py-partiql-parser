from .json_parser import MissingVariable, Variable
from typing import Any, Dict, List, Union


def find_nested_data(
    select_clause: str, data_source: List[Dict[str, Any]]
) -> List[str]:
    """
    Iterate over a list of JSON objects, and return only the keys specified
    :param select_clause: Key of the data source, in dot-notation: a.b
    :param data_source: List of JSON documents as dictionary
    :return: A list of JSON keys as dictionary
    """

    results: List[str] = []

    for row in data_source:
        # Run the select-clause over each row
        result = _find_nested_data(select_clause=select_clause, json_doc=row)
        results.append(result)
    return results


def _find_nested_data(select_clause: Union[None, str, Variable], json_doc: Any):
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
                        _find_nested_data(row[current_key], Variable(remaining_keys))
                    )
            return result
        elif isinstance(json_doc, dict):
            if current_key not in json_doc:
                return MissingVariable()
            if remaining_keys:
                return _find_nested_data(
                    json_doc[current_key], Variable(remaining_keys)
                )
            return {current_key: json_doc[current_key]}
    if isinstance(select_clause, dict):
        result = [
            {k: v.apply(row) for k, v in select_clause.items()} for row in json_doc
        ]
        return [
            {k: v for k, v in row.items() if not isinstance(v, MissingVariable)}
            for row in result
        ]
    if isinstance(select_clause, list):
        return [
            [_find_nested_data(data_row, x) for x in select_clause]
            for data_row in json_doc
        ]
    return []
