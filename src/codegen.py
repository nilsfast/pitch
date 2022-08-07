from copy import deepcopy
from dataclasses import dataclass
import sys
from types import NoneType
from error import comp_err, ice
from ir import IRAlloc, IRArrayLoad, IRArrayPtr, IRBitcast, IRLoad, IRStore, IRStructLoad, IRStructStore, IRVariable, IRCall
from util.type_table import TypeTable
from util.var import Var
from util.scope import Scope
from util.writer import Writer

from util.type_manager import *

COM_RET = "cr"
RETVAL = "retptr"

def check_types(a, b):
    print("checking types", a, b)

    # TODO implement real type system with types as arguments
    if ResultType in [type(a), type(b)]:
        return True

    if type(a) == Ref:
        return True

    if a == b:
        return True
    
    if type(a) != type(b):
        return False
    
    if type(a) == IntType:
        if -1 in [a.size, b.size]:
            return True
        if type(a.size) == int and type(b.size) == int:
             return False
        

    ice("Check type function exhausted")
    return False


def deref_one_layer(wr, sc, ptr):
    target = sc.symbol('symp', ptr.type.to)
    wr.emit(1, f'%{target.value} = load {target.type.str}, {ptr.type.str} %{ptr.value}')
    return target

def acc_struct(struct:Var, n:int, wr:Writer, dest:Var):
    '''stores a pointer in dest to the n-th element of the struct '''
    
    wr.emit(1, f'%{dest.value} = getelementptr {struct.type.to.str}, {struct.type.str} %{struct.value}, i32 0, i32 {n}')

@dataclass
class CodegenBase():
    pass
    def compile(self, wr:Writer, sc:Scope, dest:Var):
        ice("Codegen inheritor compile function not implemented")

@dataclass
class Module():
    dependencies: ...
    definitions: ...

    def cpv(self):
        for fn in self.definitions:
            return fn.cpv()
        
    def typecheck(self, tt):
        tt.register("Ok", TypeSignature(ResultType(), Ref(to=None)))
        tt.register("Err", TypeSignature(ResultType(), Ref(to=None)))
        tt.register("Unwrap", TypeSignature(ResultType(), IntType(32)))
        print(tt.table)
        for fn in self.definitions:
            fn.typecheck(tt)
        

    def compile(self, wr:Writer, sc:Scope):
        wr.emit_post('declare i8* @malloc(i32)')
        wr.emit_post('declare i32 @printf(i8*, ...)')
        
        
        # TODO Move to module
        wr.emit_pre('')



        wr.emit(0, '')
        #wr.emit(0, '@fmtstr = private constant [4 x i8] c"%p  "')

        for fn in self.definitions:
            # TODO move scope stuff here; add support for globals
            fn.compile(wr, sc)

         
@dataclass 
class Function():
    name: str
    params: ... 
    rettype: ...
    block: ...

    def cpv(self):
        #print("CPV", self.rettype)
        if self.rettype in ['void', '']:
            return True
        else:
            return self.block.cpv()
    
    def typecheck(self, tt: TypeTable):
        #TODO scope the type table
        tt.register(self.name, TypeSignature(ret=self.rettype, args=[]))
        new_tt = TypeTable(deepcopy(tt.table))
        #print("NEW type table", new_tt.table)
        new_tt.register("__self__", TypeSignature(ret=self.rettype, args=[]))
        self.block.typecheck(new_tt)
        print(f"Function {self.name} type table: {new_tt.table}")

    def compile(self, wr, sc:Scope):
        safe_name = sc.register(self.name, typ=TypeSignature(ret=self.rettype, args=[]))
        child_sc = sc.copy_to_new_scope()

        com_ret = child_sc.register(COM_RET) # Common return label
        retval = child_sc.register(RETVAL, typ=Ref(to=self.rettype)) # Common return value

        print("[DBG][CMP][FUN][LOC]", sc.locals)

        arg_names_and_ptr = []
        if self.params != [None]:
            for p in self.params:
                arg_names_and_ptr.append(
                    {'n':child_sc.register(p.id+'val', p.t), 'ptr':child_sc.register(str(p.id), Ref(to=p.t))}
                )
            args_type = list(map(lambda a: f'{a["n"].type.str} %{a["n"].value}', arg_names_and_ptr))
        else:
            args_type = []

        print("[DBG][CMP][FUN][ARG]", self.params, list(arg_names_and_ptr))

        wr.emit(0, f'define {self.rettype.str} @{safe_name.value}({", ".join(args_type)}) {{')

        if arg_names_and_ptr:
            for a in list(arg_names_and_ptr):
                #Update type signature
                safe_name.type.args.append(a["n"].type)
                wr.emit(1, f'%{a["ptr"].value} = alloca {a["n"].type.str}, align 8')
                wr.emit(1, f'store {a["n"].type.str} %{a["n"].value}, {a["ptr"].type.str} %{a["ptr"].value}, align 8')

        wr.emit(1, f'%{retval.value} = alloca {self.rettype.str}, align 8')
        
        self.block.compile(wr, child_sc)
        wr.emit(0, f'{com_ret.value}:')

        tmp_retval = sc.symbol(typ=self.rettype)
        wr.emit(1, f'%{tmp_retval.value} = load {tmp_retval.type.str}, {retval.type.str} %{retval.value}, align 8')
        wr.emit(1, f'ret {self.rettype.str} %{tmp_retval.value}')

        wr.emit(0, '}\n')
