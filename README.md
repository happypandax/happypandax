# Dependecies
- Qt5 (install this first)
- PyQt5

# How to run
1. Run main.py, click on "Add series" dropdown, and click Populate from folder.
    - Currently supports the following folder structures:
        + .../My_manga_folder
            - --/Series1
                - --/Chp_1
                    - --/image_1
                    - --/image_2
                - --/Chp_n
                    - --/image_n

        + .../My_manga_folder
            - --/Series1
                - --/image_1
                - --/image_2
            - --/Series_n
                - --/image_n
                - --/image_n

3. Navigate to root folder and run main.py

# Notes
Aside from making an usable program, I seriously need to fix the import system in the code.

# What to expect
I'm currently only trying to make a mockup program while learning/discovering PyQt5. More and more features will be added as time progresses. I expect to release an usable program in about a month depending on how busy school will be. (Current Date: 28 april)
The code is currently a mess.
Since this is my first time using PyQt I'll be saving alot of old code, and run the risk of making spaghetti code.

# Contributing
Like stated earlier, my code is currently a mess (will try to fix when done testing), but incase you still want to contribute then these are the tasks in my TODO list in no particular order:
- Implement a database using sqlite3 or pickle module
- implement list view for chapters/mangas (PyQt)
- implement opening chapter in external image viewer feature
- implement hotkeys (PyQt)
- implement searching for genres (PyQt)
- implement searching for manga title/artist (PyQt)
- implement sorting & filtering (sort by:(rank, title, artists, recent read, last updated) filter by: (status, genres, string/text, date) (PyQt)
- implement a "Favourite" view (PyQt)
- implement adding new manga/chapter manually (PyQt, Database)
- implement adding new manga/chapter from website (sadpanda and popular manga providers)
- implement checking for & downloading new chapters automatically
- implement adding new manga/chapter by drag & dropping (zip, cbz, etc)/folder to program (PyQt)

**Things to note**:
The text in parantheses after each task is how and what i intended to implement it with. Since this is still in the "testing" state I might move some files or code; alot. I only expect to move my own code, but if nessecary then I'll talk to you first before moving anything. I don't expect this behaviour to continue when it's out of "testing" state. 
