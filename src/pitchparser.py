import ply.yacc as yacc
import src.nodes as nodes
from src.pitchlexer import PitchLexer
from src.pitchtypes import MaybeType, ReferenceType, TypeBase, UnknownType, UnresolvedType
from src.scope import Scope


class PitchParser(object):

    tokens = PitchLexer.tokens

    def p_program(self, t):
        '''
        program : top_level_statement
                | program top_level_statement
        '''
        if len(t) == 2:
            t[0] = nodes.Program([t[1]])
        else:
            t[0] = t[1].append(t[2])

    def p_top_level_def(self, t):
        '''
        top_level_statement : def_statement
                            | def_definition
                            | function
                            | statement
        '''
        t[0] = t[1]

    def p_function(self, t):
        '''
        function : FN ID LPAREN RPAREN type block
                | FN ID LPAREN parameters RPAREN type block
        '''
        if len(t) == 7:
            t[0] = nodes.Function(id=t[2], params=None,
                                  return_type=t[5],  block=t[6])
        else:
            t[0] = nodes.Function(id=t[2], params=t[4],
                                  return_type=t[6], block=t[7])

    def p_block(self, t):
        '''
        block : LBRACE statement_list RBRACE
        '''
        t[0] = nodes.Block(t[2])

    def p_statement_list(self, t):
        '''
        statement_list : statement
                       | statement_list statement
        '''
        if len(t) == 2:
            t[0] = nodes.StatementList([t[1]])
        else:
            t[0] = t[1].append(t[2])

    def p_expression_binop(self, t):
        '''
        expression : expression PLUS expression
                   | expression MINUS expression
                   | expression TIMES expression
                   | expression DIVIDE expression
                   | expression DOUBLE_EQUALS expression
        '''
        left_hand_side = t[1]
        right_hand_side = t[3]
        operator = t[2]

        t[0] = nodes.Expression(left_hand_side, right_hand_side, operator)

    def p_expression_group(self, t):
        '''
        expression : LPAREN expression RPAREN
        '''
        t[0] = nodes.Group(t[2])

    def p_expression_int(self, t):
        '''
        expression : ICONST
        '''
        t[0] = nodes.Integer(t[1], 32)

    def p_expression_id(self, t):
        '''
        expression : ID
        '''
        t[0] = nodes.Identifier(t[1])

    def p_refernce(self, t):
        '''
        expression : AMPERSAND expression
        '''
        t[0] = nodes.Reference(t[2])

    def p_dereference(self, t):
        '''
        expression : TIMES expression
        '''
        t[0] = nodes.Dereference(t[2])

    def p_return(self, t):
        '''
        statement : RETURN expression SEMI
        '''
        t[0] = nodes.Return(t[2])

    def p_assignment(self, t):
        '''
        statement : LET ID EQUALS expression SEMI
        '''
        t[0] = nodes.Assignment(id=t[2], expression=t[4], type=UnknownType())

    def p_typed_assignment(self, t):
        '''
        statement : LET ID COLON type EQUALS expression SEMI
        '''
        t[0] = nodes.Assignment(id=t[2], expression=t[6], type=t[4])

    def p_reassignment(self, t):
        '''
        statement : ID EQUALS expression SEMI
        '''
        t[0] = nodes.Assignment(type="int", id=t[1], expression=t[3])

    def p_if(self, t):
        '''
        statement : IF LPAREN expression RPAREN block
        '''
        t[0] = nodes.If(t[3], t[5])

    def p_call(self, t):
        '''
        expression : ID LPAREN RPAREN
                     | ID LPAREN arguments RPAREN
        '''
        if len(t) == 4:
            t[0] = nodes.Call(id=t[1])
        else:
            t[0] = nodes.Call(id=t[1], args=t[3])

    def p_arguments(self, t):
        '''
        arguments : expression
                  | arguments COMMA expression
        '''
        if len(t) == 2:
            t[0] = nodes.ArgumentList([t[1]])
        else:
            t[0] = t[1].append(t[3])

    def p_compiler_func_call(self, t):
        '''
        expression : HASH ID LPAREN arguments RPAREN
        '''
        t[0] = nodes.CompCall(id=t[2], arguments=t[4])

    def p_error(self, t):
        print(f"Syntax error at {t.value}")

    def p_string(self, t):
        '''
        expression : STRCONST
        '''
        t[0] = nodes.String(t[1])

    def p_def_statement(self, t):
        '''
        def_statement : DEF ID SEMI
        '''
        t[0] = nodes.DefStatement(id=t[2])

    def p_def_definition(self, t):
        '''
        def_definition : DEF ID FOR ID expression SEMI
        '''

        t[0] = nodes.DefDefinition(
            id=t[2], def_for=t[4], expression=t[5]
        )

    def p_parameter(self, t):
        '''
        parameter : ID COLON ID
        '''
        t[0] = nodes.Parameter(id=t[1], type=t[3])

    def p_parameters(self, t):
        '''
        parameters : parameter
                   | parameters COMMA parameter
        '''
        if len(t) == 2:
            t[0] = nodes.ParameterList([t[1]])
        else:
            t[0] = t[1].append(t[3])

    def p_named_block(self, t):
        '''
        named_block : ID block
        '''
        t[0] = nodes.NamedBlock(id=t[1], block=t[3])

    def p_type(self, t):
        '''
        type : ID
        '''
        t[0] = UnresolvedType(t[1]).resolve()

    def p_reference_type(self, t):
        '''
        type : REF type
        '''
        print("Reference 1 to ", t[2])
        t[0] = ReferenceType(t[2])

    def p_type_or_err(self, t):
        '''
        type : type QUESTIONMARK
        '''
        t[0] = MaybeType(ok_type=t[1])

    start = 'program'

    precedence = (
        ('left', 'DOUBLE_EQUALS'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('nonassoc', 'LBRACE'),
        ('nonassoc', 'TIMES'),
        ('nonassoc', 'AMPERSAND'),


    )

    def __init__(self):
        self.lexer = PitchLexer()
        self.parser = yacc.yacc(module=self, outputdir="generated")

    def parse(self, data):
        return self.parser.parse(data, debug=False)
