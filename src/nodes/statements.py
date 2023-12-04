from abc import abstractmethod
from src.context import ContextVar
from src.error import throw_compiler_error
from src.nodes.expressions import Expression, ExpressionBase
from src.pitchtypes import FunctionType, IntType, LocalStringType, ReferenceType, TypeBase, UnknownType, parse_type
from src.scope import Scope
import src.cgen as cgen
from src.nodes.utils import printlog, Base


class StatementBase(Base):
    @abstractmethod
    def populate_scope(self, scope, block):
        pass

    @abstractmethod
    def check_references(self, context):
        pass

    @abstractmethod
    def generate_c(self, writer: cgen.CWriter, context) -> str:
        pass


class ExpressionStatement(StatementBase):
    def __init__(self, expression: ExpressionBase):
        self.expression = expression

    def __repr__(self):
        return f'ExprStmt(expr={self.expression})'

    def populate_scope(self, scope: Scope, block):
        self.expression.compute_type(scope, block)

    def to_c(self):
        return f'{self.expression.to_c()};'

    def check_references(self, context):
        print("checking referencess...")


class StatementList(Base):
    def __init__(self, statements: list[StatementBase]):
        self.statements = statements

    def __repr__(self):
        return f'StatementList(statements={repr(self.statements)}))'

    def append(self, statement: StatementBase):
        self.statements.append(statement)
        return self

    def find(self, id):
        matches = []
        for statement in self.statements:
            if statement.__class__.__name__ == "If":
                matches += statement.find(id)
            if statement.__class__.__name__ == id:
                matches.append(statement)
        return matches

    def populate_scope(self, scope, block):
        for statement in self.statements:
            statement.populate_scope(scope, block)

    def to_c(self, level=0):
        return "    "*level + f'\n{"    "*level}'.join([statement.to_c() for statement in self.statements])

    def check_references(self, context):
        for statement in self.statements:
            print("ctx", context)
            statement.check_references(context)
        print("ctx", context)


class Return(StatementBase):

    def __init__(self, expression: Expression):
        self.expression = expression

    def __repr__(self):
        return f'Return({repr(self.expression)}, {repr(self.expression.t)})'

    def populate_scope(self, scope: Scope, block):
        block.returns = True
        expression_type = self.expression.compute_type(scope)
        block.parent_function.return_types.append(expression_type)

        if isinstance(self.expression.t, ReferenceType) and self.expression.t.scope == "local":
            throw_compiler_error(
                f'Cannot return reference type {self.expression.t}')

    def generate_c(self, writer, context):
        writer.append_statement(
            f'return {self.expression.generate_c(writer, context, "return")};')

    def check_references(self, context):
        print("return issue")


class Assignment(StatementBase):

    def __init__(self, id: str, expression: Expression, type=None):
        self.id = id
        self.t: TypeBase = type  # TODO rename var type
        self.expression = expression

    def __repr__(self):
        return f'Assignment(id={self.id}, t={self.t}, {self.expression})'

    def populate_scope(self, scope: Scope, block):
        expression_type = self.expression.compute_type(scope)
        # check types.

        if isinstance(self.t, UnknownType):
            printlog("inferred type for", self.id, "as", expression_type)
            self.t = expression_type
        elif not self.t.equal_to(expression_type):
            throw_compiler_error(
                f'Identifier "{self.id}" type does not match expression type')
        else:
            printlog("type matches", self.t, expression_type)
            self.t = expression_type
        scope.add(self.id, expression_type)
        return expression_type

    def generate_c(self, writer: cgen.CWriter, context):

        printlog("Generating c for assignment",
                 self.id, self.t, writer, context)

        writer.append_statement(data=f'{self.t.to_c()} {self.id} = {
            self.expression.generate_c(writer, context, "assignment")};')

    def check_references(self, context):
        context.add(self.id, ContextVar(liveness=0, scope="local"))
        print("checking referencess...")


class Reassignment(StatementBase):
    def __init__(self, id: str, expression: Expression):
        self.id = id
        self.expression = expression

    def __repr__(self):
        return f'Reassignment({self.id=}, {self.expression=})'

    def populate_scope(self, scope: Scope, block):
        if not scope.find(self.id):
            throw_compiler_error(f'Identifier "{self.id}" not found')
        # changing types not allowed, therefore no update to the scope required
        pass

    def check_types(self, scope: Scope):
        if not scope.find(self.id):
            throw_compiler_error(f'Identifier "{self.id}" not found')
        if scope.find(self.id).type != self.expression.t:
            throw_compiler_error(
                f'Identifier "{self.id}" type does not match expression type')

    def generate_c(self, writer, context):
        return cgen.CStatement(data=f'{self.id} = {self.expression.generate_c(writer, context, "reassignment")};')

    def check_references(self, context):
        print("checking referencess...")


class ArgumentList():

    def __init__(self, expressions: list[Expression]):
        self.expressions = expressions

    def __repr__(self):
        return f'ArgumentList({self.expressions})'

    def append(self, expression: Expression):
        self.expressions.append(expression)
        return self

    def generate_c(self, writer, context):
        return ", ".join([expression.generate_c(writer, context) for expression in self.expressions])


class Call(ExpressionBase):

    def __init__(self, id: str, args=None):
        self.id = id
        self.args: ArgumentList = args
        self.t: FunctionType = None

    def __repr__(self):
        return f'Call({repr(self.id)}, {repr(self.args)})'

    def compute_type(self, scope: Scope):
        printlog("Computing call type")
        arg_types = []
        if self.args:
            for arg in self.args.expressions:
                arg_type = arg.compute_type(scope)
                arg_types.append(arg_type)
        printlog("Call with arg types", arg_types)
        # Return type
        # Look for own type signature in scope
        if not scope.find(self.id):
            raise Exception(f'Function "{self.id}" not found')

        self.t = scope.find(self.id).type
        printlog("Call return type", self.t)

        return self.t.return_type

    def generate_c(self, writer, context):
        if self.args:
            print("function has args, passing those")
            return f'{self.id}({self.args.generate_c(writer, context)})'
        else:
            return f'{self.id}(void)'
