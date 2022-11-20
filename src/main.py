import os
from codegen import Module
from parser import parser
from error import comp_err, ice
import sys
import pprint
from util.scope import Scope
from util.type_table import TypeTable
from util.writer import MemWriter, Writer
import pathlib
from timeit import default_timer as timer

STD_LIB = """
%pitch.res = type {i1, ptr} ; 0 = ok, 1 = err

define ptr @pitch_err(ptr %vptr) {
    %r = alloca %pitch.res, align 8
    %t = getelementptr %pitch.res, ptr %r, i32 0, i32 0
    store i1 1, i1* %t
    %v = getelementptr %pitch.res, ptr %r, i32 0, i32 1
    store ptr %vptr, ptr %v
    ret ptr %r
}
define %pitch.res @pitch_ok(ptr %vptr) {
    %r = alloca %pitch.res, align 8
    %t = getelementptr %pitch.res, ptr %r, i32 0, i32 0
    store i1 0, i1* %t
    %v = getelementptr %pitch.res, ptr %r, i32 0, i32 1
    store ptr %vptr, ptr %v
    %drefv = load %pitch.res, ptr %r
    ret %pitch.res %drefv
}
"""

def main():

    #print(pathlib.Path(__file__).parent.resolve())
    outpath = os.path.normpath(os.getcwd())+os.sep+'build'+os.sep+'out.ll'
    filename = sys.argv[1]

    pp = pprint.PrettyPrinter(indent=1)

    with open(filename, 'r') as f:
        input = f.read()
        start = timer()
        tree = parser.parse(input)
        parser_end = timer()
        print("AST:")
        pp.pprint(tree)
        
        if not tree:
            ice("Compilation failed during parsing")


        #ast = tree.specify()
        ast = tree
        #pp.pprint(ast)

        print("Compiler output:")
        #res = cst.cpv()
        #if res:
        #    print("[CPV] Finished sucessfully.")
        #else:
        #    print("[CPV] Error during control path validation")
        #tt = TypeTable()
        ##cst.typecheck(tt)
        #print("\nType Table:")
        #print(pp.pprint(tt.table))

        code_writer = Writer()
        #w.emit_pre(STD_LIB)
        main_scope = Scope()
        ast.compile(code_writer, main_scope)
        end = timer()
        print(f"[BEN][PAR] Finished in {(parser_end-start)*1000:.2f}ms")
        print(f"[BEN][CMP] Finished in {(end-parser_end)*1000:.2f}ms")
        print(f"[BEN][TOT] Finished in {(end-start)*1000:.2f}ms")


        print("\nGenerated code:")
        print('  '+str(code_writer))
        outf = open(outpath, "w")
        outf.write(str(code_writer))
        outf.close()
        print("Output:")


if __name__ == '__main__':
    main()