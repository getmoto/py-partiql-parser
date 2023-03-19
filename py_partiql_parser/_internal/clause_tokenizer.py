from typing import Optional, AnyStr, List


class ClauseTokenizer:
    def __init__(self, from_clause) -> None:
        self.token_list = from_clause
        self.token_pos = 0

    def current(self):
        """
        Returns the current char - or None
        """
        try:
            return self.token_list[self.token_pos]
        except IndexError:
            return None

    def next(self) -> Optional[AnyStr]:
        """
        Returns the next token - or None
        :return:
        """
        try:
            crnt_token = self.token_list[self.token_pos]
            self.token_pos += 1
            return crnt_token
        except IndexError:
            return None

    def peek(self):
        try:
            return self.token_list[self.token_pos + 1]
        except IndexError:
            return None

    def revert(self):
        self.token_pos -= 1

    def skip_white_space(self) -> None:
        try:
            while self.token_list[self.token_pos] in [" ", "\n"]:
                self.token_pos += 1
        except IndexError:
            pass

    def next_until(self, chars: List[str]) -> str:
        """
        Return the following characters up until (but not including) any of the characters defined in chars
        :param chars:
        :return:
        """
        phrase = ""
        crnt = self.next()
        while crnt and crnt not in chars:
            phrase += crnt
            crnt = self.next()
        return phrase

    def skip_until(self, chars: List[str]) -> None:
        """
        Skip until we encounter one of the provided chars. Inclusive, so we also skip the first char encountered
        :param chars:
        """
        crnt = self.next()
        while crnt and crnt not in chars:
            crnt = self.next()
