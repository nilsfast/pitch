from dataclasses import dataclass
from types import NoneType
from ir import IRArrayLoad, IRBitcast, IRStructLoad, IRStructStore
from util.var import Var
from util.scope import Scope
from util.writer import Writer

from util.type_manager import *

COM_RET = "cr"
RETVAL = "retptr"

def deref_one_layer(wr, sc, ptr):
    target = sc.symbol('symp', ptr.type.to)
    wr.emit(1, f'%{target.value} = load {target.type.str}, {ptr.type.str} %{ptr.value}')
    return target

def acc_struct(struct:Var, n:int, wr:Writer, dest:Var):
    '''stores a pointer in dest to the n-th element of the struct '''
    
    wr.emit(1, f'%{dest.value} = getelementptr {struct.type.to.str}, {struct.type.str} %{struct.value}, i32 0, i32 {n}')


@dataclass
class Module():
    dependencies: ...
    definitions: ...

    def cpv(self):
        for fn in self.definitions:
            return fn.cpv()

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

        wr.emit(0, f'define i32 @{safe_name.value}({", ".join(args_type)}) {{')

        if arg_names_and_ptr:
            for a in list(arg_names_and_ptr):
                #Update type signature
                safe_name.type.args.append(a["n"].type)
                wr.emit(1, f'%{a["ptr"].value} = alloca {a["n"].type.str}, align 8')
                wr.emit(1, f'store {a["n"].type.str} %{a["n"].value}, {a["ptr"].type.str} %{a["ptr"].value}, align 8')

        wr.emit(1, f'%{retval.value} = alloca i32, align 8')
        
        self.block.compile(wr, child_sc)
        wr.emit(0, f'{com_ret.value}:')

        tmp_retval = sc.symbol(typ=IntType(size=32))
        wr.emit(1, f'%{tmp_retval.value} = load {tmp_retval.type.str}, {retval.type.str} %{retval.value}, align 8')
        wr.emit(1, f'ret i32 %{tmp_retval.value}')

        wr.emit(0, '}\n')

@dataclass
class Return():
    value: ...

    def compile(self, wr, sc, dest):
        wr.emit(1, f'; return')
        #print("RET SC", sc.locals)
        return_value = sc.symbol()
        self.value.compile(wr, sc, return_value)
        wr.emit(1, f'store {return_value.type.str} %{return_value.value}, {sc.get(RETVAL).type.str} %{sc.get(RETVAL).value}, align 8')
        wr.emit(1, f'br label %{sc.get(COM_RET).value}')


@dataclass
class Block():
    name: str
    content: ...
    
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
            exp.compile(wr, sc, Var(sc.symbol(), None))



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

# TODO find a way to fix this in parser with reference (value)
@dataclass
class Variable():
    name: str

    def compile(self, wr, sc, dest):
        print("LOAD VAR ", self.name)
        location = sc.get(self.name)
        if not location:
            print(f"[ERR][CMP] Variable '{self.name}' does not exist")

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

    def __init__(self, value):
        self.value = int(value)

    def compile(self, wr, sc, dest):
        wr.emit(1, f'%{dest.value} = add {dest.type.str} {self.value}, 0')


@dataclass
class BinaryOp():
    left: ...
    right: ...

class Sum(BinaryOp):
    def compile(self, wr, sc, dest):
        left = sc.symbol()
        right = sc.symbol()
        self.left.compile(wr, sc, left)
        self.right.compile(wr, sc, right)
        wr.emit(1, f'%{dest.value} = add i32 %{left}, %{right}')

class Sub(BinaryOp):
    def compile(self, wr, sc, dest):
        left = sc.symbol()
        right = sc.symbol()
        self.left.compile(wr, sc, left)
        self.right.compile(wr, sc, right)
        wr.emit(1, f'%{dest.value} = sub i32 %{left}, %{right}')



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
            wr.emit(1, f'%{dest.value} = load i32, i32* %{sc.get(RETVAL).value}, align 8')


@dataclass
class Call():
    fn: str
    args: ...
    
    def compile(self, wr, sc:Scope, dest):
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

    def compile(self, wr, sc, dest):
        OPS = {'+': 'add', '-': 'sub', '*': 'mul nuw', '==': 'icmp eq' }
        left = sc.symbol()
        right = sc.symbol()
        self.left.compile(wr, sc, left)
        self.right.compile(wr, sc, right)
        wr.emit(1, f'%{dest.value} = {OPS[self.op]} i32 %{left.value}, %{right.value}')

@dataclass
class Reference():
    id: str
    mut: bool

    def compile(self, wr, sc, dest):
        pass


