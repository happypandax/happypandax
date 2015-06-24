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
from .. import settings
"""Contains constants to be used by several modules"""

# Version number
vs  = '0.15'

get = settings.get

current_dir, f = os.path.split(os.path.realpath(__file__))
static_dir = os.path.join(current_dir, "static")
temp_dir = os.path.join('temp')

#default stylesheet path
default_stylesheet_path = static_dir + '/' + "style.css"
user_stylesheet_path = ""

# sizes
MAIN_W = 1029 # main window
MAIN_H = 650 # main window
GRIDBOX_H_SIZE = 230
GRIDBOX_W_SIZE = GRIDBOX_H_SIZE//1.40 #1.47
GRIDBOX_LBL_H = 60
GRIDBOX_H_SIZE += GRIDBOX_LBL_H
THUMB_H_SIZE = 200
THUMB_W_SIZE = 143

# Columns
COLUMNS = [0, 1, 2, 3, 4, 5, 6, 7]
TITLE = 0
ARTIST = 1
TAGS = 2
TYPE = 3
FAV = 4
CHAPTERS = 5
LANGUAGE = 6
LINK = 7


# image paths
GALLERY_ICO_PATH = os.path.join(static_dir, "gallery_ico.ico")
GALLERY_DEF_ICO_PATH = os.path.join(static_dir, "gallery_def_ico.ico")
GALLERY_EXT_ICO_PATH = os.path.join(static_dir, "gallery_ext_ico.ico")
APP_ICO_PATH = os.path.join(static_dir, "happypanda.ico")
STAR_BTN_PATH = os.path.join(static_dir, "btn_star.png")
STAR_PATH = os.path.join(static_dir, "star.png")
STAR_SMALL_PATH = os.path.join(static_dir, "star_small.png")
PLUS_PATH = os.path.join(static_dir, "plus.png")
HOME_BTN_PATH = os.path.join(static_dir, "home.png")
SETTINGS_PATH = os.path.join(static_dir, "settings.png")
GRID_PATH = os.path.join(static_dir, "grid.png")
LIST_PATH = os.path.join(static_dir, "list.png")
NO_IMAGE_PATH = os.path.join(static_dir, "default.jpg")

# External Viewer
EXTERNAL_VIEWER_SUPPORT = {'honeyview':['Honeyview.exe'], 'irfanview':['i_view32.exe']}
USE_EXTERNAL_VIEWER = get(False, 'Advanced', 'use external viewer', bool)
EXTERNAL_VIEWER_PATH = os.path.normcase(get('', 'Advanced', 'external viewer path', str))
_REFRESH_EXTERNAL_VIEWER = False

# controls
THUMBNAIL_CACHE_SIZE = (1024, get(200, 'Advanced', 'cache size', int)) #1024 is 1mib
PREFETCH_ITEM_AMOUNT = get(1, 'Advanced', 'prefetch item amount', int)# amount of items to prefetch
SCROLL_SPEED = get(7, 'Advanced', 'scroll speed', int) # controls how many steps it takes when scrolling

# POPUP
POPUP_WIDTH = get(450, 'Visual', 'popup.w', int)
POPUP_HEIGHT = get(220, 'Visual', 'popup.h', int)

# Gallery
HIGH_QUALITY_THUMBS = get(False, 'Visual', 'high quality thumbs', bool)
USE_EXTERNAL_PROG_ICO = get(True, 'Visual', 'use external prog ico', bool)
DISPLAY_GALLERY_TYPE = get(True, 'Visual', 'display gallery type', bool)
GALLERY_FONT = (get('Segoe UI', 'Visual', 'gallery font family', str),
				get(11, 'Visual', 'gallery font size', int))
GALLERY_FONT_ELIDE = get(True, 'Visual', 'gallery font elide', bool)

# Colors
GRID_VIEW_TITLE_COLOR = get('#323232', 'Visual', 'grid view title color', str)
GRID_VIEW_ARTIST_COLOR = get('#585858', 'Visual', 'grid view artist color', str)
GRID_VIEW_LABEL_COLOR = get('#F2F2F2', 'Visual', 'grid view label color', str)

