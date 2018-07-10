from src import utils

from src.state import state
from src.client import client

from org.transcrypt.stubs.browser import __pragma__

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
__pragma__('noskip')

_translations_d = {}
_translations_load_state = {}


def add_translation(ctx, data, err):
    _translations_load_state[ctx['hash_id']] = False
    if not err:
        _translations_d[ctx['hash_id']] = {'text': data,
                                           'placeholder': ctx['placeholder'],
                                           'count': ctx['count'],
                                           }
    elif not state.translation_id_error:
        _translations_d[ctx['hash_id']] = {}


def add_translation_component(ctx, data, err):
    add_translation(ctx, data, err)
    if not err and ctx['cmp'] and ctx['cmp'].mounted:
        ctx['cmp'].forceUpdate()


__pragma__("kwargs")
__pragma__("tconv")
__pragma__("iconv")


def tr(that, t_id, default_txt, placeholder=None, count=None):
    if state.untranslated_text:
        default_txt = "<UT>" + default_txt + "</UT>"
    if placeholder is None and count is None and state.translations is None:
        return default_txt
    elif placeholder is None and count is None and state.translations is not None:
        if state.translations[t_id]:
            return state.translations[t_id]
    t_txt = None
    curr_locale = utils.storage.get("locale", "unknown")
    ctx = {'t_id': t_id,
           'placeholder': placeholder,
           'count': count,
           'locale': curr_locale,
           }
    ctx['hash_id'] = utils.stringify(ctx)

    if t_id and curr_locale:
        t_txt = _translations_d.get(ctx['hash_id'])

    if t_txt is None and t_id:
        if _translations_load_state[ctx['hash_id']]:
            return default_txt
        _translations_load_state[ctx['hash_id']] = True
        fargs = {"t_id": t_id, "count": count}

        if not state.translation_id_error:
            fargs["default"] = default_txt

        if placeholder:
            fargs["placeholder"] = placeholder

        if that:
            ctx["cmp"] = that
            client.call_func("translate", add_translation_component, ctx, **fargs)
        else:
            client.call_func("translate", add_translation, ctx, **fargs)
    elif t_txt:
        default_txt = t_txt["text"]
    return default_txt


__pragma__("noiconv")
__pragma__("notconv")
__pragma__("nokwargs")
