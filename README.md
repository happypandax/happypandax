# Happypanda
A cross platform manga/doujinshi manager with namespace & tag support.

Development is done in alpha branch

I'm here if you have any questions!

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Pewpews/happypanda?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# Screenshots
<img src="misc/screenshot1.png" width="300">
<img src="misc/screenshot2.png" width="300">
<img src="misc/screenshot3.png" width="300">
<img src="misc/screenshot4.png" width="300">

# How to install & run
*(Tested on windows and linux)*

For Mac & Linux see [INSTALL.md](INSTALL.md)

1. Download the installer from [releases](https://github.com/Pewpews/happypanda/releases)
2. Extract to desired location (avoid locations where you need admin rights)
3. Run the program by clicking on Happypanda

# Features
- Keep track of your galleries and organize them more easily
- Search for galleries through title, artist or namespaces & tags
- Fetch metadata which includes namespace & tags from the web (Currently only supports g.e-hentai and exhentai) without getting you banned
- Favourite your favourite galleries and keep them in a seperate view
- View your galleries with highquality thumbnails or in a simple table list
- Add your galleries easily without worrying about adding duplicates with one of the 3 available modes:
	+ Add a single gallery. *Note: this way you can add even if the gallery already exist*
	+ Add galleries from different locations
	+ Or just populate from a single folder containing all your galleries
- Currently supports ZIP/CBZ and the following folder structures:
    + .../My_general_gallery_folder
        - --/gallery1_folder
            - --/Chp_1_folder
                - --/image_1
                - --/image_2
            - --/Chp_n_folder
                - --/image_n

    + .../My_general_gallery_folder
        - --/gallery1_folder
            - --/image_1
            - --/image_2
        - --/gallery_n_folder
            - --/image_n
            - --/image_n
- Add new released chapters to your gallery easily
- Monitor 1 or more folders for events and be notified:
	+ Renaming a gallery source  will prompt the program to ask if you want to update the renamed gallery's source
	+ Deleting a gallery source will prompt the program to ask if you want to remove the gallery from the program as well
	+ Adding new gallery sources will prompt the program to ask you if you want to add them
- Customize your program with lots of options in the settings
- And lots more...

# Dependencies
- Qt5 (Install this first) >= 5.4
- PyQt5
- requests (pip) >= 2.6.0
- BeautifulSoup 4 (pip)
- watchdog (pip)
- porc (pip)

# Contributing
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Pewpews/happypanda?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
Meet me there!