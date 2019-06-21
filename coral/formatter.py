"""Formatting tools for xonsh."""
import ast

from coral.parser import parse, add_comments

OP_STRINGS = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.FloorDiv: "//",
    ast.Pow: "**",
    ast.MatMult: "@",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.BitAnd: "&",
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.Or: "or",
    ast.And: "and",
    ast.USub: "-",
    ast.UAdd: "+",
    ast.Invert: "~",
    ast.Not: "not",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Is: "is",
    ast.IsNot: "is not",
    ast.In: "in",
    ast.NotIn: "not in",
}


def op_to_str(op):
    return OP_STRINGS[type(op)]


def remove_outer_quotes(s):
    if not s.endswith('"'):
        return s
    return s.partition('"')[2].rpartition('"')[0]



class Formatter(ast.NodeVisitor):
    """Converts a node into a coral-formatted string."""

    # indent helpers

    base_indent = "    "
    indent = ""
    nl_indent = "\n"
    indent_level = 0

    def inc_indent(self):
        self.indent_level += 1
        self.indent = self.base_indent * self.indent_level
        self.nl_indent = "\n" + self.indent

    def dec_indent(self):
        self.indent_level -= 1
        self.indent = self.base_indent * self.indent_level
        self.nl_indent = "\n" + self.indent

    # other helpers

    def _func_args(self, args):
        """converts function arguments to a str"""
        rendered = []
        npositional = len(args.args) - len(args.defaults)
        positional_args = args.args[:npositional]
        keyword_args = args.args[npositional:]
        keywordonly_args = args.kwonlyargs
        for arg in positional_args:
            rendered.append(arg.arg)
        for arg, default in zip(keyword_args, args.defaults):
            rendered.append(arg.arg + "=" + self.visit(default))
        if args.vararg is not None:
            rendered.append("*" + args.vararg.arg)
        if keywordonly_args:
            if args.vararg is None:
                rendered.append("*")
            for arg, default in zip(keywordonly_args, args.kw_defaults):
                rendered.append(arg.arg + "=" + self.visit(default))
        if args.kwarg is not None:
            rendered.append("**" + args.kwarg.arg)
        return ", ".join(rendered)

    def _generators(self, node):
        s = ""
        for generator in node.generators:
            s += " for " + self.visit(generator.target)
            s += " in " + self.visit(generator.iter)
            for clause in generator.ifs:
                s += " if " + self.visit(clause)
        return s

    def _loop_body(self, node):
        self.inc_indent()
        s = self.nl_indent + self.nl_indent.join(map(self.visit, node.body))
        self.dec_indent()
        if node.orelse:
            s += "\nelse:"
            self.inc_indent()
            s += self.nl_indent + self.nl_indent.join(map(self.visit, node.orelse))
            self.dec_indent()
        s += "\n"
        return s

    def _withitem(self, item):
        s = self.visit(item.context_expr)
        if item.optional_vars is not None:
            s += " as " + self.visit(item.optional_vars)
        return s

    # top-level visitors

    def generic_visit(self, node):
        return "<coral:" + str(node.__class__) + " not implemented>"

    def visit_Module(self, node):
        parts = []
        for n in node.body:
            parts.append(self.visit(n))
        s = "\n".join(parts)
        if not s.endswith("\n"):
            s += "\n"
        return s

    visit_Interactive = visit_Module

    def visit_Expression(self, node):
        return self.visit(node.body)

    # expression visitors

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Comment(self, node):
        _, _, comment = node.s.partition('#')
        return '# ' + comment.strip()

    def visit_Name(self, node):
        return node.id

    def visit_Str(self, node):
        return '"' + node.s  + '"'

    def visit_FormattedValue(self, node):
        s = "{" + self.visit(node.value)
        if node.format_spec is not None:
            s += ":" + remove_outer_quotes(self.visit(node.format_spec))
        if node.conversion >= 0:
            s += "!" + chr(node.conversion)
        s += "}"
        return s

    def visit_JoinedStr(self, node):
        s = 'f"'
        for value in node.values:
            s += remove_outer_quotes(self.visit(value))
        s += '"'
        return s

    def visit_Bytes(self, node):
        return 'b"' + repr(node.s)[2:-1].replace("'", "\\'") + '"'

    def visit_Num(self, node):
        return str(node.n)

    def visit_NameConstant(self, node):
        return str(node.value)

    def visit_Ellipsis(self, node):
        return "..."

    def visit_Constant(self, node):
        return "<coral:constant not implemented>"

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

    def visit_Lambda(self, node):
        s = "lambda"
        args = self._func_args(node.args)
        if args:
            s += " " + args
        s += ": " + self.visit(node.body)
        return s

    def visit_BinOp(self, node):
        s = self.visit(node.left) + " "
        s += op_to_str(node.op)
        s += " " + self.visit(node.right)
        return s

    def visit_BoolOp(self, node):
        op = " " + op_to_str(node.op) + " "
        s = op.join(map(self.visit, node.values))
        return s

    def visit_UnaryOp(self, node):
        space = ""
        if isinstance(node.op, ast.Not):
            space = " "
        s = op_to_str(node.op) + space + self.visit(node.operand)
        return s

    def visit_IfExp(self, node):
        s = self.visit(node.body) + " if " + self.visit(node.test)
        s += " else " + self.visit(node.orelse)
        return s

    def visit_ListComp(self, node):
        return "[" + self.visit(node.elt) + self._generators(node) + "]"

    def visit_DictComp(self, node):
        s = "{" + self.visit(node.key) + ": " + self.visit(node.value)
        s += self._generators(node) + "}"
        return s

    def visit_SetComp(self, node):
        return "{" + self.visit(node.elt) + self._generators(node) + "}"

    def visit_GeneratorExp(self, node):
        return "(" + self.visit(node.elt) + self._generators(node) + ")"

    def visit_Await(self, node):
        return "await " + self.visit(node.value)

    def visit_Yield(self, node):
        return "yield " + self.visit(node.value)

    def visit_YieldFrom(self, node):
        return "yield from " + self.visit(node.value)

    def visit_Compare(self, node):
        s = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            s += " " + op_to_str(op) + " " + self.visit(comparator)
        return s

    def visit_Call(self, node):
        s = self.visit(node.func) + "("
        all_args = []
        all_args.extend(map(self.visit, node.args))
        for keyword in node.keywords:
            kw = keyword.arg + "=" + self.visit(keyword.value)
            all_args.append(kw)
        s += ", ".join(all_args) +  ")"
        return s

    def visit_Slice(self, node):
        s = ""
        if node.lower is not None:
            s += self.visit(node.lower)
        s += ":"
        if node.upper is not None:
            s += self.visit(node.upper)
        if node.step is not None:
            s += ':' + self.visit(node.step)
        return s

    # assignable expression visitors

    def visit_Attribute(self, node):
        return self.visit(node.value) + '.' + node.attr

    def visit_Subscript(self, node):
        return  self.visit(node.value) + '[' + self.visit(node.slice) + ']'

    def visit_Starred(self, node):
        return '*' + self.visit(node.value)

    # statement visitors

    def visit_FunctionDef(self, node):
        s = "def " + node.name + "(" + self._func_args(node.args) + "):"
        self.inc_indent()
        s += self.nl_indent + self.nl_indent.join(map(self.visit, node.body))
        if node.returns:
            s += self.nl_indent + self.visit(node.returns)
        self.dec_indent()
        s += "\n"
        return s

    def visit_AsyncFunctionDef(self, node):
        return "async " + self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        s = "class " + node.name
        if node.bases or node.keywords:
            s += "("
            parts = list(map(self.visit, node.bases))
            for keyword in node.keywords:
                parts.append(keyword.arg + '=' + self.visit(keyword.value))
            s += ", ".join(parts) + ")"
        self.inc_indent()
        s += ":" + self.nl_indent
        parts = list(map(self.visit, node.body))
        s += self.nl_indent.join(parts)
        self.dec_indent()
        s += "\n"
        return s

    def visit_Return(self, node):
        s = "return"
        if node.value is not None:
            s += " " + self.visit(node.value)
        return s

    def visit_Delete(self, node):
        return "del " + ", ".join(map(self.visit, node.targets))

    def visit_Assign(self, node):
        if isinstance(node, ast.AnnAssign):
            return self.visit_AnnAssign(node)
        return ", ".join(map(self.visit, node.targets)) + " = " + self.visit(node.value)

    def visit_AugAssign(self, node):
        return self.visit(node.target) + " " + op_to_str(node.op) + "= " + self.visit(node.value)

    def visit_AnnAssign(self, node):
        use_paren = node.simple == 0 and isinstance(node.target, ast.Name)
        s = "(" if use_paren else ""
        s += self.visit(node.target)
        if use_paren:
            s += ")"
        s += ": " + self.visit(node.annotation)
        if node.value is not None:
            s += " = " + self.visit(node.value)
        return s

    def visit_For(self, node):
        s = "for " + self.visit(node.target) + " in "
        s += self.visit(node.iter) + ":"
        s += self._loop_body(node)
        return s

    def visit_AsyncFor(self, node):
        return "async " + self.visit_For(node)

    def visit_While(self, node):
        s = "while " + self.visit(node.test) + ":"
        s += self._loop_body(node)
        return s

    def visit_If(self, node):
        s = "if " + self.visit(node.test) + ":"
        self.inc_indent()
        s += self.nl_indent + self.nl_indent.join(map(self.visit, node.body))
        self.dec_indent()
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            s += "\nel" + self.visit_If(node.orelse[0])
        elif node.orelse:
            s += "\nelse:"
            self.inc_indent()
            s += self.nl_indent + self.nl_indent.join(map(self.visit, node.orelse))
            self.dec_indent()
        if not s.endswith("\n"):
            s += "\n"
        return s

    def visit_With(self, node):
        s = "with " + ", ".join(map(self._withitem, node.items)) + ":"
        self.inc_indent()
        s += self.nl_indent + self.nl_indent.join(map(self.visit, node.body))
        self.dec_indent()
        return s

    def visit_AsyncWith(self, node):
        return "async " + self.visit_With(node)

    def visit_Pass(self, node):
        return "pass"

    def visit_Break(self, node):
        return "break"

    def visit_Continue(self, node):
        return "continue"



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
