#!/usr/bin/python3
import happypanda.common.patch
if __name__ in ('__main__', '__mp_main__'):
    happypanda.common.patch.patch()

import multiprocessing as mp # noqa: E402
from happypanda import main # noqa: E402

if __name__ == '__main__':
    mp.set_start_method("spawn")
    mp.freeze_support()
    main.start()
