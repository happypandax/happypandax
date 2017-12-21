import nacl

from happypanda.common import constants, utils

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


def check_release(archive=True):
    "Check for new release"
    with utils.intertnal_db() as db:
        past_rels = db['past_releases']
