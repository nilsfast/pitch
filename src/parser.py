from lark import Lark, Transformer, Tree, tree
from lark.reconstruct import Reconstructor
import pitch_ast as ast
from pprint import pprint
from semantic_analyzer import SemanticAnalyzer
from compiler import CodeGenerator
from memory_manager import MemoryManager

from shared import logger

# from code_generator import CodeGenerator

parser = Lark(open("src/pitch.lark"), start="program")


source_code = ""

with open("test.p") as f:
    source_code = f.read()

ast1 = parser.parse(source_code)
print(f"vorher: {source_code}")
print(ast1.pretty())

print()


class AstBuilder(Transformer):
    def __init__(self):
        super().__init__()

    def program(self, items):
        return ast.Program(items)

    def func_decl(self, items):
        print(items)

        return ast.Function(
            str(items[0]),  # function name
            items[1],  # parameters
            items[2],  # return type
            items[3],  # function body
        )

    def param_list(self, items):
        return items

    def param(self, items):
        return ast.Param(items[0], items[1])

    def block(self, items):
        return ast.Block(items)

    def var_decl(self, items):
        name = items[0]
        type_ = items[1]
        expr = items[2]
        return ast.VarDecl(name, type_, expr)

    def type(self, items):
        str_items = list(map(str, items))
        print("Type", str_items)
        _box = "box" in str_items
        _typename = str_items[0] if not _box else str_items[1]
        _nullable = "?" in str_items

        return ast.Type(_typename, _nullable, _box)

    def block(self, items):
        return ast.Block(items)

    def identifier(self, items):
        return ast.Id(str(items[0]))

    def base_type(self, items):
        print("Base type", items)
        return ast.Type(str(items[0]))

    def nullable_type(self, items):
        print("Nullable type", items)
        if isinstance(items[0], ast.Type):
            return ast.Type(
                typename=str(items[0].typename), nullable=True, of=items[0].of
            )

    def type_template(self, items):
        print("Type template", items)
        assert isinstance(items[2], ast.Type), "Expected a TypeBase instance"
        return ast.Type(typename=str(items[0]), nullable=False, of=items[2])

    def NUMBER(self, items):
        return {
            "type": "number",
            "value": str(items[0]),
        }

    def literal(self, items):
        return ast.NumberLiteral(items[0])

    def assignment(self, items):
        return ast.Assignment(items[0], items[1])

    def string_literal(self, items):
        return ast.StringLiteral(str(items[0]))

    def return_stmt(self, items):
        return ast.Return(items[1])

    def expr(self, items):
        return items[0]

    def add(self, items):
        return ast.BinaryExpr(items[0], "+", items[2])

    def subtract(self, items):
        return ast.BinaryExpr(items[0], "-", items[2])

    def multiply(self, items):
        return ast.BinaryExpr(items[0], "*", items[2])

    def divide(self, items):
        return ast.BinaryExpr(items[0], "/", items[2])

    def modulo(self, items):
        return ast.BinaryExpr(items[0], "%", items[2])

    def negate(self, items):
        return ast.UnaryExpr("-", items[1])

    def reference(self, items):
        return ast.Reference(str(items[0]))

    def group(self, items):
        return ast.GroupedExpr(items[1])

    def call(self, items):
        return ast.Call(items[0], items[1])

    def call_args(self, items):
        return items

    def dereference(self, items):
        return ast.Dereference(items[1])

    LITERAL = str
    IDENTIFIER = str


# Example usage
ast2 = AstBuilder().transform(ast1)

pprint(ast2, indent=2)

logger.start_span("SA")
# Perform semantic analysis
analyzer = SemanticAnalyzer()
semantic_errors = analyzer.analyze(ast2)
logger.log(analyzer.get_symbol_table())

if semantic_errors:
    logger.error("Semantic errors found:")
    for error in semantic_errors:
        logger.error(error)
    exit(1)

logger.info("No semantic errors found.")
pprint(ast2, indent=2)
logger.end_span()

memory_manager = MemoryManager()
errors = memory_manager.analyze(ast2)

if errors:
    print("Memory management errors found:")
    for error in errors:
        print(error)
    exit(1)
print("No memory management errors found.")

code_generator = CodeGenerator()
c_code = code_generator.generate(ast2)

print()
print(c_code)

# Generate C code
# generator = CodeGenerator()
# c_code = generator.generate(ast2)
#
# # Output the generated C code
# output_file = "output.c"
# with open(output_file, "w") as f:
#     f.write(c_code)
#
# print(f"C code generated and written to {output_file}")
