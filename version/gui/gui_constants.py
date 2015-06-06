"""
This file is part of Happypanda.
Happypanda is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
any later version.
Happypanda is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
"""Contains constants to be used by several modules"""

# Version number
vs  = '0.14'

current_dir, f = os.path.split(os.path.realpath(__file__))
static_dir = os.path.join(current_dir, "static")

#default stylesheet path
default_stylesheet_path = static_dir + '/' + "style.css"
user_stylesheet_path = ""

# sizes
MAIN_W = 1029 # main window
MAIN_H = 650 # main window
GRIDBOX_H_SIZE = 250
GRIDBOX_W_SIZE = GRIDBOX_H_SIZE//1.47
THUMB_H_SIZE = 200
THUMB_W_SIZE = 145

# Columns
COLUMNS = [0, 1, 2, 3, 4]
TITLE = 0
ARTIST = 1
TAGS = 2
TYPE = 3
FAV = 4

# image paths
APP_ICO_PATH = os.path.join(static_dir, "happypanda.ico")
STAR_BTN_PATH = os.path.join(static_dir, "btn_star.png")
STAR_PATH = os.path.join(static_dir, "star.png")
STAR_SMALL_PATH = os.path.join(static_dir, "star_small.png")
PLUS_PATH = os.path.join(static_dir, "plus.png")
HOME_BTN_PATH = os.path.join(static_dir, "home.png")
SETTINGS_PATH = os.path.join(static_dir, "settings.png")
GRID_PATH = os.path.join(static_dir, "grid.png")
LIST_PATH = os.path.join(static_dir, "list.png")

# controls
THUMBNAIL_CACHE_SIZE = 10240*100 #10240 is 10mb, so sum is 1gb
PREFETCH_ITEM_AMOUNT = 100 # amount of items to prefetch
SCROLL_SPEED = 9 # controls how many steps it takes when scrolling

# POPUP
POPUP_WIDTH = 450
POPUP_HEIGHT = 220