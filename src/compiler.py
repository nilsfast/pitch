import pitch_ast as ast

TYPE_MAPPING = {
    "int": "int",
    "float": "float",
    "string": "char*",
    "bool": "bool",
    "none": "void",
}


def translate_type(type: ast.Type):

    if type.typename == "Box":
        assert type.of is not None, "Box type must have an 'of' attribute."
        c_typename = f"{translate_type(type.of)}*"
    else:
        c_typename = TYPE_MAPPING.get(type.typename, type.typename)

    return c_typename


class CodeGenerator:
    def __init__(self):
        self.indent_level = 0

    def indent(self):
        return "    " * self.indent_level

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")

    def visit_Program(self, node):
        return "\n".join(self.visit(function) for function in node.functions)

    def visit_BinaryExpr(self, node: ast.BinaryExpr):
        left = self.visit(node.left)
        right = self.visit(node.right)
        operator = node.operator
        return f"{left} {operator} {right}"

    def visit_Dereference(self, node: ast.Dereference):
        # Dereferencing in C is done with the '*' operator
        return f"*{self.visit(node.expr)}"

    def visit_Function(self, node: ast.Function):

        test_comment = node.context.get("comment", "")

        params = ", ".join(
            f"{self.visit(param.type)} {param.name}" for param in node.params
        )
        body = self.visit(node.body)
        return f"\n{self.visit(node.return_type)} {node.name}({params}) {{\n{body}\n}}"

    def visit_Block(self, node: ast.Block):
        self.indent_level += 1
        statements = "\n".join(
            self.indent() + self.visit(statement) for statement in node.statements
        )
        self.indent_level -= 1
        return statements

    def visit_VarDecl(self, node):
        var_type = self.visit(node.type)
        var_name = node.id.name
        var_value = f" = {self.visit(node.expr)}" if node.expr else ""
        return f"{var_type} {var_name}{var_value};"

    def visit_Assignment(self, node):
        var_name = node.id.name
        value = self.visit(node.expr)
        return f"{var_name} = {value};"

    def visit_PrintStatement(self, node):
        value = self.visit(node.value)
        return f'printf("{value}\\n");'

    def visit_NumberLiteral(self, node):
        return str(node.value)

    def visit_Id(self, node):
        return node.name

    def visit_Type(self, node):

        c_type = translate_type(node)

        return c_type

    def visit_Call(self, node):
        func_name = node.name
        args = ", ".join(self.visit(arg) for arg in node.args)
        return f"{func_name}({args})"

    def visit_Cleanup(self, node):
        return f"free({node.identifier.name});"

    def visit_StringLiteral(self, node):
        return f'"{node.value}"'

    def visit_Return(self, node: ast.Return):
        value = self.visit(node.expr)
        return f"return {value};"

    def visit_Reference(self, node: ast.Reference):
        return f"{node.name}"

    def generate(self, ast):
        return self.visit(ast)
