import sys

def eprint(*args, **kwargs):
    "Prints to stderr"
    print(*args, file=sys.stderr, **kwargs)


class MethodResult:
    "Encapsulates return values from methods in the interface module"
    pass


