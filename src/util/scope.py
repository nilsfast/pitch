from .var import Var
import util.type_manager as tm

class Scope():
    locals = {}

    def __init__(self) -> None:
        self.locals = {}

    def register(self, name, typ=tm.IntType(size=32)):
        """
        Adds name and a unique suffix to the local register and returns the new name 
        """
        suffix = 1
        name_with_suffix = name 

        if name == 'sym':
            name_with_suffix += str(suffix)

        while name_with_suffix in list(map(lambda x: self.locals[x].value, self.locals)):
            name_with_suffix = name + str(suffix)
            suffix += 1
        
        if name == 'sym':  
            self.locals[name_with_suffix] = Var(name_with_suffix, typ)
        else:
            self.locals[name] = Var(name_with_suffix, typ)

        return Var(name_with_suffix, typ)

    def reassign(self, var:Var, value):
        self.locals[var.value] = value

    def symbol(self, prefix='sym', typ=tm.IntType(size=32)):
        """Returns a safe new name"""
        return self.register(prefix, typ=typ)   

    def get(self, name):
        if not name in self.locals:
            return None
        return self.locals[name]
    
    def copy_to_new_scope(self):
        s = Scope()
        s.locals = s.locals | self.locals
        return s 