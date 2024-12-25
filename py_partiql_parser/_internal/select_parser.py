from typing import Dict, Any, List, Optional

from .clause_tokenizer import ClauseTokenizer
from .utils import (
    find_nested_data_in_object,
    MissingVariable,
    is_dict,
    CaseInsensitiveDict,
)


class SelectClause:
    def __init__(self, value: str, table_prefix: Optional[str] = None):
        self.table_prefix = table_prefix
        self.value = value.strip()

        if self.value == self.table_prefix:
            self.value = "*"

    def select(self, document: CaseInsensitiveDict) -> Any:
        if self.value == "*":
            return document
        if self.value.startswith(f"{self.table_prefix}."):
            # removeprefix() is only available in py 3.9
            self.value = self.value.replace(f"{self.table_prefix}.", "")
        if "." in self.value:
            key, remaining = self.value.split(".", maxsplit=1)
            return find_nested_data_in_object(
                select_clause=remaining, json_doc=document[key]
            )
        elif not self.table_prefix:
            return find_nested_data_in_object(
                select_clause=self.value, json_doc=document
            )
        else:
            if is_dict(document[self.value]):
                return document[self.value]
            else:
                return document.get_original(self.value)

    def __repr__(self) -> str:
        return f"<SelectClause({self.value})>"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, SelectClause) and other.value == self.value


class FunctionClause(SelectClause):
    def __init__(self, value: str, function_name: str):
        super().__init__(value)
        self.function_name = function_name.strip()

    def execute(
        self, aliases: Dict[str, str], document: CaseInsensitiveDict, results: List[Any]
    ) -> None:
        if results:
            results[0]["_1"] += 1
        else:
            results.append({"_1": 1})

    def __repr__(self) -> str:
        return f"<FunctionClause({self.function_name}({self.value}))>"

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, FunctionClause)
            and other.value == self.value
            and other.function_name == self.function_name
        )


class SelectParser:
    @classmethod
    def parse_clauses(
        cls, select_clause: str, prefix: Optional[str] = None
    ) -> List[SelectClause]:
        results = []
        tokenizer = ClauseTokenizer(select_clause)
        current_clause = fn_name = ""
        while True:
            c = tokenizer.next()
            if not c or c in [","]:
                if current_clause != "":
                    results.append(
                        SelectClause(value=current_clause, table_prefix=prefix)
                    )
                if not c:
                    break
                else:
                    current_clause = ""
                    continue
            if c in ["("]:
                fn_name = current_clause
                current_clause = ""
                continue
            if c in [")"]:
                results.append(
                    FunctionClause(function_name=fn_name, value=current_clause)
                )
                current_clause = ""
                continue
            current_clause += c
        return results


class S3SelectClauseParser(SelectParser):
    def __init__(self, table_prefix: Optional[str]):
        self.table_prefix = table_prefix

    def parse(
        self,
        select_clause: str,
        aliases: Dict[str, Any],
        document: CaseInsensitiveDict,
        results: List[Any],
    ) -> None:
        """
        Select appropriate data and add it to the results
        This data can be one of the following:
          - the whole document
          - part of the document
          - the result of a function like COUNT()
        """
        clauses = SelectParser.parse_clauses(select_clause, prefix=self.table_prefix)

        has_fn_clause = False

        for clause in clauses:
            if isinstance(clause, FunctionClause):
                has_fn_clause = True
                clause.execute(aliases, document, results)

        if has_fn_clause:
            return

        filtered_document = dict()
        for clause in clauses:
            attr = clause.select(document)
            if attr is not None and not isinstance(attr, MissingVariable):
                # Specific usecase:
                # select * from s3object[*].Name my_n
                if (
                    "." in list(aliases.values())[0]
                    and list(aliases.keys()) != list(aliases.values())
                    and list(aliases.keys())[0] in attr
                    and select_clause == "*"
                ):
                    filtered_document.update({"_1": attr[list(aliases.keys())[0]]})
                else:
                    filtered_document.update(attr)
        results.append(filtered_document)


class DynamoDBSelectParser(SelectParser):
    def parse(
        self,
        select_clause: str,
        aliases: Dict[str, Any],
        documents: List[CaseInsensitiveDict],
    ) -> List[Dict[str, Any]]:
        clauses = SelectParser.parse_clauses(select_clause)

        result: List[Dict[str, Any]] = []

        for json_document in documents:
            filtered_document = dict()
            for clause in clauses:
                attr = clause.select(json_document)
                if attr is not None and not isinstance(attr, MissingVariable):
                    # Specific usecase:
                    # select * from s3object[*].Name my_n
                    if (
                        "." in list(aliases.values())[0]
                        and list(aliases.keys())[0] in attr
                        and select_clause == "*"
                    ):
                        filtered_document.update({"_1": attr[list(aliases.keys())[0]]})
                    else:
                        filtered_document.update(attr)
            result.append(filtered_document)
        return result
