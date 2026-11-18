"""
A plugin left out of the frontend build is disabled at start-up rather than
left enabled, where every page loading its navigation would fail with a
server error (as the stock learn and coach plugins did on an LSHE server).
"""
import os
import shutil
import sys
import tempfile

import pytest
from mock import patch

from kolibri.plugins.utils import disable_unbuilt_plugins

PLUGIN = "unbuilt_test_plugin"


@pytest.fixture
def plugins():
    from kolibri import plugins

    _, config_file = tempfile.mkstemp(suffix="json")
    old_config_file = plugins.conf_file
    plugins.conf_file = config_file
    plugins.config.set_defaults()
    yield plugins
    plugins.conf_file = old_config_file


@pytest.fixture
def plugin_dir():
    """A plugin package with a frontend (buildConfig.js) and no build yet."""
    root = tempfile.mkdtemp()
    package = os.path.join(root, PLUGIN)
    os.makedirs(package)
    open(os.path.join(package, "__init__.py"), "w").close()
    open(os.path.join(package, "buildConfig.js"), "w").close()
    sys.path.insert(0, root)
    yield package
    sys.path.remove(root)
    sys.modules.pop(PLUGIN, None)
    shutil.rmtree(root)


def enable(plugins):
    plugins.config["INSTALLED_PLUGINS"].add(PLUGIN)
    plugins.config.save()


@patch("kolibri.plugins.registry.is_initialized", return_value=False)
@patch.dict(os.environ, {"KOLIBRI_DEVELOPER_MODE": ""})
def test_unbuilt_plugin_disabled(_, plugins, plugin_dir):
    enable(plugins)
    disable_unbuilt_plugins()
    assert PLUGIN not in plugins.config.ACTIVE_PLUGINS
    assert PLUGIN in plugins.config["DISABLED_PLUGINS"]


@patch("kolibri.plugins.registry.is_initialized", return_value=False)
@patch.dict(os.environ, {"KOLIBRI_DEVELOPER_MODE": ""})
def test_built_plugin_kept(_, plugins, plugin_dir):
    os.makedirs(os.path.join(plugin_dir, "build"))
    open(os.path.join(plugin_dir, "build", PLUGIN + ".app_stats.json"), "w").close()
    enable(plugins)
    disable_unbuilt_plugins()
    assert PLUGIN in plugins.config.ACTIVE_PLUGINS


@patch("kolibri.plugins.registry.is_initialized", return_value=False)
@patch.dict(os.environ, {"KOLIBRI_DEVELOPER_MODE": ""})
def test_plugin_without_frontend_kept(_, plugins, plugin_dir):
    os.remove(os.path.join(plugin_dir, "buildConfig.js"))
    enable(plugins)
    disable_unbuilt_plugins()
    assert PLUGIN in plugins.config.ACTIVE_PLUGINS


@patch("kolibri.plugins.registry.is_initialized", return_value=False)
@patch.dict(os.environ, {"KOLIBRI_DEVELOPER_MODE": "1"})
def test_developer_mode_kept(_, plugins, plugin_dir):
    enable(plugins)
    disable_unbuilt_plugins()
    assert PLUGIN in plugins.config.ACTIVE_PLUGINS
