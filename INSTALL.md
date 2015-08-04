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

*Note: make sure to mark the 'Add to path' checkbox when available on windows*

# Linux
1. Install these dependencies:
  - Qt5 (Install this first) >= 5.4
    + sudo pacman -S qt5-base ('apt-get install' on Ubuntu)
  - requests >= 2.6.0 & BeautifulSoup 4(PyPi)
    + Python 3.4 should've included pip on install. Incase it didn't: 'sudo pacman -S pip3'
    + To install 'requests': pip3 install requests
    + To install 'BeautifulSoup 4': pip3 install bs4
    + To install 'porc': pip3 install porc
  - PyQt5
    + I'm pretty sure you can install this through pip3, but if not: sudo pacman -S python-pyqt5 ('apt-get install python-pyqt5' on Ubuntu)
    
2. Now go where you want happypanda to be downloaded (E.g. 'cd ~'), and write: git clone https://github.com/Pewpews/happypanda.git
  - If it fails with something like 'unrecognized command 'git'' then do: sudo pacman -S git (apt-get install git on Ubuntu), and try again
3. Now enter the cloned directory (should be named 'happypanda') and write: python3 main.py
4. The program should now be running

# Windows
1. Install these dependencies:
  - Qt5 (Install this first) >= 5.4
    + Download from https://www.qt.io/download-open-source/#section-2
  - pip
    + Python 3.4 should've included pip on install. Incase it didn't https://pip.pypa.io/en/latest/installing.html
    Make sure python is in your PATH. (http://stackoverflow.com/questions/6318156/adding-python-path-on-windows-7)
    + Now open cmd and write these commands:
    + pip install requests
    + pip install bs4
    + pip install porc
  - PyQt5
    + I'm pretty sure you can install this through pip, but here is the download location
    http://www.riverbankcomputing.com/software/pyqt/download5 (see Binary Packages for windows)
    
2. Now go to the frontpage of the happypanda repo and click Download Zip
3. Extract to desired location
4. Open a cmd in that location. (in Windows you can write 'cmd' in the folder explorer url-bar and then press enter)
5. Write in cmd: python main.py
6. The program should now be running.

Note: Try renaming the 'main.py' file to 'main.pyw' and then just doubleclick on it to try running without console (not guaranteed to work)

# Mac OS X
1. Install Homebrew (this makes everything easier)
  - Open Terminal
  - Run the following
   + ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
   + brew update && brew upgrade --all
2. Install Python3, PyQt5, and sip
  - Run the following
   + brew install PyQt5
3. Install requests, BeautifulSoup4, Watchdog, and Porc
  - Run the following
   + python3 -m pip install requests
   + python3 -m pip install beautifulsoup4
   + python3 -m pip install watchdog
   + python3 -m pip install proc
4. Download HappyPanda
  - Go to github.com/Pewpews/happypanda
  - Press the "Download ZIP" button
  - UnZip happypanda-master.zip
5. Running HappyPanda
  - Run the following
   + cd /where/ever/you/put/the/folder/happypanda-master
     + (For example cd /Users/username/Downloads/happypanda-master)
   + python3 main.py
