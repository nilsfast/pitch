from abc import ABC, ABCMeta, abstractmethod
import re

from src import cgen
from src.context import Context
from src.error import throw_compiler_error
from src.nodes.utils import printlog


def resolve_with_scope(type, scope):
    if isinstance(type, UnresolvedType):
        type = scope.find(type.name)
        if not type:
            throw_compiler_error(f'Could not resolve type {
                                 type.name}. Did you forget to declare it?')
        type = type.type

    if isinstance(type, ReferenceType):
        type.to = resolve_with_scope(type.to, scope)

    return type


class UnknownType(object):
    def __repr__(self):
        return "T(Unknown)"


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
        if not self.to or not other.to:
            throw_compiler_error("Hey stupid, you have a reference to nothing")
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
        throw_compiler_error("Unimplemented equal to")


class UnresolvedType(TypeBase):
    def __init__(self, name: str):
        self.name = name

    def resolve(self):

        if re.match(r"i\d+", self.name):
            return IntType(int(self.name[1:]))
        if re.match(r"u\d+", self.name):
            return UnsigendIntType(int(self.name[1:]))
        if self.name == "str":
            return LocalStringType(None)
        if self.name == "void":
            return VoidType()
        else:
            return UnresolvedType(self.name)

    def __repr__(self):
        return f"T_unres({self.name})"

    def to_c(self):
        throw_compiler_error("Cannot convert unresolved type to C")

    def equal_to(self, other):
        throw_compiler_error("Cannot compare unresolved type")


class IntType(object):
    def __init__(self, size):
        self.size = size

    def __repr__(self):
        return f"T(i{self.size})"

    def to_c(self):
        if self.size == 8:
            return "int8_t"
        elif self.size == 16:
            return "int16_t"
        elif self.size == 32:
            return "int32_t"
        elif self.size == 64:
            return "int64_t"
        else:
            throw_compiler_error("Invalid int size, must be 8, 16, 32 or 64")

    def equal_to(self, other):
        return type(other) == IntType and self.size == other.size


class UnsigendIntType(object):
    def __init__(self, size):
        self.size = size

    def __repr__(self):
        return f"T(u{self.size})"

    def to_c(self):
        if self.size == 8:
            return "uint8_t"
        elif self.size == 16:
            return "uint16_t"
        elif self.size == 32:
            return "uint32_t"
        elif self.size == 64:
            return "uint64_t"
        else:
            throw_compiler_error("Invalid uint size, must be 8, 16, 32 or 64")

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
        printlog("params are", self.params)
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
