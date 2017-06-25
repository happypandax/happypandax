import pytest
from unittest import mock

pytestmark = pytest.mark.searchcmdtest

from happypanda.server.core import command, db
from happypanda.server.core.commands import search_cmd

def test_search_parse():
    "Test search filter parsing"

    p = search_cmd.ParseSearch()

    s = "one -two three:[four, -five] six:>seven, eigth, -nine:ten"
    s_a = ("one", "-two", "three:four", "-three:five", "six:>seven", "eigth", "-nine:ten")

    terms = p.main(s)

    assert len(terms) == len(s_a)
    assert all(x in s_a for x in terms)

@mock.patch.object(search_cmd.ParseSearch.parse, "call")
def test_search_parse_command_parse(m_call):
    "Test parse command is called"

    p = search_cmd.ParseSearch()
    s = "this is a term"
    p.main(s)
    m_call.assert_called_with(s)

@mock.patch.object(search_cmd.ParseSearch.parsed, "emit")
def test_search_parse_event_parse(m_emit):
    "Test parsed event is called"

    p = search_cmd.ParseSearch()
    s = "this is a term"
    t = p.main(s)
    m_emit.assert_called_with(t)

def test_partial_model_filter():
    "Test partial searching on db model"

    p = search_cmd.PartialModelFilter()
    model = db.Gallery


