from urllib.error import ContentTooShortError

class Substatement():
    in_block = False
    def __init__(self) -> None:
        self.in_block = False
        pass

    def __str__(self) -> str:
        pass

class String(Substatement):
    content = ""
    def __init__(self, content) -> None:
        self.content = content
    
    def __str__(self) -> str:
        return f'{self.content}'

class Statement(Substatement):
    in_block = False
    def __init__(self) -> None:
        self.in_block = False
        pass

    def __str__(self) -> str:
        pass


class Block():
    content = []
    indent = 0
    top_lvl = False
    def __init__(self, is_top_level=False, indent=4) -> None:
        self.indent = indent
        self.content = []
        self.top_lvl = is_top_level
    
    def add(self, elem, is_string=False):
        if not is_string:
            if type(elem) == Function:
                is_string = True
        if isinstance(elem, Statement):
            elem.in_block = True
        self.content.append({'str': is_string, 'elem': elem})
    
    def add_str(self, elem):
        self.content.append({'str': True, 'elem': elem})
    
    
    def __str__(self) -> str:
        txt = ''
        for c in self.content:
            print(c)
            txt += str(c['elem'])
            if not c['str']:
                txt += ';\n'
            if self.top_lvl:
                txt += '\n'
        return txt


class Variable(Substatement):
    name = ""
    typ = ""

    def __init__(self, name , typ) -> None:
        self.name = name
        self.typ = typ

    def __str__(self) -> str:
        return f'{self.typ} {self.name}'

class Assignment(Statement):
    var: Variable = None
    val: any = None

    def __init__(self, variable, value) -> None:
        self.var = variable
        self.val = value

    def __str__(self) -> str:
        return f'{str(self.var)} = {str(self.val)}'



class Return(Statement):
    val: any = None

    def __init__(self, value) -> None:
        self.val = value

    def __str__(self) -> str:
        return f'return {str(self.val)}'


class Call(Statement):
    args = []
    fn = ""

    def __init__(self, fn, args) -> None:
        self.fn = fn
        self.args = args

    def __str__(self) -> str:
        args = ', '.join([str(a) for a in self.args])
        if self.in_block:   
            return f'{self.fn}({args});\n'
        else:
            return f'{self.fn}({args})'

class Function(Statement):
    ret_type = None
    name = ""
    args = []
    content = None

    def __init__(self, return_type, name, args) -> None:
        self.ret_type = return_type
        self.name = name
        self.args = args
        self.content = Block()
        
    def __str__(self) -> str:
        args = ', '.join([str(a) for a in self.args])
        return f'{self.ret_type} {self.name}({args}) {"{"}\n{str(self.content)}{"}"}\n'

