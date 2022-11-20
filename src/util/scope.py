from mimetypes import suffix_map
from .var import Var
import util.type_manager as tm

class Scope():
    locals = {}

    def __init__(self) -> None:
        self.locals = {}

    def register(self, name, typ=tm.IntType(size=32), dyn_type=False):
        """
        Adds name and a unique suffix to the local register and returns the new name 
        """
        print("[CMP][REG] Registering", name)
        dynamic_type = True if dyn_type else False
        name_with_suffix = name 
        suffix = 0

        while name_with_suffix in list(map(lambda x: self.locals[x].value, self.locals)):
            name_with_suffix = name + str(suffix)
            suffix += 1
        
        if name[0:2] == 'sym':  
            self.locals[name_with_suffix] = Var(name_with_suffix, typ, dynamic_type)
        else:
            self.locals[name] = Var(name_with_suffix, typ, dynamic_type)

        return Var(name_with_suffix, typ, dynamic_type)

    def reassign(self, var:Var, value):
        self.locals[var.value] = value

    def symbol(self, prefix='sym', typ=tm.IntType(size=32), dyn_type=False):
        """Returns a safe new name"""
        return self.register(prefix+str(len(self.locals)), typ, dyn_type)   

    def get(self, name):
        if not name in self.locals:
            return None
        return self.locals[name]
    
    def copy_to_new_scope(self):
        s = Scope()
        s.locals = s.locals | self.locals
        return s 