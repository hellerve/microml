import itertools

from microml import ast, exceptions, lexer


class Type:
    def __str__(self):
        return self.name

    __repr__ = __str__

    def __eq__(self, other):
        return type(self) == type(other)

    def to_c(self):
        return self.c


class Int(Type):
    name = 'Int'
    c = 'int'


class Bool(Type):
    name = 'Bool'
    c = 'int'


class Func(Type):
    def __init__(self, argtypes, rettype):
        self.argtypes = argtypes
        self.rettype = rettype

    def __str__(self):
        if not len(self.argtypes):
            return '(-> {})'.format(self.rettype)
        if len(self.argtypes) == 1:
            return '({} -> {})'.format(self.argtypes[0], self.rettype)
        return '({} -> {})'.format(' -> '.join(map(str, self.argtypes)),
                                   self.rettype)

    __repr__ = __str__

    def __eq__(self, other):
        return (type(self) == type(other) and
                self.rettype == other.rettype and
                all(self.argtypes[i] == other.argtypes[i]
                    for i in range(len(self.argtypes))))

    def to_c(self):
        return self.rettype.to_c()


class TypeVar(Type):
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name

    def to_c(self):
        return self.name


def _type_counter():
    i = 0
    while True:
        yield i
        i += 1


type_counter = _type_counter()


def get_fresh_typename():
    return 't{}'.format(next(type_counter))


def reset_type_counter():
    global type_counter
    type_counter = _type_counter()


def exceptor(msg):
    raise exceptions.MLTypingException(msg)


def make_type_var():
    return TypeVar(get_fresh_typename())


def assign_typenames(node, symtab=None):
    if symtab is None:
        symtab = {}

    if isinstance(node, ast.Id):
        if node.name in symtab:
            node.typ = symtab[node.name]
        else:
            exceptor('unbound name "{}"'.format(node.name))
    elif isinstance(node, ast.Lambda):
        node.typ = make_type_var()
        local_symtab = {}
        for argname in node.argnames:
            local_symtab[argname] = make_type_var()
        node.argtypes = local_symtab
        assign_typenames(node.expr, {**symtab, **local_symtab})
    elif isinstance(node, ast.Op):
        node.typ = make_type_var()
        node.visit_children(lambda c: assign_typenames(c, symtab))
    elif isinstance(node, ast.If):
        node.typ = make_type_var()
        node.visit_children(lambda c: assign_typenames(c, symtab))
    elif isinstance(node, ast.App):
        node.typ = make_type_var()
        node.visit_children(lambda c: assign_typenames(c, symtab))
    elif isinstance(node, ast.Int):
        node.typ = Int()
    elif isinstance(node, ast.Bool):
        node.typ = Bool()
    else:
        exceptor('unknown node {}', type(node))
    return symtab


def show_type_assignment(node):
    lines = []

    def show_rec(node):
        lines.append('{:60} {}'.format(str(node), node.typ))
        node.visit_children(show_rec)

    show_rec(node)
    return '\n'.join(lines)


class Equation:
    def __init__(self, left, right, original):
        self.left = left
        self.right = right
        self.original = original

    def __str__(self):
        return '{} :: {} [from {}]'.format(self.left, self.right, self.original)

    __repr__ = __str__


BOOL_OPS = {lexer.NEQ, lexer.EQEQ, lexer.GEQ, lexer.LEQ, lexer.GT, lexer.LT}


