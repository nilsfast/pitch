from dataclasses import dataclass
import struct
from util.scope import Scope
from util.var import Var
from util.type_manager import * 
from util.writer import Writer


@dataclass
class IRBase():
    def compile(self, wr: Writer, sc:Scope, dest:Var):
        wr.emit("; ICE ")
        print("ICE: IR Class unimplemented")

@dataclass
class IRAlloc(IRBase):
    var: Var

    def compile(self, wr: Writer, sc: Scope):
        wr.emit(1, f'%{self.var.value} = alloca {self.var.type.str}, align 8')

@dataclass
class IRStore(IRBase):
    var: Var
    data: Var

    def compile(self, wr: Writer, sc: Scope):
        wr.emit(1, f'store {self.data.type.str} %{self.data.value}, {Ref(self.var.type).str} %{self.var.value}')

@dataclass
class IRLoad(IRBase):
    var: Var
    into: Var

    def compile(self, wr: Writer, sc: Scope):
        wr.emit(1, f'%{self.into.value} = load {self.into.type.str}, {Ref(self.var.type).str} %{self.var.value}, align 4')


@dataclass
class IRInitArray(IRBase):
    pass

@dataclass
class IRVariable():
    var: ...

@dataclass
class IRBitcast(IRBase):
    from_type: BaseType
    to_type: BaseType
    data: ...

    def compile(self, wr: Writer, sc: Scope, dest: Var):
        wr.emit(1,f'%{dest.value} = bitcast {self.to_type.str} %{self.data} to i32*')



@dataclass
class IRArrayLoad(IRBase):
    array: Var
    index: Var

    def compile(self, wr: Writer, sc: Scope, dest: Var):
        ptr = sc.symbol(typ=Ref(to=dest.type))
        
        wr.emit(1, f'%{ptr.value} = getelementptr {ptr.type.to.str}, {ptr.type.str} %{self.array.value}, {self.index.type.str} %{self.index.value}')

        wr.emit(1, f'%{dest.value} = load {dest.type.str}, {Ref(dest.type).str} %{ptr.value}')

@dataclass
class IRArrayPtr(IRBase):
    array: Var
    index: Var

    def compile(self, wr: Writer, sc: Scope, dest: Var):
       
        wr.emit(1, f'%{dest.value} = getelementptr {dest.type.to.str}, {dest.type.str} %{self.array.value}, {self.index.type.str} %{self.index.value}')

@dataclass
class IRCall(IRBase):
    ret: ...
    argtypes: ...
    arguments: ...
    name: ...

    def compile(self, wr: Writer, sc: Scope, dest: Var):
        argstr = ', '.join(a.str for a in self.argtypes)
        paramstr = ', '.join(str(a.type.str)+' '+ (a.value[:] if a.value[0] == '@' else "%"+a.value) for a in self.arguments)
        wr.emit(1, f'%{dest.value} = call {self.ret.type.str} ({argstr}) @{self.name}({paramstr})') 


@dataclass
class IRStructInit(IRBase):
    struct: Var
    def compile(self, wr: Writer, sc: Scope, dest: Var):
        return super().compile(wr, sc, dest)


@dataclass
class IRStructLoad(IRBase):
    struct: Var
    i: int
    # NOTE: struct indexes MUST be constants

    def compile(self, wr: Writer, sc: Scope, dest: Var):
        val_ptr = sc.symbol(typ=Ref(dest.type))
        print("IRStructLoad", dest, val_ptr, self.i)
        #wr.emit(1, f'%nils = sext i32 %{self.i.value} to i32')
        wr.emit(1, f'%{val_ptr.value} = getelementptr inbounds {self.struct.type.to.str}, {self.struct.type.str} %{self.struct.value}, i32 0, i32 {self.i}')
        wr.emit(1, f'%{dest.value} = load {dest.type.str}, {val_ptr.type.str} %{val_ptr.value}')

@dataclass
class IRStructStore(IRBase):
    struct: Var
    i: int
    value: ...

    def compile(self, wr: Writer, sc: Scope, dest: Var):
        struct = self.struct
        struct_member_type = struct.type.to.members[self.i]
        ptr_to_struct_member = sc.symbol(typ=Ref(to=struct_member_type))
        print("STRUCT", self.struct, struct_member_type)
        wr.emit(1, f'%{ptr_to_struct_member.value} = getelementptr inbounds {struct.type.to.str}, {struct.type.str} %{struct.value}, i32 0, i32 {self.i} ; ag')
        val_to_store = sc.symbol(typ=struct_member_type)
        self.value.compile(wr, sc, val_to_store)
        wr.emit(1, f'store {val_to_store.type.str} %{val_to_store.value}, {ptr_to_struct_member.type.str} %{ptr_to_struct_member.value}')
