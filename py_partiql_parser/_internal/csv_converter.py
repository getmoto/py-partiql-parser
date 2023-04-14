import json
from typing import List


def csv_to_json(input: str, headers_included=False) -> str:
    output = ""
    headers: List[str] = []
    for line in input.split("\n"):
        values = line.split(",")
        if len(headers) == 0:
            if headers_included:
                headers = values
                continue
            else:
                headers = [f"_{x}" for x in range(1, len(values) + 1)]
        line = json.dumps({f"{headers[idx]}": key for idx, key in enumerate(values)})
        output += f"{line}\n"
    if output.endswith("\n"):
        output = output.rstrip("\n")
    return output
