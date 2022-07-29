import os
from parser import parser
import sys
import pprint
from util.scope import Scope
from util.writer import Writer
import pathlib
from timeit import default_timer as timer


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
        res = cst.cpv()
        if res:
            print("[CPV] Finished sucessfully.")
        else:
            print("[CPV] Error during control path validation")
        w = Writer()
        main_scope = Scope()
        cst.compile(w, main_scope)
        end = timer()
        print(f"[OUT][CMP] Finished in {(end-start)*1000:.2f}ms")

        print("\nGenerated code:")
        print('  '+str(w).replace('\n', '\n  '))
        outf = open(outpath, "w")
        outf.write(str(w))
        outf.close()
        print("Output:")


if __name__ == '__main__':
    main()