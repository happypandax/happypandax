Twitter: [@pewspew](https://twitter.com/pewspew)

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Pewpews/happypandax?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/Pewpews/happypandax.svg?branch=master)](https://travis-ci.org/Pewpews/happypandax)

### This is project is under heavy development and is not ready for deployment. If you want to speed up the development, please consider [contributing](https://pewpews.github.io/happypandax/env.html).

# Building

1. install `Python 3.5` and `pip`
2. install `virtualenv` (`pip3 install virtualenv`)
3. clone or download Happypanda X
4. setup virtual env in the cloned/downloaded folder by running: `virtualenv env`
5. activate the virtual env by running: (Posix: `. env/bin/activate`) (Windows: `env\Scripts\activate.bat`)
6. install the dependencies by running: `pip3 install -r requirements.txt`
7. build the javascript files to use the webclient by running: `python build_js.py`

# Documentation

An online version of the doc can be found [here](https://pewpews.github.io/happypandax)

In case it's down, build the docs by running: `python build_docs.py` *(Note: this requires `pip3 install -r requirements-dev.txt`)*

# Contributing

Please refer to [doc](https://pewpews.github.io/happypandax/#for-developers)

# License

```
    Happypanda X is a cross platform manga/doujinshi manager with namespace & tag support;
    Copyright (C) 2017  Pewpew

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