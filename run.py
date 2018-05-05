#!/usr/bin/python3
import multiprocessing as mp
from gevent import monkey
if mp.current_process().name in ("MainProcess", "gevent"):
    monkey.patch_all(thread=False)
from happypanda import main # noqa: E402

if __name__ == '__main__':
    mp.freeze_support()
    mp.set_start_method("spawn")
    main.start()
