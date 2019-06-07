"""A custom parser and AST for analyzing xonsh code."""
import os
from ast import AST
from contextlib import contextmanager

from xonsh import lexer
from xonsh.ply.ply.lex import LexToken
from xonsh.tokenize import NL, COMMENT, ENCODING, ENDMARKER
from xonsh.parser import Parser as XonshParser


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


def handle_indentity(state, token):
    yield token


#def handle_nl(state, token):
#    yield _new_token("NEWLINE", token.string, token.start[0], token.start[1])


def handle_comment(state, token):
    yield _new_token("COMMENT", token.string, token.start[0], token.start[1])


@contextmanager
def swaplexer():
    """Performs some global lexer context switching"""
    shold = lexer.special_handlers.copy()
    shnew = {
        #NL: handle_nl,
        COMMENT: handle_comment,
        #ENCODING: handle_indentity,
        #ENDMARKER: handle_indentity,
        }
    lexer.special_handlers.update(shnew)
    yield
    lexer.special_handlers.clear()
    lexer.special_handlers.update(shold)


class Lexer(lexer.Lexer):
    """A lexer that exposes more tokens"""

    @property
    def tokens(self):
        if self._tokens is None or 'COMMENT' not in self._tokens:
            super().tokens
            self._tokens += ('COMMENT', 'ENCODING', 'ENDMARKER', 'NL')
        return self._tokens



#
# Parser tools
#

@contextmanager
def swapcomments(parser):
    parser.comments = []
    yield
    parser.comments = None


class Parser(XonshParser):
    """Custom parser that is suited to static code analysis because
    it does not throw away unused tokens. This makes the job of
    rewriting code much easier.
    """

    def __init__(
        self,
        lexer_optimize=True,
        lexer_table="coral.lexer_table",
        yacc_optimize=True,
        yacc_table="coral.parser_table",
        yacc_debug=False,
        outputdir=None,
        lexer=None,
    ):
        """Parameters
        ----------
        lexer_optimize : bool, optional
            Set to false when unstable and true when lexer is stable.
        lexer_table : str, optional
            Lexer module used when optimized.
        yacc_optimize : bool, optional
            Set to false when unstable and true when parser is stable.
        yacc_table : str, optional
            Parser module used when optimized.
        yacc_debug : debug, optional
            Dumps extra debug info.
        outputdir : str or None, optional
            The directory to place generated tables within. Defaults to the root
            coral dir.
        lexer : Lexer instance or None:
            optional lexer object to pass in.
        """
        lexer = Lexer() if lexer is None else lexer
        tok_rules = [
            "errortoken",
            "comment",
            "nl",
            "encoding",
            "endmarker",
            ]
        for rule in tok_rules:
            self._tok_rule(rule)
        if outputdir is None:
            outputdir = os.path.dirname(os.path.dirname(__file__))
        super().__init__(lexer_optimize=lexer_optimize, lexer_table=lexer_table,
                         yacc_optimize=yacc_optimize, yacc_table=yacc_table,
                         yacc_debug=yacc_debug, outputdir=outputdir, lexer=lexer)
        self.comments = None

    def parse(self, s, filename="<code>", mode="exec", debug_level=0):
        """Returns an abstract syntax tree of xonsh code.

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
        """
        with swaplexer(), swapcomments(self):
            tree = super().parse(s, filename=filename, mode=mode, debug_level=debug_level)
            tree.comments = comments
        return tree

    def p_comment(self, p):
        """comment : comment_tok"""
        # it is important that this isn't pushed onto the parser stack!
        # don't assign to p[0]!
        p1 = p[1]
        c = Comment(s=p1.value, lineno=p1.lineno, col_offset=p1.lexpos)
        self.comments.append(c)
