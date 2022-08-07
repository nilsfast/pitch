from dataclasses import dataclass

@dataclass
class TypeSignature():
    ret: ...
    args: ...

@dataclass
class ArrayType():
    member_type: ...
    length: ...
    
    @property
    def str(self):
        return f"[{str(self.length)} x {self.member_type.str}]"

    def ptr_depth(o=0):
        return 0
    
    @property
    def memsize(self):
        return int(self.length) * self.member_type.memsize

@dataclass
class ArrType():
    pointer: ...
    member_type: ...
    size: ...
    allocated: ...
    
    @property
    def str(self):
        return f"[{str(int(self.size / self.member_type.memsize))} x {self.member_type.str}]"

    def ptr_depth(o=0):
        return 0
    
    @property
    def memsize(self):
        return int(self.length) * self.member_type.memsize

@dataclass
class StructType():
    name: ...
    members: ...
    
    @property
    def str(self):
        return f"%{self.name}"

    @property
    def sign_str(self):
        print("struct members", list(map(lambda t: t.str, self.members)))
        return f"{{{', '.join(list(map(lambda t: t.str, self.members)))}}}"
        

    def ptr_depth(o=0):
        return 0
    
    @property
    def memsize(self):
        return int(self.length) * self.member_type.memsize


@dataclass
class IntType():
    size: int

    @property
    def str(self):
        return f"i{self.size}"

    def ptr_depth(o=0):
        return 0
    
    @property
    def memsize(self):
        return self.size / 8


@dataclass
class Ref():
    to: ...

    @property
    def str(self):
        #return f"{self.to.str}*"
        return 'ptr'


    def ptr_depth(self, o=0):
        if type(self.to) != Ref:
            return o+1
        return self.to.ptr_depth(o=o+1)
    
    @property
    def memsize(self):
        return self.to.memsize 

@dataclass
class DynamicType():
    pass

    @property
    def str(self):
        return "..."


@dataclass
class NoType():
    pass

    def ptr_depth(o=0):
        return 0

@dataclass
class ResultType():
    pass

    def ptr_depth(o=0):
        return 0

    @property
    def str(self):
        return '%pitch.res'

@dataclass
class BaseType():
    t: ...
    def __init__(self, t) -> None:
        self.t = t
    
    def resolve(self):
        print("[TYM][DBG]", self.t)
        if self.t[0] == "Result":
            return ResultType() 
        if type(self.t[0]) == ArrayType:
            return self.t[0]
        if self.t[0] == '&':
            return Ref(BaseType(self.t[1:]).resolve())
        if self.t[0][0] == 'i':
            return IntType(size=int(self.t[0][1:]))
        
        return NoType()

    def ptr_depth(o=0):
        return 0