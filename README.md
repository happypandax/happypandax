# Happypanda
A cross platform manga/doujinshi manager with tagging support(soon).

I'm here if you've got any questions!

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Pewpews/Sadpanda?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# Screenshots
![alt-text][logo]

[logo]: "Screenshot 1"

# Dependecies
I wanted to keep the list short (I know the pain of wasting hours trying to install the correct dependecies)
- Qt5 (install this first)
- PyQt5

# How to run/use
*(I actually haven't tested this on other systems yet)*

1. Run main.py, add a series by clicking on the "Add series". Choose your series folder, and edit the metadata, click done.
2. Or you can populate the program with all series' from folder:
    - Currently supports the following folder structures *(folders containing both structures are supported)*:
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

3. If everything fails, or you fucked up, then feel free to delete the DB folder and start over. Find me in the gitter chat, if you have any questions.

# What to expect
I'm making this program while learning/discovering PyQt5 and python. More and more features will be added as time progresses. I expect to deploy an executable when i have implemented all the main features. Depending on school, this might take a while.

Since this is my first time using PyQt, I'll be saving old code and run the risk of making spaghetti code. (Sorry for that)

# Contributing
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Pewpews/Sadpanda?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Like stated earlier, my code is currently a mess (i think), but incase you still want to contribute then these are *some* tasks in my TODO list in no particular order:
- implement list view for chapters/mangas (PyQt)
- Set hotkeys (PyQt)
- implement searching for genres (PyQt)
- implement searching for manga title/artist (PyQt)
- implement sorting & filtering (sort by:(rank, title, artists, recent read, last updated) filter by: (status, genres, string/text, date) (PyQt)
- implement adding new manga/chapter from website (sadpanda and popular manga providers)
- implement checking for & downloading new chapters automatically (if possible)
- implement adding new manga/chapter by drag & dropping (zip, cbz, folder, etc..)/folder to program (PyQt)

**Things to note**:
The text in parantheses after each task is how and what i intended to implement it with. Since this is still in the "aplha" state I might move files or code, alot. I only expect to move my own code, but if nessecary then I'll talk to you first before moving anything. I don't expect this behaviour to continue when it's out of "alpha" state. Also please join the gitter chat so we can keep eachother updated.
