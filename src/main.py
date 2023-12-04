
import os
from src.error import throw_compiler_error
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

        test_code = """
        
        struct Point {
            x: i32;
            y: i32;
        }

        fn main() i32 {
            let x = Point { x: 1, y: 2};
            return 0;
        }
        """
        parser = PitchParser(self.out_dir)
        parse_tree: Program = parser.parse(source)
        pprint(parse_tree)
        # print("RECURSIVE?", pprint.isrecursive(parse_tree))

        try:
            assert (parse_tree is not None)
        except AssertionError:
            print("Parse tree is None")

        definitions = {}

        parse_tree.preprocess(definitions)

        print("Defs", definitions)

        parse_tree.populate_scope()

        # parse_tree.typecheck()
        # parse_tree.expand()
        # parse_tree.validate_branches()
        context = Context()
        parse_tree.check_references(context)

        pprint(parse_tree, indent=4)
        print("")
        c_tree = parse_tree.generate_c()
        print(c_tree)
        print("C PROGRAM:")
        c = c_tree.to_string()
        print(c)

        assert (c_tree is not None)
        # assert (type(c_tree) == cgen.CProgram)

        # c = parse_tree.to_c()
        # print(c)

        if not os.path.isdir(self.out_dir):
            os.makedirs(self.out_dir)

        c_file_out = os.path.join(self.out_dir, "out.c")

        with open(c_file_out, "w") as f:
            f.write(c)
