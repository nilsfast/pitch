from src import cgen
from src.nodes import Base
from src.pitchtypes import FunctionType, TypeBase
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


class ParameterList(Base):
    def __init__(self, parameters: list[Parameter]):
        self.parameters = parameters

    def __repr__(self):
        return f'ParameterList({self.parameters=})'

    def append(self, parameter: str):
        self.parameters.append(parameter)
        return self

    def generate_c(self, writer, context):
        return ", ".join([f'{parameter.type} {parameter.id}' for parameter in self.parameters])


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

    def generate_c(self, writer, context):
        # c_block = cgen.CBlock(root=root, parent=parent)
        # for statement in self.statement_list.statements:
        #    statement.generate_c(writer, context)
        # return c_block
        pass

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
        return self.block.generate_c(writer, context)


class Function(Base):
    def __init__(self, id: str, params: ParameterList | None, return_type: str,  block: Block):
        self.id = id
        self.return_type: TypeBase = return_type
        print("return type is", self.return_type)
        self.params = params
        self.block: Block = block
        self.scope = None
        self.return_types = []

    def __repr__(self):
        return f'Function(id={repr(self.id)}, ret={repr(self.return_type)}, params={repr(self.params)}, block={repr(self.block)})'

    def populate_scope(self, scope):
        printlog("populating scope for function",
                 self.id, self.return_type)
        self.block.parent_function = self
        printlog("params", self.params)

        if self.params:
            param_types = [param.type for param in self.params.parameters]

        scope.add(self.id, FunctionType(
            self.return_type, param_types if self.params else []))

        scope_injections: list[ScopeEntry] = []
        if self.params:
            for param in self.params.parameters:
                scope_injections.append(ScopeEntry(param.id, param.type))

        self.block.populate_scope(scope, self.block, inject=scope_injections)

        printlog(self.return_types)
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

        printlog(f"Done with function {self.id}")

    def generate_c(self, writer, context):
        #  params_as_c = "void"
        # if self.params:
        #     args_as_c = self.params.generate_c(None, None)
        # c_function = cgen.CFunction(
        #     name=self.id, return_type=self.return_type.to_c(), args=params_as_c, root=root, parent=parent
        # )
        # c_function.body = self.block.generate_c(writer, context)
        # return c_function
        pass

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
        print("checking referencess...")
