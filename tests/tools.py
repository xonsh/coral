"""Some test tool helpers"""
import ast
from itertools import zip_longest


def nodes_equal(x, y, check_attributes=True):
    __tracebackhide__ = True
    assert type(x) == type(y), "Ast nodes do not have the same type: '%s' != '%s'" % (
        type(x),
        type(y),
    )
    if x is None and y is None:
        return True
    if check_attributes and isinstance(x, (ast.Expr, ast.FunctionDef, ast.ClassDef)):
        assert (
            x.lineno == y.lineno
        ), "Ast nodes do not have the same line number : %s != %s" % (
            x.lineno,
            y.lineno,
        )
        assert x.col_offset == y.col_offset, (
            "Ast nodes do not have the same column offset number : %s != %s"
            % (x.col_offset, y.col_offset)
        )
    for (xname, xval), (yname, yval) in zip(ast.iter_fields(x), ast.iter_fields(y)):
        assert xname == yname, (
            "Ast nodes fields differ : %s (of type %s) != %s (of type %s)"
            % (xname, type(xval), yname, type(yval))
        )
        assert type(xval) == type(yval), (
            "Ast nodes fields differ : %s (of type %s) != %s (of type %s)"
            % (xname, type(xval), yname, type(yval))
        )
    for xchild, ychild in zip_longest(ast.iter_child_nodes(x), ast.iter_child_nodes(y)):
        assert xchild is not None, "AST node has fewer childern"
        assert ychild is not None, "AST node has more childern"
        assert nodes_equal(xchild, ychild, check_attributes=check_attributes), "Ast node children differs"
    return True
