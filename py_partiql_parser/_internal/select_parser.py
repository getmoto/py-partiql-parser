from typing import Dict, Any, List, Optional

from .case_insensitive_dict import CaseInsensitiveDict
from .clause_tokenizer import ClauseTokenizer
from .utils import find_nested_data_in_object, MissingVariable


class SelectClause:
    def __init__(self, value: str, table_prefix: Optional[str] = None):
        self.table_prefix = table_prefix
        self.value = value.strip()

    def select(self, aliases: Dict[str, str], document: Dict[str, Any]):
        if self.value == "*":
            if self.table_prefix:
                return document[self.table_prefix]
            else:
                return document
        if "." in self.value:
            key, remaining = self.value.split(".", maxsplit=1)
            return find_nested_data_in_object(
                select_clause=remaining, json_doc=document[aliases.get(key, key)]
            )
        elif not self.table_prefix:
            return find_nested_data_in_object(
                select_clause=self.value, json_doc=document
            )
        else:
            return document[aliases.get(self.value, self.value)]

    def __repr__(self):
        return f"<SelectClause({self.value})>"

    def __eq__(self, other):
        return isinstance(other, SelectClause) and other.value == self.value


class FunctionClause(SelectClause):
    def __init__(self, value: str, function_name: str):
        super().__init__(value)
        self.function_name = function_name.strip()

    def execute(self, aliases: Dict[str, str], documents: List[Dict[str, Any]]):
        return {"_1": len(documents)}

    def __repr__(self):
        return f"<FunctionClause({self.function_name}({self.value}))>"

    def __eq__(self, other):
        return (
            isinstance(other, FunctionClause)
            and other.value == self.value
            and other.function_name == self.function_name
        )


class SelectParser:
    def __init__(self, table_prefix: Optional[str]):
        self.table_prefix = table_prefix

    def parse(
        self,
        select_clause: str,
        aliases: Dict[str, Any],
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        clauses = self.parse_clauses(select_clause)

        for clause in clauses:
            if isinstance(clause, FunctionClause):
                return [clause.execute(aliases, documents)]

        result: List[Dict[str, Any]] = []

        for json_document in documents:
            if self.table_prefix is not None:
                json_document = {self.table_prefix: json_document}
            filtered_document = dict()
            for clause in clauses:
                attr = clause.select(aliases, json_document)
                if attr is not None and not isinstance(attr, MissingVariable):
                    filtered_document.update(attr)
            result.append(filtered_document)
        return result

    def parse_clauses(self, select_clause: str) -> List[SelectClause]:
        results = []
        tokenizer = ClauseTokenizer(select_clause)
        current_clause = fn_name = ""
        while True:
            c = tokenizer.next()
            if not c or c in [","]:
                if current_clause != "":
                    results.append(
                        SelectClause(
                            value=current_clause, table_prefix=self.table_prefix
                        )
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