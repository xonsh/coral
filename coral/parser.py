"""A custom parser and AST for analyzing xonsh code."""
import os
import re
import builtins
from ast import AST, NodeTransformer, Module, If
from contextlib import contextmanager

from xonsh import lexer
from xonsh.ply.ply.lex import LexToken
from xonsh.tokenize import NL, COMMENT, ENCODING, ENDMARKER
from xonsh.execer import Execer

from lazyasd import lazyobject


#
# AST Nodes
#


class Comment(AST):
    _attributes = ("lineno", "col_offset")
    _fields = "s"

    def __eq__(self, other):
        return (
            self.s == other.s
            and self.lineno == other.lineno
            and self.col_offset == other.col_offset
        )

    def __repr__(self):
        return "Comment(s={self.s!r}, lineno={self.lineno}, col_offset={self.col_offset})".format(
            self=self
        )


class NodeWithComment(AST):
    _attributes = ("lineno", "col_offset")
    _fields = ("node", "comment")

    def __eq__(self, other):
        return (
            self.node == other.node
            and self.comment == other.comment
            and self.lineno == other.lineno
            and self.col_offset == other.col_offset
        )

    def __repr__(self):
        return "NodeWithComment(node={self.node!r}, comment={self.comment!r}, lineno={self.lineno}, col_offset={self.col_offset})".format(
            self=self
        )


class IfWithComments(AST):
    _attributes = ("lineno", "col_offset")
    _fields = ("node", "comment", "elsecomment")

    def __eq__(self, other):
        return (
            self.node == other.node
            and self.comment == other.comment
            and self.elsecomment == other.elseomment
            and self.lineno == other.lineno
            and self.col_offset == other.col_offset
        )

    def __repr__(self):
        return "IfWithComments(node={self.node!r}, comment={self.comment!r}, elsecomment={self.elsecomment!r}, lineno={self.lineno}, col_offset={self.col_offset})".format(
            self=self
        )


#
# Execution tools
#


@contextmanager
def swapexec(debug_level):
    """Performs some global lexer context switching"""
    execer = builtins.__xonsh__.execer
    orig_debug_level, execer.debug_level = execer.debug_level, debug_level
    lines = {}
    comments = []

    def handle_comment(state, token):
        comment = Comment(
            s=token.string, lineno=token.start[0], col_offset=token.start[1]
        )
        lines[token.start[0]] = token.line
        comments.append(comment)
        yield from []

    shold = lexer.special_handlers.copy()
    shnew = {
        # NL: handle_nl,
        COMMENT: handle_comment,
        # ENCODING: handle_indentity,
        # ENDMARKER: handle_indentity,
    }
    lexer.special_handlers.update(shnew)
    yield (execer, comments, lines)
    execer.debug_level = orig_debug_level
    lexer.special_handlers.clear()
    lexer.special_handlers.update(shold)


#
# Parser tools
#

def parse(s, ctx=None, filename="<code>", mode="exec", debug_level=0):
    """Returns an abstract syntax tree of xonsh code. Unlike the
    normal xonsh parser, this also returns additional information about
    the file being parsed.

    Parameters
    ----------
    s : str
        The xonsh code.
    ctx : dict, optional
        Execution context to evaluate within
    filename : str, optional
        Name of the file.
    mode : str, optional
        Execution mode, one of: exec, eval, or single.
    debug_level : str, optional
        Debugging level passed down to yacc.

    Returns
    -------
    tree : AST
        Normal xonsh AST, as returned by the xonsh parser
    lines : dict
        Maps line numbers to string lines
    comments : list of Comment
        A list of xonsh comment instances.
    """
    if ctx is None:
        ctx = set(__builtins__.keys())
    with swapexec(debug_level) as (execer, comments, lines):
        tree = execer.parse(s, ctx, filename=filename, mode=mode)
    return tree, comments, lines


#
# commented tree
#

@lazyobject
def re_else_comment():
    return re.compile(r"^\s*else:\s*#.*")


def merge_body_comments(body, comments):
    """Takes a body (list of nodes) and adds in comments
    that appear at the root level of the body. This operates in-place
    """
    i = 0
    while comments and i < len(body):
        if comments[0].lineno < body[i].lineno:
            body.insert(i, comments.pop(0))
        i += 1
    body.extend(comments)


