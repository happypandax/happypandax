import nacl
import sys

from contextlib import suppress
from functools import reduce

from happypanda.common import constants, utils, config, exceptions, hlogger
from happypanda.core.commands.networkcmd import SimplePOSTRequest

log = hlogger.Logger(__name__)

class Release:

    def __init__(self):
        self._signed = None

    def sign(self, from_input=False):
        if from_input:
            k = input("Signing key:")
        else:
            raise NotImplemented

        sign_key = nacl.signing.SigningKey(k, encoder=nacl.encoding.HexEncoder)
        #self._signed = sign_key.sign(msg)


def verify_release(msg):
    "Verify a new release"
    for k in (constants.update_public_key['main'],
              constants.update_public_key['backup']):
        if k:
            try:
                vf_key = nacl.signing.VerifyKey(k, encoder=nacl.encoding.HexEncoder)
                vf_key.verify(msg)
                return True
            except nacl.exceptions.BadSignatureError:
                pass
    return False

def generate_key():
    "Generate a key pair"
    sign_key = nacl.signing.SigningKey.generate()
    return dict(private=sign_key.encode(encoder=nacl.encoding.HexEncoder),
                public=sign_key.verify_key.encode(encoder=nacl.encoding.HexEncoder))


extract_version = lambda v: tuple([x for x in (reduce((lambda a,b: a+b),filter(str.isdigit,i)) for i in v.split("."))][:3])

def check_release(archive=True, silent=True):
    """
    Check for new release

    Args:
        silent: suppress any network error

    Returns:
        None or {'url':'', 'changes':'', 'tag':''} for new release
    """
    if config.check_new_releases.value:
        with utils.intertnal_db() as db:
            past_rels = db['past_releases']
        repo_name = config.github_repo.value['repo']
        repo_owner = config.github_repo.value['owner']
        try:
            r = SimpleGETRequest("https://api.github.com/repos/{}/{}/tags".format(repo_owner, repo_name)).run()
            data = r.json
            with utils.intertnal_db() as db:
                tags = [x['name'] for x in data] if data else []
                db['release_tags'] = tags

            new_rel = None
            # go down in releases until a suitable new release or we match local release
            while tags:
                t = tags.pop(0)
                if 'alpha' in t and not config.allow_alpha_releases.value:
                    continue
                elif 'beta' in t and not config.allow_beta_releases.value:
                    continue
                v = extract_version(t)
                if v <= constants.version:
                    break
                else:
                    new_rel = t
            download_url = None
            changes = ""
            if new_rel:
                r = SimpleGETRequest("https://api.github.com/repos/{}/{}/releases/tags/{}".format(repo_owner, repo_name, new_rel)).run()
                data = r.json
                if data:
                    changes = data['body']
                    if sys.platform.startswith('darwin'):
                        txt = "osx"
                    elif os.name == 'nt':
                        txt = "win"
                    elif os.name == 'posix':
                        txt = "linux"
                    for a in data['assets']:
                        if txt in a['name'].lower():
                            download_url = a['browser_download_url']
                            break
            latest_rel = dict(url=download_url,tag=new_rel, changes=changes)
            with utils.intertnal_db() as db:
                db['latest_release'] = latest_rel

            return latest_rel if download_url else None
        except exceptions.NetworkError:
            if not silent:
                raise
            log.exception("Supressed error when checking for new release")

