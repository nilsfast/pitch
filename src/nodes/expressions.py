from abc import ABC, abstractmethod, abstractproperty
from src.context import Context, ContextVar
from src.error import throw_compiler_error
from src.pitchtypes import FunctionType, IntType, LocalStringType, ReferenceType, StructType, TypeBase, UnknownType
from src.scope import Scope, ScopeEntry
import src.cgen as cgen
from src.nodes.utils import printlog, Base


class ExpressionBase(Base):
    @abstractmethod
    def compute_type(self, scope):
        pass

    @abstractmethod
    def generate_c(self, writer: cgen.CWriter, context: Context, role=None) -> str:
        pass

    @abstractmethod
    def evaluates_to(self):
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

    def generate_c(self, writer: cgen.CWriter, context: Context, role=None):
        return f'{self.left.generate_c(writer, context)} {self.operator} {self.right.generate_c(writer, context)}'

    def evaluates_to(self):
        return "value"


class Group(Expression):
    def __init__(self, expression: ExpressionBase):
        self.expression = expression
        self.t: TypeBase = None

    def __repr__(self):
        return f'Group({self.expression})'

    def compute_type(self, scope):
        self.t = self.expression.compute_type(scope)
        return self.t

    def generate_c(self, writer: cgen.CWriter, context: Context, role=None):
        return f'({self.expression.generate_c(writer, context)})'

    def evaluates_to(self):
        return self.expression.evaluates_to()


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

    def generate_c(self, writer: cgen.CWriter, context: Context, role=None):
        return str(self.value)

    def evaluates_to(self):
        return "value"


class String(ExpressionBase):
    def __init__(self, value: str):
        self.value = value.replace('"', '')
        self.t: LocalStringType = None

    def __repr__(self):
        return f'String(value={self.value})'

    def compute_type(self, scope):
        self.t = LocalStringType(len(self.value))
        return self.t

    def generate_c(self, writer: cgen.CWriter, context: Context, role=None):
        writer.append_statement(f"// {role}")
        # Add factory
        # return self.t.generate_c_static(self.value, )
        return cgen.PitchString(self.value, self.t.size).to_const(writer, context)

    def evaluates_to(self):
        return "value"


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

    def generate_c(self, writer: cgen.CWriter, context: Context, role=None):
        return self.id

    def evaluates_to(self):
        return "identifier"


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

    def generate_c(self, writer: cgen.CWriter, context: Context, role=None):
        return f'&{self.id.generate_c(writer, context)}'

    def evaluates_to(self):
        return "reference"


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

    def generate_c(self, writer: cgen.CWriter, context: Context, role=None):
        return f'*{self.id.generate_c(writer, context)}'

    def evaluates_to(self):
        return "identifier"


class FieldDereference(ExpressionBase):
    def __init__(self, expression: ExpressionBase, field: str):
        self.expression = expression
        self.field = field
        self.t: TypeBase = None

    def __repr__(self):
        return f'FieldDereference({self.expression}, {self.field})'

    def compute_type(self, scope):
        ref_struct_type = self.expression.compute_type(scope)
        printlog("Ref struct type", ref_struct_type)

        if not isinstance(ref_struct_type, ReferenceType):
            throw_compiler_error(
                f'Cannot dereference non-reference type {ref_struct_type}')

        struct_type: StructType = ref_struct_type.to
        printlog("Struct type", struct_type)

        if not isinstance(struct_type, StructType):
            throw_compiler_error(
                f'Cannot dereference non-struct type {struct_type}')

        if not struct_type.has_member(self.field):
            throw_compiler_error(
                f'Struct "{struct_type.id}" does not have member "{self.field}"')

        field_type = struct_type.get_member(self.field)

        self.t = field_type
        return self.t

    def generate_c(self, writer: cgen.CWriter, context: Context, role=None):
        return f'{self.expression.generate_c(writer, context)}->{self.field}'

    def evaluates_to(self):
        return "identifier"


class StructInitMember(ExpressionBase):
    def __init__(self, id: str, expression: ExpressionBase):
        self.id = id
        self.value = expression
        self.t: TypeBase = None

    def __repr__(self):
        return f'StructInitMember({self.id}, {self.value})'

    def compute_type(self, scope):
        pass

    def generate_c(self, writer: cgen.CWriter, context: Context, role=None):
        pass

    def evaluates_to(self):
        return "identifier"


class StructInit(ExpressionBase):
    def __init__(self, id: str, members: list):
        self.id = id
        self.members = members
        self.t: TypeBase = None

    def __repr__(self):
        return f'StructInitializer({self.id}, {self.members})'

    def compute_type(self, scope: Scope):

        for memeber in self.members:
            memeber.value.compute_type(scope)

        struct_init_type = scope.find(self.id)
        if not struct_init_type:
            throw_compiler_error(f'Identifier "{self.id}" not found')
        self.t = struct_init_type.type
        return self.t

    def generate_c(self, writer: cgen.CWriter, context: Context, role=None) -> str:
        struct_member_c = []
        for member in self.members:
            struct_member_c.append(
                f'.{member.id}={member.value.generate_c(writer, context, role="struct.init")}')
        return f"(struct {self.id}){{ {", ".join(struct_member_c)} }}"

    def evaluates_to(self):
        return "identifier"
