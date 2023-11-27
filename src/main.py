
from src.pitchparser import PitchParser
from src.nodes.program import Program
from prettyprinter import pprint
import logging
from src.context import Context

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)


class PitchCompiler():
    def __init__(self):
        pass

    def compile(self):
        test_code = """
        fn main () i32 {
            let a = "hallo";
            let b: i32 = 1;
            return 0;
        }
        """
        parser = PitchParser()
        parse_tree: Program = parser.parse(test_code)
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
        print("")
        print(c_tree.to_string())

        assert (c_tree is not None)
        # assert (type(c_tree) == cgen.CProgram)

        # c = parse_tree.to_c()
        # print(c)

        # with open("out.c", "w") as f:
        #    f.write(c)