@dataclass
class Block():
    name: str
    content: ...

    def typecheck(self, tt):
        for c in self.content:
            c.typecheck(tt)
    
    def returns(self):
        return Return in list(map(type, self.content))

    def cpv(self) -> bool:
        stms = list(map(type, self.content))
        if Return in stms:
            return True
        conds = list(filter(lambda s: type(s)==Conditional, self.content))
        cond_results = list(map(lambda c: c.cpv(), conds))
        #print(conds, cond_results)
        if True in cond_results:
            return True
        
        return False
        
    def compile(self, wr, sc):
        for exp in self.content:
            dest = sc.symbol()
            print("dest", dest)
            exp.compile(wr, sc, dest)


@dataclass
class CompilerDirective():
    # NOTE looks weird in ast because of intent (i think)
    content: str

    def compile(self, wr, sc, dest=None):
        print("COMPILER DIRECTIVE", self.content)
        pass

@dataclass
class Return():
    value: ...

    def typecheck(self, tt: TypeTable):
        if not check_types(tt.get('__self__').ret, self.value.get_type(tt)):
            comp_err(f"Type mismatch: Function return type is {tt.get('__self__').ret.str}; you're trying to return {self.value.get_type(tt).str}")

    def compile(self, wr, sc:Scope, dest):
        wr.emit(1, f'; return')
        #print("RET SC", sc.locals)
        return_value = sc.symbol(typ=sc.get(RETVAL).type.to)
        print("RETVAL", return_value)
        self.value.compile(wr, sc, return_value)
        wr.emit(1, f'store {return_value.type.str} %{return_value.value}, {sc.get(RETVAL).type.str} %{sc.get(RETVAL).value}, align 8')
        wr.emit(1, f'br label %{sc.get(COM_RET).value}')



@dataclass
class Struct():
    name: str
    members: ...

@dataclass
class Parameter():
    id: str
    t: str


@dataclass
class String():
    value: str

    def get_type(self, tt):
        return ArrayType(IntType(size=8), -1)

    def compile(self, wr, sc:Scope, dest):
        value = self.value[1:-1]
        value = value.replace('n', '0A')
        length = len(value) - (value.count("\\")*2)
        strconst = sc.register('@str', Ref(ArrayType(IntType(size=8), length)) )
        
        wr.emit_pre(f'{strconst.value} = private constant {strconst.type.to.str} c"{value}"')
        wr.emit(1, f'%{dest.value} = getelementptr inbounds {strconst.type.to.str}, {strconst.type.str} {strconst.value}, i32 0, i32 0')
        
        strconst.type = Ref(IntType(size=8))
        return strconst

