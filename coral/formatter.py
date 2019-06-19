"""Formatting tools for xonsh."""
from ast import NodeVisitor

from coral.parser import parse, add_comments


class Formatter(NodeVisitor):
    """Converts a node into a coral-formatted string."""

    def visit_Module(self, node):
        parts = []
        for n in node.body:
            parts.append(self.visit(n))
        return "\n".join(parts) + "\n"

    def visit_Comment(self, node):
        _, _, comment = node.s.partition('#')
        return '# ' + comment.strip()


def format(tree):
    """Formats an AST of xonsh code into a nice string"""
    formatter = Formatter()
    s = formatter.visit(tree)
    return s


def reformat(inp, debug_level=0):
    """Reformats xonsh code (str) into a nice string"""
    tree, comments, lines = parse(inp, debug_level=debug_level)
    tree = add_comments(tree, comments, lines)
    return format(tree)
