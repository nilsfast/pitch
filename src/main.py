
import os
from src.error import print_success, throw_compiler_error
from src.nodes.utils import printlog
import src.pitch_std as std
from src.pitchparser import PitchParser
from src.nodes.program import Program
from prettyprinter import pprint
import logging
from src.context import Context

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)


class PitchCompiler():
    def __init__(self, source_file: str = None, out_path=None, debug=False):
        self.debug = debug
        self.source_file = source_file
        self.out_dir = out_path

    def compile(self):

        if self.source_file is None:
            throw_compiler_error("No source file specified")

        source = ""

        with open(self.source_file, "r") as f:
            source = f.read()
            f.close()

        parser = PitchParser(self.out_dir)
        parse_tree: Program = parser.parse(source)
        # printlog("RECURSIVE?", pprint.isrecursive(parse_tree))

        if not parse_tree:
            throw_compiler_error("No parse tree generated")
        else:
            print_success("Parse tree generated")
            print(parse_tree)

        definitions = {}

        parse_tree.preprocess(definitions)

        printlog("Defs", definitions)

        libs = [std.Alloc()]

        parse_tree.populate_scope(libs)

        # parse_tree.typecheck()
        # parse_tree.expand()
        # parse_tree.validate_branches()
        context = Context()
        parse_tree.check_references(context)
        print("PT", parse_tree)
        print(parse_tree)
        printlog("")
        c_tree = parse_tree.generate_c()
        if not c_tree:
            throw_compiler_error("No C tree generated")
        else:
            print_success("\nC tree generated\n")
        c = c_tree.to_string()
        printlog(c)

        assert (c_tree is not None)
        # assert (type(c_tree) == cgen.CProgram)

        # c = parse_tree.to_c()
        # printlog(c)

        if not os.path.isdir(self.out_dir):
            os.makedirs(self.out_dir)

        c_file_out = os.path.join(self.out_dir, "out.c")

        with open(c_file_out, "w") as f:
            f.write(c)
