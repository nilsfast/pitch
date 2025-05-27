

from abc import ABC

from src.pitchtypes import AnyType, FunctionType, IntType, ReferenceType, TType


class LibFunction(ABC):
    def __init__(self, name, t):
        self.name = name
        self.t = t

    def __str__(self):
        return self.name + "(" + ", ".join(self.args) + ")"

    def __repr__(self):
        return self.__str__()

    @classmethod
    def to_c(self, args):
        pass


class Alloc(LibFunction):
    def __init__(self):
        super().__init__("alloc", FunctionType(
            ReferenceType(TType("T")), [ReferenceType(TType("T")), IntType(32)]))

    @classmethod
    def to_c(self, args):
        return f"alloc({args[0]})"
