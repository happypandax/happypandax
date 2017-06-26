[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Pewpews/happypandax?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/Pewpews/happypandax.svg?branch=master)](https://travis-ci.org/Pewpews/happypandax)
[![GitHub release](https://img.shields.io/github/release/happypandax/server.svg)]()
[![Github All Releases](https://img.shields.io/github/downloads/happypandax/server/total.svg)]()
[![Twitter Follow](https://img.shields.io/twitter/follow/pewspew.svg?style=social&label=Follow)](https://twitter.com/pewspew)

> **This is project is under heavy development and not yet ready for deployment. If you want to speed up the development, please consider [contributing](https://pewpews.github.io/happypandax/env.html).**

# Building

1. install `Python 3.5` and `pip3`
    > **Note**: Python 3.5 is the only supported version
2. install `virtualenv` by running: `pip3 install virtualenv`
3. clone or download this repository
4. setup a virtualenv in the cloned/downloaded folder by running: `virtualenv env`
5. activate the virtualenv by running: (on windows: `env\Scripts\activate.bat`) (on posix: `. env/bin/activate`)
6. install the dependencies by running: `pip3 install -r requirements.txt`
    > **Windows users**: If you get `error: command '..\cl.exe' failed with exit status 2`, download `bitarray` from [here](http://www.lfd.uci.edu/%7Egohlke/pythonlibs/#bitarray)
7. run the server: `python run.py -h`

# Documentation

An online version of the doc can be found [here](https://pewpews.github.io/happypandax)

In case it's ever down, build the docs by running: `python build_docs.py`
>**Note**: this requires `pip3 install -r requirements-dev.txt`)

# Contributing

Please refer to [doc](https://pewpews.github.io/happypandax/#for-developers)

# License

```
    Happypanda X is a cross platform manga/doujinshi manager with namespace & tag support;
    Copyright (C) 2017  Twiddly

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
```