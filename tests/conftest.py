import pytest
import responses

def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item

def pytest_runtest_setup(item):
    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail("previous test failed (%s)" %previousfailed.name)

@pytest.fixture
def mresponses():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps

        
internaldb = None

@pytest.fixture(autouse=True)
def test_internaldb(monkeypatch, tmpdir):

    global internaldb

    from happypanda.common import constants, clsutils

    db_p = internaldb = internaldb or tmpdir.join("internals.db")
    db = clsutils.InternalDatabase(str(db_p))
    monkeypatch.setattr(constants, "internaldb", db)
    monkeypatch.setattr(clsutils, "internaldb", db)
    yield

def pytest_configure(config):
    import sys

    sys._called_from_test = True

def pytest_unconfigure(config):
    import sys

    del sys._called_from_test