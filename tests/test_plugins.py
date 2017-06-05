"""test plugins module."""
from unittest import mock, TestCase
import itertools

import pytest

from happypanda.server.core import plugins
from happypanda.server.core.plugins import PluginManager, HPluginMeta
from happypanda.common import exceptions as hp_exceptions

def _create_hplugin():
    attr = dict(
        ID = "0890c892-cfa4-4e06-8962-460d395a7c5d",
        NAME = "Test",
        AUTHOR = "Pewpew",
        DESCRIPTION = "A test plugin",
        VERSION = (0, 0, 1),
        WEBSITE = "www.test.test")
    return type("HPlugin", (), attr)

def test_plugin_load():
    hpm = plugins._plugin_load(_create_hplugin(), 'test')

def test_hplugin_missing_attrib_error():
    hplugin = type("HPlugin", (), {})
    for a, v in (("ID", ""), ("NAME", ""), ("VERSION", (0,0,0)), ("AUTHOR", ""), ("DESCRIPTION", "")):
        with pytest.raises(hp_exceptions.PluginAttributeError):
            hpm = plugins._plugin_load(hplugin, 'test')
        setattr(hplugin, a, v)

def test_hplugin_validuuid_error():
    hplugin = _create_hplugin()
    hplugin.ID = "123"
    with pytest.raises(hp_exceptions.PluginIDError):
        hpm = plugins._plugin_load(hplugin, 'test')

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
                assert hasattr(hpm, 'on_plugin_command')
                assert hasattr(hpm, 'on_command')
                assert hasattr(hpm, 'create_command')
                # don't have attr
                assert not hasattr(hpm, '__getattr__')

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

    def test_create_command(self):
        """test create command with error."""
        m_name = ''
        m_bases = ()
        m_dct = {}
        m_obj = mock.Mock()
        m_id = mock.Mock()
        for m_hook_name in (m_obj, ''):
            hpm = HPluginMeta(m_name, m_bases, m_dct)
            if isinstance(m_hook_name, mock.Mock):
                with pytest.raises(AssertionError):
                    hpm.create_command(m_hook_name)
            else:
                with pytest.raises(AttributeError):
                    hpm.create_command(m_hook_name)
                with pytest.raises(KeyError):
                    hpm.ID = m_id
                    hpm.create_command(m_hook_name)

class PluginsTest(TestCase):
    """plugin class init."""

    def test_init(self):
        """test init the class."""
        plugins = PluginManager()
        assert vars(plugins) == {}

    def test_register_with_mock_input(self):
        """test register."""
        plugins = PluginManager()
        mock_plugin = mock.Mock()
        with pytest.raises(AssertionError):
            plugins.register(mock_plugin)

    def test_register_with_correct_assertion(self):
        """test register but with correct type."""
        pass


