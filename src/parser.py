import ply.yacc as yacc
from codegen import *
from util.type_manager import *

from lexer import tokens, lineno


def p_module(p):
    ''' module : definitions'''
    p[0] = Module(dependencies=[], definitions=p[1])

def p_definitions(p):
    ''' definitions : function definitions
                 | function
                 | compiler_directive
                 | compiler_directive definitions'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]


def p_function(p):
    ''' function : FN ID LPAREN parameters RPAREN type block'''
    
    p[0] = Function(name=p[2], params=p[4], rettype=p[6], block=p[7])

def p_block(p):
    ''' block : LBRACE statements RBRACE'''
    p[0] = Block('entry', p[2])


def p_statements(p):
    ''' statements : statements statement
                   | statement
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_statement(p):
    ''' statement : acc_call SEMI
                | assignment
                | reassignment
                | function
                | call SEMI
                | conditional
                | for
                | return
                | compiler_directive '''  
    p[0] = p[1]

def p_return(p):
    ''' return : RETURN expr SEMI
                | RETURN SEMI'''
    p[0] = Return(value=p[2])

def p_conditional(p):
    ''' conditional : IF expr block ELSE block'''
    p[0] = Conditional(condition=p[2], if_true=p[3], if_false=p[5])

def p_for(p):
    ''' for : WHILE expr block'''
    p[0] = WhileLoop(cond=p[2], content=p[3])

#def p_for(p):
#    ''' for : FOR LPAREN expr RPAREN block 
#            | FOR LPAREN expr RPAREN block '''
#    p[0] = For(p[3], p[5], p[7])

def p_struct(p):
    ''' struct : STRUCT ID block'''
    p[0] = Struct(name=p[2], members=p[3])

def p_assignee(p):
    ''' assignee : deref
                 | ID
    '''
    print("ASS", p[1])
    p[0] = p[1]

def p_reassignment(p):
    ''' reassignment : assignee EQUALS expr SEMI
                    | array_index EQUALS expr SEMI'''
    
    # TODO rename id to var
    p[0] = Reassignment(id=p[1], value=p[3])
    

def p_assignment(p):
    ''' assignment : LET assignee COLON type EQUALS expr SEMI
                   | LET assignee EQUALS expr SEMI'''

    if p[3] == ":":
        # TODO new variable
        p[0] = Assignment(var=V(p[4], p[2]), value=p[6])
    else:
        # TODO implement NewVariable
        p[0] = Assignment(id=p[2], vartype=p[4], value=p[6])

def p_list(p):
    '''list : value COMMA list
            | value'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_array(p):
    '''array : LBRACKET list RBRACKET
                | LBRACKET empty RBRACKET'''
    p[0] = ArrayLiteral(members=p[2])

def p_array_index(p):
    ''' array_index : value LBRACKET value RBRACKET'''
    p[0] = ArrayIndex(var=p[1], i=p[3])


def p_n_reference(p):
    ''' n_reference : AMP ID'''
    print("FOUND REFERENCE")
    p[0] = Reference(p[2], False)

    
def p_deref(p):
    ''' deref : DEREF ID'''
    p[0] = Deref(name=p[2], depth=len(p[1])).resolve()  

#def p_type_or_value(p):
#    '''type_or_value : value
#                    | I32
#                    | I64
#                    | AMP I32
#                    | template_type '''
#    p[0] = p[1]


def p_value(p):
    ''' value : var
              | number
              | call
              | acc_call
              | bool
              | array
              | array_index
              | n_reference
              | TIMES var
              | string
              | multiple_reassignments'''
    if p[1] == '*':
        print("found deref")
        p[0] = Deref(ref=p[2])
    else:
        p[0] = p[1]
    

def p_var(p):
    ''' var : ID'''
    p[0] = Variable(p[1])

def p_multiple_reassignments(p):
    ''' multiple_reassignments : LPAREN mult_reas RPAREN'''
    p[0] = MR(p[2])

def p_mult_reas(p):
    ''' mult_reas : EQUALS expr mult_reas
                  | EQUALS expr
    '''
    if len(p) == 3:
        p[0] = p[2]
    else:
        if type(p[3]) == list:
            p[0] = [p[2]]+ p[3]
        else: 
            p[0] = [p[2], p[3]]

def p_arrtype(p):
    '''arrtype : LBRACKET type SEMI number RBRACKET
               | LBRACKET type SEMI TIMES RBRACKET
               | LBRACKET type empty empty RBRACKET'''
    p[0] = ArrayType(member_type=p[2], length=p[4])

# ERROR RESOLVE TYPE MEHTOD

def p_template_type(p):
    ''' template_type : type LBRACKET list RBRACKET'''
    print("TEMPLATE FOUND",p[1])
    p[0] = TemplateType(p[1], p[3])


def p_type(p):
    '''type : AMP type
            | arrtype
            | template_type
            | ID'''
    print("TYPE", p[1])
    if type(p[1]) == str:
        p[0] = resolve_type(p[1])
    elif len(p) == 3:
        p[0] = BaseType(p[1:]).resolve()
    elif len(p) == 4:
        p[0] = BaseType(p[1:]).resolve()
    elif type(p[1]) == TemplateType:
        p[0] = p[1]
    else:
        p[0] = BaseType([p[1]]).resolve()


def p_expr(p):
    ''' expr : expr PLUS expr
             | expr MINUS expr
             | expr TIMES expr
             | expr DIVIDE expr
             | expr LT expr
             | expr GT expr
             | expr LE expr
             | expr GE expr
             | expr EQ expr
             | expr NE expr
             | value
    '''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = Expression(op=p[2], left=p[1], right=p[3])



def p_empty(p):
    'empty :'
    return

def p_acc_call(p):
    '''acc_call : ID PERIOD call
               | ID PERIOD acc_call
    '''
    p[0] = AccCall(of=p[1], to=p[3])

def p_call(p):
    ''' call : ID LPAREN arguments RPAREN
    '''
    p[0] = Call(fn=p[1], args=p[3])


def p_arguments(p):
    ''' arguments : arg COMMA arguments
              | arg
              | empty
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_arg(p):
    ''' arg : expr'''
    p[0] = p[1]


def p_parameters(p):
    ''' parameters : parameter COMMA parameters
              | parameter
              | empty
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_parameter(p):
    ''' parameter : ID COLON type
    '''

    p[0] = Parameter(id=p[1], t=p[3])

def p_compiler_directive(p):
    ''' compiler_directive : COMP_DIR '''
    print("PARSER GOT", type(p[1]), p[1])
    p[0] = CompilerDirective(p[1])


def p_number(p):
    ''' number : ICONST
    '''
    p[0] = Number(value=p[1])

def p_string(p):
    ''' string : SCONST
    '''
    p[0] = String(value=p[1][1:-1])

def p_bool(p):
    ''' bool : TRUE
             | FALSE
    '''
    p[0] = True if p == "true" else False


precedence = (
    ('left', 'LOR'),
    ('left', 'LAND'),
    ('left', 'EQ', 'NE'),
    ('left', 'LT', 'GT', 'LE', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('nonassoc', 'LNOT'),
    ('nonassoc', 'AMP'),
    ('nonassoc', 'DEREF'),
    ('nonassoc', 'LBRACE'),

)

start = 'module'


parser = yacc.yacc()


# TODO implement, fix
#def p_boolexpr(p):
#    ''' boolexpr : boolexpr LAND boolexpr
#                 | boolexpr LOR boolexpr
#                 | LNOT boolexpr
#                 | bool'''
#    p[0] = BoolExp(op=p[2], left=p[1], right=p[3])
