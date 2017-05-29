"""test happypanda.clients.web.views."""
from unittest import mock

from happypanda.webclient import views


def test_index():
    """test index."""
    with mock.patch('happypanda.clients.web.views.render_template') as m_render_template:
        res = views.library()
        m_render_template.assert_called_once_with('index.html')
        assert res == m_render_template.return_value
