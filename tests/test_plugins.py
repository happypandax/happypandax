"""test plugins module."""
from unittest import mock, TestCase
import itertools

import pytest

from happypanda.server.core.plugins import Plugins, HPluginMeta
from happypanda.common import exceptions as hp_exceptions


class PluginsTest(TestCase):
    """plugin class init."""

    def test_init(self):
        """test init the class."""
        plugins = Plugins()
        assert vars(plugins) == {}

    def test_register_with_mock_input(self):
        """test register."""
        plugins = Plugins()
        mock_plugin = mock.Mock()
        with pytest.raises(AssertionError):
            plugins.register(mock_plugin)

    def test_register_with_correct_assertion(self):
        """test register but with correct type."""
        pass


class HPluginMetaTest(TestCase):
    """test HPluginMeta."""

    def test_init(self):
        """test init."""
        val_data = [
            (mock.Mock(), ''),
            (mock.Mock(), ()),
            (mock.Mock(), {}),
        ]
        for input_args in itertools.product([0, 1], repeat=3):
            m_name = val_data[0][input_args[0]]
            m_bases = val_data[1][input_args[1]]
            m_dct = val_data[2][input_args[2]]
            if any(isinstance(x, mock.Mock) for x in (m_name, m_bases, m_dct)):
                with pytest.raises(TypeError):
                    HPluginMeta(m_name, m_bases, m_dct)
            else:
                hpm = HPluginMeta(m_name, m_bases, m_dct)
                # have attribute
                assert hasattr(hpm, 'connect_plugin')
                assert hasattr(hpm, 'connect_hook')
                assert hasattr(hpm, 'create_hook')
                # don't have attr
                assert not hasattr(hpm, 'newHook')
                assert not hasattr(hpm, '__getattr__')

    def test_connect_plugin_with_error(self):
        """test connect plugin."""
        m_name = ''
        m_bases = ()
        m_dct = {}
        mock_obj = mock.Mock()
        # run
        for m_plugin_id, m_cls_name in itertools.product([mock_obj, ''], repeat=2):
            hpm = HPluginMeta(m_name, m_bases, m_dct)
            hpm.NAME = m_cls_name
            if m_plugin_id == '' and m_cls_name == '':
                with pytest.raises(hp_exceptions.PluginIDError):
                    hpm.connect_plugin(m_plugin_id)
            elif isinstance(m_plugin_id, mock.Mock) or m_plugin_id == '':
                with pytest.raises(TypeError):
                    hpm.connect_plugin(m_plugin_id)

    def test_connect_hook_with_error(self):
        """test connect hook with error."""
        m_name = ''
        m_bases = ()
        m_dct = {}
        m_obj = mock.Mock()
        m_handler = mock.Mock()
        for m_plugin_id, m_hook_name in itertools.product([m_obj, ''], repeat=2):
            hpm = HPluginMeta(m_name, m_bases, m_dct)
            if isinstance(m_plugin_id, mock.Mock) or isinstance(m_hook_name, mock.Mock):
                with pytest.raises(AssertionError):
                    hpm.connect_hook(m_plugin_id, m_hook_name, m_handler)

            else:
                with pytest.raises(KeyError):
                    hpm.connect_hook(m_plugin_id, m_hook_name, m_handler)

    def test_create_hook(self):
        """test create hook with error."""
        m_name = ''
        m_bases = ()
        m_dct = {}
        m_obj = mock.Mock()
        m_id = mock.Mock()
        for m_hook_name in (m_obj, ''):
            hpm = HPluginMeta(m_name, m_bases, m_dct)
            if isinstance(m_hook_name, mock.Mock):
                with pytest.raises(AssertionError):
                    hpm.create_hook(m_hook_name)
            else:
                with pytest.raises(AttributeError):
                    hpm.create_hook(m_hook_name)
                with pytest.raises(KeyError):
                    hpm.ID = m_id
                    hpm.create_hook(m_hook_name)
