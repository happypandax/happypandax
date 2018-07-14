"""test updater module."""
import pytest
import json
import sys
import os
import shutil

from unittest import mock

pytestmark = pytest.mark.updatertest

import updater as happyupd
from happypanda.common import constants, utils, clsutils
from happypanda.core import updater

github_repo_tags = [
  {
    "name": "v0.0.2",
    "zipball_url": "https://api.github.com/repos/happypandax/server/zipball/v0.0.2",
    "tarball_url": "https://api.github.com/repos/happypandax/server/tarball/v0.0.2",
    "commit": {
      "sha": "bba3f48fd8a53625ec5eb5877d58f2e16687f7a1",
      "url": "https://api.github.com/repos/happypandax/server/commits/bba3f48fd8a53625ec5eb5877d58f2e16687f7a1"
    }
  },
  {
    "name": "v0.0.1",
    "zipball_url": "https://api.github.com/repos/happypandax/server/zipball/v0.0.1",
    "tarball_url": "https://api.github.com/repos/happypandax/server/tarball/v0.0.1",
    "commit": {
      "sha": "450c98dd983e36a4ce6538558160a4aac1b871fc",
      "url": "https://api.github.com/repos/happypandax/server/commits/450c98dd983e36a4ce6538558160a4aac1b871fc"
    }
  },
  {
    "name": "b112",
    "zipball_url": "https://api.github.com/repos/happypandax/server/zipball/b112",
    "tarball_url": "https://api.github.com/repos/happypandax/server/tarball/b112",
    "commit": {
      "sha": "bba3f48fd8a53625ec5eb5877d58f2e16687f7a1",
      "url": "https://api.github.com/repos/happypandax/server/commits/bba3f48fd8a53625ec5eb5877d58f2e16687f7a1"
    }
  },
]

asset_files = ("happyupd.txt", "installedfromtest.txt")
if constants.is_osx:
    asset_files = ("happyupd.txt", "installedfromtest.txt",
                   "../Resources/hello.txt")
asset_url_win = "tests/data/happypandax0.0.2.win.zip"
asset_url_linux = "tests/data/happypandax0.0.2.linux.tar.gz"
asset_url_osx = "tests/data/happypandax0.0.2.osx.tar.gz"
if constants.is_win:
    asset_url_platform = asset_url_win
elif constants.is_linux:
    asset_url_platform = asset_url_linux
elif constants.is_osx:
    asset_url_platform = asset_url_osx

with open(asset_url_platform, "rb") as f:
    asset_data = f.read()

asset_data_checksum = updater.sha256_checksum(asset_url_platform)

github_repo_v0_0_2 = {
  "url": "https://api.github.com/repos/happypandax/server/releases/9067700",
  "assets_url": "https://api.github.com/repos/happypandax/server/releases/9067700/assets",
  "upload_url": "https://uploads.github.com/repos/happypandax/server/releases/9067700/assets{?name,label}",
  "html_url": "https://github.com/happypandax/server/releases/tag/v0.0.2",
  "id": 9067700,
  "tag_name": "v0.0.2",
  "target_commitish": "dev",
  "name": "HappyPanda X PREVIEW v0.0.2",
  "prerelease": False,
  "created_at": "2017-12-31T00:19:26Z",
  "published_at": "2017-12-31T00:52:06Z",
  "assets": [
    {
      "url": "https://api.github.com/repos/happypandax/server/releases/assets/5746997",
      "id": 5746997,
      "name": "happypandax0.0.2.linux.zip",
      "label": None,
      "content_type": "application/x-zip-compressed",
      "state": "uploaded",
      "size": 91638757,
      "download_count": 11,
      "created_at": "2017-12-31T00:48:54Z",
      "updated_at": "2017-12-31T00:51:01Z",
      "browser_download_url": asset_url_linux
    },
    {
      "url": "https://api.github.com/repos/happypandax/server/releases/assets/5746995",
      "id": 5746995,
      "name": "happypandax0.0.2.win.installer.exe",
      "label": None,
      "content_type": "application/x-msdownload",
      "state": "uploaded",
      "size": 54085121,
      "download_count": 63,
      "created_at": "2017-12-31T00:48:47Z",
      "updated_at": "2017-12-31T00:49:19Z",
      "browser_download_url": "https://github.com/happypandax/server/releases/download/v0.0.2/happypandax0.0.2.win.installer.exe"
    },
    {
      "url": "https://api.github.com/repos/happypandax/server/releases/assets/5746996",
      "id": 5746996,
      "name": "happypandax0.0.2.win.zip",
      "label": None,
      "content_type": "application/x-zip-compressed",
      "state": "uploaded",
      "size": 82448863,
      "download_count": 95,
      "created_at": "2017-12-31T00:48:47Z",
      "updated_at": "2017-12-31T00:50:03Z",
      "browser_download_url": asset_url_win
    },
        {
      "url": "https://api.github.com/repos/happypandax/server/releases/assets/5746996",
      "id": 5746996,
      "name": "happypandax0.0.2.osx.tar.gz",
      "label": None,
      "content_type": "application/x-zip-compressed",
      "state": "uploaded",
      "size": 82448863,
      "download_count": 95,
      "created_at": "2017-12-31T00:48:47Z",
      "updated_at": "2017-12-31T00:50:03Z",
      "browser_download_url": asset_url_osx
    }
  ],
  "tarball_url": "https://api.github.com/repos/happypandax/server/tarball/v0.0.2",
  "zipball_url": "https://api.github.com/repos/happypandax/server/zipball/v0.0.2",
  "body": "test"
  }

