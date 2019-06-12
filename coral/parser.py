"""A custom parser and AST for analyzing xonsh code."""
import os
import builtins
from ast import AST
from contextlib import contextmanager

from xonsh import lexer
from xonsh.ply.ply.lex import LexToken
from xonsh.tokenize import NL, COMMENT, ENCODING, ENDMARKER
from xonsh.execer import Execer


#
# AST Nodes
#

class Errortoken(AST):
    _attributes = ('lineno', 'col_offset')
    _fields = ('token')


class Comment(AST):
    _attributes = ('lineno', 'col_offset')
    _fields = ('s')

    def __eq__(self, other):
        return self.s == other.s and self.lineno == other.lineno and self.col_offset == other.col_offset

    def __repr__(self):
        return "Comment(s={self.s!r}, lineno={self.lineno}, col_offset={self.col_offset})".format(self=self)


#
# Lexer tools
#

def _new_token(type, value, lineno, lexpos):
    o = LexToken()
    o.type = type
    o.value = value
    o.lineno = lineno
    o.lexpos = lexpos
    return o


@contextmanager
def swapexec(debug_level):
    """Performs some global lexer context switching"""
    execer = builtins.__xonsh__.execer
    orig_debug_level, execer.debug_level = execer.debug_level, debug_level
    comments = []

    def handle_comment(state, token):
        comment = Comment(s=token.string, lineno=token.start[0],
                          col_offset=token.start[1])
        comments.append(comment)
        yield from []

    shold = lexer.special_handlers.copy()
    shnew = {
        #NL: handle_nl,
        COMMENT: handle_comment,
        #ENCODING: handle_indentity,
        #ENDMARKER: handle_indentity,
        }
    lexer.special_handlers.update(shnew)
    yield (execer, comments)
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
    comments : list of Comment
        A list of xonsh comment instances.
    """
    with swapexec(debug_level) as (execer, comments):
        tree = execer.parse(s, ctx, filename=filename, mode=mode,)
    return tree, comments

