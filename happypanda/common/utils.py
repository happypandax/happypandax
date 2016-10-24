import sys

def eprint(*args, **kwargs):
    "Prints to stderr"
    print(*args, file=sys.stderr, **kwargs)


