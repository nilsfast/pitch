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
    print("[CMP][TYC] Checking types", a, b)

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
        for fn in self.definitions:
            fn.typecheck(tt)
        

    def compile(self, wr:Writer, sc:Scope):
        wr.emit_post('declare ptr @malloc(i32)')
        wr.emit_post('declare i32 @printf(ptr, ...)')
        wr.emit_pre('')
        wr.emit(0, '')
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
        tt.register(self.name, TypeSignature(ret=self.rettype, args=[]))
        new_tt = TypeTable(deepcopy(tt.table))
        #print("NEW type table", new_tt.table)
        new_tt.register("__self__", TypeSignature(ret=self.rettype, args=[]))
        self.block.typecheck(new_tt)
        #print(f"Function {self.name} type table: {new_tt.table}")

    def compile(self, wr, sc:Scope):
        safe_name = sc.register(self.name, typ=TypeSignature(ret=self.rettype, args=[]))
        child_sc = sc.copy_to_new_scope()

        com_ret = child_sc.register(COM_RET) # Common return label
        retval = child_sc.register(RETVAL, typ=Ref(to=self.rettype)) # Common return value

        print("[CMP][FUN] Locals:", sc.locals)

        arg_names_and_ptr = []
        if self.params != [None]:
            for p in self.params:
                arg_names_and_ptr.append(
                    {'n':child_sc.register(p.id+'val', p.t), 'ptr':child_sc.register(str(p.id), Ref(to=p.t))}
                )
            args_type = list(map(lambda a: f'{a["n"].type.str} %{a["n"].value}', arg_names_and_ptr))
        else:
            args_type = []

        print("[CMP][FUN] Arguments:", self.params, list(arg_names_and_ptr))

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
            print("[CMP][BLO] Block dest", dest)
            exp.compile(wr, sc, dest)


@dataclass
class CompilerDirective():
    # NOTE looks weird in ast because of intent (i think)
    content: str

    def compile(self, wr, sc, dest=None):
        #print("COMPILER DIRECTIVE", self.content)
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
        print("[CMP][RET] Return value:", return_value)
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
class MR():
    test: ...
    def compile(self, wr, sc:Scope, dest):
        pass

@dataclass
class String():
    value: str

    def get_type(self, tt):
        return ArrayType(IntType(size=8), -1)

    def compile(self, wr, sc:Scope, dest):
        value = self.value.replace('n', '0A')
        length = len(value) - (value.count("\\")*2)
        strconst = sc.register('@str', Ref(ArrayType(IntType(size=8), length)) )
        
        wr.emit_pre(f'{strconst.value} = private constant {strconst.type.to.str} c"{value}"')
        wr.emit(1, f'%{dest.value} = getelementptr inbounds {strconst.type.to.str}, {strconst.type.str} {strconst.value}, i32 0, i32 0')
        
        strconst.type = Ref(IntType(size=8))
        return strconst

# TODO find a way to fix this in parser with mult reference (value)

@dataclass
class V():
    t: Type
    name: str


