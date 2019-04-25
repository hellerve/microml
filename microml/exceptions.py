class MLException(Exception):
    module = None


class MLLexerException(MLException):
    module = 'lexer'


class MLParserException(MLException):
    module = 'parser'


class MLTypingException(MLException):
    module = 'types'


class MLEvalException(MLException):
    module = 'interpretation'


class MLCompilerException(MLException):
    module = 'compiler'
