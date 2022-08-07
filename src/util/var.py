from dataclasses import dataclass

class Var():
    value = ''
    type = None
    dynamic_type = False

    def __init__(self, value, typ, dynamic_type) -> None:
        self.value = value
        self.type = typ
        self.dynamic_type = dynamic_type
    
    def __repr__(self):
        return f"Var(value={self.value}, type={self.type}, dyn_type={self.dynamic_type})"





@dataclass
class ArrayVar():
    ptr: ...
    memtype: ...
    length: Var
    allocated: Var