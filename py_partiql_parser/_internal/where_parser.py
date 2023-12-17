from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional

from .clause_tokenizer import ClauseTokenizer
from .utils import find_value_in_document
from .utils import find_value_in_dynamodb_document, CaseInsensitiveDict
from .utils import serializer


class AbstractWhereClause:
    def __init__(self) -> None:
        self.children: List[AbstractWhereClause] = []

    def apply(self, find_value: Any, row: Any) -> bool:
        return NotImplemented

    def get_filter_names(self) -> List[str]:
        all_names: List[str] = []
        for child in self.children:
            all_names.extend(child.get_filter_names())
        return all_names

    def process_value(self, fn: Callable[[str], Dict[str, Any]]) -> None:
        """
        Transform all the values in this Where-clause, using a custom function
        """
        for child in self.children:
            child.process_value(fn)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, AbstractWhereClause):
            return self.children == other.children
        return NotImplemented

    def __str__(self) -> str:
        return f"<{type(self)} {self.children}>"

    def __repr__(self) -> str:
        return str(self)


class WhereAndClause(AbstractWhereClause):
    def __init__(self, left: Optional["AbstractWhereClause"]):
        super().__init__()
        self.children.append(left)  # type: ignore[arg-type]

    def apply(self, find_value: Callable[[str], Dict[str, Any]], row: Any) -> bool:
        return all([child.apply(find_value, row) for child in self.children])


class WhereOrClause(AbstractWhereClause):
    def __init__(self, left: Optional["AbstractWhereClause"]):
        super().__init__()
        self.children.append(left)  # type: ignore[arg-type]

    def apply(self, find_value: Any, row: Any) -> bool:
        return any([child.apply(find_value, row) for child in self.children])


class WhereClause(AbstractWhereClause):
    def __init__(self, fn: str, left: List[str], right: Any):
        super().__init__()
        self.fn = fn.lower()
        self.left = left
        self.right = right

    def apply(self, find_value: Any, row: Any) -> bool:
        value = find_value(self.left, row)
        if self.fn == "contains":
            if "S" in self.right and "S" in value:
                return self.right["S"] in value["S"]
        if self.fn == "is":
            if self.right == {"S": "MISSING"}:
                return value is None
            elif self.right == {"S": "NOT MISSING"}:
                return value is not None
        if self.fn in ["<=", "<", ">=", ">"]:
            actual_value = Decimal(list(value.values())[0])
            expected = Decimal(self.right["S"])
            if self.fn == "<=":
                return actual_value <= expected
            if self.fn == "<":
                return actual_value < expected
            if self.fn == ">=":
                return actual_value >= expected
            if self.fn == ">":
                return actual_value > expected
        if self.fn == "attribute_type" and value is not None:
            actual_value = list(value.keys())[0]
            return actual_value == self.right["S"]
        # Default - should we error instead if fn != '=='?
        return value == self.right

    def process_value(self, fn: Callable[[str], Dict[str, Any]]) -> None:
        self.right = fn(self.right)

    def get_filter_names(self) -> List[str]:
        return [".".join(self.left)]

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, WhereClause):
            return (
                self.fn == other.fn
                and self.left == other.left
                and self.right == other.right
            )
        return NotImplemented

    def __str__(self) -> str:
        return f"<{type(self)} {self.fn}({self.left}, {self.right})>"

    def __repr__(self) -> str:
        return str(self)


