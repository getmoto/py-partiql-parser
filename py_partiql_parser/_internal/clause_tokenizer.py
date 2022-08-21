from typing import Optional, AnyStr


class ClauseTokenizer:
    def __init__(self, from_clause) -> None:
        self.token_list = from_clause
        self.token_pos = 0

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

    def skip_white_space(self) -> None:
        try:
            while self.token_list[self.token_pos] == " ":
                self.token_pos += 1
        except IndexError:
            pass

    def next_until(self, c) -> str:
        """
        Return the following characters up until (but not including) the next occurrence of c
        :param c:
        :return:
        """
        phrase = ""
        crnt = self.next()
        while crnt and crnt != c:
            phrase += crnt
            crnt = self.next()
        return phrase