# Search
SEARCH_AUTOCOMPLETE = get(True, 'Advanced', 'search autocomplete', bool)
ALLOW_SEARCH_REGEX = get(False, 'Advanced', 'allow search regex', bool)
SEARCH_ON_ENTER = get(False, 'Advanced', 'search on enter', bool)

# Grid Tooltip
GRID_TOOLTIP = get(True, 'Visual', 'grid tooltip', bool)
TOOLTIP_TITLE = get(False, 'Visual', 'tooltip title', bool)
TOOLTIP_AUTHOR = get(False, 'Visual', 'tooltip author', bool)
TOOLTIP_CHAPTERS = get(True, 'Visual', 'tooltip chapters', bool)
TOOLTIP_STATUS = get(True, 'Visual', 'tooltip status', bool)
TOOLTIP_TYPE = get(True, 'Visual', 'tooltip type', bool)
TOOLTIP_LANG = get(True, 'Visual', 'tooltip lang', bool)
TOOLTIP_DESCR = get(False, 'Visual', 'tooltip descr', bool)
TOOLTIP_TAGS = get(True, 'Visual', 'tooltip tags', bool)
TOOLTIP_LAST_READ = get(True, 'Visual', 'tooltip last read', bool)
TOOLTIP_TIMES_READ = get(True, 'Visual', 'tooltip times read', bool)
TOOLTIP_PUB_DATE = get(False, 'Visual', 'tooltip pub date', bool)
TOOLTIP_DATE_ADDED = get(False, 'Visual', 'tooltip date added', bool)

EXHEN_COOKIE_TUTORIAL =\
	"""
How do you find these two values? <br \>
<b>Firefox:</b> <br \>
1. Navigate to exhentai.org <br \>
2. Press Shift + F2 (A console should appear below) <br \>
3. Write: cookie list <br \>
4. A popup should appear with a list over active cookies <br \>
5. Look for the 'ipb_member_id' and 'ipb_hash_pass' values <br \>
<br \>
<b>Other browsers</b> <br \>
1. Download a cookie manager (google it) <br \>
2. look for the 'ipb_member_id' and 'ipb_hash_pass' values in exhentai cookies
"""

GPL =\
	"""Happypanda is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or any later version. Happypanda is distributed in the hope that it will
be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details. You should have received a copy of the GNU General Public License along with Happypanda. 
If not, see http://www.gnu.org/licenses/."""

TROUBLE_GUIDE =\
	""" Did you find any bugs? Then please walk through this guide, so we can fix it together! <br/>
	<br/>
<b>Can you start a new instance of happypanda and reproduce the bug?</b><br/>
	- If that's not the case then skip the steps below and go to <i>How to report</i>:<br/>
	1. First close all instances of Happypanda.<br/>
	2. Open a console and navigate to where Happypanda is installed. <i>Eg.: cd path/to/happypanda</i><br/>
	3. Now type: <i>Happypanda.exe -d</i> or <i>main.py -d</i> depending on what the main file is called.<br/>
	4. The program will now open, and create a new file named <i>happypanda_debug.log</i>.<br/>
	5. Reproduce the error/bug<br/>
	<br/>
<b>How to report</b><br/>
If you did the steps written above, then be sure to include the <i>happypanda_debug.log</i> file which was created<br/>
and how you reproduced the error/bug. <br/>
1. Navigate to where you installed Happypanda with a file explorer, <br/>and find <i>happypanda.log<i>. Send it to me with a description of the bug.<br/>
2. You have 3 options of contacting me:<br/>
- Go to the github repo issue page <a href='https://github.com/Pewpews/happypanda/issues'>here</a>, <br/>and create a new issue <i>(if it doesn't already exist, 
if it does then comment the last iteration of your log contents)</i><br/>
- Enter the chat <a href='https://gitter.im/Pewpews/happypanda'>here</a>, and tell me about your issue.<br/>
- If for some reason you don't want anything to do with github, <br/>then feel free to email me: happypandabugs@gmail.com
"""

SUPPORTED_EXTERNAL_VIEWER_LBL =\
	"""Currently only these programs are officially supported (tested and works):

Windows: Default Viewer, Honeyview, Irfanview
Linux: Default Viewer
Mac: Default Viewer

Note: Your viewer *might* still work, even though it's not on the list.
You preffered viewer not on the list? Hit me up on github/gitter-chat to add official support.
"""