github_checksum = {
  "name": "checksums.txt",
  "path": "checksums.txt",
  "sha": "148c065a0f7d29b8055c3b1f8fcaebc4fb7a9c19",
  "size": 194,
  "url": "https://api.github.com/repos/happypandax/updates/contents/checksums.txt?ref=master",
  "html_url": "https://github.com/happypandax/updates/blob/master/checksums.txt",
  "git_url": "https://api.github.com/repos/happypandax/updates/git/blobs/148c065a0f7d29b8055c3b1f8fcaebc4fb7a9c19",
  "download_url": "https://raw.githubusercontent.com/happypandax/updates/master/checksums.txt",
  "type": "file",
  "content": "test",
  "encoding": "base64",
  "_links": {
    "self": "https://api.github.com/repos/happypandax/updates/contents/checksums.txt?ref=master",
    "git": "https://api.github.com/repos/happypandax/updates/git/blobs/148c065a0f7d29b8055c3b1f8fcaebc4fb7a9c19",
    "html": "https://github.com/happypandax/updates/blob/master/checksums.txt"
  }
}

def define_github_responses(rsp):
    #rsp.add(responses.GET, 'https://api.github.com/repos/happypandax/server/tags',
    #              json=github_repo_tags, status=404)
    rsp.add(rsp.GET, 'https://api.github.com/repos/happypandax/server/tags',
                  json=github_repo_tags, status=200)

    rsp.add(rsp.GET, 'https://api.github.com/repos/happypandax/server/releases/tags/v0.0.2',
                  json=github_repo_v0_0_2, status=200)

    rsp.add(rsp.GET, 'http://randomurl.abc',
                  body=asset_data, status=200)

    rsp.add(rsp.GET, 'https://api.github.com/repos/happypandax/updates/contents/checksums.txt',
                json=github_checksum, status=200)

    rsp.add(rsp.GET, 'https://raw.githubusercontent.com/happypandax/updates/master/checksums.txt',
                body=asset_data_checksum, status=200)

@pytest.fixture(scope='session')
def tmp_update_folder(tmpdir_factory):
    fn = tmpdir_factory.mktemp('updater')
    return fn

@pytest.fixture(scope='session')
def app_path():
    root_p = p = os.path.join("tests", "data", "tmp_upd_app_path")
    if constants.is_osx:
        p = os.path.join(p, "Contents", "MacOS")
    os.makedirs(p)
    yield p
    shutil.rmtree(root_p)

