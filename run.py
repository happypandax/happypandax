#!/usr/bin/python3
import multiprocessing
from happypanda import main

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main.start()
