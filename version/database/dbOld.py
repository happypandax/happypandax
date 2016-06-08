#"""
#This file is part of Happypanda.
#Happypanda is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 2 of the License, or
#any later version.
#Happypanda is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#You should have received a copy of the GNU General Public License
#along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
#"""

import os
import sqlite3
import threading
import queue
import logging
import time
import shutil
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, BLOB, ForeignKey

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class DBBase:
    "The base DB class. _DB_CONN should be set at runtime on startup"
    _DB_CONN = None
    _AUTO_COMMIT = True
    _STATE = {'active':False}

    def __init__(self, **kwargs):
        pass

    @classmethod
    def begin(cls):
        "Useful when modifying for a large amount of data"
        if not cls._STATE['active']:
            cls._AUTO_COMMIT = False
            cls.execute(cls, "BEGIN TRANSACTION")
            cls._STATE['active'] = True
        #print("STARTED DB OPTIMIZE")

    @classmethod
    def end(cls):
        "Called to commit and end transaction"
        if cls._STATE['active']:
            try:
                cls.execute(cls, "COMMIT")
            except sqlite3.OperationalError:
                pass
            cls._AUTO_COMMIT = True
            cls._STATE['active'] = False
        #print("ENDED DB OPTIMIZE")

    def execute(self, *args):
        "Same as cursor.execute"
        if not self._DB_CONN:
            raise db_constants.NoDatabaseConnection
        log_d('DB Query: {}'.format(args).encode(errors='ignore'))
        if self._AUTO_COMMIT:
            try:
                with self._DB_CONN:
                    return self._DB_CONN.execute(*args)
            except sqlite3.InterfaceError:
                    return self._DB_CONN.execute(*args)

        else:
            return self._DB_CONN.execute(*args)
    
    def executemany(self, *args):
        "Same as cursor.executemany"
        if not self._DB_CONN:
            raise db_constants.NoDatabaseConnection
        log_d('DB Query: {}'.format(args).encode(errors='ignore'))
        if self._AUTO_COMMIT:
            with self._DB_CONN:
                return self._DB_CONN.executemany(*args)
        else:
            c = self._DB_CONN.executemany(*args)
            return c

    def commit(self):
        self._DB_CONN.commit()

    @classmethod
    def analyze(cls):
        cls._DB_CONN.execute('ANALYZE')

    @classmethod
    def close(cls):
        cls._DB_CONN.close()

if __name__ == '__main__':
    raise RuntimeError("Unit tests not yet implemented")
    # unit tests here!