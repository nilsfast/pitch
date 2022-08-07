import os
from parser import parser
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
    start = timer()

    #print(pathlib.Path(__file__).parent.resolve())
    outpath = os.path.normpath(os.getcwd())+os.sep+'build'+os.sep+'out.ll'
    filename = sys.argv[1]

    pp = pprint.PrettyPrinter(indent=2)

    with open(filename, 'r') as f:
        input = f.read()
        cst = parser.parse(input)
        print("AST:")
        pp.pprint(cst)

        print("Compiler output:")
        #res = cst.cpv()
        #if res:
        #    print("[CPV] Finished sucessfully.")
        #else:
        #    print("[CPV] Error during control path validation")
        tt = TypeTable()
        #cst.typecheck(tt)
        print("\nType Table:")
        print(pp.pprint(tt.table))

        code_writer = Writer()
        #w.emit_pre(STD_LIB)
        main_scope = Scope()
        cst.compile(code_writer, main_scope)
        end = timer()
        print(f"[OUT][CMP] Finished in {(end-start)*1000:.2f}ms")

        print("\nGenerated code:")
        print('  '+str(code_writer).replace('\n', '\n  | '))
        outf = open(outpath, "w")
        outf.write(str(code_writer))
        outf.close()
        print("Output:")


if __name__ == '__main__':
    main()