def generate_equations(node, type_equations=None):
    if type_equations is None:
        type_equations = []

    if isinstance(node, ast.Int):
        type_equations.append(Equation(node.typ, Int(), node))
    elif isinstance(node, ast.Bool):
        type_equations.append(Equation(node.typ, Bool(), node))
    elif isinstance(node, ast.Id):
        pass
    elif isinstance(node, ast.Op):
        node.visit_children(lambda c: generate_equations(c, type_equations))
        type_equations.append(Equation(node.left.typ, Int(), node))
        type_equations.append(Equation(node.right.typ, Int(), node))
        typ = Bool if node.op in BOOL_OPS else Int
        type_equations.append(Equation(node.typ, typ(), node))
    elif isinstance(node, ast.App):
        node.visit_children(lambda c: generate_equations(c, type_equations))
        argtypes = [arg.typ for arg in node.args]
        type_equations.append(
            Equation(node.f.typ, Func(argtypes, node.typ), node)
        )
    elif isinstance(node, ast.If):
        node.visit_children(lambda c: generate_equations(c, type_equations))
        type_equations.append(Equation(node.ifx.typ, Bool(), node))
        type_equations.append(Equation(node.typ, node.thenx.typ, node))
        type_equations.append(Equation(node.typ, node.elsex.typ, node))
    elif isinstance(node, ast.Lambda):
        node.visit_children(lambda c: generate_equations(c, type_equations))
        argtypes = [node.argtypes[name] for name in node.argnames]
        type_equations.append(
            Equation(node.typ, Func(argtypes, node.expr.typ), node)
        )
    else:
        exceptor('unknown node {}', type(node))

    return type_equations


def unify(typ_x, typ_y, subst):
    if subst is None:
        return None
    if typ_x == typ_y:
        return subst
    if isinstance(typ_x, TypeVar):
        return unify_variable(typ_x, typ_y, subst)
    if isinstance(typ_y, TypeVar):
        return unify_variable(typ_y, typ_x, subst)
    if isinstance(typ_x, Func) and isinstance(typ_y, Func):
        if len(typ_x.argtypes) != len(typ_y.argtypes):
            return None
        else:
            subst = unify(typ_x.rettype, typ_y.rettype, subst)
            for i in range(len(typ_x.argtypes)):
                subst = unify(typ_x.argtypes[i], typ_y.argtypes[i], subst)
            return subst


def occurs_check(v, typ, subst):
    assert isinstance(v, TypeVar)
    if v == typ:
        return True
    if isinstance(typ, TypeVar) and typ.name in subst:
        return occurs_check(v, subst[typ.name], subst)
    if isinstance(typ, Func):
        return (occurs_check(v, typ.rettype, subst) or
                any(occurs_check(v, arg, subst) for arg in typ.argtypes))
    return False


def unify_variable(v, typ, subst):
    assert isinstance(v, TypeVar)
    if v.name in subst:
        return unify(subst[v.name], typ, subst)
    if isinstance(typ, TypeVar) and typ.name in subst:
        return unify(v, subst[typ.name], subst)
    if occurs_check(v, typ, subst):
        return None
    return {**subst, v.name: typ}


def unify_equations(eqs):
    subst = {}
    for eq in eqs:
        subst = unify(eq.left, eq.right, subst)
        if subst is None:
            break
    return subst


def apply_unifier(typ, subst):
    if subst is None:
        return None
    if len(subst) == 0:
        return typ
    if isinstance(typ, (Bool, Int)):
        return typ
    if isinstance(typ, TypeVar):
        if typ.name in subst:
            return apply_unifier(subst[typ.name], subst)
        return typ
    if isinstance(typ, Func):
        newargtypes = [apply_unifier(arg, subst) for arg in typ.argtypes]
        return Func(newargtypes, apply_unifier(typ.rettype, subst))


def get_expression_type(typ, subst):
    typ = apply_unifier(typ, subst)
    namecounter = itertools.count(start=0)
    namemap = {}
    def rename_type(typ):
        if isinstance(typ, TypeVar):
            if typ.name in namemap:
                typ.name = namemap[typ.name]
            else:
                name = chr(ord('a') + next(namecounter))
                namemap[typ.name] = name
                namemap[name] = name
                typ.name = namemap[typ.name]
        elif isinstance(typ, Func):
            rename_type(typ.rettype)
            for argtyp in typ.argtypes:
                rename_type(argtyp)
    rename_type(typ)
    return typ
