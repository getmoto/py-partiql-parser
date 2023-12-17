from typing import Optional, List


class ClauseTokenizer:
    def __init__(self, from_clause: str):
        self.token_list = from_clause
        self.token_pos = 0

    def current(self) -> Optional[str]:
        """
        Returns the current char - or None
        """
        try:
            return self.token_list[self.token_pos]
        except IndexError:
            return None

    def next(self) -> Optional[str]:
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

    def peek(self) -> Optional[str]:
        try:
            return self.token_list[self.token_pos + 1]
        except IndexError:
            return None

    def revert(self) -> None:
        self.token_pos -= 1

    def skip_white_space(self) -> None:
        try:
            while self.token_list[self.token_pos] in [" ", "\n"]:
                self.token_pos += 1
        except IndexError:
            pass

    def give_remaining(self) -> str:
        return self.next_until(chars=[None])

    def next_until(self, chars: List[Optional[str]]) -> str:
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
