from dataclasses import dataclass
from codegen import Assignment, Function, Number, Block, NoOp, Return, Variable, Call, String
from util.type_manager import BaseType

@dataclass
class Statement():
    cmp: ...

    def specify(self):
        c = self.cmp
        match c:
            case [Symbol(val='fn'), Symbol(val=_), List(items=_), Symbol(val=_), NBlock(stm=_)]:
                # Function definition
                print("YES")
                return Function(c[1].val, [], c[3].to_type(), c[4].specify())
            case [Symbol(val='var'), Symbol(val=_), Symbol(val=_), _]:
                return Assignment(c[1].val, c[2].to_type(), c[3].specify())
            case [Symbol(val=_), List(items=_)]:
                return Call(c[0].val, c[1].as_arguments())
            case [Symbol(val='return'), _]:
                return Return(c[1].specify())
        return NoOp()


@dataclass
class NBlock():
    stm: ...
    def specify(self):
        return Block('entry',[s.specify() for s in self.stm])          

@dataclass
class Num():
    val: ...
    def specify(self):
        return Number(self.val)


@dataclass
class Str():
    val: ...

    def specify(self):
        return String(self.val) 

@dataclass
class Symbol():
    val: ...

    def specify(self):
        return Variable(self.val)

    def to_type(self):
        return BaseType([self.val]).resolve()

@dataclass
class List():
    items: ...

    def as_arguments(self):
        return [i.specify() for i in self.items]