@dataclass
class Variable():
    name: str

    def get_type(self, tt):
        return tt.get(self.name)

    def compile(self, wr, sc, dest):
        print("[CMP][VAR] Loading", self.name, "to", dest)
        location = sc.get(self.name)
        if not location:
            comp_err(f"Variable '{self.name}' does not exist")

        #print("[CMP][VAR]", location, "DEPTH", location.type.ptr_depth())
        #if location.type.ptr_depth() == 0:
        #    wr.emit(1, f'%{dest.value} = add {location.type.str} %{location.value}, 0')
        #else:
        wr.emit(1, f"; accessing '{location.value}', d={location.type.ptr_depth()}")
        
        IRLoad(location, dest).compile(wr, sc)
        
        #ptr = location
        #while ptr.type.ptr_depth() > 0:
        #    if ptr.type.ptr_depth() == 1:
        #        target = dest
        #    else:
        #        target = sc.symbol(typ=ptr.type.to)
        #    wr.emit(1, f'%{target.value} = load {target.type.str}, {ptr.type.str} %{ptr.value}, align 4')
        #    ptr = target
        


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
        OPS = {'+': 'add', '-': 'sub', '*': 'mul', '<': 'icmp slt'}
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
        true_label = sc.register('iftrue')
        false_label = sc.register('iffalse')
        wr.emit(1, f'br i1 %{test_var.value}, label %{true_label.value}, label %{false_label.value}')

        # Compile true section
        wr.emit(0, f'{true_label.value}:')
        self.if_true.compile(wr, sc)
        
        if not self.if_true.returns():
            end_label = sc.register('ifend')
            wr.emit(1, f'br label %{end_label.value}')
        
        wr.emit(0, f'{false_label.value}:')
        self.if_false.compile(wr, sc)

        if not self.if_true.returns():
            wr.emit(1, f'br label %{end_label.value}')
            wr.emit(0, f'{end_label.value}:')
            wr.emit(1, f'%{dest.value} = load {dest.type}, ptr %{sc.get(RETVAL).value}, align 8') # TODO remove hard-coded type

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
        print("[CMP][CLL] Calling", self.fn)
        print("[CMP][CLL] Call dest", dest)
        
        if self.fn == 'printf':
            printsig = [Ref(to=IntType(size=8)), DynamicType()]
            printargs = [Ref(to=IntType(size=8)), IntType(32)]
            printret = sc.symbol()
            arg_list = []
            for i,arg in enumerate(self.args):
                if arg:
                    #print("arg smyt", sc.locals)
                    arg_dest = sc.symbol(typ=printargs[i], dyn_type=True)
                    arg.compile(wr, sc, arg_dest)
                    arg_list.append(arg_dest)
            IRCall(printret, printsig, arg_list, 'printf').compile(wr, sc, dest)    
        elif self.fn == 'Ok':
            print("[CMP][CLL] OK fuction")
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
            print("[CMP][CLL] Unwrap function")
            wr.emit(1, f'%{extracted.value} = extractvalue %pitch.res %{result.value}, 1')
            wr.emit(1, f'%{dest.value} = load {extracted.type.to.str}, ptr %{extracted.value}')
        elif self.fn == 'alloc':
            size = self.args[0].value
            #i8ptr = sc.symbol(typ=Ref(to=IntType(size=8))) # make i8 ptr for malloc
            wr.emit(1, f'%{dest.value} = call ptr (i32) @malloc(i32 {size})') 
            #wr.emit(1, f'%{dest.value} = bitcast i8* %{i8ptr.value} to {dest.type.str}')
        elif self.fn == 'realloc':
            size = self.args[0].value
            wr.emit(1, f'%{dest.value} = call ptr (i32) @realloc(i32 {size})') 
        
        else:
            valid_fn = sc.get(self.fn)
            if not valid_fn:
                comp_err(f'Cound not find function {self.fn}')                

            arg_list = []
            print("[CMP][CLL] Function arguments:", valid_fn.type.args)
            for i,arg in enumerate(self.args):
                print("[CMP][CLL] Processing argument", arg)
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

    def compile(self, wr, sc:Scope, dest):
        OPS = {'+': 'add', '-': 'sub', '*': 'mul nuw', '==': 'icmp eq', '<':'icmp slt' }
        BIN_OPS = ['<', '==']

        if self.op in BIN_OPS:
            left = sc.symbol(dyn_type=True)
            right = sc.symbol(dyn_type=True)
            self.left.compile(wr, sc, left)
            self.right.compile(wr, sc, right)
            if left.type != right.type:
                ice("Fatal inequality of operation types")
            wr.emit(1, f'%{dest.value} = {OPS[self.op]} {left.type.str} %{left.value}, %{right.value}')
        else:
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
class Deref():
    
    name: str
    depth: int
    def resolve(self):
        return self

    def typecheck(self, tt:TypeTable):
        print("[DBG][DER]", tt.get(self.ref))

    def dest_compile(self, wr: Writer, sc: Scope):
        print("[CMP][DER] begin dereference")
        scope_object = sc.get(self.name)
        print("[CMP][DER] scope says", scope_object)

        reference_root = scope_object
        for _ in range(self.depth):
            print("[CMP][DER] dereferencing...")
            reference_root = deref_one_layer(wr, sc, reference_root)

            if reference_root.type.ptr_depth() == 1:
                print("PTR DEPTH == 1")
        print("[CMP][DER] result", reference_root)
        return reference_root

    def compile(self, wr, sc: Scope, dest):
        depth = self.ref.count("*")
        name = self.ref[depth:]
        print("DEREF NAME", name)
        to_deref = sc.get(name)
        wr.emit(1, f'; Dereference')

        # dereference the pointer to get a pointer to where the referenced data lives
        reference_root = to_deref
        for _ in range(depth):
            print("DEREF PASS")
            reference_root = deref_one_layer(wr, sc, reference_root)

            if reference_root.type.ptr_depth() == 1:
                print("PTR DEPTH == 1")
        return reference_root
        
        #wr.emit(1, f'%{dest.value} = load i32, {reference_root.type.str} %{reference_root.value}')

        # Store the data from reference root 
        #wr.emit(1, f'store {new_val.type.str} %{new_val.value}, {reference_root.type.str} %{reference_root.value}, align 8')

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

        
        print("reassign", self.value, type(self.value))

        if type(self.id) == str:   
            to_reassign: Var = sc.get(self.id)
            if not to_reassign:
                comp_err(f"'{self.id}' could not be found.")
        elif type(self.id) == Deref:
            # TODO: why
            
            to_reassign = self.id.dest_compile(wr, sc)

            #to_reassign = sc.symbol(typ=Ref(to=IntType(32)))
            #self.id.compile(wr, sc, to_reassign)
        else:
            ice("Left hand side derefence error")
        print("[CMP][RAS] Reassigning",to_reassign)

             
        

        if type(self.value) == ArrayType:
            malloc_result = sc.symbol(typ=Ref(to=None))
            self.value.compile(wr, sc, malloc_result)
            IRStore(to_reassign, malloc_result).compile(wr, sc)
        
        elif type(self.value) == Reference:
            var_to_ref = sc.get(self.value.id.name) # Variable that shall be referenced
            wr.emit(1, f'store {var_to_ref.type.str} %{var_to_ref.value}, {to_reassign.type.str} %{to_reassign.value}, align 8')
        
        else:
            new_value = sc.symbol(typ=to_reassign.type)
            self.value.compile(wr, sc, new_value)            
            IRStore(to_reassign, new_value).compile(wr, sc)            
            #new_val = sc.symbol()
            #self.value.compile(wr, sc, new_val)
