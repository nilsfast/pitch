from abc import abstractmethod
from ast import Expression
from src.error import throw_compiler_error
from src.nodes.expressions import ExpressionBase
from src.nodes.statements import ArgumentList
from src.pitchtypes import TypeBase
from src.scope import Scope, ScopeEntry
from src.nodes.utils import printlog, Base


class PreprocessorBase(Base):
    @abstractmethod
    def preprocess(self, definitions):
        pass


class DefStatement():

    def __init__(self, id: str):
        self.id = id

    def __repr__(self):
        return f'DefStatement({self.id=})'

    def fill_types(self, scope):
        pass

    def type_check(self, scope):
        pass

    def to_c(self, level=0):
        return ""

    def preprocess(self, definitions):
        definitions[self.id] = None


class DefDefinition():

    def __init__(self, id: str, def_for: str, expression: Expression):
        self.id = id
        self.def_for = def_for
        self.expression = expression

    def __repr__(self):
        return f'DefDefinition({self.id=}, {self.def_for=}, {self.expression=})'

    def fill_types(self, scope):
        pass

    def type_check(self, scope):
        pass

    def to_c(self, level=0):
        return ""

    def preprocess(self, definitions):
        definitions[f"{self.def_for}.{self.id}"] = self.expression.value.replace(
            '"', '')


class CompCall(ExpressionBase):

    TYPES = {"print_i": "void"}

    def __init__(self, id: str, arguments: ArgumentList):
        self.id = id
        self.arguments = arguments
        self.t: TypeBase = None

    def __repr__(self):
        return f'CompCall({repr(self.id)}, {repr(self.arguments)})'

    def compute_type(self, scope):
        self.t = self.TYPES[self.id]
        # self.arguments.fill_types(scope)
        return self.t

    def to_c(self):
        match self.id:
            case "print_i":
                return f'printf("%d\\n", {self.arguments.to_c()})'
