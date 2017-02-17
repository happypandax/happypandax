"""test interface module."""
from unittest import mock

from happypanda.server.core.interface import interactive


@mock.patch('happypanda.core.interface.sys')
@mock.patch('happypanda.core.interface.code')
def test_run_interactive(mock_code, mock_sys):
    """test run interactive."""
    exc_info_retval = mock.Mock()
    mock_sys.exc_info.return_value = ['', '', exc_info_retval]
    # run
    interactive()
    # test
    mock_sys.exc_info.assert_called_once_with()

    exc_info_retval.assert_has_calls([
        mock.call.tb_frame.f_back.f_globals.copy(),
        (mock.call.tb_frame.f_back.f_globals.copy()
            .update(exc_info_retval.tb_frame.f_back.f_locals))
    ])
    code_calls = [
        mock.call.interact(
            '======== Start Happypanda Debugging ========',
            local=exc_info_retval.tb_frame.f_back.f_globals.copy())
    ]
    mock_code.assert_has_calls(code_calls, any_order=True)