#
            ## XXX: is this stil valid?
            #if to_reassign.type.ptr_depth() == 0:
            #    print("DOES THIS RUN???")
            #    # for registers and vars (?)
            #    sc.reassign(to_reassign, new_val) 
            #else:
            #    # Explaination: dereference the pointer to get a pointer to where the referenced data lives
            #    reference_root = to_reassign
            #    while reference_root.type.ptr_depth() > 1:
            #        reference_root = deref_one_layer(wr, sc, reference_root)
            #    
            #    # Store the data from reference root 
            #    wr.emit(1, f'store {new_val.type.str} %{new_val.value}, {reference_root.type.str} %{reference_root.value}, align 8')
#
            ##print("reassign", to_reassign, "to", new_val)

@dataclass
class ArrayIndex():
    var: ...
    i: ...
    
    def compile(self, wr, sc:Scope, dest):
        wr.emit(1,'; array access')
        index = sc.symbol(typ=IntType(size=32))
        self.i.compile(wr,sc,index)

        # TODO add i compile, (change to value in parser)
        ## TODO: Runtime Bounds check?
        array_ptr = sc.get(self.var.name)
        array = sc.symbol(typ=Ref(to=None))
        wr.emit(1, f'%{array.value} = load {array.type.str}, {array_ptr.type.str} %{array_ptr.value}')

        if type(dest.type) == Ref:
            wr.emit(1, f'%{dest.value} = getelementptr ptr, ptr %{array.value}, {index.type.str} %{index.value}')
        else:
            value_ptr = sc.symbol(typ=Ref(to=None))
            wr.emit(1, f'%{value_ptr.value} = getelementptr ptr, ptr %{array.value}, {index.type.str} %{index.value}')
            wr.emit(1, f'%{dest.value} = load {dest.type.str}, {value_ptr.type.str} %{value_ptr.value}')
            
