import operator

from microml import exceptions


class Node:
    typ = None
    children = []

    def visit_children(self, f):
        for child in self.children:
            f(child)


class Val(Node):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def compile(self, unifier):
        return str(int(self.value))


class Int(Val):
    def eval(self, env):
        return int(self.value)


class Bool(Val):
    def eval(self, env):
        return bool(self.value)


class Id(Node):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def compile(self, unifier):
        return self.name

    def eval(self, env):
        return env[self.name]


OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
}


class Op(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
        self.children = [self.left, self.right]

    def __str__(self):
        return "({} {} {})".format(self.left, self.op, self.right)

    def compile(self, unifier):
        return "{} {} {}".format(
            self.left.compile(unifier), self.op, self.right.compile(unifier)
        )

    def find_op(self):
        return OPERATORS[self.op]

    def eval(self, env):
        return self.find_op()(self.left.eval(env), self.right.eval(env))


class App(Node):
    def __init__(self, f, args=()):
        self.f = f
        self.args = args
        self.children = [self.f, *self.args]

    def __str__(self):
        return "{}({})".format(self.f, ", ".join(str(a) for a in self.args))

    def compile(self, unifier):
        return "{}({})".format(self.f, ", ".join(a.compile(unifier) for a in self.args))

    def eval(self, env):
        f = self.f.eval(env)
        return f.eval(env, [arg.eval(env) for arg in self.args])


class If(Node):
    def __init__(self, ifx, thenx, elsex):
        self.ifx = ifx
        self.thenx = thenx
        self.elsex = elsex
        self.children = [self.ifx, self.thenx, self.elsex]

    def __str__(self):
        return "(if {} then {} else {})".format(self.ifx, self.thenx, self.elsex)

    def compile(self, unifier):
        return "{} ? {} : {}".format(
            self.ifx.compile(unifier),
            self.thenx.compile(unifier),
            self.elsex.compile(unifier),
        )

    def eval(self, env):
        if self.ifx.eval(env):
            return self.thenx.eval(env)
        return self.elsex.eval(env)


class Lambda(Node):
    def __init__(self, argnames, expr):
        self.argnames = argnames
        self.expr = expr
        self.children = [self.expr]

    def __str__(self):
        return "(lambda {} -> {})".format(", ".join(self.argnames), self.expr)

    argtypes = None

    def compile(self, unifier):
        typ = unifier(self.expr.typ).to_c()
        compiled = self.expr.compile(unifier)
        body = "return {};".format(compiled)
        return "({}) {{\n{}\n}}".format(
            ", ".join(
                "{} {}".format(unifier(self.argtypes[name]).to_c(), name)
                for name in self.argnames
            ),
            "\n".join("  {}".format(l) for l in body.split("\n")),
        )

    def eval(self, env, args):
        new_env = dict(env)
        if len(args) != len(self.argnames):
            raise exceptions.MLEvalException(
                "lambda was called with {} arguments, but expected {}".format(
                    len(args), len(self.argnames)
                )
            )
        for i in range(len(args)):
            new_env[self.argnames[i]] = args[i]
        return self.expr.eval(new_env)


class Decl(Node):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr
        self.children = [self.expr]

    def __str__(self):
        return "{} = {}".format(self.name, self.expr)

    def compile(self, unifier):
        typ = unifier(self.expr.typ).to_c()
        if isinstance(self.expr, Lambda):
            return "{} {}{}".format(typ, self.name, self.expr.compile(unifier))
        return "{} {} = {};".format(typ, self.name, self.expr.compile(unifier))

    def eval(self, env):
        env[self.name] = self.expr
