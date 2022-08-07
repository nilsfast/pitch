import sys

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def exit_comp():
    print("Compilation terminated.")
    sys.exit(1)

def comp_err(err, id='-'):
    print(f'{bcolors.FAIL}ERROR: {err} {bcolors.ENDC}')
    exit_comp()

def ice(err):
    print(f'{bcolors.FAIL}{bcolors.BOLD}ICE: {err} {bcolors.ENDC}')
    exit_comp()

