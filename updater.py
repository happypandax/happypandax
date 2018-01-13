import os
import sys
import shutil
import atexit

from happypanda.common import constants, hlogger, utils

log = hlogger.Logger("HappyUpdater")


def move_replace(root_src_dir, root_dst_dir):
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            shutil.move(src_file, dst_dir)

def main():
    log.setup_logger()
    try:
        with utils.intertnal_db() as db:
            update_info = db.get(constants.updater_key, {})
        if not update_info:
            log.e("No update info registered")
            sys.exit(1)

        if not os.path.exists(update_info.get('from', '')):
            log.e("New release does not exist")
            sys.exit(1)

        if not os.path.exists(update_info.get('to', '')):
            log.e("Application location does not exist")
            sys.exit(1)

        state = constants.UpdateState.Success
        log.i("Installing new release..")
        try:
            move_replace(update_info['from'], update_info['to'])
            log.i("Removing leftovers..")
            shutil.rmtree(update_info['from'])
        except BaseException:
            log.exception("Failed to install new release")
            state = constants.UpdateState.Failed

        if update_info.get('restart', False):
            app = update_info.get('app', '')
            if app:
                args = update_info.get('args', [])
                log.i('Launching application', app, "with args", args)
                atexit.register(os.execl, app, app, *args)
            else:
                log.e('No launch application provided')

        with utils.intertnal_db() as db:
            update_info['state'] = state.value
            db[constants.updater_key] = update_info
        log.i('Finished with state:', state)
    except BaseException:
        log.exception("Updater failed")

if __name__ == '__main__':
    main()