class CommentAdder(NodeTransformer):
    """Transformer for adding comment nodes to a tree"""

    def __init__(self, comments, lines=None):
        self.lines = {} if lines is None else lines
        self._comments = list(reversed(comments))
        self._next_comment = self._comments.pop() if self._comments else None
        # this is a list of lists of comments, representing the stack
        self._comments_in_body = []

    def _attach_comment(self, node, node_with_comment_class=None):
        # attach comments to current node or continue
        node_with_comment_class = node_with_comment_class or NodeWithComment
        if self._next_comment.lineno == node.lineno:
            new_node = node_with_comment_class(
                node=node,
                comment=self._next_comment,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
            self._next_comment = self._comments.pop() if self._comments else None
        else:
            new_node = node
        return new_node

    def _grab_prior_body_comments(self, node):
        while (
            self._next_comment is not None and self._next_comment.lineno < node.lineno
        ):
            self._comments_in_body[-1].append(self._next_comment)
            self._next_comment = self._comments.pop() if self._comments else None

    def _next_comment_on_else_line(self):
        # we have to look at the actual line contents for this because
        # the col_offsets for "elif" and "else" are actually not at the same
        # level of the original "if". Oddly, they are also not at the same
        # col_offset of their blocks. (This is not just a xonsh issue, this
        # is how CPython ASTs look. Because of this and that different
        # blocks in the same if-elif-else statement can have different
        # indentations, it is not reliable to use col_offsets to find
        # comments appearing on the else line. Best to just check if a
        # comment line *has* an else on it, since that is the only thing
        # that can be on that line anyway.
        if self._next_comment is None:
            return False
        line = self.lines.get(self._next_comment.lineno, '')
        return re_else_comment.match(line) is not None

    def generic_visit(self, node):
        # first handle some early exits
        if self._next_comment is None:
            return node
        elif node is None:
            # this can happen if the module contains nothing but comments
            comments = [self._next_comment]
            self._next_comment = None
            comments.extend(reversed(self._comments))
            self._comments.clear()
            new_node = Module(body=comments)
            return new_node

        # grab prior body comments
        self._grab_prior_body_comments(node)
        if self._next_comment is None:
            # can early exit again
            return node

        new_node = self._attach_comment(node)
        if hasattr(node, "body"):
            self._comments_in_body.append([])
            for i, n in enumerate(node.body):
                node.body[i] = self.visit(n)
            # grab trainling body comments
            while (
                self._next_comment is not None
                and self._next_comment.col_offset >= n.col_offset
            ):
                self._comments_in_body[-1].append(self._next_comment)
                self._next_comment = self._comments.pop() if self._comments else None
            merge_body_comments(node.body, self._comments_in_body.pop())
        elif node is not new_node:
            self.visit(node)
        return new_node

    def visit_If(self, node):
        # we have to scan body and orelse separately for comments
        self._grab_prior_body_comments(node)
        if self._next_comment is None:
            # can early exit again
            return node

        new_node = self._attach_comment(node, IfWithComments)
        new_node.elsecomment = None
        # go through body
        self._comments_in_body.append([])
        for i, n in enumerate(node.body):
            node.body[i] = self.visit(n)
            # grab trainling body comments
        # figure out if the else-clause exists and if it is an actual "else"
        # rather than an "elif"
        orelse0 = node.orelse[0] if len(node.orelse) > 0 else None
        orelse0_iselse = orelse0 is not None and not isinstance(orelse0, If)
        while (
            self._next_comment is not None
            and (orelse0 is None or self._next_comment.lineno < orelse0.lineno)
            and self._next_comment.col_offset >= n.col_offset
            and (not orelse0_iselse or (orelse0_iselse and not self._next_comment_on_else_line()))
        ):
            self._comments_in_body[-1].append(self._next_comment)
            self._next_comment = self._comments.pop() if self._comments else None
        merge_body_comments(node.body, self._comments_in_body.pop())
        # add else comment
        if self._next_comment is not None and orelse0_iselse and self._next_comment_on_else_line():
            new_node.elsecomment = self._next_comment
            self._next_comment = self._comments.pop() if self._comments else None
        # go through orelse
        self._comments_in_body.append([])
        for i, n in enumerate(node.orelse):
            node.orelse[i] = self.visit(n)
            # grab trainling body comments
        while (
            self._next_comment is not None
            and self._next_comment.col_offset >= n.col_offset
        ):
            self._comments_in_body[-1].append(self._next_comment)
            self._next_comment = self._comments.pop() if self._comments else None
        merge_body_comments(node.orelse, self._comments_in_body.pop())
        return new_node

    def visit_Module(self, node):
        # ast.Module does not have a lineno attr
        self._comments_in_body.append([])
        for i, n in enumerate(node.body):
            node.body[i] = self.visit(n)
        merge_body_comments(node.body, self._comments_in_body.pop())
        # if there are any remaining comments, add them to the end
        if self._next_comment is not None:
            node.body.append(self._next_comment)
            self._next_comment = None
        if self._comments:
            node.body.extend(reversed(self._comments))
            self._comments.clear()
        return node


def add_comments(tree, comments, lines=None):
    """Adds comment nodes to a tree"""
    adder = CommentAdder(comments, lines=lines)
    new_tree = adder.visit(tree)
    return new_tree
