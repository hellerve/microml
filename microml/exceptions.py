class MLException(Exception):
    module = None

    def __init__(self, msg, location=None):
        super().__init__(msg)
        self.location = location


class MLLexerException(MLException):
    module = "lexer"


class MLParserException(MLException):
    module = "parser"


class MLTypingException(MLException):
    module = "types"


class MLEvalException(MLException):
    module = "interpretation"


class MLCompilerException(MLException):
    module = "compiler"
