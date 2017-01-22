from sys import exit
from os import chdir, path

# Change current working directory. This makes it so run_tests.py is required to be on the same level as the happypanda folder
chdir(path.abspath(path.dirname(__file__)))

import unittest

if __name__ == '__main__':
    suite = unittest.TestLoader().discover(".")
    unittest.TextTestRunner(verbosity=2).run(suite)