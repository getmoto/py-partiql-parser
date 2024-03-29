from py_partiql_parser._internal.clause_tokenizer import ClauseTokenizer


def test_immediate_overrun() -> None:
    assert ClauseTokenizer("").next() is None


def test_overrun() -> None:
    tokenizer = ClauseTokenizer("ab")
    assert tokenizer.next() == "a"
    assert tokenizer.next() == "b"
    assert tokenizer.next() is None


def test_current() -> None:
    tokenizer = ClauseTokenizer("ab")
    assert tokenizer.current() == "a"
    assert tokenizer.current() == "a"
    assert tokenizer.next() == "a"
    assert tokenizer.current() == "b"
    assert tokenizer.next() == "b"
    assert tokenizer.current() is None


def test_peek() -> None:
    tokenizer = ClauseTokenizer("abc")
    assert tokenizer.peek() == "b"
    tokenizer.next()
    assert tokenizer.peek() == "c"
    assert tokenizer.next() == "b"
    assert tokenizer.peek() is None


def test_next_until() -> None:
    tokenizer = ClauseTokenizer("sth (relevant data) else")
    while tokenizer.next() != "(":
        pass
    assert tokenizer.next_until([")"]) == "relevant data"
