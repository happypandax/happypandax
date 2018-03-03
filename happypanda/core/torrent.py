import asyncio
import os
import re
import signal
import multiprocessing as mp

from contextlib import closing, suppress
from functools import partial

from happy_bittorrent.control import ControlManager, ControlClient, ControlServer, DaemonExit, formatters
from happy_bittorrent.models import TorrentInfo, TorrentState
from happypanda.common import exceptions, constants, hlogger

log = hlogger.Logger(constants.log_ns_core+__name__)


async def check_daemon_absence():
    try:
        async with ControlClient():
            pass
    except RuntimeError:
        pass
    else:
        raise exceptions.CoreError(
            "torrent daemon",
            'A daemon on this port is already running')


def run_daemon():
    try:
        with closing(asyncio.get_event_loop()) as loop:
            loop.run_until_complete(check_daemon_absence())

            control = ControlManager()
            loop.run_until_complete(control.start())

            try:
                control.load_state()
            except Exception as err:
                log.exception('Failed to load program state:', err)
            control.invoke_state_dumps()

            stopping = False

            def stop_daemon(server: ControlServer):
                nonlocal stopping
                if stopping:
                    return
                stopping = True

                stop_task = asyncio.ensure_future(
                    asyncio.wait([server.stop(), server.control.stop()]))
                stop_task.add_done_callback(lambda fut: loop.stop())

            control_server = ControlServer(control, stop_daemon)
            loop.run_until_complete(control_server.start())

            if os.name == 'posix':
                for sig in (signal.SIGINT, signal.SIGTERM):
                    loop.add_signal_handler(
                        sig, partial(stop_daemon, control_server))

            loop.run_forever()
    except OSError as e:
        log.exception(
            "Error: Failed to start torrent daemon (Port might already be in use)")


def show(filename):
    "Show torrent content (no daemon required)"
    tf = TorrentInfo.from_file(filename, download_dir=None)
    return formatters.join_lines(
        formatters.format_title(tf, True) + formatters.format_content(tf))


PATH_SPLIT_RE = re.compile(r'/|{}'.format(re.escape(os.path.sep)))


async def _add(filename, download_dir=None, files=None, mode=None):
    tf = TorrentInfo.from_file(filename, download_dir=download_dir)
    if mode:
        if tf.download_info.single_file_mode:
            raise exceptions.CoreError(
                "torrent addition",
                "Can't select files in a single-file torrent")

        files = [PATH_SPLIT_RE.split(path) for path in files]
        tf.download_info.select_files(files, mode)

    async with ControlClient() as client:
        await client.execute(partial(ControlManager.add, torrent_info=tf))


def add(filename, download_dir=constants.dir_download, files=None, mode=None):
    """
    Add a new torrent
    Params:
        - filename -- path to torrent file
        - download_dir -- directory to download torrent
        - files -- list of filenames to include or exclude
        - mode -- 'include' or 'exclude' files
    """
    _run_in_event_loop(_add, filename, download_dir, filename, mode)


async def _set_state(filenames, state):
    assert isinstance(filenames, list)
    state = getattr(ControlManager, state)

    torrents = [
        TorrentInfo.from_file(
            filename,
            download_dir=None) for filename in filenames]
    # FIXME: Execute action with all torrents if torrents == []

    async with ControlClient() as client:
        for info in torrents:
            await client.execute(partial(state, info_hash=info.download_info.info_hash))


def set_state(filenames, state):
    """
    Set state of torrents
    Params:
        - filenames -- list of filenames of torrents
        - state -- 'pause', 'resume', 'remove'
    """
    _run_in_event_loop(_set_state, filenames, state)


def _status_server_handler(manager):
    torrents = manager.get_torrents()
    if not torrents:
        return 'No torrents added'

    torrents.sort(key=lambda info: info.download_info.suggested_name)
    return [TorrentState(torrent_info) for torrent_info in torrents]


async def _status(future, verbose=True):
    async with ControlClient() as client:
        torrent_states = await client.execute(_status_server_handler)

    future.set_result([formatters.join_lines(formatters.format_title(state, verbose) +
                                             formatters.format_status(state, verbose))
                       for state in torrent_states])


def status(verbose=True):
    "Get torrent status"
    f = asyncio.Future()
    asyncio.ensure_future(_status(f, verbose))
    _run_in_event_loop_future(f)
    return f.result()


def _stop_server_handler(_: ControlManager):
    raise DaemonExit()


async def _stop():
    async with ControlClient() as client:
        with suppress(DaemonExit):
            await client.execute(_stop_server_handler)


def stop():
    "Stop the daemon"
    _run_in_event_loop(_stop)


def _run_in_event_loop_future(future):
    with closing(asyncio.get_event_loop()) as loop:
        loop.run_until_complete(future)


def _run_in_event_loop(coro_function, *args, **kwargs):
    with closing(asyncio.get_event_loop()) as loop:
        loop.run_until_complete(coro_function(*args, **kwargs))


def start():
    "Starts daemon in a different process, returns process object"
    p = mp.Process(target=run_daemon)
    p.start()
    return p


if __name__ == '__main__':
    start().join()
