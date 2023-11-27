class CProgram():
    def __init__(self):
        self._children = []

    def append_function(self, function):
        self._children.append(function)
        return self

    def to_string(self, level=0):
        return '\n'.join([child.to_string() for child in self._children])


class CStatement():
    def __init__(self, data):
        self.data = data

    def to_string(self, level=0):
        return self.data


class CBlock():
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self._statements: list[CStatement] = []

    def append(self, statement: CStatement):
        self._statements.append(statement)
        return self

    def to_string(self, level=0):
        return '    '*(level+1) + '\n'.join([statement.to_string() for statement in self._statements])


class CFunction():
    def __init__(self, return_type, name, args, root, parent):
        self.return_type = return_type
        self.name = name
        self.args = args
        self.body = CBlock(root, self)
        self.root = root
        self.parent = parent

    def append_statement(self, statement: CStatement):
        self.body.append(statement)
        return self

    def to_string(self, level=0):
        return f'{self.return_type} {self.name}({self.args}) {{\n{self.body.to_string()}\n}}'


class CWriter():
    def __init__(self, block=None):
        self.imports = []
        self.block = block

    def add_import(self, data):
        self.program.append_function(CStatement(data))
        return self

    def append_statement(self, data):
        self.block.append_function(CStatement(data))
        return self

    def to_string(self):
        return self.program.to_string()
