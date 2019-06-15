"""Tests coral parser"""
import ast
from textwrap import dedent
from itertools import zip_longest

import pytest

from xonsh.ast import (
    pdump,
    pprint_ast,
    Module,
    Expr,
    Expression,
    NameConstant,
    FunctionDef,
    arguments,
    ClassDef,
    If,
    Assign,
    Name,
    Store,
    Num,
    Str,
)

from coral.parser import Comment, NodeWithComment, IfWithComments, parse, add_comments


def nodes_equal(x, y):
    __tracebackhide__ = True
    assert type(x) == type(y), "Ast nodes do not have the same type: '%s' != '%s'" % (
        type(x),
        type(y),
    )
    if isinstance(x, (ast.Expr, ast.FunctionDef, ast.ClassDef)):
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
        assert nodes_equal(xchild, ychild), "Ast node children differs"
    return True


#
# parse tests
#


def test_parse_only_comment():
    tree, comments = parse("# I'm a comment\n")
    assert tree is None
    assert comments == [Comment(s="# I'm a comment", lineno=1, col_offset=0)]


def test_parse_twoline_comment():
    tree, comments = parse("True  \n# I'm a comment\n", debug_level=0)
    exp = Module(body=[Expr(value=NameConstant(value=True), lineno=1, col_offset=0)])
    assert nodes_equal(tree, exp)
    assert comments == [Comment(s="# I'm a comment", lineno=2, col_offset=0)]


def test_parse_inline_comment():
    tree, comments = parse("True  # I'm a comment\n", debug_level=0)
    exp = Module(body=[Expr(value=NameConstant(value=True), lineno=1, col_offset=0)])
    assert nodes_equal(tree, exp)
    assert comments == [Comment(s="# I'm a comment", lineno=1, col_offset=6)]


#
# add_comments() tests
#


def check_add_comments(code, exp_tree, debug_level=0):
    code = dedent(code).lstrip()
    tree, comments = parse(code, debug_level=debug_level)
    tree = add_comments(tree, comments)
    try:
        assert nodes_equal(tree, exp_tree)
    except AssertionError:
        pprint_ast(tree, include_attributes=True)
        raise
    return tree


def test_add_only_comment():
    code = "# I'm a comment\n"
    exp = Module(body=[Comment(s="# I'm a comment", lineno=1, col_offset=0)])
    check_add_comments(code, exp)


def test_add_twoline_comment():
    code = "True  \n# I'm a comment\n"
    exp = Module(
        body=[
            Expr(value=NameConstant(value=True), lineno=1, col_offset=0),
            Comment(s="# I'm a comment", lineno=2, col_offset=0),
        ]
    )
    check_add_comments(code, exp)


def test_add_inline_comment():
    code = "True  # I'm a comment\n"
    exp = Module(
        body=[
            NodeWithComment(
                node=Expr(value=NameConstant(value=True), lineno=1, col_offset=0),
                comment=Comment(s="# I'm a comment", lineno=1, col_offset=6),
                lineno=1,
                col_offset=0,
            )
        ]
    )
    check_add_comments(code, exp)


def test_add_inline_comment_func():
    code = """
    # comment 1
    def func():  # comment 2
        # comment 3
        True  # comment 4
        # comment 5
    # comment 6
    """
    exp = Module(
        body=[
            Comment(s="# comment 1", lineno=1, col_offset=0),
            NodeWithComment(
                node=FunctionDef(
                    name="func",
                    args=arguments(
                        args=[],
                        vararg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        kwarg=None,
                        defaults=[],
                    ),
                    body=[
                        Comment(s="# comment 3", lineno=3, col_offset=4),
                        NodeWithComment(
                            node=Expr(
                                value=NameConstant(value=True, lineno=4, col_offset=4),
                                lineno=4,
                                col_offset=4,
                            ),
                            comment=Comment(s="# comment 4", lineno=4, col_offset=10),
                            lineno=4,
                            col_offset=4,
                        ),
                        Comment(s="# comment 5", lineno=5, col_offset=4),
                    ],
                    decorator_list=[],
                    returns=None,
                    lineno=2,
                    col_offset=0,
                ),
                comment=Comment(s="# comment 2", lineno=2, col_offset=13),
                lineno=2,
                col_offset=0,
            ),
            Comment(s="# comment 6", lineno=6, col_offset=0),
        ]
    )
    check_add_comments(code, exp)


