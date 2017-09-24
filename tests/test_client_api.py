import pytest
import threading

from happypanda.core.client import Client
from happypanda.core import db
from happypanda import main

pytestmark = pytest.mark.clientapitest


@pytest.fixture(scope="function")
def sample_db(tmpdir):
    pass

@pytest.fixture(scope="module")
def server(monkeypatch, tmpdir, sample_db):
    monkeypatch.chdir(tmpdir)
    t = threading.Thread(target=main.start, kwargs={'db_kwargs':{'path':sample_db}}, daemon=True)
    yield t.start()
    t.kill()

class APITest(unittest.TestCase):
    """
    Test server API
    """
    def setUp(self):
        self.client = Client("test")
        self.client.connect()

    def tearDown(self):
        self.client.close()