@pytest.mark.incremental
class TestUpdating:
    
    def test_check_release(self, mresponses):
        define_github_responses(mresponses)
        with mock.patch("happypanda.common.constants.version", (0, 0, 0)):
            r = updater.check_release()
            assert r is not None
            assert utils.compare_json_dicts(r, {'url':asset_url_platform, 'changes':'test', 'tag':'v0.0.2', 'version':(0, 0, 2)})

        with mock.patch("happypanda.common.constants.version", (2, 0, 0)):
            r = updater.check_release()
            assert r is None

    def test_get_release(self, mresponses, tmpdir):
        define_github_responses(mresponses)
        p = tmpdir.mkdir("updater_get")
        db_p = p.join("internals.db")
        p = str(p)
        with mock.patch("happypanda.common.constants.version", (2, 0, 0)),\
            mock.patch("happypanda.common.constants.dir_cache", p),\
            mock.patch("happypanda.common.constants.internal_db_path", str(db_p)),\
            mock.patch("happypanda.common.constants.internaldb", clsutils.InternalDatabase(str(db_p))),\
            mock.patch("happypanda.common.constants.dir_temp", p):
            r = updater.get_release("http://randomurl.abc", silent=False)
            assert r is not None
            assert isinstance(r, dict) and 'path' in r and 'hash' in r
            old_r = r
            r = updater.get_release()
            assert r is None
            r = updater.get_release(asset_url_platform)
            assert r is not None
            assert utils.compare_json_dicts(r, old_r)

    def test_register_release(self, tmp_update_folder, app_path):
        p = str(tmp_update_folder.mkdir("updater_register"))
        db_p = tmp_update_folder.join("internals.db")
        idb = clsutils.InternalDatabase(str(db_p))
        with mock.patch("happypanda.common.constants.internal_db_path", str(db_p)),\
            mock.patch("happypanda.common.constants.internaldb", idb),\
            mock.patch("happypanda.common.clsutils.internaldb", idb),\
            mock.patch("happypanda.common.constants.app_path", app_path),\
            mock.patch("happypanda.common.utils.create_temp_dir") as utils_temp,\
            mock.patch("happypanda.core.commands.io_cmd.CoreFS.delete"),\
            mock.patch("happypanda.common.constants.dir_update", p):
            utils_temp.return_value = str(tmp_update_folder.mkdir("updater_release"))
            assert updater.register_release(asset_url_platform, silent=False, restart=False)
            assert constants.internal_db_path == str(db_p)
            db = constants.internaldb
            d = db[constants.updater_key]
            assert utils.compare_json_dicts(d, {'from': utils_temp.return_value,
                                                'to': os.path.abspath(constants.app_path),
                                                'restart': False,
                                                'app': sys.argv[0],
                                                'args': sys.argv[1:],
                                                'state': constants.UpdateState.Registered.value})

    def test_updater(self, tmp_update_folder, app_path):
        db_p = tmp_update_folder.join("internals.db")
        idb = clsutils.InternalDatabase(str(db_p))
        with mock.patch("happypanda.common.constants.internal_db_path", str(db_p)),\
            mock.patch("happypanda.common.constants.internaldb", idb),\
            mock.patch("happypanda.common.clsutils.internaldb", idb),\
            mock.patch("happypanda.common.constants.app_path", app_path),\
            mock.patch("updater.constants.internal_db_path", str(db_p)):
            assert constants.internal_db_path == str(db_p)
            happyupd.main()
            db = constants.internaldb
            d = db[constants.updater_key]
            assert d['state'] == constants.UpdateState.Success.value
            assert all(os.path.exists(os.path.join(constants.app_path, x)) for x in asset_files)

    def test_updater_overwrite(self, tmp_update_folder, app_path):

        all(os.path.exists(os.path.join(constants.app_path, x)) for x in asset_files)
        db_p = tmp_update_folder.join("internals.db")
        p = str(tmp_update_folder.mkdir("updater_register2"))
        idb = clsutils.InternalDatabase(str(db_p))
        with mock.patch("happypanda.common.constants.internal_db_path", str(db_p)),\
            mock.patch("happypanda.common.constants.internaldb", idb),\
            mock.patch("happypanda.common.clsutils.internaldb", idb),\
            mock.patch("happypanda.common.constants.app_path", app_path),\
            mock.patch("happypanda.common.utils.create_temp_dir") as utils_temp,\
            mock.patch("happypanda.core.commands.io_cmd.CoreFS.delete"),\
            mock.patch("happypanda.common.constants.dir_update", p):
            utils_temp.return_value = str(tmp_update_folder.mkdir("updater_release2"))
            assert updater.register_release(asset_url_platform, silent=False, restart=True)

        idb = clsutils.InternalDatabase(str(db_p))
        with mock.patch("happypanda.common.constants.internal_db_path", str(tmp_update_folder.join("internals"))),\
            mock.patch("happypanda.common.constants.app_path", app_path),\
            mock.patch("happypanda.common.constants.internaldb", idb),\
            mock.patch("happypanda.common.clsutils.internaldb", idb),\
            mock.patch("updater.constants.internal_db_path", str(db_p)):
            assert constants.internal_db_path == str(db_p)
            with mock.patch("updater.atexit.register") as aexit:
                happyupd.main()
                assert aexit.called
            db = constants.internaldb
            d = db[constants.updater_key]
            assert d['state'] == constants.UpdateState.Success.value
            assert all(os.path.exists(os.path.join(constants.app_path, x)) for x in asset_files)