# TODO find a way to fix this in parser with mult reference (value)
@dataclass
class Variable():
    name: str

    def get_type(self, tt):
        return tt.get(self.name)

    def compile(self, wr, sc, dest):
        print("LOAD VAR ", self.name, "to", dest)
        location = sc.get(self.name)
        if not location:
            comp_err(f"Variable '{self.name}' does not exist")

        print("[DBG][CMP][VAR]", location, "DEPTH", location.type.ptr_depth())
        if location.type.ptr_depth() == 0:
            wr.emit(1, f'%{dest.value} = add {location.type.str} %{location.value}, 0')
        else:
            wr.emit(1, f"; accessing `{location.value}`, d={location.type.ptr_depth()}")
            ptr = location
            while ptr.type.ptr_depth() > 0:
                if ptr.type.ptr_depth() == 1:
                    target = dest
                else:
                    target = sc.symbol(typ=ptr.type.to)
                wr.emit(1, f'%{target.value} = load {target.type.str}, {ptr.type.str} %{ptr.value}, align 4')
                ptr = target
            


@dataclass
class Number():
    value: int

    def get_type(self, tt):
        return IntType(-1)

    def __init__(self, value):
        self.value = int(value)

    def compile(self, wr, sc, dest):
        if dest.dynamic_type:
            dest.type = IntType(32)
        wr.emit(1, f'%{dest.value} = add {dest.type.str} {self.value}, 0')


@dataclass
class BinaryOp():
    left: ...
    right: ...


@dataclass
class MathExp():
    op: str
    left: ...
    right: ...

    def compile(self, wr, sc, dest):
        OPS = {'+': 'add', '-': 'sub', '*': 'mul', }
        left = sc.symbol()
        right = sc.symbol()
        self.left.compile(wr, sc, left)
        self.right.compile(wr, sc, right)
        wr.emit(1, f'%{dest.value} = {OPS[self.op]} i32 %{left.value}, %{right.value}')

@dataclass
class BoolExp():
    op: str
    left: ...
    right: ...

    def compile(self, wr, sc, dest):
        LT = {'<': 'icmp slt'}
        left = sc.symbol()
        right = sc.symbol()
        self.left.compile(wr, sc, left)
        self.right.compile(wr, sc, right)
        wr.emit(1, f'%{dest.value} = {LT[self.op]} i32 %{left.value}, %{right.value}')

@dataclass
class Conditional():
    condition: ...
    if_true: ...
    if_false: ...

    def cpv(self):
        return self.if_true.cpv() and self.if_false.cpv()

    def compile(self, wr, sc, dest):
        test_var = sc.symbol()
        self.condition.compile(wr, sc, test_var)
     
        # Compile the expression and branch
        true_label = sc.symbol('iftrue')
        false_label = sc.symbol('iffalse')
        wr.emit(1, f'br i1 %{test_var.value}, label %{true_label.value}, label %{false_label.value}')

        # Compile true section
        wr.emit(0, f'{true_label.value}:')
        self.if_true.compile(wr, sc)
        
        if not self.if_true.returns():
            end_label = sc.symbol('ifend')
            wr.emit(1, f'br label %{end_label.value}')
        
        wr.emit(0, f'{false_label.value}:')
        self.if_false.compile(wr, sc)

        if not self.if_true.returns():
            wr.emit(1, f'br label %{end_label}')
            wr.emit(0, f'{end_label}:')
            wr.emit(1, f'%{dest.value} = load i32, ptr %{sc.get(RETVAL).value}, align 8') # TODO remove hard-coded type

@dataclass
class ForLoop():
    var: ...
    iterator: ...
    content: ...

    #def cpv(self):
    #    return self.if_true.cpv() and self.if_false.cpv()

    def compile(self, wr, sc, dest):
        index = sc.register('forvar')
        IRVariable(index).compile(wr, sc, dest)

