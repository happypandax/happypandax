#!/usr/bin/python3
import gevent.monkey
import sys
import ssl, socket, select
import multiprocessing as mp
if mp.current_process().name in ("gevent",) or __name__ == '__main__':
    for x in (ssl, socket, select):
        del sys.modules[x.__name__]
    gevent.monkey.patch_all(thread=False)
from happypanda import main # noqa: E402

if __name__ == '__main__':
    mp.freeze_support()
    mp.set_start_method("spawn")
    main.start()
