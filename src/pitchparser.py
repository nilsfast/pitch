import ply.yacc as yacc
import src.nodes as nodes
from src.nodes.utils import printlog
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
        top_level_statement : function
                            | statement
                            | struct
                            | import_statement
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

    def p_import_statement(self, t):
        '''
        import_statement : IMPORT ID SEMI
        '''
        t[0] = nodes.ImportStatement(id=t[2])

    def p_struct_member(self, t):
        '''
        struct_member : ID COLON type SEMI
        '''
        t[0] = nodes.StructMember(id=t[1], type=t[3])

    def p_struct_members(self, t):
        '''
        struct_members : struct_member
                       | struct_members struct_member
        '''
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            t[1].append(t[2])
            t[0] = t[1]

    def p_struct(self, t):
        '''
        struct : STRUCT ID LBRACE struct_members RBRACE
        '''
        printlog("struct", t[4])
        t[0] = nodes.Struct(id=t[2], members=t[4])

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

    def p_field_dereference(self, t):
        '''
        expression : expression FIELD_DEREFERENCE ID
        '''
        t[0] = nodes.FieldDereference(t[1], t[3])

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
        statement : expression EQUALS expression SEMI
        '''
        t[0] = nodes.Reassignment(lexpr=t[1], rexpr=t[3])

    def p_if(self, t):
        '''
        statement : IF LPAREN expression RPAREN block
        '''
        t[0] = nodes.If(t[3], t[5])

    def p_call_statement(self, t):
        '''
        statement : expression SEMI
        '''
        t[0] = nodes.ExpressionStatement(t[1])

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
        printlog(f"Syntax error")
        printlog(t.type, t.value, t.lineno, t.lexpos)

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
        parameter : ID COLON type
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

    def p_ref_expression(self, t):
        '''
        expression : REF ID
        '''
        t[0] = nodes.Reference(nodes.Identifier(t[2]))

    def p_type_ref(self, t):
        '''
        type : REF type
            | AMPERSAND type
        '''
        t[0] = ReferenceType(t[2])

    def p_type_or_err(self, t):
        '''
        type : type QUESTIONMARK
        '''
        t[0] = MaybeType(ok_type=t[1])

    def p_struct_inint_member(self, t):
        '''
        struct_init_member : ID COLON expression
        '''
        t[0] = nodes.StructInitMember(id=t[1], expression=t[3])

    def p_struct_init_members(self, t):
        '''
        struct_init_members : struct_init_member
                            | struct_init_members COMMA struct_init_member
        '''
        if len(t) == 2:
            t[0] = [t[1]]
        else:
            printlog(t[0], t[1], t[3])
            t[0] = t[1] + [t[3]]

    def p_struct_init(self, t):
        '''
        expression : ID LBRACE struct_init_members RBRACE
        '''
        t[0] = nodes.StructInit(id=t[1], members=t[3], alloc=False)

    start = 'program'

    precedence = (
        ('left', 'DOUBLE_EQUALS'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('nonassoc', 'LBRACE'),
        ('nonassoc', 'TIMES'),
        ('nonassoc', 'REF'),
        ('nonassoc', 'AMPERSAND'),



    )

    def __init__(self, outputdir="generated"):
        self.lexer = PitchLexer()
        self.parser = yacc.yacc(module=self, outputdir=outputdir)

    def parse(self, data):
        return self.parser.parse(data, debug=False)
