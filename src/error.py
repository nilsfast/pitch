import logging
import sys


def throw_compiler_error(msg):
    logging.error(msg)
    sys.exit(1)
