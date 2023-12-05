from weakref import ReferenceType
from src import cgen
from src.nodes.utils import Base
from src.pitchtypes import FunctionType, StructType,  TypeBase, UnresolvedType, VoidType, resolve_with_scope
from src.error import throw_compiler_error
from src.nodes.expressions import Expression
from src.nodes.statements import StatementBase, StatementList
from src.nodes.utils import printlog
from src.scope import Scope, ScopeEntry


class Parameter():
    def __init__(self, type: str, id: str):
        printlog("init param", type, id)
        self.type: TypeBase = type
        self.id = id

    def __repr__(self):
        return f'{self.id=}: {self.type=}'

    def compute_type(self, scope: Scope):
        type = resolve_with_scope(self.type, scope)
        if not type:
            throw_compiler_error(f'Could not resolve type {self.type.id}')
        return type


class ParameterList(Base):
    def __init__(self, parameters: list[Parameter]):
        self.parameters = parameters

    def __repr__(self):
        return f'ParameterList({self.parameters=})'

    def append(self, parameter: str):
        self.parameters.append(parameter)
        return self

    def generate_c(self, writer, context):
        return ", ".join([f'{parameter.type.to_c()} {parameter.id}' for parameter in self.parameters])


class Block(Base):
    def __init__(self, statement_list: StatementList, parent_function=None) -> None:
        self.statement_list: StatementList = statement_list
        self.parent_function: Function = parent_function
        self.scope = None
        self.returns = False

    def populate_scope(self, scope, block, inject=None):

        if not self.parent_function:
            self.parent_function: Function = block.parent_function

        self.scope = Scope("__block__", scope, inject=inject)
        self.statement_list.populate_scope(self.scope, self)
        printlog(f"Block scope after pop {
            self.scope}, {self.scope.parent}")

    def find(self, id):
        return self.statement_list.find(id)

    def prepend(self, statement: StatementBase):
        self.statement_list.statements.insert(0, statement)
        return self

    def append(self, statement: StatementBase):
        self.statement_list.statements.append(statement)
        return self

    def insert_before(self, statement: StatementBase, before: StatementBase):
        index = self.statement_list.statements.index(before)
        self.statement_list.statements.insert(index, statement)
        return self

    def insert_after(self, statement: StatementBase, after: StatementBase):
        index = self.statement_list.statements.index(after)
        self.statement_list.statements.insert(index+1, statement)
        return self

    def __repr__(self):
        return f'Block({repr(self.statement_list)}, ret={repr(self.returns)})'

    def generate_c(self, writer: cgen.CWriter, context):
        for statement in self.statement_list.statements:
            statement.generate_c(writer, context)
            printlog("statement", statement)
        printlog(writer.statements)

    def check_references(self, context):
        self.statement_list.check_references(context)


class NamedBlock(Base):
    def __init__(self, name: str, block: Block):
        self.name = name
        self.block = block

    def __repr__(self):
        return f'NamedBlock({self.name=}, {self.block=})'

    def populate_scope(self, scope, block):
        self.block.populate_scope(scope, block)

    def find(self, id):
        return self.block.find(id)

    def generate_c(self, writer, context):
        self.block.generate_c(writer, context)


class Function(Base):
    def __init__(self, id: str, params: ParameterList | None, return_type: str,  block: Block):
        self.id = id
        self.return_type: TypeBase = return_type
        self.params = params
        self.block: Block = block
        self.scope = None
        self.return_types = []
        if not self.params:
            self.params = ParameterList([])

    def __repr__(self):
        return f'Function(id={repr(self.id)}, ret={repr(self.return_type)}, params={repr(self.params)}, block={repr(self.block)})'

    def populate_scope(self, scope):
        printlog("populating scope for function",
                 self.id, self.return_type)
        self.block.parent_function = self
        printlog("params", self.params)

        if self.params:
            for param in self.params.parameters:
                param.compute_type(scope)
            param_types = [param.type
                           for param in self.params.parameters]

        # TODO determine return types first
        # TODO check if the types are recurisve

        scope.add(self.id, FunctionType(
            self.return_type, param_types if self.params else []))

        scope_injections: list[ScopeEntry] = []
        if self.params:
            for param in self.params.parameters:
                scope_injections.append(ScopeEntry(param.id, param.type))

        self.block.populate_scope(scope, self.block, inject=scope_injections)

        printlog(self.return_types)

        if isinstance(self.return_type, VoidType):
            return

        if len(self.return_types) == 0:
            throw_compiler_error(
                f'Function "{self.id}" does not return anything')

        # Check if all possible returnt types are the same

        if len(set(self.return_types)) > 1:
            throw_compiler_error(
                f'Function "{self.id}" has multiple return types')

        if not self.return_type.equal_to(self.return_types[0]):
            throw_compiler_error(
                f'Function "{self.id}" has return type {self.return_types[0]}, but declared as {self.return_type}')
        self.return_type = self.return_types[0]
        printlog(f"Done with function {self.id}, return type {
                 self.return_type} {self.return_types}")

    def generate_c(self, top_level_writer: cgen.CWriter, context) -> cgen.CFunction:
        printlog("C ing function")
        # Maybe make a function writer and let the function arguments do stuff in the body
        c_function = cgen.CFunction(
            name=self.id, return_type=self.return_type.to_c(), args=self.params.generate_c(top_level_writer, context), root=None, parent=None
        )
        function_writer = cgen.CWriter(top_level_writer)

        self.block.generate_c(function_writer, context)

        c_function.body.statements = function_writer.export()

        top_level_writer.append(c_function)
        printlog("writer", function_writer.statements)

    def check_references(self, context):
        self.block.check_references(context)


class If(StatementBase):

    def __init__(self, condition: Expression, block: Block):
        self.condition = condition
        self.block = block

    def __repr__(self):
        return f'If({self.condition=}, {self.block=})'

    def populate_scope(self, scope: Scope, block):
        self.condition.compute_type(scope)
        # TODO check if expression type == bool
        self.block.populate_scope(scope, block)

    def find(self, id):
        return self.block.find(id)

    def generate_c(self, level=0):
        return f'if ({self.condition.to_c()}) {{\n{self.block.to_c(level+1)}\n{"    "*(level+1)}}}'

    def check_references(self, context):
        printlog("checking referencess...")


class StructMember(Base):
    def __init__(self, type: str, id: str):
        printlog(id,  type)
        self.type: TypeBase = type
        self.id = id

    def compute_type(self, scope: Scope):
        if isinstance(self.type, UnresolvedType):
            type = scope.find(self.type.name)
            if not type:
                throw_compiler_error(
                    f'Could not resolve type {self.type.id}')
            self.type = type.type

        return self.type

    def __repr__(self):
        return f'{self.id=}: {self.type=}'


class Struct(Base):
    def __init__(self, id: str, members):
        self.id = id
        self.member_list: list[StructMember] = members

    def __repr__(self):
        return f'Struct({self.id}, {self.member_list})'

    def populate_scope(self, scope: Scope):

        printlog("POPULATE SCOPE STRUCT")
        printlog(self.member_list)
        member_types = {}
        for member in self.member_list:
            member_types[member.id] = member.compute_type(scope)
        struct_type = StructType(self.id, member_types)
        scope.add(self.id, struct_type)
        printlog("struct type", struct_type)

    def generate_c(self, top_level_writer: cgen.CWriter, context):
        member_list_c = "\n    ".join(
            [f'{member.type.to_c()} {member.id};' for member in self.member_list])
        top_level_writer.append_statement(
            f'struct {self.id} {{\n    {member_list_c}\n}};')
