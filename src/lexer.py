import ply.lex as lex

lineno = 0
# Reserved words
reserved = (
    'LET', 'FN', 'RETURN', 'IF', 'ELSE','TRUE', 'FOR', 'WHILE', 'FALSE', 'STRUCT', 'TYPE', 'IN', 'OR',
)

tokens = reserved + (
    # Literals (identifier, integer constant, float constant, string constant,
    # char const)
    'TYPEID', 'ID', 'ICONST', 'SCONST', 'BCONST',
    'INTTYPE',

    # Operators (+,-,*,/,%,|,&,~,^,<<,>>, ||, &&, !, <, <=, >, >=, ==, !=)
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'AMP', 'LOR', 'LAND', 'LNOT', 'EQ', 'LT', 'GT', 'GE', 'LE', 'NE', 'TILDE', 'DEREF',

    # Assignment (=, *=, /=, %=, +=, -=, <<=, >>=, &=, ^=, |=)
    'EQUALS', 
    

    # Increment/decrement (++,--)
    #'PLUSPLUS', 'MINUSMINUS',

    # Structure dereference (->)
    'ARROW',

    # Conditional operator (?)
    #'CONDOP',

    # Compiler directive
    'COMP_DIR',

    # Delimeters ( ) [ ] { } , . ; :
    'LPAREN', 'RPAREN',
    'LBRACKET', 'RBRACKET',
    'LBRACE', 'RBRACE',
    'COMMA', 'SEMI', 'COLON', 'PERIOD',

    # Ellipsis (...)
    #'ELLIPSIS',
)

# Completely ignored characters
t_ignore = ' \t\x0c'

# Newlines


def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

# Operators
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DEREF = r'\*+'
t_DIVIDE = r'/'
t_MOD = r'%'
#t_OR = r'\|'
t_AMP = r'&+'
t_TILDE = r'~'
#t_XOR = r'\^'
#t_LSHIFT = r'<<'
#t_RSHIFT = r'>>'
t_LOR = r'\|\|'
t_LAND = r'&&'
t_LNOT = r'!'

t_LT = r'<'
t_GT = r'>'
t_LE = r'<='
t_GE = r'>='
t_EQ = r'=='
t_NE = r'!='

#t_HASHTAG = r'#'

# Assignment operators

t_EQUALS = r'='
#t_TIMESEQUAL = r'\*='
#t_DIVEQUAL = r'/='
#t_MODEQUAL = r'%='
#t_PLUSEQUAL = r'\+='
#t_MINUSEQUAL = r'-='
#t_LSHIFTEQUAL = r'<<='
#t_RSHIFTEQUAL = r'>>='
#t_ANDEQUAL = r'&='
#t_OREQUAL = r'\|='
#t_XOREQUAL = r'\^='

# Increment/decrement
#t_PLUSPLUS = r'\+\+'
#t_MINUSMINUS = r'--'

# ->
t_ARROW = r'->'

# ?
#t_CONDOP = r'\?'

# Delimeters
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_COMMA = r','
t_PERIOD = r'\.'
t_SEMI = r';'
t_COLON = r':'
#t_ELLIPSIS = r'\.\.\.'

# Identifiers and reserved words

reserved_map = {}
for r in reserved:
    reserved_map[r.lower()] = r


def t_ID(t):
    r'[A-Za-z_][\w_]*'
    t.type = reserved_map.get(t.value, "ID")
    #print(t)
    return t



# Integer literal
t_ICONST = r'\d+'

# Floating literal
#t_FCONST = r'((\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))([lL]|[fF])?'

# String literal
t_SCONST = r'\"([^\\\n]|(\\.))*?\"'

# Character constant 'c' or L'c'
#t_CCONST = r'(L)?\'([^\\\n]|(\\.))*?\''

# Comments
def t_comment(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

# Preprocessor directive (ignored)
def t_COMP_DIR(t):
    r'\#.*'
    #print("LEXER GOT", t)
    t.lexer.lineno += 1
    return t


def t_error(t):
    #print("WARN: Illegal character %s" % repr(t.value[0]))
    t.lexer.skip(1)

lexer = lex.lex()
#print(lexer)