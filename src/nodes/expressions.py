from abc import ABC, abstractmethod, abstractproperty
from src.context import ContextVar
from src.error import throw_compiler_error
from src.pitchtypes import FunctionType, IntType, LocalStringType, ReferenceType, TypeBase, UnknownType, parse_type
from src.scope import Scope, ScopeEntry
import src.cgen as cgen
from src.nodes.utils import printlog, Base


class ExpressionBase(Base):
    @abstractmethod
    def compute_type(self, scope):
        pass

    @abstractmethod
    def generate_c(self, writer: cgen.CWriter, context) -> str:
        pass


class Expression(ExpressionBase):
    def __init__(self, left: ExpressionBase, right: ExpressionBase, operator: str):
        self.left = left
        self.right = right
        self.operator = operator
        self.t: TypeBase = None

    def __repr__(self):
        return f'Expr(l={self.left}, op={self.operator}, r={self.right}, t={self.t})'

    def compute_type(self, scope) -> TypeBase:
        # TODO check if types compatible
        self.t = self.left.compute_type(scope)
        return self.t

    def generate_c(self, writer, context):
        return f'{self.left.generate_c(writer, context)} {self.operator} {self.right.generate_c(writer, context)}'


class Group(Expression):
    def __init__(self, expression: ExpressionBase):
        self.expression = expression
        self.t: TypeBase = None

    def __repr__(self):
        return f'Group({self.expression})'

    def compute_type(self, scope):
        self.t = self.expression.compute_type(scope)
        return self.t

    def generate_c(self, writer, context):
        return f'({self.expression.generate_c(writer, context)})'


class Integer(ExpressionBase):
    def __init__(self, value: int, size: int):
        self.value = value
        self.size = size
        self.t: TypeBase = None

    def __repr__(self):
        return f'Int(value={self.value}, size={self.size})'

    def compute_type(self, scope):
        self.t = IntType(self.size)
        return self.t

    def generate_c(self, writer, context):
        return str(self.value)


class String(ExpressionBase):
    def __init__(self, value: str):
        self.value = value.replace('"', '')
        self.t: TypeBase = None

    def __repr__(self):
        return f'String(value={self.value})'

    def compute_type(self, scope):
        self.t = LocalStringType(len(self.value))
        return self.t

    def generate_c(self, writer, context):
        chars = self.value
        return "{"+",".join([f'"{char}"' for char in chars])+"}"


class Identifier(ExpressionBase):

    def __init__(self, id: str):
        self.id = id
        self.t: TypeBase = None

    def __repr__(self):
        return f'Identifier({self.id})'

    def compute_type(self, scope: Scope):
        if not scope.find(self.id):
            throw_compiler_error(f'Identifier "{self.id}" not found')
        self.t = scope.find(self.id).type
        return self.t

    def generate_c(self, writer, context):
        return self.id


class Reference(ExpressionBase):
    def __init__(self, id: str):
        self.id: Identifier = id
        self.t: TypeBase = None

    def __repr__(self):
        return f'Reference({self.id})'

    def compute_type(self, scope):
        # Check if there is pointer arithmetic going on
        self.t = ReferenceType(self.id.compute_type(scope))
        if isinstance(self.id, Expression):
            throw_compiler_error("Cannot reference expression")
        return self.t

    def generate_c(self, parent, root, statement=None):
        return f'&{self.id.generate_c(parent, root)}'


class Dereference(ExpressionBase):
    def __init__(self, id: str):
        self.id: Identifier = id
        self.t: TypeBase = None

    def __repr__(self):
        return f'Dereference({self.id})'

    def compute_type(self, scope):
        id_type: TypeBase = self.id.compute_type(scope)
        if id_type != ReferenceType:
            throw_compiler_error("Cannot dereference non-reference")
        assert isinstance(id_type, ReferenceType)
        self.t = id_type.to
        return self.t

    def generate_c(self, parent, root, statement=None):
        return f'*{self.id.generate_c(parent, root)}'
