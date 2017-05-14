import os
import configparser
import json

from contextlib import contextmanager

from happypanda.common import utils, constants, exceptions

log = utils.Logger(__name__)

class Config:

    def __init__(self, path):
        self._cfg = configparser.ConfigParser()
        self._cfg_d = {}
        self._current_ns = None
        self._path = path
        self._settings_f = os.path.join(self._path, constants.settings_file)
        self._descr_f = os.path.join(self._path, constants.settings_descr_file)
        self._load()

    def _load(self):
        assert self._settings_f and self._descr_f

        if os.path.exists(self._settings_f) and os.path.exists(self._descr_f):
            self._cfg.read(self._settings_f)

            with open(self._descr_f, 'r') as f:
                self._cfg_d = json.load(f)

    def save(self):
        assert self._settings_f and self._descr_f

        with open(self._settings_f, 'w') as f:
            self._cfg.write(f)

        with open(self._descr_f, 'w') as f:
            json.dump(self._cfg_d, f)

    @contextmanager
    def namespace(self, ns):
        assert isinstance(ns, str), "Namespace must be str"
        ns = ns.capitalize()
        if not ns in self._cfg:
            self._cfg[ns] = {}
        if not ns in self._cfg_d:
            self._cfg_d[ns] = {}

        self._current_ns = ns
        yield
        self._current_ns = None

    def define(self, key, value, description=""):
        assert self._current_ns, "No namespace has been set"
        self._cfg[self._current_ns][key] = value
        self._cfg_d[self._current_ns][key] = {'type':type(value), 'descr':description}

    def doc_render(self):
        sections = []
        for s in self._cfg:
            con = []
            for key in self._cfg[s]:
                con.append([key, self._cfg[s][key], self._cfg_d[s][key]['descr']])
            sections.append([con, s])
        return sections


config = Config(constants.dir_root)

doc_render = config.doc_render()

# [
#   [   
#    [[val1, val2, val3], ...]],
#    "header descr"
#   ],
# ]

