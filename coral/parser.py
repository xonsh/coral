"""A custom parser and AST for analyzing xonsh code."""
import os
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
def swaplexer(comments):
    """Performs some global lexer context switching"""
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
    yield comments
    lexer.special_handlers.clear()
    lexer.special_handlers.update(shold)



#
# Parser tools
#


class Parser:
    """Custom parser that is suited to static code analysis because
    it does not throw away unused tokens. This makes the job of
    rewriting code much easier.
    """

    def __init__(
        self,
    ):
        self.execer = Execer()

    @property
    def lexer(self):
        return self.execer.parser.lexer

    @property
    def parser(self):
        return self.execer.parser

    def parse(self, s, filename="<code>", mode="exec", debug_level=0):
        """Returns an abstract syntax tree of xonsh code. Unlike the
        normal xonsh parser, this also returns additional information about
        the file being parsed.

        Parameters
        ----------
        s : str
            The xonsh code.
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
        with swaplexer() as comments:
            tree = self.parser.parse(s, filename=filename, mode=mode, debug_level=debug_level)
        return tree, comments

