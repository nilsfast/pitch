from error import comp_err
from .var import Var
import util.type_manager as tm

class TypeTable():
    table = {}

    def __init__(self, parent = {}) -> None:
        self.table = parent

    def register(self, name:str, t:tm.BaseType):
        if name in self.table:
            comp_err(f"Type '{name}' already in type table")

        self.table[name] = t        

    def get(self, name):
        return self.table[name]

    def check_type(self, name, type):
        return self.get(name) == type
    
