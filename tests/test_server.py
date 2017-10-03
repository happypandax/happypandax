"""test server module."""
from unittest import mock
import itertools

from gevent import socket
import pytest

from happypanda.core.server import HPServer

pytestmark = pytest.mark.servertest


@pytest.mark.parametrize('is_public_server', [True, False])
def test_init(is_public_server):
    """test init of the object."""
    with mock.patch('happypanda.server.core.server.socket') as m_socket, \
            mock.patch('happypanda.server.core.server.StreamServer') as m_stream_server, \
            mock.patch('happypanda.server.core.server.pool') as m_pool, \
            mock.patch('happypanda.server.core.server.config') as m_config, \
            mock.patch('happypanda.server.core.server.constants') as m_constants:
        m_constants.public_server = is_public_server
        hps = HPServer()
        if is_public_server:
            m_socket.gethostname.assert_called_once_with()
        else:
            m_socket.gethostname.assert_not_called()
        m_pool.Pool.assert_called_with(m_constants.client_limit)
        assert hps._pool == m_pool.Pool.return_value
        if is_public_server:
            m_stream_server.assert_called_with(
                (m_socket.gethostname.return_value, m_constants.public_port),
                hps._handle,
                spawn=m_pool.Pool.return_value
            )
        else:
            m_stream_server.assert_called_with(
                (m_config.host.value, m_constants.local_port.value),
                hps._handle,
                spawn=m_pool.Pool.return_value
            )
        hps._server == m_stream_server.return_value
        assert hps._web_server is None
        assert hps._clients == set()


@mock.patch('happypanda.server.core.print')
def test_parse(m_print):
    """test parse method."""
    m_xml_data = mock.Mock()
    hps = HPServer()
    res = hps.parse(m_xml_data)
    m_print.assert_called_once_with(m_xml_data)
    assert res == b'<xml>Received</xml>'


@pytest.mark.parametrize(
    'is_web, serve_forever_func_raise_error, web_server_start_raise_error',
    itertools.product([True, False], repeat=3)
)
def test_run(is_web, serve_forever_func_raise_error, web_server_start_raise_error):
    """test run."""
    with mock.patch('happypanda.server.core.server.hweb') as m_hweb, \
            mock.patch('happypanda.server.core.server.config') as m_config,\
            mock.patch('happypanda.server.core.server.constants') as m_constants:
        # prepare before run the func.
        with mock.patch('happypanda.server.core.server.pool'), \
                mock.patch('happypanda.server.core.server.print') as m_print, \
                mock.patch('happypanda.server.core.server.WSGIServer') as m_wsgi_server:
            m_server = mock.Mock()
            hps = HPServer()
            hps._server = m_server
            if serve_forever_func_raise_error:
                hps._server.serve_forever.side_effect = socket.error
            if web_server_start_raise_error:
                m_wsgi_server.return_value.start.side_effect = socket.error
            # run the function
            hps.run(web=is_web)
            # testing
            if not is_web:
                hps._server.serve_forever.assert_called_once_with()
                m_wsgi_server.assert_not_called()
            else:
                if serve_forever_func_raise_error and web_server_start_raise_error:
                    m_wsgi_server.assert_has_calls([
                        mock.call((m_config.host.value, m_constants.web_port.value), m_hweb.happyweb),
                        mock.call().start()
                    ])
                else:
                    m_wsgi_server.assert_called_with(
                        (m_config.host.value, m_constants.web_port.value),
                        m_hweb.happyweb
                    )
                m_wsgi_server.return_value.start.assert_called_once_with()
            m_print.assert_not_called()


@pytest.mark.parametrize(
    'recv_first_val',
    [None, bytes(1), b'end']
)
def test_handle(recv_first_val):
    """test handle method."""
    m_obj_clients = mock.Mock()
    m_client = mock.Mock()
    m_address = mock.Mock()
    postfix = b'end'
    with mock.patch('happypanda.server.core.server.ClientHandler.parse'), \
            mock.patch('happypanda.server.core.server.pool'), \
            mock.patch('happypanda.server.core.server.print') as m_print, \
            mock.patch('happypanda.server.core.server.constants') as m_constants:
        hps = HPServer()
        hps._clients = m_obj_clients
        if recv_first_val is None:
            with pytest.raises(TypeError):
                hps._handle(m_client, m_address)
        else:
            # pre_run
            m_constants.postfix = postfix
            m_client.recv.side_effect = [recv_first_val, socket.error]
            # run
            hps._handle(m_client, m_address)
            # testing
            if recv_first_val == bytes(1):
                hps.parse.assert_not_called()
            elif recv_first_val == b'end':
                hps.parse.assert_called_once_with(b'end')
            m_client.assert_has_calls([
                mock.call.sendall(b'Welcome'),
                mock.call.recv(m_constants.data_size)
            ], any_order=True)
            # hps._clients
            hps._clients.add.assert_called_with(m_client)
            hps._clients.remove.assert_called_with(m_client)
            # m_print
            if recv_first_val == bytes(1) or recv_first_val == b'end':
                m_print.assert_called_once_with('Client connected')
            else:
                m_print.assert_has_calls([
                    mock.call('Client connected'),
                    mock.call('Client disconnected', mock.ANY)
                ], any_order=True)
