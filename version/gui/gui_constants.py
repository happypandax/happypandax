import os
"""Contains constants to be used by several modules"""

current_dir, f = os.path.split(os.path.realpath(__file__))
static_dir = os.path.join(current_dir, "static")

#default stylesheet path
default_stylesheet_path = static_dir + '/' + "style.css"
user_stylesheet_path = ""

# sizes
GRIDBOX_H_SIZE = 250
GRIDBOX_W_SIZE = GRIDBOX_H_SIZE//1.47
THUMB_H_SIZE = 200
THUMB_W_SIZE = 145

# chapterview
CHAP_IMAGE_H = 325

# image paths
STAR_BTN_PATH = os.path.join(static_dir, "btn_star.png")
STAR_PATH = os.path.join(static_dir, "star.png")
STAR_SMALL_PATH = os.path.join(static_dir, "star_small.png")
PLUS_PATH = os.path.join(static_dir, "plus.png")
HOME_BTN_PATH = os.path.join(static_dir, "home.png")
SETTINGS_PATH = os.path.join(static_dir, "settings.png")

# controls
THUMBNAIL_CACHE_SIZE = 10240*100 #10240 is 10mb, so sum is 1gb