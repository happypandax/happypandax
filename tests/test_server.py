"""test server module."""
from unittest import TestCase, mock
import itertools

from gevent import socket
import pytest

from happypanda.core.server import HPServer


class HPServerTest(TestCase):
    """test for HPServer."""

    @mock.patch('happypanda.core.server.socket')
    @mock.patch('happypanda.core.server.StreamServer')
    @mock.patch('happypanda.core.server.pool')
    @mock.patch('happypanda.core.server.constants')
    def test_init(self, m_constants, m_pool, m_stream_server, m_socket):
        """test init of the object."""
        for is_public_server in (True, False):
            m_constants.public_server = is_public_server
            hps = HPServer()
            m_socket.gethostname.assert_called_once_with()
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
                    (m_constants.host, m_constants.local_port),
                    hps._handle,
                    spawn=m_pool.Pool.return_value
                )
            hps._server == m_stream_server.return_value
            assert hps._web_server is None
            assert hps._clients == set()

    @mock.patch('happypanda.core.server.print')
    def test_parse(self, m_print):
        """test parse method."""
        m_xml_data = mock.Mock()
        hps = HPServer()
        res = hps.parse(m_xml_data)
        m_print.assert_called_once_with(m_xml_data)
        assert res == b'<xml>Received</xml>'

    @mock.patch('happypanda.core.server.hweb')
    @mock.patch('happypanda.core.server.constants')
    def test_run(self, m_constants, m_hweb):
        """test run."""
        err_msg = 'Error: Port might already be in use'
        for val_pack in itertools.product([True, False], repeat=3):
            # unpack value
            is_web = val_pack[0]
            serve_forever_func_raise_error = val_pack[1]
            web_server_start_raise_error = val_pack[2]
            # prepare before run the func.
            with mock.patch('happypanda.core.server.pool'), \
                    mock.patch('happypanda.core.server.print') as m_print, \
                    mock.patch('happypanda.core.server.WSGIServer') as m_wsgi_server:
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
                    m_wsgi_server.assert_called_with(
                        (m_constants.host, m_constants.web_port),
                        m_hweb.happyweb
                    )
                    m_wsgi_server.return_value.start.assert_called_once_with()
                if (not is_web and serve_forever_func_raise_error) or \
                        (is_web and web_server_start_raise_error):
                    m_print.assert_called_once_with(err_msg)

    def test_handle(self):
        """test handle method."""
        m_obj_clients = mock.Mock()
        m_client = mock.Mock()
        m_address = mock.Mock()
        recv_retval = bytes(1)
        recv_retval_with_end = b'end'
        with mock.patch('happypanda.core.server.HPServer.parse') as m_parse, \
                mock.patch('happypanda.core.server.pool'), \
                mock.patch('happypanda.core.server.print') as m_print, \
                mock.patch('happypanda.core.server.constants') as m_constants:
            hps = HPServer()
            hps._clients = m_obj_clients
            with pytest.raises(TypeError):
                hps._handle(m_client, m_address)
            for recv_first_val in (recv_retval, recv_retval_with_end):
                m_client.recv.side_effect = [recv_first_val, socket.error]
                hps._handle(m_client, m_address)
                # testing
                if recv_first_val == recv_retval:
                    hps.parse.assert_not_called()
                elif recv_first_val == recv_retval_with_end:
                    hps.parse.assert_called_once_with(recv_retval_with_end)
                m_client.assert_has_calls([
                    mock.call.sendall(b'Welcome'),
                    mock.call.recv(m_constants.data_size)
                ], any_order=True)
                # hps._clients
                hps._clients.add.assert_called_with(m_client)
                hps._clients.remove.assert_called_with(m_client)
                # m_print
                m_print.assert_has_calls([
                    mock.call('Client connected'),
                    mock.call('Client disconnected', mock.ANY)
                ], any_order=True)
