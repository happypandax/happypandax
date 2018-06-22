import sys
import hashlib
import os
import pathlib
import arrow

from functools import reduce

from happypanda.common import constants, utils, config, exceptions, hlogger
from happypanda.core.commands.network_cmd import SimpleGETRequest, RequestProperties
from happypanda.core.commands.io_cmd import CoreFS

log = hlogger.Logger(constants.log_ns_core + __name__)


def verify_release(checksum, silent=True, cmd=None):
    """
    Verify a new release by checking against a key provider

    Args:
        silent: suppress any network error
    """
    log.d("Checking release checksum", checksum)
    repo_name = config.checksum_provider_repo.value['repo']
    repo_owner = config.checksum_provider_repo.value['owner']
    repo_file = config.checksum_provider_repo.value['file']
    checksum_rel_key = "release_checksums"
    db = constants.internaldb
    rels_checks = db.get(checksum_rel_key, '')
    if checksum in rels_checks:
        return True
    try:
        r = SimpleGETRequest(
            "https://api.github.com/repos/{}/{}/contents/{}".format(repo_owner, repo_name, repo_file)).merge(cmd).run()
        data = r.json
        if data:
            r = SimpleGETRequest(data['download_url']).merge(cmd).run()
            if r.text:
                db[checksum_rel_key] = r.text
                log.d("Matching checksum", checksum)
                return checksum in r.text
    except exceptions.NetworkError:
        if not silent:
            raise
        log.exception("Supressed error when verifying release checksum")
    return False


def sha256_checksum(path, block_size=64 * 1024):
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()


def extract_version(v): return tuple(  # noqa: E704
    [int(x) for x in (reduce((lambda a, b: a + b), filter(str.isdigit, i)) for i in v.split("."))][:3])  # noqa: E704


next_check = None


def check_release(silent=True, cmd=None):
    """
    Check for new release

    Args:
        silent: suppress any network error

    Returns:
        None or {'url':'', 'changes':'', 'tag':'', 'version':(0, 0, 0)} for new release
    """
    global next_check

    if config.check_new_releases.value:
        if constants.dev or next_check and next_check > arrow.now():
            log.d("Skipping release check, still within interval")
            log.d("Checking local")
            latest_rel = constants.internaldb.latest_release.get({})
            if latest_rel and tuple(latest_rel['version']) > constants.version:
                return latest_rel
            return None
        next_check = arrow.now().replace(minutes=+max(config.check_release_interval.value, 5))
        log.d("Checking for new release with interval set to", config.check_release_interval.value, "minutes")
        repo_name = config.github_repo.value['repo']
        repo_owner = config.github_repo.value['owner']
        try:
            r = SimpleGETRequest(
                "https://api.github.com/repos/{}/{}/tags".format(repo_owner, repo_name)).merge(cmd).run()
            data = r.json
            tags = [x['name'] for x in data] if data else []
            constants.internaldb.release_tags.set(tags)

            new_rel = None
            new_version = tuple()
            log.d("Most recent 5 tags:", tags[:5])
            # go down in releases until a suitable new release or we match local release
            while tags:
                t = tags.pop(0)
                log.d("Checking tag:", t)
                if 'alpha' in t and not config.allow_alpha_releases.value:
                    continue
                elif 'beta' in t and not config.allow_beta_releases.value:
                    continue
                v = extract_version(t)
                if len(v) < 2 or v <= constants.version:
                    log.d("Stopping at", t)
                    break
                else:
                    new_rel = t
                    new_version = v
                    break
            download_url = None
            changes = ""
            if new_rel:
                r = SimpleGETRequest(
                    "https://api.github.com/repos/{}/{}/releases/tags/{}".format(repo_owner, repo_name, new_rel)).merge(cmd).run()
                data = r.json
                ignore_words = ['installer']
                if data and 'body' in data and 'assets' in data:
                    changes = data['body']
                    if constants.is_osx:
                        txt = "osx"
                    elif constants.is_win:
                        txt = "win"
                    elif constants.is_linux:
                        txt = "linux"
                    for a in data['assets']:
                        if txt in a['name'].lower() and all([x not in a['name'].lower() for x in ignore_words]):
                            download_url = a['browser_download_url']
                            break

            latest_rel = None
            if download_url:
                latest_rel = dict(url=download_url, tag=new_rel, changes=changes, version=new_version)
                constants.internaldb.latest_release.set(latest_rel)

            return latest_rel
        except exceptions.NetworkError:
            if not silent:
                raise
            log.exception("Supressed error when checking for new release")


