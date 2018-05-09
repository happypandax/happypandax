"""test plugins module."""
from unittest import mock
import itertools
import os
import pytest
import uuid
import json

from happypanda.core import plugins, command
from happypanda.common import hlogger
from happypanda.core.plugins import PluginManager
from happypanda.common import exceptions as hp_exceptions
from happypanda.common import constants

pytestmark = pytest.mark.plugintest

constants.available_commands = command.get_available_commands()

def plugin_manifest(plugin_name):
    return dict(
        id = str(uuid.uuid4()),
        shortname = plugin_name,
        name = "Test",
        author = "Pewpew",
        description = "A test plugin",
        entry = 'main.py',
        test = 'test.py',
        version = "1.0.0",
        website = "www.test.test",
        require = ["happypanda >= {}".format(constants.version_str)])

@pytest.fixture(scope='function')
def hplugin_a(tmpdir_factory):
    plugin_name = "hplugin_a"
    plugin_dir = tmpdir_factory.mktemp('plugins').mkdir(plugin_name)
    hplugin_attr = plugin_manifest(plugin_name)
    with open(str(plugin_dir.join("hplugin.json")), 'w', encoding='utf-8') as f:
        json.dump(hplugin_attr, f)
    with open(str(plugin_dir.join('main.py')), 'x') as f:
        pass
    with open(str(plugin_dir.join('test.py')), 'x') as f:
        pass
    return plugin_dir

@pytest.fixture(scope='function')
def hplugin_b(tmpdir_factory):
    plugin_name = "hplugin_b"
    plugin_dir = tmpdir_factory.mktemp('plugins').mkdir(plugin_name)
    hplugin_attr = plugin_manifest(plugin_name)
    with open(str(plugin_dir.join("hplugin.json")), 'w', encoding='utf-8') as f:
        json.dump(hplugin_attr, f)
    with open(str(plugin_dir.join('main.py')), 'x') as f:
        pass
    with open(str(plugin_dir.join('test.py')), 'x') as f:
        pass
    return plugin_dir

@pytest.fixture(scope='function')
def hplugin_c(tmpdir_factory):
    plugin_name = "hplugin_c"
    plugin_dir = tmpdir_factory.mktemp('plugins').mkdir(plugin_name)
    hplugin_attr = plugin_manifest(plugin_name)
    with open(str(plugin_dir.join("hplugin.json")), 'w', encoding='utf-8') as f:
        json.dump(hplugin_attr, f)
    with open(str(plugin_dir.join('main.py')), 'x') as f:
        pass
    with open(str(plugin_dir.join('test.py')), 'x') as f:
        pass
    return plugin_dir

@pytest.mark.incremental
class TestPluginLoad:
    
    def test_plugin_load(self, hplugin_a):
        "Test if a plugin can be loaded"
        with mock.patch("happypanda.core.plugins.PluginManager.register") as pm_register,\
            mock.patch("happypanda.core.plugins.log_plugin_error"):
            pm = PluginManager()
            hpm = plugins.plugin_load(pm, str(hplugin_a))

            assert pm_register.called

            hplugin_a.join('main.py').remove()
            with pytest.raises(hp_exceptions.PluginLoadError) as excinfo:
                hpm = plugins.plugin_load(pm, str(hplugin_a))
            assert "Plugin entry" in str(excinfo.value)
            with open(str(hplugin_a.join('main.py')), 'x') as f:
                pass
            hplugin_a.join('test.py').remove()
            with pytest.raises(hp_exceptions.PluginLoadError) as excinfo:
                hpm = plugins.plugin_load(pm, str(hplugin_a))
            assert "Plugin test entry" in str(excinfo.value)
            with open(str(hplugin_a.join('test.py')), 'x') as f:
                pass
            with open(str(hplugin_a.join('hplugin.json')), 'w') as f:
                f.write('')

            with pytest.raises(hp_exceptions.PluginLoadError) as excinfo:
                hpm = plugins.plugin_load(pm, str(hplugin_a))
            assert "Failed to decode manifest file:" in str(excinfo.value)

            hplugin_a.join('hplugin.json').remove()
            with pytest.raises(hp_exceptions.PluginLoadError) as excinfo:
                hpm = plugins.plugin_load(pm, str(hplugin_a))
            assert "No manifest file named 'HPlugin.json' found" in str(excinfo.value)

    def test_plugin_register(self, hplugin_a, hplugin_b):
        pm = PluginManager()
        for h in (hplugin_a, hplugin_b):
            node = plugins.plugin_load(pm, str(h))
            assert isinstance(node, plugins.PluginNode) and pm.get_node(node.info.id)

        with mock.patch("happypanda.core.plugins.log_plugin_error"):
            with pytest.raises(hp_exceptions.PluginLoadError) as excinfo:
                plugins.plugin_load(pm, str(hplugin_a))
            assert "Plugin ID already exists" in str(excinfo.value)


@pytest.mark.parametrize("attr,value,exc_msg",
                          [
                              ('id', None, "attribute is missing"),
                              ('id', '', "attribute cannot be empty"),
                              ('id', '1234', "A valid UUID4 is required"),
                              ('id', '00000000-0000-0000-0000-000000000000', "A valid UUID4 is required"),
                              ('entry', None, "attribute is missing"),
                              ('entry', '', "attribute cannot be empty"),
                              ('entry', 123, "Plugin entry should be a filename"),
                              ('name', None, "attribute is missing"),
                              ('name', '', "attribute cannot be empty"),
                              ('name', 123, "Plugin name should be a string"),
                              ('shortname', None, "attribute is missing"),
                              ('shortname', '', "attribute cannot be empty"),
                              ('shortname', 123, "Plugin shortname should be a string"),
                              ('shortname', 'egfhghghjhgukhkhjildfhgstth', "Plugin shortname cannot exceed"),
                              ('shortname', 'a b', "Plugin shortname must not contain any whitespace"),
                              ('shortname', 'AbC', "Plugin shortname should be all lowercase"),
                              ('version', None, "attribute is missing"),
                              ('version', 123, "Plugin version should be a string"),
                              ('version', 'a.2.c', "Plugin version should conform to PEP 440"),
                              ('version', '', "attribute cannot be empty"),
                              ('author', None, "attribute is missing"),
                              ('author', '', "attribute cannot be empty"),
                              ('author', 123, "Plugin author should be a string"),
                              ('description', None, "attribute is missing"),
                              ('description', '', "attribute cannot be empty"),
                              ('description', 123, "Plugin description should be a string"),
                              ('website', 123, "Plugin website should be a string"),
                              ('test', 123, "Plugin test entry should be a filename"),
                              ('require', 123, "Plugin require should be a list of strings"),
                              ('require', [1,2,3], "Plugin require should be a list of strings"),
                              ('require', ["happypandax==abc"], "Invalid requirement"),
                              ('require', ["happypandax==1.2.3;hello"], " on "),
                              ('require', ["happypandax==1.2.3;hello=='a'"], " on "),
                              ('require', ["happypandax==1.2.3;os_name=='a'"], "cannot contain a marker"),
                              ])
def test_plugin_manifest(attr, value, exc_msg):
    hplugin_attr = plugin_manifest('test')
    hplugin_attr.pop(attr)
    if value is not None:
        hplugin_attr[attr] = value
    with pytest.raises(hp_exceptions.PluginAttributeError) as excinfo:
        m = plugins.PluginManifest(hplugin_attr)
    assert exc_msg in str(excinfo.value)