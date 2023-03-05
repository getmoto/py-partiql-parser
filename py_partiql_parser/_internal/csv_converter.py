import json


def csv_to_json(input: str) -> str:
    output = ""
    for line in input.split("\n"):
        output += json.dumps({f"_{idx+1}": key for idx, key in enumerate(line.split(","))}) + "\n"
    if output.endswith("\n"):
        output = output.rstrip("\n")
    return output