def get_release(download_url=None, archive=True, silent=True, cmd=None):
    """
    Download a new release from provided url

    Args:
        download_url: url to the new release, will query for the latest release if not provided
        archive: cache the downloaded file
        silent: suppress any network error

    Returns:
        None or {'path': path to downloaded file, 'hash': ''}

    """
    if download_url:
        log.i("Getting release", download_url, stdout=True)

    down_rels_key = "downloaded_releases"
    db = constants.internaldb

    if not download_url:
        l_rel = db.get(constants.internaldb.latest_release.key, {})
        download_url = l_rel.get('url', False)
        if not download_url or (tuple(l_rel.get('version', tuple())) < constants.version):
            log.d("No new release found in internal db")
            return None

    down_rels = db.get(down_rels_key, {})

    d_file = None
    try:
        if download_url not in down_rels or not os.path.exists(down_rels[download_url]['path']):
            d_file = {}
            if os.path.exists(download_url):  # TODO: if is filepath but not existing, raise appropriate error
                log.i("Getting release from existing file", stdout=True)
                d_file['path'] = download_url
            else:
                log.i("Getting release from web", stdout=True)
                r = SimpleGETRequest(download_url, RequestProperties(stream=True)).merge(cmd).run()
                d_file['path'] = r.save(
                    os.path.join(
                        constants.dir_cache if archive else constants.dir_temp,
                        utils.random_name()),
                    extension=True)
            d_file['hash'] = sha256_checksum(d_file['path'])
            log.i("Computed file checksum", d_file['hash'])
            if not constants.dev and not verify_release(d_file['hash'], silent, cmd=cmd):
                log.w("File checksum mismatch from download url", download_url)
                return None
            down_rels[download_url] = d_file
            if archive:
                log.d("Archiving release file")
                db[down_rels_key] = down_rels
        else:
            d_file = down_rels[download_url]
            log.i("Release file found in archive", stdout=True)
    except exceptions.NetworkError:
        if not silent:
            raise
        log.exception("Supressed error when getting new release")

    return d_file


def register_release(filepath, silent=True, restart=True):
    """
    Register the new release for installation

    Args:
        filepath: also accepts CoreFS
        silent: suppress any error

    Returns:
        bool indicating whether the registration succeded or not
    """

    if not isinstance(filepath, CoreFS):
        filepath = CoreFS(filepath)
    log.d("Registering new release", filepath.path)
    db = constants.internaldb
    try:
        up = CoreFS(constants.dir_update)
        if up.exists:
            log.d("Nuking existing update folder")
            up.delete(ignore_errors=True)
        os.makedirs(up.path, exist_ok=True)  # exists_ok: needed by pytest
        log.d("Extracting new release")
        p = filepath.extract(target=up.path)
        log.d("Saving update info")
        extracted_content = p.path
        app_path = os.path.abspath(constants.app_path)
        if constants.is_osx:  # we're in Contents/MacOS, need to go two dir up
            app_path = pathlib.Path(app_path)
            app_path = os.path.join(*list(app_path.parts)[:-2])

            # also, we only extract contents in the bundle (not the bundle itself)
            extracted_content = os.path.join(extracted_content, constants.osx_bundle_name)

        if constants.dev and not constants.is_frozen:
            app_path = constants.dir_temp

        db[constants.updater_key] = {'from': extracted_content,
                                     'to': app_path,
                                     'restart': restart,
                                     'app': sys.argv[0],
                                     'args': sys.argv[1:],
                                     'state': constants.UpdateState.Registered.value}
        up_name = constants.updater_name
        if constants.is_win:
            up_name += '.exe'
        updater_path = os.path.join(p.path, up_name)
        if os.path.exists(updater_path):
            log.d("Getting new updater file")
            os.replace(updater_path, os.path.join(constants.app_path, up_name))
    except PermissionError:
        log.exception("Failed to register new release")
        return False
    log.d("Finished registering release")
    return True