@dataclass
class Reassignment():
    id: str
    value: ...
    
    def compile(self, wr, sc:Scope, dest):
        
        wr.emit(1, f'; Reassignment')

        
        print("reassign", self.value)
           
        to_reassign = sc.get(self.id)
        if not to_reassign:
            print(f"ERROR: Identifier {self.id} does not exist in the current scope")        
            return
        
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
        print("Index", index)
        # TODO add i compile, (change to value in parser)
        wr.emit(1,'; array access')
        ## TODO: Runtime Bounds check?
        struct = sc.get(self.var.name)
        print("arr acc", struct, self.i)
        load_dest = sc.symbol(typ=struct.type.to.members[0])
        
        IRStructLoad(struct, 0).compile(wr, sc, load_dest)
        IRArrayLoad(load_dest, index).compile(wr, sc, dest)
        print("LOAD DEST", load_dest)

        # print("geting index of ", struct)
        # arr_member_type = struct.type.to.members[0].to
        # print("vec ist filled with", arr_member_type)
        # ptr_to_arr = sc.symbol(typ=Ref(to=struct.type.to.members[0]))
        # print("vec ptr", ptr_to_arr)
        # acc_struct(struct, 0, wr, ptr_to_arr)
        # arr = sc.symbol(typ=ptr_to_arr.type.to)
        # wr.emit(1, f'%{arr.value} = load {arr.type.str}, {ptr_to_arr.type.str} %{ptr_to_arr.value}')
        # index_ptr = sc.symbol(typ=Ref(arr_member_type))
        # wr.emit(1, f'%{index_ptr.value} = getelementptr {arr_member_type.str}, {arr.type.str} %{arr.value}, i32 {self.i.value}')
        #wr.emit(1, f'%{dest.value} = load {load_dest.type.to.str}, {load_dest.type.str} %{load_dest.value}')


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
        
        IRBitcast(Ref(to=arr_const.type), Ref(to=IntType(size=32)), arr_const.value).compile(wr, sc, dest)



@dataclass
class Assignment():
    id: str
    vartype: ...
    value: ...
    
    def compile(self, wr, sc:Scope, dest):
            # TODO static-size array
        
        if type(self.vartype) == ArrayType:
            # TODO break up into / use IR* Classes
            wr.emit_post('declare void @llvm.memcpy.p0.p0.i32(i32*, i32*, i32, i1)') 
            struct = sc.register('vec', NoneType)
            struct.type = StructType(struct.value, [Ref(IntType(size=32)), IntType(size=64), IntType(size=64)]) # TODO make dynamic
            wr.emit_pre(f'{struct.type.str} = type {struct.type.sign_str}') # ptr, size, alloc

            # value result is a pointer to the member type
            value_result = sc.symbol(typ=Ref(to=self.vartype.member_type))
            self.value.compile(wr, sc, value_result)
            wr.emit(1, f'; array init')
            
            if self.vartype.length == '*' or not self.vartype.length:
                arr_size = int(self.vartype.member_type.memsize) * len(self.value.members)
            else:
                arr_size = self.vartype.memsize
            
            the_vector = sc.register(self.id,typ=Ref(to=struct.type)) 
            
            # Allocate memory
            wr.emit(1, f'%{the_vector.value} = alloca {struct.type.str}')
            i8ptr = sc.symbol(typ=Ref(to=IntType(size=8))) # make i8 ptr for malloc
            wr.emit(1, f'%{i8ptr.value} = call i8* (i32) @malloc(i32 {arr_size})') 
            cast_result = sc.symbol(typ=the_vector.type.to.members[0])
            wr.emit(1, f'%{cast_result.value} = bitcast i8* %{i8ptr.value} to {cast_result.type.str}') # cast i8 ptr to i32 ptr
            
            vec_ptr = sc.symbol(typ=Ref(to=struct.type.members[0]))
            print("vec ptr", vec_ptr)
            print("arrptr", the_vector)
            acc_struct(the_vector, 0, wr, vec_ptr)
            wr.emit(1, f'store {cast_result.type.str} %{cast_result.value}, {vec_ptr.type.str} %{vec_ptr.value}' )

            #TODO: Make into IR function:
            wr.emit(1, f'call void @llvm.memcpy.p0.p0.i32(i32* %{cast_result.value}, i32* %{value_result.value}, i32 {arr_size}, i1 false)')
            IRStructStore(the_vector, 1, Number(arr_size)).compile(wr, sc, dest)
            IRStructStore(the_vector, 2, Number(arr_size)).compile(wr, sc, dest)


        else:
            # Compile what the variable is assigned to

            variable = sc.register(self.id, typ=Ref(to=self.vartype))

            # Just a regular variable
            if self.vartype.ptr_depth() == 0:
                value = sc.symbol()
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
