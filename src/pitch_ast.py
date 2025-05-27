from dataclasses import dataclass

from base import ASTObject


@dataclass
class TypeBase(ASTObject):
    typename: str
    nullable: bool = False


@dataclass
class BaseType(TypeBase):
    pass


@dataclass
class Type(TypeBase):
    of: TypeBase = None


@dataclass
class Param(ASTObject):
    name: str
    type: Type


@dataclass
class Block(ASTObject):
    statements: list[ASTObject]
    symbols: dict = None


@dataclass
class Function(ASTObject):
    name: str
    params: list[Param]
    return_type: Type
    body: Block


@dataclass
class Program(ASTObject):
    functions: list[Function]
    symbols: dict = None


@dataclass
class Cleanup(ASTObject):
    identifier: id


@dataclass
class Id(ASTObject):
    name: str

    type: Type = None

    def __str__(self):
        return self.name


@dataclass
class Assignment(ASTObject):
    id: Id
    expr: ASTObject


@dataclass
class VarDecl(ASTObject):
    id: Id
    type: Type
    expr: ASTObject


@dataclass
class Literal(ASTObject):
    value: str


@dataclass
class NumberLiteral(ASTObject):
    value: str


@dataclass
class BinaryExpr(ASTObject):
    left: ASTObject
    operator: str
    right: ASTObject


@dataclass
class UnaryExpr(ASTObject):
    operator: str
    operand: ASTObject


@dataclass
class GroupedExpr(ASTObject):
    expr: ASTObject


@dataclass
class Return(ASTObject):
    expr: ASTObject
    type: Type = None


@dataclass
class Call(ASTObject):
    name: str
    args: list[ASTObject]


@dataclass
class StringLiteral(ASTObject):
    value: str


@dataclass
class Reference(ASTObject):
    name: str


@dataclass
class Dereference(ASTObject):
    expr: ASTObject
    inner_type: Type = None
