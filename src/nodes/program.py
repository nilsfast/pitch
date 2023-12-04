
from src import cgen
from src.context import Context
from src.nodes.utils import Base
from src.nodes.block import Function
from src.nodes.preprocessor import PreprocessorBase
from src.scope import Scope


class Program(Base):

    def __init__(self, statements: list):
        # TODO add var statements. Do preprocessing. then make var functions.
        self.statements = statements
        self.functions: list[Function] = []
        self.preprocessor_statements: list[PreprocessorBase] = None
        self.scope = None

    def append(self, statement):
        self.statements.append(statement)
        return self

    def __repr__(self) -> str:
        return f'Program({repr(self.statements)})'

    def preprocess(self, definitions):
        for statement in self.statements:
            if isinstance(statement, PreprocessorBase):
                statement.preprocess(definitions)
            elif isinstance(statement, Function):
                self.functions.append(statement)

    def populate_scope(self):
        assert (len(self.functions) > 0)
        self.scope = Scope("__program__")
        for stm in self.statements:
            stm.populate_scope(self.scope)

    def generate_c(self):
        top_level = cgen.CProgram()
        top_level_writer = cgen.CWriter()
        context = Context()
        for statement in self.statements:
            statement.generate_c(top_level_writer, context)

        top_level.set_statement(top_level_writer.export())

        return top_level

    def check_references(self, context):
        for function in self.functions:
            function.block.check_references(context)
