# Happypanda
A cross platform manga/doujinshi manager with tagging support(soon).

I'm here if you have any questions!

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Pewpews/happypanda?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# Screenshots
![alt-text][logo]

[logo]: https://raw.githubusercontent.com/Pewpews/Sadpanda/master/misc/screenshot1.png "Screenshot 1"

# Dependencies
I wanted to keep the list short (I know the pain of wasting hours trying to install the correct dependencies)
- Qt5 (Install this first)
- PyQt5

# How to run/use
*(I actually haven't tested this on other systems yet)*

1. Run main.py, add a series by clicking on the "Add series". Choose your series folder and edit the metadata, at last click done.
2. Or you can populate the program with all series' from folder:
    - Currently supports the following folder structures *(Folders containing both structures are supported)*:
        + .../My_general_series_folder
            - --/Series1_folder
                - --/Chp_1_folder
                    - --/image_1
                    - --/image_2
                - --/Chp_n_folder
                    - --/image_n

        + .../My_general_series_folder
            - --/Series1_folder
                - --/image_1
                - --/image_2
            - --/Series_n_folder
                - --/image_n
                - --/image_n

3. If everything fails or you somehow messed up, then feel free to delete the DB folder and start over. Find me in the gitter chat, if you have any questions.

# What to expect
I'm making this program while learning/discovering PyQt5 and python. More features will be added in the future. I expect to deploy an executable when I have implemented all the main features. Depending on school, this might take a while.

Since this is my first time using PyQt, I'll be saving old code and run the risk of making spaghetti code. (Sorry about that)

# Contributing
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Pewpews/happypanda?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Like stated earlier, my code is currently a mess (I think), but in case you still want to contribute, then these are *some* tasks in my TODO list in no particular order:
- implement list view for chapters/mangas (PyQt)
- Set hotkeys (PyQt)
- implement searching for genres (PyQt)
- implement searching for manga title/artist (PyQt)
- implement sorting & filtering (sort by:(rank, title, artists, recent read, last updated) filter by: (status, genres, string/text, date) (PyQt)
- implement adding new manga/chapter from website (sadpanda and popular manga providers)
- implement checking for & downloading new chapters automatically (if possible)
- implement adding new manga/chapter by drag & dropping (zip, cbz, folder, etc..)/folder to program (PyQt)

**Things to note**:
The text in parentheses after each task is how and what I intended to implement it with. Since this is still the aplha version I might move files or code a lot. I only expect to move my own code, but if nessecary then I'll talk to you first before moving anything. I don't expect this behaviour to continue when it's out of alpha version. Also please join the gitter chat so we can keep eachother updated.
