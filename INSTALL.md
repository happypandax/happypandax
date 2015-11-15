This guide will show you how to run from source.

A better option is dowloading the latest version
for your OS from
https://github.com/Pewpews/happypanda/releases

If you have any questions, please find me here
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Pewpews/happypanda?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)  I'll try to answer as soon as possible.

First make sure you have python of minimum version 3.4 installed.

Download from here https://www.python.org/downloads/
- arch: sudo pacman -S python3
- ubuntu: apt-get install python3
- OSX: see below

*Note: make sure to mark the 'Add to path' checkbox when available on windows*

# Linux
1. Go where you want happypanda to be downloaded (E.g. `cd ~`), and write `git clone https://github.com/Pewpews/happypanda.git`
  - If it fails with something like 'unrecognized command 'git'' then do: `sudo pacman -S git` (`apt-get install git` on Ubuntu), and try again
2. Install these dependencies:
  - Qt5 (Install this first) >= 5.4
    + `sudo pacman -S qt5-base` (`apt-get install qt5-default` on Ubuntu)
  - pip
    + Python 3.4 should've included pip on install. Incase it didn't: `sudo pacman -S python-pip`
    + Enter the happypanda folder and write `pip3 install -r requirements.txt`
  - PyQt5
    + I'm pretty sure you can install this through pip3, but if not then just `sudo pacman -S python-pyqt5` on Arch
    + On Ubuntu
        - `apt-get install python3-pyqt5`
        - `apt-get install PyQt5`
        - `apt-get install python3-pyqt5`
        - `apt-get install python3-pyqt5.qtsql`
3. In the happypanda directory go to the *version* directory and write `python3 main.py`
4. The program should now be running

# Windows
1. Go to the frontpage of the happypanda repo and click Download Zip
2. Extract to desired location
3. Install these dependencies:
  - Qt5 (Install this first) >= 5.4
    + Download from https://www.qt.io/download-open-source/#section-2
  - pip
    + Python 3.4 should've included pip on install. Incase it didn't https://pip.pypa.io/en/latest/installing.html
    Make sure python is in your PATH. (http://stackoverflow.com/questions/6318156/adding-python-path-on-windows-7)
    + Now open cmd and `cd` to the happypanda folder
    + Write: `pip install -r requirements.txt` and press enter
  - PyQt5
    + I'm pretty sure you can install this through pip, but here is the download location
    http://www.riverbankcomputing.com/software/pyqt/download5 (see Binary Packages for windows)
4. Finally, write `python main.py` to run the program
5. The program should now be running.

Note: Try renaming the 'main.py' file to 'main.pyw' and then just doubleclick on it to try running without console (not guaranteed to work)

# Mac OS X
(Note: PyQt5 MUST be installed via Homebrew and NOT via Pip)

1. Install Homebrew (this makes everything easier)
  - Open Terminal
  - Run the following
     + `ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`
     + `brew update && brew upgrade --all`
    
2. To install Python3, PyQt5, and sip (*still in Terminal*)
     + `brew install PyQt5`
3. To install other dependencies
     - Download HappyPanda
        + Go to github.com/Pewpews/happypanda
        + Press the "Download ZIP" button
        + UnZip happypanda-master.zip
  - In Terminal, navigate to the happypanda-master folder (E.g.: `cd /where/ever/you/put/the/folder/happypanda-master`)
    + Write `pip3 install -r requirements.txt`
5. Running HappyPanda
  - Run the following
   + `cd /where/ever/you/put/the/folder/happypanda-master/version`
     + (For example `cd /Users/username/Downloads/happypanda-master/version`)
   + `python3 main.py`
