import unittest

from happypanda.common.client import Client

def start_server():
    pass

class APITest(unittest.TestCase):
    """
    Test server API
    """
    def setUp(self):
        self.client = Client("test")
        self.client.connect()

    def tearDown(self):
        self.client.close()
