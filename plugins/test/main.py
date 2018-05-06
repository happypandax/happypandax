import tests
import sys
import pprint
import __hpx__ as hpx
print = pprint.pprint

print(sys)
print("hello plugin")
print(sys.path)

def main():
    print("calling main")

import os
print(os.getcwd())
hpx.log("hi")
print(__name__)
main()
