from dataclasses import dataclass

@dataclass
class Var():
    value: ...
    type: str

@dataclass
class ArrayVar():
    ptr: ...
    memtype: ...
    length: Var
    allocated: Var