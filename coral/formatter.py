"""Formatting tools for xonsh."""
from ast import NodeVisitor

from coral.parser import parse, add_comments


class Formatter(NodeVisitor):
    """Converts a node into a coral-formatted string."""

    base_indent = "    "
    indent = ""
    indent_level = 0

    def inc_indent(self):
        self.indent_level += 1
        self.indent = self.base_indent * self.indent_level

    def dec_indent(self):
        self.indent_level -= 1
        self.indent = self.base_indent * self.indent_level

    def visit_Module(self, node):
        parts = []
        for n in node.body:
            parts.append(self.visit(n))
        return "\n".join(parts) + "\n"

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Comment(self, node):
        _, _, comment = node.s.partition('#')
        return '# ' + comment.strip()

    def visit_Str(self, node):
        return '"' + node.s  + '"'

    def visit_Num(self, node):
        return str(node.n)

    def visit_NameConstant(self, node):
        return str(node.value)

    def visit_List(self, node):
        s = "["
        new_elts = []
        for elt in node.elts:
            new_elts.append(self.visit(elt))
        s += ", ".join(new_elts)
        s += "]"
        return s

    def visit_Tuple(self, node):
        if len(node.elts) == 0:
            return "()"
        elif len(node.elts) == 1:
            return "(" + self.visit(node.elts[0]) + ",)"
        s = "("
        new_elts = []
        for elt in node.elts:
            new_elts.append(self.visit(elt))
        s += ", ".join(new_elts)
        s += ")"
        return s

    def visit_Dict(self, node):
        s = "{"
        new_elts = []
        for key, value in zip(node.keys, node.values):
            k = self.visit(key)
            v = self.visit(value)
            new_elts.append(k + ": " + v)
        s += ", ".join(new_elts)
        s += "}"
        return s

    def visit_Set(self, node):
        s = "{"
        new_elts = []
        for elt in node.elts:
            new_elts.append(self.visit(elt))
        s += ", ".join(new_elts)
        s += "}"
        return s


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