@dataclass
class Call():
    fn: str
    args: ...

    def typecheck(self, tt):
        return True

    def get_type(self, tt: TypeTable):
        return tt.get(self.fn).ret
    
    def compile(self, wr, sc:Scope, dest):
        print("CALL to", self.fn)
        print("DEST", dest)
        
        if self.fn == 'printf':
            printsig = [Ref(to=IntType(size=8)), DynamicType()]
            printargs = [Ref(to=IntType(size=8)), IntType(32)]
            printret = sc.symbol()
            arg_list = []
            for i,arg in enumerate(self.args):
                if arg:
                    arg_dest = sc.symbol(typ=printargs[i], dyn_type=True)
                    arg.compile(wr, sc, arg_dest)
                    arg_list.append(arg_dest)
            IRCall(printret, printsig, arg_list, 'printf').compile(wr, sc, dest)    
        elif self.fn == 'Ok':
            print("OK fuction")
            okret = sc.symbol(typ=ResultType())
            value = sc.symbol(typ=IntType(32))
            value_ptr = sc.symbol(typ=Ref(to=IntType(32)))
            IRAlloc(value_ptr).compile(wr, sc, value_ptr)
            self.args[0].compile(wr, sc, value)
            IRStore(value_ptr, value).compile(wr, sc, dest)
            IRCall(okret, [Ref(to=IntType(32))], [value_ptr], 'pitch_ok').compile(wr, sc, dest)    
            #IRLoad(okret).compile(wr, sc, dest)
        elif self.fn == 'Unwrap':
            result = sc.symbol(typ=ResultType())
            self.args[0].compile(wr, sc, result)
            extracted = sc.symbol(typ=Ref(to=IntType(32)))
            print("Unwrap function")
            wr.emit(1, f'%{extracted.value} = extractvalue %pitch.res %{result.value}, 1')
            wr.emit(1, f'%{dest.value} = load {extracted.type.to.str}, ptr %{extracted.value}')
        elif self.fn == 'alloc':
            size = self.args[0].value
            i8ptr = sc.symbol(typ=Ref(to=IntType(size=8))) # make i8 ptr for malloc
            wr.emit(1, f'%{i8ptr.value} = call i8* (i32) @malloc(i32 {size})') 
            wr.emit(1, f'%{dest.value} = bitcast i8* %{i8ptr.value} to {dest.type.str}')



        else:
            
            valid_fn = sc.get(self.fn)
            if not valid_fn:
                print("[ERR][CMP] The function could not be found")

            arg_list = []
            print("CALL FN TYPE SIGN", valid_fn.type.args)
            for i,arg in enumerate(self.args):
                print("CALL ARG LOOP", arg)
                if arg:
                    arg_dest = sc.symbol(typ=valid_fn.type.args[i])
                    arg.compile(wr, sc, arg_dest)
                    arg_list.append(f'{valid_fn.type.args[i].str} %{arg_dest.value}')
            argstr = ', '.join(arg_list)
            #print(argstr)
            wr.emit(1, f'%{dest.value} = call {valid_fn.type.ret.str} @{valid_fn.value}({argstr})')

@dataclass
class AccCall():
    of: ...
    to: ...
    
    def compile(self, wr, sc:Scope, dest):
        pass



@dataclass
class Expression():
    op: str
    left: ...
    right: ...

    def get_type(self, tt):
        leftt = self.left.get_type(tt)
        rightt = self.right.get_type(tt)
        if not check_types(leftt, rightt):
            comp_err(f"Operation {self.op} is not supported between types {leftt.str} and {rightt.str}")
        
        return leftt if leftt.size > 0 else rightt

    def compile(self, wr, sc, dest):
        OPS = {'+': 'add', '-': 'sub', '*': 'mul nuw', '==': 'icmp eq' }
        left = sc.symbol(typ=dest.type)
        right = sc.symbol(typ=dest.type)
        self.left.compile(wr, sc, left)
        self.right.compile(wr, sc, right)
        wr.emit(1, f'%{dest.value} = {OPS[self.op]} {dest.type.str} %{left.value}, %{right.value}')

@dataclass
class Reference():
    id: str
    mut: bool

    def get_type(self, tt):
        return tt.get(self.id.name)

    def compile(self, wr, sc, dest):
        pass


