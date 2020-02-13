from microml import ast, exceptions, lexer


OPERATORS = {
    lexer.NEQ,
    lexer.EQEQ,
    lexer.GEQ,
    lexer.LEQ,
    lexer.LT,
    lexer.GT,
    lexer.PLUS,
    lexer.MINUS,
    lexer.TIMES,
    lexer.DIV,
}


class Parser:
    def __init__(self):
        self.lexer = lexer.Lexer()
        self.token = None
        self.operators = {"!=", "==", ">=", "<=", "<", ">", "+", "-", "*"}

    def parse(self, source, should_terminate=True):
        self.lexer.start(source)
        self.next()

        decl = self.decl()
        if self.token.typ is not None and should_terminate:
            self.error(
                'Unexpected token "{}" at {}'.format(self.token.val, self.token.pos)
            )
        return decl, self.token.pos

    def error(self, msg):
        raise exceptions.MLParserException(msg, self.token.pos)

    def next(self):
        self.token = self.lexer.token()

        if self.token is None:
            self.token = lexer.Token(None, None, None)

    def match(self, typ):
        tok_type = self.token.typ
        if tok_type == typ:
            val = self.token.val
            self.next()
            return val
        else:
            self.error(
                "Expected {}, but found {} at {}".format(typ, tok_type, self.token.pos)
            )

    def decl(self):
        name = self.match(lexer.ID)
        argnames = []

        while self.token.typ == lexer.ID:
            argnames.append(self.token.val)
            self.next()

        self.match(lexer.EQ)
        expr = self.expr()

        if len(argnames):
            return ast.Decl(name, ast.Lambda(argnames, expr))
        return ast.Decl(name, expr)

    def expr(self):
        node = self.expr_component()
        if self.token.typ in OPERATORS:
            op = self.token.typ
            self.next()
            rhs = self.expr_component()
            return ast.Op(op, node, rhs)
        return node

    def expr_component(self):
        token = self.token

        if token.typ == lexer.INT:
            self.next()
            return ast.Int(token.val)
        if token.typ in [lexer.FALSE, lexer.TRUE]:
            self.next()
            return ast.Bool(token.typ == lexer.TRUE)
        if token.typ == lexer.ID:
            self.next()
            if self.token.typ == lexer.LPAREN:
                return self.app(token.val)
            return ast.Id(token.val)
        if token.typ == lexer.LPAREN:
            self.next()
            expr = self.expr()
            self.match(lexer.RPAREN)
            return expr
        if token.typ == lexer.IF:
            return self.ifexpr()
        if token.typ == lexer.LAMBDA:
            return self.lambdaexpr()
        self.error("We don’t support {} yet!".format(token.typ))

    def ifexpr(self):
        self.match(lexer.IF)
        ifexpr = self.expr()
        self.match(lexer.THEN)
        thenexpr = self.expr()
        self.match(lexer.ELSE)
        elseexpr = self.expr()
        return ast.If(ifexpr, thenexpr, elseexpr)

    def lambdaexpr(self):
        self.match(lexer.LAMBDA)
        argnames = []

        while self.token.typ == lexer.ID:
            argnames.append(self.token.val)
            self.next()

        self.match(lexer.ARROW)
        expr = self.expr()
        return ast.Lambda(argnames, expr)

    def app(self, name):
        self.match(lexer.LPAREN)
        args = []
        while self.token.typ != lexer.RPAREN:
            args.append(self.expr())
            if self.token.typ == lexer.COMMA:
                self.next()
            elif self.token.typ == lexer.RPAREN:
                break
            else:
                self.error(
                    "Unexpected {} in application at {}".format(
                        self.token.val, self.token.pos
                    )
                )
        self.match(lexer.RPAREN)
        return ast.App(ast.Id(name), args)
