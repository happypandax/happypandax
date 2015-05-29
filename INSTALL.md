This guide will show you how to run from source.

A better option is dowloading the latest version
for your OS from
https://github.com/Pewpews/happypanda/releases

If you have any questions, please find me here
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Pewpews/happypanda?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)  I'll try to answer as soon as possible.

First make sure you have python of minimum version 3.4 installed.

Download from here https://www.python.org/downloads/

*Note: make sure to mark the 'Add to path' checkbox when available*

# Linux & Mac
i'm petty sure it's the same way as on windows but incase not, please tell me.

# Windows
1. Install these dependencies:
  - Qt5 (Install this first) >= 5.4
    + Download from https://www.qt.io/download-open-source/#section-2
  - requests (pip) >= 2.6.0
    + Python 3.4 should've included pip on install. Incase it didn't https://pip.pypa.io/en/latest/installing.html
    Make sure python is in your PATH. (http://stackoverflow.com/questions/6318156/adding-python-path-on-windows-7)
    + Now open cmd; Write: pip install requests
  - PyQt5
    + I'm pretty sure you can install this through pip, but here is the download location
    http://www.riverbankcomputing.com/software/pyqt/download5 (see Binary Packages for windows)
    
2. Now go to the frontpage of the happypanda repo and click Download Zip
3. Extract to desired location
4. Open a cmd in that location. (in Windows you can write 'cmd' in the fodler explorer url bar and then press enter)
5. Write: python main.py
6. The program should now be running.

Note: Try renaming the 'main.py' file to 'main.pyw' to try running without console (not guaranteed to work)
