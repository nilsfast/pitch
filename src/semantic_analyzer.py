import pitch_ast as ast
from ast_common import NodeVisitor
from shared import logger


class SemanticAnalyzer(NodeVisitor):
    def __init__(self):
        self.symbol_table = {}
        self.scopes = [{}]  # Stack of scopes for block-level symbol checking
        self.dataflow = []

    def analyze(self, ast):
        """
        Perform semantic analysis on the given AST.
        Returns a list of semantic errors, if any.
        """
        self.errors = []
        self.visit(ast)
        return self.errors

    def get_symbol_table(self):
        """
        Returns the symbol table after analysis.
        """
        return self.symbol_table

    def visit_Program(self, node: ast.Program):
        for item in node.functions:
            self.visit(item)

        # Store the symbol table for the program
        self.symbol_table = self.scopes[0].copy()

    def visit_Function(self, node: ast.Function):
        if node.name in self.scopes[-1]:
            self.errors.append(f"Function '{node.name}' is already defined.")
        else:
            self.scopes[-1][node.name] = node.return_type

        # Create a new scope for the function
        self.scopes.append(self.scopes[-1].copy())
        # Set the return type in the function's scope
        self.scopes[-1]["return_type"] = node.return_type

        for param in node.params:
            self.visit(param)
        self.visit(node.body)

        self.scopes.pop()  # Exit the function scope

    def visit_Param(self, node: ast.Param):
        # Ensure parameter types are valid
        if not self.is_valid_type(node.type):
            self.errors.append(
                f"Invalid type '{node.type}' for parameter '{node.name}'."
            )
        # Add parameter to the current scope
        self.scopes[-1][node.name] = node.type

    def visit_Block(self, node: ast.Block):
        # Create a new scope for the block
        self.scopes.append(self.scopes[-1].copy())
        for stmt in node.statements:
            self.visit(stmt)
        node.symbols = self.scopes.pop()  # Exit the block scope

    def visit_VarDecl(self, node: ast.VarDecl):
        current_scope = self.scopes[-1]
        if node.id.name in current_scope:
            self.errors.append(
                f"Variable '{node.id.name}' is already defined in this scope."
            )
        else:
            # Infer type if not explicitly declared
            if node.type is None:
                inferred_type = self.infer_type(node.expr)
                if inferred_type:
                    node.type = inferred_type
                else:
                    self.errors.append(
                        f"Could not infer type for variable '{node.name.name}'."
                    )
            current_scope[node.id.name] = node.type

        # Check the expression assigned to the variable
        self.visit(node.expr)

    def visit_Assignment(self, node: ast.Assignment):
        current_scope = self.scopes[-1]
        if node.id.name not in current_scope:
            self.errors.append(f"Assignment to undefined variable '{node.id.name}'.")
        else:
            # Check the type of the expression being assigned
            assigned_type = self.infer_type(node.expr)
            if assigned_type != current_scope[node.id.name]:
                self.errors.append(
                    f"Type mismatch in assignment: {current_scope[node.id.name]} expected, got {assigned_type}."
                )

    def visit_NumberLiteral(self, node):
        # Number literals are always valid
        pass

    def visit_Id(self, node: ast.Id):
        # Check all scopes for the identifier
        if not any(node.name in scope for scope in reversed(self.scopes)):
            self.errors.append(f"Undefined identifier '{node.name}'.")

    def visit_BinaryExpr(self, node: ast.BinaryExpr):
        # Check the left and right expressions
        self.visit(node.left)
        self.visit(node.right)

        # Check if the operator is valid
        if node.operator not in {"+", "-", "*", "/"}:
            self.errors.append(f"Invalid operator '{node.operator}'.")

        # Perform type checking for binary expressions
        left_type = self.infer_type(node.left)
        right_type = self.infer_type(node.right)
        if left_type != right_type:
            self.errors.append(
                f"Type mismatch in binary expression: {left_type} {node.operator} {right_type}."
            )

    def visit_GroupedExpr(self, node: ast.GroupedExpr):
        # Visit the inner expression
        self.visit(node.expr)

    def visit_Return(self, node: ast.Return):
        # Debugging print removed
        func_scope = self.scopes[-1]
        func_return_type = func_scope.get("return_type")
        if func_return_type and node.expr:
            return_type = self.infer_type(node.expr)
            if return_type != func_return_type:
                self.errors.append(
                    f"Return type mismatch: expected {func_return_type}, got {return_type}."
                )
            node.type = return_type

    def visit_Dereference(self, node: ast.Dereference):
        """
        Handle dereferencing of pointers or box types.
        """

        assert isinstance(
            node.expr, ast.Id
        ), "Dereference must be applied to an identifier."
        # Check if the identifier is defined
        self.visit(node.expr)

        # Infer the type of the dereferenced expression
        deref_type = self.infer_type(node.expr)

        logger.debug(f"deref_type {deref_type}")

        DEREFERABLE = ["Box"]

        if deref_type.typename not in DEREFERABLE:
            self.errors.append(
                f"Cannot dereference non-box type '{deref_type.typename}' for '{node.expr.name}'."
            )
        else:
            assert (
                deref_type.of is not None
            ), "Dereferenced type must have an 'of' attribute."
            node.inner_type = deref_type.of

    def is_valid_type(self, type_: ast.Type):
        """
        Check if the given type is valid in the language.
        """
        valid_types = {"int", "float", "string", "bool", "Box"}
        return type_.typename in valid_types

    def infer_type(self, expr) -> ast.Type | str:
        """
        Infer the type of an expression.
        """
        if isinstance(expr, ast.NumberLiteral):
            return ast.Type("int")
        elif isinstance(expr, ast.StringLiteral):
            return ast.Type("string")
        elif isinstance(expr, ast.GroupedExpr):
            return self.infer_type(expr.expr)
        elif isinstance(expr, ast.BinaryExpr):
            left_type = self.infer_type(expr.left)
            right_type = self.infer_type(expr.right)
            if left_type == right_type:
                return left_type
        elif isinstance(expr, ast.UnaryExpr):
            return self.infer_type(expr.operand)
        elif isinstance(expr, ast.Id):
            for scope in reversed(self.scopes):
                if expr.name in scope:
                    return scope[expr.name]
        elif isinstance(expr, ast.Call):
            # Check if the function is defined
            for scope in reversed(self.scopes):
                if expr.name.name in scope:
                    return scope[expr.name.name]
            # TODO buildiins
            if expr.name.name == "Box":
                if len(expr.args) == 1:
                    arg_type = self.infer_type(expr.args[0])
                    return ast.Type("Box", of=arg_type, nullable=False)
                else:
                    self.errors.append(
                        f"Box function expects exactly one argument, got {len(expr.args)}."
                    )
            self.errors.append(f"Undefined function '{expr.name.name}'.")
        elif isinstance(expr, ast.Dereference):
            self.visit(expr)
            if hasattr(expr, "inner_type"):
                return expr.inner_type
            else:
                self.errors.append(
                    f"Cannot infer type for dereference '{expr.expr.name}'."
                )

        logger.error(f"Could not infer type for expression: {expr}")
        return "Not inferrable"