class WhereParser:
    def __init__(self, source_data: List[CaseInsensitiveDict]):
        self.source_data = source_data

    @classmethod
    def parse_where_clause(
        cls, where_clause: str, tokenizer: Optional[ClauseTokenizer] = None
    ) -> AbstractWhereClause:
        where_clause_parser = tokenizer or ClauseTokenizer(where_clause)
        current_clause: Optional[AbstractWhereClause] = None
        processing_function = False
        left = []
        fn: str = ""
        section: Optional[str] = "KEY"
        current_phrase = ""
        while True:
            c = where_clause_parser.next()
            if c is None:
                if section == "KEY" and current_phrase != "":
                    left.append(current_phrase)
                if section == "START_VALUE" and current_phrase != "":
                    current_clause = cls._determine_current_clause(
                        current_clause, left=left.copy(), fn=fn, right=current_phrase
                    )
                break
            if section == "KEY" and c == "(":
                if current_phrase == "":
                    # Process a subsection of the WHERE-clause
                    # .. and (sub-clause) and ...
                    next_clause = WhereParser.parse_where_clause(
                        where_clause="", tokenizer=where_clause_parser
                    )
                    if current_clause is None:
                        current_clause = next_clause
                    else:
                        current_clause.children.append(next_clause)
                    section = "END_VALUE"
                    where_clause_parser.skip_white_space()
                    continue
                else:
                    # Function
                    fn = current_phrase
                    current_phrase = ""
                    processing_function = True
                    continue
            if c == ")":
                if processing_function:
                    #               |
                    #               v
                    #  fn("key", val)
                    processing_function = False
                    continue
                else:
                    # Finished processing a subsection of the WHERE-clause
                    # .. and (sub-clause) and ...
                    return current_clause  # type: ignore[return-value]
            if c == ".":
                if section in ["KEY", "END_KEY"]:
                    if current_phrase != "":
                        left.append(current_phrase)
                    current_phrase = ""
                    section = "KEY"
                    continue
            if c in [","]:
                if section in ["END_KEY"]:
                    #          |
                    #          v
                    #  fn("key", val)
                    section = "START_VALUE"
                    where_clause_parser.skip_white_space()
                    continue
            if c in ['"', "'"]:
                if section == "KEY":
                    # collect everything between these quotes
                    left.append(where_clause_parser.next_until([c]))
                    # This could be the end of a key
                    #         |
                    #         v
                    #     "key" = val
                    #  fn("key", val)
                    #     "key".subkey = val
                    #
                    # Note that in the last example, the key isn't actually finished
                    # When we encounter a '.' next, will we return to processing a KEY
                    section = "END_KEY"
                    continue
                if section == "START_VALUE":
                    current_phrase = where_clause_parser.next_until([c])
                    section = "END_VALUE"
                    current_clause = cls._determine_current_clause(
                        current_clause, left=left.copy(), fn=fn, right=current_phrase
                    )
                    left.clear()
                    current_phrase = ""
                    where_clause_parser.skip_white_space()
                    continue
            if c in [" "] and section in ["KEY", "END_KEY"]:
                #         |
                #         v
                #   "key" = val
                #     key >= val
                if current_phrase != "":
                    left.append(current_phrase)
                current_phrase = ""
                fn = where_clause_parser.next_until([" "])
                if fn == "IS":
                    # Options:
                    #   IS MISSING
                    #   IS NOT MISSING
                    current_phrase = where_clause_parser.next_until([" "])
                    if current_phrase == "NOT":
                        current_phrase = (
                            f"{current_phrase} {where_clause_parser.next_until([' '])}"
                        )
                    current_clause = cls._determine_current_clause(
                        current_clause, left=left.copy(), fn=fn, right=current_phrase
                    )
                    left.clear()
                    current_phrase = ""
                    section = "END_VALUE"
                    continue
                where_clause_parser.skip_white_space()
                section = "START_VALUE"
                continue
            if c in [" "] and section == "START_VALUE":
                #            |
                #            v
                #   "key" = 0 AND ..
                current_clause = cls._determine_current_clause(
                    current_clause, left=left.copy(), fn=fn, right=current_phrase
                )
                left.clear()
                current_phrase = ""
                section = "END_VALUE"
                continue
            if c in [" "] and section == "END_VALUE":
                if current_phrase.upper() == "AND":
                    current_clause = WhereAndClause(current_clause)
                    current_phrase = ""
                    section = "KEY"
                    where_clause_parser.skip_white_space()
                elif current_phrase.upper() == "OR":
                    current_clause = WhereOrClause(current_clause)
                    current_phrase = ""
                    section = "KEY"
                    where_clause_parser.skip_white_space()
                continue
            if c in ["?"] and section == "START_VALUE":
                # Most values have to be surrounded by quotes
                # Question marks are parameters, and are valid values on their own
                current_clause = cls._determine_current_clause(
                    current_clause, left=left.copy(), fn=fn, right="?"
                )
                left.clear()
                section = "END_VALUE"  # Next step is to look for other key/value pairs
                continue
            if current_phrase == "" and section == "START_KEY":
                section = "KEY"
            if section in ["KEY", "VALUE", "START_VALUE", "END_VALUE"]:
                current_phrase += c
        return current_clause  # type: ignore[return-value]

    @classmethod
    def _determine_current_clause(
        cls,
        current_clause: Optional[AbstractWhereClause],
        left: List[str],
        fn: str,
        right: str,
    ) -> AbstractWhereClause:
        if current_clause is not None and isinstance(
            current_clause, (WhereAndClause, WhereOrClause)
        ):
            current_clause.children.append(
                WhereClause(fn=fn, left=left.copy(), right=right)
            )
            return current_clause
        else:
            return WhereClause(fn=fn, left=left.copy(), right=right)


class DynamoDBWhereParser(WhereParser):
    def parse(
        self, _where_clause: str, parameters: Optional[List[Dict[str, Any]]]
    ) -> List[CaseInsensitiveDict]:
        where_clause = WhereParser.parse_where_clause(_where_clause)

        def prep_value(val: str) -> Dict[str, Any]:
            # WHERE key = ?
            #     ? should be parametrized
            if val == "?" and parameters:
                return parameters.pop(0)
            # WHERE key = val
            #     'val' needs to be comparable with a DynamoDB document
            #     So we need to turn that into {'S': 'val'}
            else:
                return serializer.serialize(val)

        where_clause.process_value(prep_value)

        return [
            row
            for row in self.source_data
            if where_clause.apply(find_value_in_dynamodb_document, row)
        ]


class S3WhereParser(WhereParser):
    def parse(self, _where_clause: str) -> Any:
        # parameters argument is ignored - only relevant for DynamoDB
        where_clause = WhereParser.parse_where_clause(_where_clause)

        return [
            row
            for row in self.source_data
            if where_clause.apply(find_value_in_document, row)
        ]
