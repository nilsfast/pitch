#!/usr/bin/python3.12
import argparse
import os

from src.main import PitchCompiler

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('source', metavar='source', type=str, help='Input file')
parser.add_argument('-d', dest='debug', action='store_true',
                    help='Debug enabled')

args = parser.parse_args()
print(args.debug)

# get filepath from call
current_directory = os.getcwd()
source_path = os.path.join(current_directory, args.source)
print(source_path)

# source_path, debug=args.debug
compiler = PitchCompiler()
compiler.compile()