def test_add_inline_comment_class():
    code = """
    # comment 1
    class Class:  # comment 2
        # comment 3
        '''
        # not a comment
        '''

        # comment 4
        x = True  # comment 5
        # comment 6

    # comment 7
    """
    exp = Module(
        body=[
            Comment(s="# comment 1", lineno=1, col_offset=0),
            NodeWithComment(
                node=ClassDef(
                    name="Class",
                    bases=[],
                    keywords=[],
                    body=[
                        Comment(s="# comment 3", lineno=3, col_offset=4),
                        Expr(
                            value=Str(
                                s="\n    # not a comment\n    ", lineno=4, col_offset=4
                            ),
                            lineno=4,
                            col_offset=4,
                        ),
                        Comment(s="# comment 4", lineno=8, col_offset=4),
                        NodeWithComment(
                            node=Assign(
                                targets=[
                                    Name(id="x", ctx=Store(), lineno=9, col_offset=4)
                                ],
                                value=NameConstant(value=True, lineno=9, col_offset=8),
                                lineno=9,
                                col_offset=4,
                            ),
                            comment=Comment(s="# comment 5", lineno=9, col_offset=14),
                            lineno=9,
                            col_offset=4,
                        ),
                        Comment(s="# comment 6", lineno=10, col_offset=4),
                    ],
                    decorator_list=[],
                    lineno=2,
                    col_offset=0,
                ),
                comment=Comment(s="# comment 2", lineno=2, col_offset=14),
                lineno=2,
                col_offset=0,
            ),
            Comment(s="# comment 7", lineno=12, col_offset=0),
        ]
    )
    check_add_comments(code, exp)


def test_add_inline_comment_if_else():
    code = """
    # comment 1
    if True:  # comment 2
        # comment 3
        x = 1  # comment 4
        # comment 5
    else: # comment 6
        # comment 7
        x = 4  # comment 8
        # comment 9
    # comment 10
    """
    exp = Module(
        body=[
            Comment(s="# comment 1"),
            IfWithComments(
                node=If(
                    test=NameConstant(value=True),
                    body=[
                        Comment(s="# comment 3"),
                        NodeWithComment(
                            node=Assign(
                                targets=[Name(id="x", ctx=Store())], value=Num(n=1)
                            ),
                            comment=Comment(s="# comment 4"),
                        ),
                        Comment(s="# comment 5"),
                    ],
                    orelse=[
                        Comment(s="# comment 7"),
                        NodeWithComment(
                            node=Assign(
                                targets=[Name(id="x", ctx=Store())], value=Num(n=4)
                            ),
                            comment=Comment(s="# comment 8"),
                        ),
                        Comment(s="# comment 9"),
                    ],
                ),
                comment=Comment(s="# comment 2"),
                elsecomment=Comment(s="# comment 6"),
            ),
            Comment(s="# comment 10"),
        ]
    )
    check_add_comments(code, exp)


def test_add_inline_comment_elif():
    code = """
    # comment 1
    if True:  # comment 2
        # comment 3
        x = 1  # comment 4
        # comment 5
    elif True: # comment 6
        # comment 7
        x = 2  # comment 8
        # comment 9
    elif False: # comment 10
        # comment 11
        x = 3  # comment 12
        # comment 13
    else: # comment 14
        # comment 15
        x = 4  # comment 16
        # comment 17
    # comment 18
    """
    exp = Module(
        body=[
            Comment(s="# comment 1", lineno=1, col_offset=0),
            NodeWithComment(
                node=If(
                    test=NameConstant(value=True, lineno=2, col_offset=3),
                    body=[
                        Comment(s="# comment 3", lineno=3, col_offset=4),
                        NodeWithComment(
                            node=Assign(
                                targets=[
                                    Name(id="x", ctx=Store(), lineno=4, col_offset=4)
                                ],
                                value=Num(n=1, lineno=4, col_offset=8),
                                lineno=4,
                                col_offset=4,
                            ),
                            comment=Comment(s="# comment 4", lineno=4, col_offset=11),
                            lineno=4,
                            col_offset=4,
                        ),
                        Comment(s="# comment 5", lineno=5, col_offset=4),
                    ],
                    orelse=[
                        If(
                            test=NameConstant(value=True, lineno=6, col_offset=5),
                            body=[
                                Assign(
                                    targets=[
                                        Name(
                                            id="x", ctx=Store(), lineno=8, col_offset=4
                                        )
                                    ],
                                    value=Num(n=2, lineno=8, col_offset=8),
                                    lineno=8,
                                    col_offset=4,
                                )
                            ],
                            orelse=[
                                If(
                                    test=NameConstant(
                                        value=False, lineno=10, col_offset=5
                                    ),
                                    body=[
                                        Assign(
                                            targets=[
                                                Name(
                                                    id="x",
                                                    ctx=Store(),
                                                    lineno=12,
                                                    col_offset=4,
                                                )
                                            ],
                                            value=Num(n=3, lineno=12, col_offset=8),
                                            lineno=12,
                                            col_offset=4,
                                        )
                                    ],
                                    orelse=[
                                        Assign(
                                            targets=[
                                                Name(
                                                    id="x",
                                                    ctx=Store(),
                                                    lineno=16,
                                                    col_offset=4,
                                                )
                                            ],
                                            value=Num(n=4, lineno=16, col_offset=8),
                                            lineno=16,
                                            col_offset=4,
                                        )
                                    ],
                                    lineno=10,
                                    col_offset=5,
                                )
                            ],
                            lineno=6,
                            col_offset=5,
                        )
                    ],
                    lineno=2,
                    col_offset=0,
                ),
                comment=Comment(s="# comment 2", lineno=2, col_offset=10),
                lineno=2,
                col_offset=0,
            ),
            Comment(s="# comment 18", lineno=18, col_offset=0),
        ]
    )
    check_add_comments(code, exp)