@dataclass
class ArrayLiteral():
    members: ...
    # TODO: Type filling ?
    def compile(self, wr, sc, dest):
        wr.emit(1, f'; array const')
        print("[CPM][ARR] Array members:", self.members)

        arr_const = sc.register('arrconst', typ=ArrayType(member_type=IntType(size=32), length=len(self.members)))
        arr_members = list(map(lambda m: IntType(size=32).str+' '+str(m.value), self.members))
        arr_members_str = '[' + ', '.join(arr_members) + ']'
        wr.emit_pre(f'@{arr_const.value} = private constant {arr_const.type.str} {arr_members_str}')
        wr.emit(1, f'%{dest.value} = getelementptr inbounds {arr_const.type.str}, {Ref(to=arr_const.type).str} @{arr_const.value}, i32 0, i32 0')
        #IRBitcast(Ref(to=arr_const.type), Ref(to=IntType(size=32)), arr_const.value).compile(wr, sc, dest)



@dataclass
class Assignment():
    #id: str
    #vartype: ...
    var: V
    value: ...
    
    def typecheck(self, tt:TypeTable):
        tt.register(self.id, self.vartype)
        if not check_types(self.vartype, self.value.get_type(tt)):
            comp_err(f"Cannot assign {self.value.get_type(tt)} to {self.vartype}")


    def compile(self, wr:Writer, sc:Scope, dest):
            # TODO static-size array
        print("[cmp][ass]",self.var)

        wr.emit(1, "; assignment")


        #if type(self.vartype) == ArrayType:
        #    print("[CMP][ASS] Assigning array")
        #    array = sc.register(self.id, Ref(to=None))
        #    IRAlloc(array).compile(wr, sc)
        #    malloc_result = sc.symbol(typ=Ref(to=None))
        #    self.value.compile(wr, sc, malloc_result)
        #    IRStore(array, malloc_result).compile(wr, sc)
        #else:

        variable = sc.register(self.var.name, typ=self.var.t)
        value = sc.symbol("val", typ=self.var.t)    
        self.value.compile(wr, sc, value) 
        wr.emit(1, f'%{variable.value} = alloca {self.var.t.str}, align 8')
        IRStore(variable, value).compile(wr, sc)

            #    wr.emit(1, f'store {value.type.str} %{value.value}, {variable.type.str} %{variable.value}, align 8')


            # Just a regular variable. Always alloc and store. opt will take care
            #if self.vartype.ptr_depth() == 0:
            #    value = sc.symbol(typ=self.vartype)
            #else:
            #    if type(self.value) == Reference:
            #        print("SELF.VALUE", self.value)
            #        var_to_ref = sc.get(self.value.id) # Variable that shall be referenced
            #        wr.emit(1, f'%{variable.value} = alloca {self.vartype.str}, align 8')
            #        wr.emit(1, f'store {var_to_ref.type.str} %{var_to_ref.value}, {variable.type.str} %{variable.value}, align 8')          
            #    #else:
            #        #comp_err("Cannot assign something referende") # TODO: find out what is disallowed here

            #print(f"[CMP][ASS] Assigned {self.id} to {variable}")


@dataclass
class Argument():
    value: ...

@dataclass
class NoOp():
    
    def compile(self, wr:Writer, sc:Scope, dest:Var):
        pass

@dataclass
class WhileLoop():
    cond: Expression
    content: Block

    #def cpv(self):
    #    return self.if_true.cpv() and self.if_false.cpv()

    def compile(self, wr:Writer, sc:Scope, dest:Var):
        whilecond = sc.register('whilecond')
        whilebody = sc.register('whilebody')
        whileafter = sc.register('whileafter')

        wr.emit(1, f'br label %{whilecond.value}')
        
        condresult = sc.register('whileres', IntType(1))
        wr.emit(0, f'{whilecond.value}:')
        self.cond.compile(wr, sc, condresult)
        wr.emit(1, f'br i1 %{condresult.value}, label %{whilebody.value}, label %{whileafter.value}')
        
        wr.emit(0, f'{whilebody.value}:')
        self.content.compile(wr, sc)
        wr.emit(1, f'br label %{whilecond.value}')
        
        wr.emit(0, f'{whileafter.value}:')

