from abc import ABC, ABCMeta, abstractmethod

from src import cgen
from src.context import Context
from src.error import throw_compiler_error
from src.nodes.utils import printlog


def resolve_with_scope(type_from_scope, scope):
    if isinstance(type_from_scope, UnresolvedType):

        type_from_scope = scope.find(type_from_scope.name)
        print("type from scope", type_from_scope)
        if not type_from_scope:
            throw_compiler_error(f'Could not resolve type {
                                 type_from_scope.name}. Did you forget to declare it?')
        type_from_scope = type_from_scope.type

    if isinstance(type_from_scope, ReferenceType):
        type_from_scope.to = resolve_with_scope(type_from_scope.to, scope)

    print("resolved type", type_from_scope)
    return type_from_scope


class UnknownType(object):
    def __repr__(self):
        return "T(Unknown)"


class TType(object):
    def __init__(self, t) -> None:
        self.t = t

    def __repr__(self):
        return "T(T)"

    def equal_to(self, other):
        if not isinstance(other, TType):
            return False
        if isinstance(self.t, UnknownType) or isinstance(other.t, UnknownType):
            throw_compiler_error("T Type shit hit the fan")
        return self.t == other.t


class AnyType(object):
    def __repr__(self):
        return "T(Any)"

    def equal_to(self, other):
        return True

    def to_c(self):
        return "void"


class ReferenceType(object):
    def __init__(self, to, is_mutable=False, scope="local"):
        self.to = to
        self.is_mutable = is_mutable
        self.scope = scope

    def __repr__(self):
        return f"RefT({self.to})"

    def to_c(self):
        return f"{self.to.to_c()}*"

    def equal_to(self, other):
        if not isinstance(other, ReferenceType):
            return False
        if not self.to or not other.to:
            raise Exception("Hey stupid, you have a reference to nothing")
        return type(other) == ReferenceType and self.to.equal_to(other.to)


class MaybeType(object):
    def __init__(self, ok_type):
        self.ok_type = ok_type

    def __repr__(self):
        return f"T(Maybe({self.ok_type}))"


class TypeBase(ABC):
    @abstractmethod
    def to_c(self):
        pass

    @abstractmethod
    def equal_to(self, other):
        raise Exception("Unimplemented Equal to")


class UnresolvedType(TypeBase):
    def __init__(self, name: str):
        self.name = name

    def resolve(self):
        if self.name == "i32":
            return IntType(32)
        if self.name == "str":
            return LocalStringType(None)
        else:
            return UnresolvedType(self.name)

    def __repr__(self):
        return f"T_unres({self.name})"

    def to_c(self):
        raise Exception("Cannot convert unresolved type to C")

    def equal_to(self, other):
        raise Exception("Cannot compare unresolved type")


class IntType(object):
    def __init__(self, size):
        self.size = size

    def __repr__(self):
        return f"T(i{self.size})"

    def to_c(self):
        if self.size == 8:
            return "char"
        elif self.size == 16:
            return "short"
        elif self.size == 32:
            return "int"
        elif self.size == 64:
            return "long"
        else:
            raise Exception("Invalid int size")

    def equal_to(self, other):
        return type(other) == IntType and self.size == other.size


class LocalStringType(TypeBase):
    def __init__(self, size):
        self.size = size

    def __repr__(self):
        return f"T_str({self.size}))"

    def to_c(self):
        return f"_pt_str"

    def equal_to(self, other):
        return type(other) == LocalStringType


class FunctionType(object):
    def __init__(self, return_type: TypeBase, params: list[TypeBase]):
        self.return_type = return_type
        self.params = params

    def __repr__(self):
        print("params are", self.params)
        return f"({",".join([param.__repr__() for param in self.params])}) -> {self.return_type}"

    def equal_to(self, other):
        if type(other) != FunctionType:
            return False
        if not self.return_type.equal_to(other.return_type):
            return False
        if len(self.params) != len(other.params):
            return False
        for i in range(len(self.params)):
            if not self.params[i].equal_to(other.params[i]):
                return False
        return True


def parse_type(_type: str):
    print("parsing type ", _type, type(_type))
    if _type == "i32":
        return IntType(32)
    else:
        raise Exception(f"Invalid type {_type}")


class StructType(object):
    def __init__(self, name, fields: dict[str, TypeBase]):
        self.name = name
        self.fields = fields

    def __repr__(self):
        return f"Struct({self.name}, {self.fields})"

    def to_c(self):
        return f"struct {self.name} {{\n{self.fields}\n}}"

    def equal_to(self, other):
        # return type(other) == StructTypes and self.name == other.name
        return True

    def has_member(self, member_name):
        return member_name in self.fields

    def get_member(self, member_name):
        return self.fields[member_name]

    def to_c(self):
        return f"struct {self.name}"


class VoidType(object):
    def __repr__(self):
        return "T(void)"

    def to_c(self):
        return "void"

    def equal_to(self, other):
        return type(other) == VoidType


class ShallowStructType(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"ShallowStruct({self.name})"

    def to_c(self):
        return f"struct {self.name}"

    def equal_to(self, other):
        return type(other) == ShallowStructType and self.name == other.name
