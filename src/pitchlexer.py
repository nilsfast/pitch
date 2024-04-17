import ply.lex as lex

from src.nodes.utils import printlog


class PitchLexer(object):
    tokens = [
        'ID',
        'PLUS',
        'MINUS',
        'TIMES',
        'DIVIDE',
        'LPAREN',
        'RPAREN',
        'LBRACE',
        'RBRACE',
        'SEMI',
        'ICONST',
        'FCONST',
        'EQUALS',
        'DOUBLE_EQUALS',
        'HASH',
        'COMMA',
        'STRCONST',
        'COLON',
        'QUESTIONMARK',
        'EXCLAMATIONMARK',
        'AMPERSAND',
        'DEREFERENCE',
        'FIELD_DEREFERENCE',
    ]

    # Reserved words
    reserved = {
        'fn': 'FN',
        'return': 'RETURN',
        'let': 'LET',
        'if': 'IF',
        'else': 'ELSE',
        'for': 'FOR',
        'def': 'DEF',
        'struct': 'STRUCT',
        'enum': 'ENUM',
        'type': 'TYPE',
        'true': 'TRUE',
        'false': 'FALSE',
        'null': 'NULL',
        'ref': 'REF',
        'mut': 'MUT',
        'impl': 'IMPL',
        'in': 'IN',
        'as': 'AS',
        'match': 'MATCH',
        'case': 'CASE',
        'default': 'DEFAULT',
        'break': 'BREAK',
        'continue': 'CONTINUE',
        'while': 'WHILE',
        'do': 'DO',
        'import': 'IMPORT',

    }

    tokens += reserved.values()

    # Regular expression rules for simple tokens
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_SEMI = r';'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_EQUALS = r'='
    t_DOUBLE_EQUALS = r'=='
    t_HASH = r'\#'
    t_COMMA = r','
    t_COLON = r':'
    t_QUESTIONMARK = r'\?'
    t_EXCLAMATIONMARK = r'!'
    t_AMPERSAND = r'&'
    t_DEREFERENCE = r'\*'
    t_FIELD_DEREFERENCE = r'\-\>'

    # A regular expression rule with some action code
    # Note addition of self parameter since we're in a class

    def t_ICONST(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_STRCONST(self, t):
        r'\".*\"'
        t.value = str(t.value)
        return t

    def t_FCONST(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'

        if t.value in self.reserved:
            t.type = self.reserved[t.value]
        return t

    # Define a rule so we can track line numbers

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore = ' \t'

    # Error handling rule
    def t_error(self, t):
        printlog(f"Illegal character '{t.value[0]}'")
        t.lexer.skip(1)

    def __init__(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # Test it output
    def test(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            printlog(tok)
