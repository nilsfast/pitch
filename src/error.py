import logging
import sys


def throw_compiler_error(msg):
    print("\n\033[91m"+"ERROR:", msg+"\033[0m")
    sys.exit(1)


def print_success(msg: str):
    print("\033[92m"+msg+"\033[0m")
