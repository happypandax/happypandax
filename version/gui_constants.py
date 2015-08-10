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

import os, sys
import settings
"""Contains constants to be used by several modules"""

# Version number
vs  = '0.21'
DEBUG = False

get = settings.get

#current_dir, f = os.path.split(os.path.realpath(__file__))
static_dir = os.path.join(os.getcwd(), "../res")
temp_dir = os.path.join('../temp')

#default stylesheet path
default_stylesheet_path = static_dir + '/' + "style.css"
user_stylesheet_path = ""

FIRST_TIME_LEVEL = get(2, 'Application', 'first time level', int)

# sizes
MAIN_W = 1029 # main window
MAIN_H = 650 # main window
GRIDBOX_H_SIZE = 230
GRIDBOX_W_SIZE = GRIDBOX_H_SIZE//1.40 #1.47
GRIDBOX_LBL_H = 60
GRIDBOX_H_SIZE += GRIDBOX_LBL_H - 10
THUMB_H_SIZE = 200
THUMB_W_SIZE = 143

# Columns
COLUMNS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
TITLE = 0
ARTIST = 1
DESCR = 2
TAGS = 3
TYPE = 4
FAV = 5
CHAPTERS = 6
LANGUAGE = 7
LINK = 8
PUB_DATE = 9
DATE_ADDED = 10

# Application
SYSTEM_TRAY = None
NOTIF_BAR = None

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

# Monitored Paths
OVERRIDE_MONITOR = False # set true to make watchers to ignore next item (will be set to False)
LOOK_NEW_GALLERY_STARTUP = get(True, 'Application', 'look new gallery startup', bool)
LOOK_NEW_GALLERY_AUTOADD = get(False, 'Application', 'look new gallery autoadd', bool)
ENABLE_MONITOR = get(True, 'Application', 'enable monitor', bool)
MONITOR_PATHS = [x for x in get('', 'Application', 'monitor paths', str).split(',') if x]
IGNORE_PATHS = [x for x in get('', 'Application', 'ignore paths', str).split(',') if x]

# GENERAL
OVERRIDE_MOVE_IMPORTED_IN_FETCH = False # set to true to make a fetch instance ignore moving files (will be set to false)
MOVE_IMPORTED_GALLERIES = get(False, 'Application', 'move imported galleries', bool)
IMPORTED_GALLERY_DEF_PATH = get('', 'Application', 'imported gallery def path', str)
SCROLL_TO_NEW_GALLERIES = get(False, 'Application', 'scroll to new galleries', bool)
OPEN_RANDOM_GALLERY_CHAPTERS = get(False, 'Application', 'open random gallery chapters', bool)
SUBFOLDER_AS_GALLERY = get(False, 'Application', 'subfolder as gallery', bool)
RENAME_GALLERY_SOURCE = get(False, 'Application', 'rename gallery source', bool)

# ADVANCED
GALLERY_DATA_FIX_REGEX = get("", 'Advanced', 'gallery data fix regex', str)
GALLERY_DATA_FIX_TITLE = get(True, 'Advanced', 'gallery data fix title', bool)
GALLERY_DATA_FIX_ARTIST = get(True, 'Advanced', 'gallery data fix artist', bool)
GALLERY_DATA_FIX_REPLACE = get("", 'Advanced', 'gallery data fix replace', str)

# HASH
HASH_GALLERY_PAGES = get('all', 'Advanced', 'hash gallery pages', int, str)

# WEB
GLOBAL_EHEN_TIME = get(10, 'Web', 'global ehen time offset', int)
GLOBAL_EHEN_LOCK = False
DEFAULT_EHEN_URL = get('http://g.e-hentai.org/', 'Web', 'default ehen url', str)
REPLACE_METADATA = get(False, 'Web', 'replace metadata', bool)
ALWAYS_CHOOSE_FIRST_HIT = get(False, 'Web', 'always choose first hit', bool)
USE_JPN_TITLE = get(False, 'Web', 'use jpn title', bool)
CONTINUE_AUTO_METADATA_FETCHER = get(True, 'Web', 'continue auto metadata fetcher', True)

# External Viewer
EXTERNAL_VIEWER_SUPPORT = {'honeyview':['Honeyview.exe']}
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
CURRENT_SORT = get('title', 'General', 'current sort')
HIGH_QUALITY_THUMBS = get(False, 'Visual', 'high quality thumbs', bool)
USE_EXTERNAL_PROG_ICO = get(True, 'Visual', 'use external prog ico', bool) if not sys.platform.startswith('darwin')  else False
DISPLAY_GALLERY_TYPE = get(True, 'Visual', 'display gallery type', bool) if not sys.platform.startswith('darwin') else False
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
TOOLTIP_LANG = get(False, 'Visual', 'tooltip lang', bool)
TOOLTIP_DESCR = get(False, 'Visual', 'tooltip descr', bool)
TOOLTIP_TAGS = get(False, 'Visual', 'tooltip tags', bool)
TOOLTIP_LAST_READ = get(True, 'Visual', 'tooltip last read', bool)
TOOLTIP_TIMES_READ = get(True, 'Visual', 'tooltip times read', bool)
TOOLTIP_PUB_DATE = get(False, 'Visual', 'tooltip pub date', bool)
TOOLTIP_DATE_ADDED = get(True, 'Visual', 'tooltip date added', bool)

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
Is your preffered viewer not on the list? Hit me up on github/gitter-chat to add official support.
"""

SEARCH_TUTORIAL_TIT_AUT =\
	"""There are two ways to search for title/author:
- 'term' or 'title:"term"'
- 'author' or 'author:"term"'

Examples:
Say we want to find 'example title' by 'anon'

First search entry: 'title:"example title"'
Result: All galleries with the string 'example title' in their title
Second search entry: example title
Result: All galleries with either example or title in their title

Same thing applies to author:

First search entry: 'author:"anon"'
Result: Same as above
Second search entry: 'anon'
Result: This will however show all galleries with the string anon in either tag, title or author
"""


SEARCH_TUTORIAL_TAGS =\
	"""There are three ways to search for namespaces and tags:
tag_term, namespace:tag_term and namespace:[tag_term1, tag_term2]

Examples:
Say we want to find a gallery with the namespace & tags: "tag1, ns:tag1, ns2:[tag1, tag2]"

First search entry: 'tag1'
Result: All galleries with a tag which is not in a namespace + the word 'tag1' in their title or author
Second search entry: 'ns:tag1'
Result: All galleries with the tag 'tag1' in namespace 'ns'
Third search entry: 'ns2:[tag1, tag2]'
Result: All galleries with 'tag1' AND 'tag2' in namespace 'ns2'
"""

SEARCH_TUTORIAL_GENERAL=\
	"""Term excluding and case sensitive searching are not yet supported. (Will be in the near future)
Some things to note when searching:
- terms are seperated by a comma
"""