@dataclass
class Reassignment():
    id: ...
    value: ...

    def typecheck(self, tt:TypeTable):
        var_type = tt.get(self.id)
        if not check_types(var_type, self.value.get_type(tt)):
            comp_err(f"Cannot assign {self.value.get_type(tt)} to {var_type}")
    
    def compile(self, wr, sc:Scope, dest):
        
        wr.emit(1, f'; Reassignment')

        
        print("reassign", self.value)
        if type(self.id) == str:   
            to_reassign = sc.get(self.id)
            if not to_reassign:
                comp_err(f"'{self.id}' could not be found.")
        else:
            to_reassign = sc.symbol(typ=Ref(to=IntType(32)))
            self.id.compile(wr, sc, to_reassign)
            print("arr ind ptr",to_reassign)

            

        if type(self.value) == Reference:
            var_to_ref = sc.get(self.value.id.name) # Variable that shall be referenced
            wr.emit(1, f'store {var_to_ref.type.str} %{var_to_ref.value}, {to_reassign.type.str} %{to_reassign.value}, align 8')
        else:
            new_val = sc.symbol()
            self.value.compile(wr, sc, new_val)

            # XXX: is this stil valid?
            if to_reassign.type.ptr_depth() == 0:
                print("DOES THIS RUN???")
                # for registers and vars (?)
                sc.reassign(to_reassign, new_val) 
            else:
                # Explaination: dereference the pointer to get a pointer to where the referenced data lives
                reference_root = to_reassign
                while reference_root.type.ptr_depth() > 1:
                    reference_root = deref_one_layer(wr, sc, reference_root)
                
                # Store the data from reference root 
                wr.emit(1, f'store {new_val.type.str} %{new_val.value}, {reference_root.type.str} %{reference_root.value}, align 8')

            print("reassign", to_reassign, "to", new_val)

@dataclass
class ArrayIndex():
    var: ...
    i: ...
    
    def compile(self, wr, sc:Scope, dest):
        index = sc.symbol(typ=IntType(size=32))
        self.i.compile(wr,sc,index)
        # TODO add i compile, (change to value in parser)
        wr.emit(1,'; array access')
        ## TODO: Runtime Bounds check?
        array_ptr = sc.get(self.var.name)
        array = sc.symbol(typ=Ref(to=None))
        wr.emit(1, f'%{array.value} = load {array.type.str}, {array_ptr.type.str} %{array_ptr.value}')

        if type(dest.type) == Ref:
            wr.emit(1, f'%{dest.value} = getelementptr ptr, ptr %sym2, i32 0')
        else:
            value_ptr = sc.symbol(typ=Ref(to=None))
            wr.emit(1, f'%{value_ptr.value} = getelementptr ptr, ptr %sym2, i32 0')
            wr.emit(1, f'%{dest.value} = load {dest.type.str}, {value_ptr.type.str} %{value_ptr.value}')
            
        
        #IRArrayPtr()

        #IRLoad(array_ptr).compile(wr, sc, array)
        #if type(dest.type) == Ref:
        #    struct_load_dest = sc.symbol(typ=dest.type)
        #    IRStructLoad(struct, 0).compile(wr, sc, struct_load_dest)
        #    IRArrayPtr(struct_load_dest, index).compile(wr, sc, dest)
        #else:
        #    load_dest = sc.symbol(typ=struct.type.to.members[0])
        #    IRStructLoad(struct, 0).compile(wr, sc, load_dest)
        #    IRArrayLoad(load_dest, index).compile(wr, sc, dest)



@dataclass
class ArrayLiteral():
    members: ...
    # TODO: Type filling ?
    def compile(self, wr, sc, dest):
        wr.emit(1, f'; array const')
        print("array const", self.members)

        arr_const = sc.register('arrconst', typ=ArrayType(member_type=IntType(size=32), length=len(self.members)))
        arr_members = list(map(lambda m: IntType(size=32).str+' '+str(m.value), self.members))
        arr_members_str = '[' + ', '.join(arr_members) + ']'
        wr.emit_pre(f'@{arr_const.value} = private constant {arr_const.type.str} {arr_members_str}')
        wr.emit(1, f'%{dest.value} = getelementptr inbounds {arr_const.type.str}, {Ref(to=arr_const.type).str} @{arr_const.value}, i32 0, i32 0')
        #IRBitcast(Ref(to=arr_const.type), Ref(to=IntType(size=32)), arr_const.value).compile(wr, sc, dest)



