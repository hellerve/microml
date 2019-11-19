import re
import sys

from microml import exceptions


class Token:
    def __init__(self, typ, val, pos):
        self.type = typ
        self.val = val
        self.pos = pos

    def __str__(self):
        return '{}({}) at {}'.format(self.type, self.val, self.pos)


IF = 'IF'
THEN = 'THEN'
ELSE = 'ELSE'
TRUE = 'TRUE'
FALSE = 'FALSE'
LAMBDA = 'LAMBDA'
INT = 'INT'
ARROW = 'ARROW'
NEQ = '!='
EQEQ = '=='
GEQ = '>='
LEQ = '<='
LT = '<'
GT = '>'
PLUS = '+'
MINUS = '-'
TIMES = '*'
DIV = '/'
LPAREN = '('
RPAREN = ')'
EQ = '='
COMMA = ','
ID = 'ID'


RULES = [
    ('if',              IF),
    ('then',            THEN),
    ('else',            ELSE),
    ('true',            TRUE),
    ('false',           FALSE),
    ('lambda',          LAMBDA),
    ('\d+',             INT),
    ('->',              ARROW),
    ('!=',              NEQ),
    ('==',              EQEQ),
    ('>=',              GEQ),
    ('<=',              LEQ),
    ('<',               LT),
    ('>',               GT),
    ('\+',              PLUS),
    ('\-',              MINUS),
    ('\*',              TIMES),
    ('/',               DIV),
    ('\(',              LPAREN),
    ('\)',              RPAREN),
    ('=',               EQ),
    (',',               COMMA),
    ('[a-zA-Z_]\w*',    ID),
]

class Lexer:
    def __init__(self):
        idx = 1
        regex_parts = []
        self.group_type = {}

        for regex, typ in RULES:
            groupname = 'GROUP%s' % idx
            regex_parts.append('(?P<%s>%s)' % (groupname, regex))
            self.group_type[groupname] = typ
            idx += 1

        self.regex = re.compile('|'.join(regex_parts))
        self.re_ws_skip = re.compile('\S')

    def start(self, buf):
        self.buf = re.sub(r'\(\*[^(\*\))]+\*\)', lambda m: ' '*(m.end()-m.start()), buf, flags=re.MULTILINE|re.DOTALL)
        self.pos = 0

    def token(self):
        if self.pos >= len(self.buf):
            return None
        m = self.re_ws_skip.search(self.buf, self.pos)

        if m:
            self.pos = m.start()
        else:
            return None

        m = self.regex.match(self.buf, self.pos)
        if m:
            groupname = m.lastgroup
            tok_type = self.group_type[groupname]
            tok = Token(tok_type, m.group(groupname), self.pos)
            self.pos = m.end()
            return tok

        raise exceptions.MLLexerException('Couldn’t match token at {}'.format(self.pos), self.pos)

    def peek(self):
        pos = self.pos
        token = self.token()
        self.pos = pos
        return token

    def tokens(self):
        while 1:
            tok = self.token()
            if tok is None: break
            yield tok
