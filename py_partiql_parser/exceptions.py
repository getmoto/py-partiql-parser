class ParserException(Exception):
    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message
        super().__init__(message)