@dataclass
class Assignment():
    id: str
    vartype: ...
    value: ...
    
    def typecheck(self, tt:TypeTable):
        tt.register(self.id, self.vartype)
        if not check_types(self.vartype, self.value.get_type(tt)):
            comp_err(f"Cannot assign {self.value.get_type(tt)} to {self.vartype}")


    def compile(self, wr, sc:Scope, dest):
            # TODO static-size array
        
        if type(self.vartype) == ArrayType:
            print("ARRAY ASSIGN")

            array = sc.register(self.id, Ref(to=None))
            IRAlloc(array).compile(wr, sc)
            malloc_result = sc.symbol(typ=Ref(to=None))
            self.value.compile(wr, sc, malloc_result)
            IRStore(array, malloc_result).compile(wr, sc)
            #arr_var = sc.register(self.id, self.vartype)
            
            ## TODO break up into / use IR* Classes
            #wr.emit_post('declare void @llvm.memcpy.p0.p0.i32(ptr, ptr, i32, i1)') 
            #struct = sc.register('vec', NoneType)
            #struct.type = StructType(struct.value, [Ref(IntType(size=32)), IntType(size=64), IntType(size=64)]) # TODO make dynamic
            #wr.emit_pre(f'{struct.type.str} = type {struct.type.sign_str}') # ptr, size, alloc
#
            ## value result is a pointer to the member type
            #value_result = sc.symbol(typ=Ref(to=self.vartype.member_type))
            #self.value.compile(wr, sc, value_result)
            #wr.emit(1, f'; array init')
            #
            #if self.vartype.length == '*' or not self.vartype.length:
            #    arr_size = int(self.vartype.member_type.memsize) * len(self.value.members)
            #else:
            #    arr_size = self.vartype.memsize
            #
            #the_vector = sc.register(self.id,typ=Ref(to=struct.type)) 
            #
            ## Allocate memory
            #wr.emit(1, f'%{the_vector.value} = alloca {struct.type.str}')
            #i8ptr = sc.symbol(typ=Ref(to=IntType(size=8))) # make i8 ptr for malloc
            #wr.emit(1, f'%{i8ptr.value} = call i8* (i32) @malloc(i32 {arr_size})') 
            #cast_result = sc.symbol(typ=the_vector.type.to.members[0])
            #wr.emit(1, f'%{cast_result.value} = bitcast i8* %{i8ptr.value} to {cast_result.type.str}') # cast i8 ptr to i32 ptr
            #
            #vec_ptr = sc.symbol(typ=Ref(to=struct.type.members[0]))
            #print("vec ptr", vec_ptr)
            #print("arrptr", the_vector)
            #acc_struct(the_vector, 0, wr, vec_ptr)
            #wr.emit(1, f'store {cast_result.type.str} %{cast_result.value}, {vec_ptr.type.str} %{vec_ptr.value}' )
#
            ##TODO: Make into IR function:
            #wr.emit(1, f'call void @llvm.memcpy.p0.p0.i32(ptr %{cast_result.value}, ptr %{value_result.value}, i32 {arr_size}, i1 false)')
            #IRStructStore(the_vector, 1, Number(arr_size)).compile(wr, sc, dest)
            #IRStructStore(the_vector, 2, Number(arr_size)).compile(wr, sc, dest)


        else:
            # Compile what the variable is assigned to

            variable = sc.register(self.id, typ=Ref(to=self.vartype))

            # Just a regular variable
            if self.vartype.ptr_depth() == 0:
                value = sc.symbol(typ=self.vartype)
                self.value.compile(wr, sc, value) 
                wr.emit(1, f'%{variable.value} = alloca {self.vartype.str}, align 8')
                wr.emit(1, f'store {value.type.str} %{value.value}, {variable.type.str} %{variable.value}, align 8')
            else:
                if type(self.value) == Reference:
                    var_to_ref = sc.get(self.value.id.name) # Variable that shall be referenced
                    wr.emit(1, f'%{variable.value} = alloca {self.vartype.str}, align 8')
                    wr.emit(1, f'store {var_to_ref.type.str} %{var_to_ref.value}, {variable.type.str} %{variable.value}, align 8')          
                else:
                    print("ERR: Nothing else allowed here ")

            print(f"assign {self.id}={variable}")


@dataclass
class Argument():
    value: ...
