from src.context import Context


class CProgram():
    def __init__(self):
        self._children = []

    def append_function(self, function):
        self._children.append(function)
        return self

    def set_statement(self, statements):
        self._children = statements
        return self

    def to_string(self, level=0):
        # print("program to string called", self._children)
        return '\n\n'.join([child.to_string() for child in self._children])


class CStatement():
    def __init__(self, data):
        self.data = data

    def to_string(self, level=0):
        return self.data


class CBlock():
    def __init__(self):
        self.statements: list[CStatement] = []

    def append(self, statement: CStatement):
        self.statements.append(statement)
        return self

    def to_string(self, level=0):
        join_char = "\n" + ("    "*level)
        return ("    "*level) + join_char.join([statement.to_string(level=level+1) for statement in self.statements])


class CFunction():
    def __init__(self, return_type, name, args, root, parent):
        self.return_type = return_type
        self.name = name
        self.args = args
        self.body = CBlock()
        self.root = root
        self.parent = parent

    def append_statement(self, statement: CStatement):
        self.body.append(statement)
        return self

    def to_string(self, level=0) -> str:
        # print("c func to string called", self.body, self.body._statements)
        return f'{self.return_type} {self.name}({self.args}) {{\n{self.body.to_string(level=level+1)}\n}}'


class CWriter():
    def __init__(self, top_level_writer=None):
        self.statements = []
        self.top_level_writer = top_level_writer
        self.imports = []

    def append_tls(self, data):
        self.top_level_writer.append_unique(data)
        return self

    def add_import(self, lib: str):
        self.imports.append(lib)
        return self

    def append_statement(self, data):
        self.statements.append(CStatement(data))
        return self

    def append(self, data):
        self.statements.append(data)
        return self

    def append_unique(self, data):
        for statement in self.statements:
            if type(statement) == type(data) and statement.data == data.data:
                return
        self.statements.append(data)

    def export(self):
        statements = []
        if not self.top_level_writer:
            for lib_import in self.imports:
                statements.append(CStatement(f"#include <{lib_import}>"))
        statements.extend(self.statements)

        return statements

    def to_string(self):
        return self.program.to_string()


class PitchString():

    def __init__(self, value, size):
        self.value = value
        self.size = size

    def to_const(self, writer: CWriter, context: Context):
        char_array = "{"+",".join([f"'{char}'" for char in self.value])+"}"

        writer.append_tls(CStatement(
            "#include <stdio.h> \n#include <string.h>"))

        writer.append_tls(CStatement(
            "typedef struct { char*ptr; int len;} _pt_str;"))

        char_const_var = context.register_symbol("cconst")

        writer.append(CStatement(
            f"char {char_const_var}[{self.size}] = {char_array};"))

        # str_struct = context.register_symbol("str")

        # writer.append(cgen.CStatement(
        #     f'_pt_str {str_struct} = {{ {char_const_var}, {self.t.size} }};'))

        return f'(_pt_str){{ {char_const_var}, {self.size} }}'
