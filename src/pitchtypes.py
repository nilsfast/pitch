from abc import ABC, ABCMeta, abstractmethod


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

    def __repr__(self):
        return f"T({self.name})"

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
        return type(other) == LocalStringType and self.size == other.size


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
