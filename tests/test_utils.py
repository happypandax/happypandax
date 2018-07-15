"""test utils module."""
import pytest

from unittest import mock
from happypanda.common.hlogger import eprint

pytestmark = pytest.mark.utilstest


@mock.patch('happypanda.common.hlogger.pprintpp.pprint')
@mock.patch('happypanda.common.hlogger.sys')
def test_eprint(m_sys, m_print):
    """test eprint."""
    m_arg = mock.Mock()
    m_key = 'key'
    m_value = mock.Mock()
    args_input = [m_arg]
    kwargs_input = {m_key: m_value}
    eprint(*args_input, **kwargs_input)
    m_print.assert_called_once_with(m_arg, stream=m_sys.stderr, **kwargs_input)
