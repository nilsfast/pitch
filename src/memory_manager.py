from dataclasses import dataclass
from ast_common import NodeVisitor
import pitch_ast as ast
import nanoid
from shared import logger


@dataclass
class Variable:
    id: str
    type: ast.Type
    status: str
    first_name: str = None
    current_name: str = None
    source: str = "local"


def gen_id():
    return nanoid.generate(size=10)


class MemoryManager(NodeVisitor):

    def __init__(self):
        # keeps track of the block, so statements can be added
        self.current_block: ast.Block = None

        # keeps track of variables in the current scope
        self.scope_var_tracker = []  # List of dictionaries to track variable status
        self.var_map = []

        self.block_stack = []
        self.current_scope = None

        self.current_symbol_table = {}

    def find_var(self, id: str):
        """
        Find a variable in the current scope or any enclosing scope.
        Returns the variable's information if found, otherwise None.
        """
        for scope in reversed(self.scope_var_tracker):
            if id in scope:
                return scope[id]
        return None

    def id_by_varname(self, name: str):
        """
        Get the variable ID by its name in the current scope.
        Returns the variable ID if found, otherwise None.
        """
        for scope in reversed(self.var_map):
            if name in scope:
                return scope[name]
        return None

    def analyze(self, ast):
        self.errors = []
        """
        Perform data flow analysis on the given AST.
        Returns a list of data flow information.
        """
        self.visit(ast)

    def enter_scope(self, scope):
        """
        Enter a new scope (function or block).
        """
        self.current_scope = scope
        self.block_stack.append(scope)

        self.scope_var_tracker.append({})
        self.var_map.append({})

    def exit_scope(self):
        """
        Exit the current scope.
        """
        if self.block_stack:
            self.block_stack.pop()
        self.current_scope = self.block_stack[-1] if self.block_stack else None

        self.scope_var_tracker.pop()
        self.var_map.pop()

    def track_var(self, name: str, type: ast.Type, status: str, source: str = "local"):
        if not self.scope_var_tracker:
            raise ValueError("No current scope to track variables.")

        var_id = gen_id()

        var = Variable(
            id=var_id,
            type=type,
            status=status,
            first_name=name,
            source=source,
            current_name=name,
        )

        self.var_map[-1][name] = var_id
        self.scope_var_tracker[-1][var_id] = var

        print(f"Tracking variable {name} with type {type} and status {status}")
        return var

    def visit_Program(self, node: ast.Program):
        for item in node.functions:
            self.visit(item)

    def visit_Function(self, node: ast.Function):
        """
        Visit a function node and analyze its body.
        If the function returns a heap object, mark it for cleanup by the caller.
        """
        self.enter_scope(node.name)

        for param in node.params:
            if is_box_type(param.type):
                print("Box type detected in parameter", param.name)
                var = self.track_var(
                    name=param.name,
                    type=param.type,
                    status="in",
                    source="param",
                )
                print("Tracking parameter", param.name, "with ID", var)
                self.var_map[-1][param.name] = var.id
        # Analyze the function body
        self.visit(node.body)

        self.exit_scope()

    def visit_Block(self, node: ast.Block):
        """
        Visit a block node and analyze its statements.
        Create a new scope for the block.
        """
        self.current_scope = node.symbols
        self.enter_scope(node)

        self.current_block = node
        original_statements = list(
            node.statements
        )  # Make a copy of the original statements
        for statement in original_statements:
            if statement not in node.statements:
                # Skip statements that were added during the iteration
                continue
            self.visit(statement)
        self.exit_scope()

    def visit_VarDecl(self, node: ast.VarDecl):
        # Tasks:
        # - Add new Heap variables to the tracker
        # - Track moved (or overwritten) variables

        assert isinstance(node, ast.VarDecl), "Node must be a VarDecl instance"
        assert isinstance(node.type, ast.Type), "Node type must be a Type instance"

        self.visit(node.expr)

        if not is_box_type(node.type):
            return

        _id = self.track_var(
            name=node.id.name,
            type=node.type,
            status="in",
            source="local",
        )

        if is_box_alloc(node.expr):
            return
        if is_call(node.expr):
            return
        if is_variable(node.expr):
            rhs_var_id = self.id_by_varname(node.expr.name)
            if rhs_var_id is None:
                raise ValueError(
                    f"Variable '{node.expr.name}' not found in current scope."
                )
            print("RHS variable ID", rhs_var_id)
            # If the right-hand side is a variable, we need to check if it is usable
            if not self.check_var_usable(rhs_var_id):
                raise ValueError(
                    f"Variable '{node.expr.name}' has been moved and is not accessible."
                )

    def visit_Assignment(self, node: ast.Assignment):
        print("=== Assignment", node.id.name, "=", node.expr, "===")

        # in case of "let b = Box(1); let a = b;" we need to see that "b" has been moved and should go out of scope
        lhs = node.id
        rhs = node.expr
        self.visit(rhs)
        self.visit(lhs)

        lhs_var_id = self.id_by_varname(lhs.name)
        if lhs_var_id is None:
            raise ValueError(f"Variable '{lhs.name}' not found in current scope.")

        lhs_var = self.find_var(lhs_var_id)
        if lhs_var is None:
            raise ValueError(f"Variable '{lhs.name}' not found in current scope.")

        print("LHS variable", lhs_var)

        # create new Variable for the right hand side
        # map the variable name to the new ID
        if not is_box_type(lhs_var.type):
            return

        flag_cleanup = False

        print(rhs)

        if is_variable(rhs):
            rhs_var_id = self.id_by_varname(rhs.name)
            if rhs_var_id is None:
                raise ValueError(f"Variable '{rhs.name}' not found in current scope.")
            print("RHS variable ID", rhs_var_id)

            # add free call afer current statement:
            # Mark the old id (left) as cleaned
            lhs_var.status = "out"
            flag_cleanup = True
            # move the variable to the new ID
            rhs_var = self.find_var(rhs_var_id)
            rhs_var.current_name = lhs.name

        elif is_box_alloc(rhs):
            # If the left-hand side is a box type, we need to track it
            rhs_var = self.track_var(
                name=lhs.name,
                type=lhs_var.type,
                status="in",
                source="local",
            )

            lhs_var.status = "out"
            flag_cleanup = True
        else:
            raise ValueError("Unsupported RHS")

        if flag_cleanup:
            self.current_block.statements.insert(
                self.current_block.statements.index(node),
                ast.Cleanup(ast.Id(lhs.name)),
            )
            print("Cleanup for", lhs.name, "added to block")
        print("=== End Assignment ===")

    def visit_Cleanup(self, node: ast.Cleanup):
        return

    def visit_Id(self, node: ast.Id):
        print("Visiting Id", node.name)

        # Check if the variable is in the current scope
        if var := self.find_var(node.name):
            print("Found variable", node.name, "with status", var["status"])
            if var["status"] != "in":
                raise ValueError(
                    f"Variable '{node.name}' has been moved and is not accessible."
                )

    def visit_BinaryExpr(self, node: ast.BinaryExpr):
        """
        If the left or right operand is a box type, we need to check if it is safe to use.
        If it is a box type, we need to mark it for cleanup if it is not already marked.
        """
        print("Visiting BinaryExpr", node.left, node.operator, node.right)

        # Visit the left and right operands
        self.visit(node.left)
        self.visit(node.right)

    def visit_Dereference(self, node: ast.Dereference):
        self.visit(node.expr)

    def visit_Return(self, node: ast.Return):
        logger.start_span("visit_Return")
        """
        If the return value is a box type, it is safe.
        """
        # Visit the expression being returned
        self.visit(node.expr)

        if is_box_type(node.type):
            if is_variable(node.expr):
                if var := self.find_var(self.id_by_varname(node.expr.name)):
                    # Mark the old value for cleanup
                    var.status = "out"
                    var.current_name = None
                    print("Return", node.expr.name, "is moved to", node.expr.name)

        return_statement_index = self.current_block.statements.index(node)

        print("=== Return ===")

        print(self.scope_var_tracker[-1])

        for var_id, var_info in self.scope_var_tracker[-1].items():
            if var_info.status == "in":
                print(f"Variable {var_id} ({var_info.first_name}) is still in scope.")
                # clean up the variable
                self.current_block.statements.insert(
                    return_statement_index,
                    ast.Cleanup(ast.Id(var_info.current_name)),
                )
        print("=== End Return ===")

    def check_var_usable(self, var_id: str):
        var: Variable = self.find_var(var_id)
        return var is not None and var.status in ["in"]


def is_box_type(type: ast.Type):
    return type.typename == "Box"


def is_variable(node: ast.ASTObject):
    if isinstance(node, ast.Id):
        return True

    # TODO Expressions?

    return False


def is_box_alloc(node: ast.ASTObject):
    if isinstance(node, ast.Call):
        if isinstance(node.name, ast.Id):
            # Check if the call is to the Box constructor
            if node.name.name == "Box" and len(node.args) == 1:
                return True
        return node.name == "Box"

    return False


def is_call(node: ast.ASTObject):
    if isinstance(node, ast.Call):
        return True

    return False
