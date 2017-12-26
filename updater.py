import shelve
import os
import sys
import shutil
import atexit

from happypanda.common import constants, hlogger

log = hlogger.Logger(__name__)

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

if __name__ == '__main__':
    log.setup_logger()

    with shelve.open(constants.internal_db_path) as db:
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
    except:
        log.exception("Failed to install new release")
        state = constants.UpdateState.Failed

    if update_info.get('restart', False):
        app = update_info.get('app', '')
        if app:
            log.i('Launching application', app)
            atexit.register(os.execv, app, update_info.get('args', []))
        else:
            log.e('No launch application provided')

    with shelve.open(constants.internal_db_path) as db:
        update_info['state'] = state.value
    log.i('Finished with state:', state)