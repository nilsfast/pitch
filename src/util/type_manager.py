from dataclasses import dataclass
import re

from error import ice


def resolve_type(typestr):
    print("[ast][rst] resolving", typestr)
    if typestr[0] == "&":
        return Ref(resolve_type(typestr[1:]))
    if re.search(r"i\d+", typestr):
        return IntType(32)
    ice(f"Type '{typestr}' could not be resolved.")

@dataclass
class Type():
    pass





@dataclass
class TypeSignature(Type):
    ret: ...
    args: ...

@dataclass
class ArrayType(Type):
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
class ArrType(Type):
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
class StructType(Type):
    name: ...
    members: ...
    
    @property
    def str(self):
        return f"%{self.name}"

    @property
    def sign_str(self):
        #print("struct members", list(map(lambda t: t.str, self.members)))
        return f"{{{', '.join(list(map(lambda t: t.str, self.members)))}}}"
        

    def ptr_depth(o=0):
        return 0
    
    @property
    def memsize(self):
        return int(self.length) * self.member_type.memsize


@dataclass
class IntType(Type):
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
class Ref(Type):
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
class DynamicType(Type):
    pass

    @property
    def str(self):
        return "..."


@dataclass
class NoType(Type):
    pass

    def ptr_depth(o=0):
        return 0
@dataclass
class TemplateType(Type):

    base: ...
    options: ...

    def ptr_depth(o=0):
        return 0


@dataclass
class ResultType(Type):
    pass

    def ptr_depth(o=0):
        return 0

    @property
    def str(self):
        return '%pitch.res'

@dataclass
class BaseType(Type):
    t: ...
    def __init__(self, t) -> None:
        self.t = t
    
    def resolve(self):
        print("[TYM][DBG] BaseType", self.t)
        if self.t[0] == "Result":
            return ResultType() 
        if type(self.t[0]) == ArrayType:
            return self.t[0]
        if self.t[0] == '&':
            print("REF!")
            return Ref(BaseType(self.t[1:]).resolve())
        if self.t[0][0] == '&':
            print("REF!")
            return Ref(BaseType([self.t[0][1:], self.t[1]]).resolve())
        
        if self.t[0][0] == 'i':
            return IntType(size=int(self.t[0][1:]))
        
        return NoType()

    def ptr_depth(o=0):
        return 0