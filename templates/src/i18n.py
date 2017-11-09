from src import utils

from src.client import client, log

current_locale = "en_us"

_translations_d = {}


def add_translation(ctx, data, err):
    _translations_d.setdefault(current_locale, {})
    if not err:
        _translations_d[current_locale][ctx['t_id']] = {'text': data, 'extra': ctx['extra']}


def add_translation_component(ctx, data, err):
    add_translation(ctx, data, err)
    if not err:
        ctx['cmp'].forceUpdate()

__pragma__("kwargs")
__pragma__("tconv")
__pragma__("iconv")


def tr(that, t_id, default_txt, placeholder=None, count=None):
    t_txt = _translations_d.get(current_locale, {}).get(t_id)
    # if not t_id:
    #    log("Translation id is None", placeholder, count)
    # if t_txt and not (utils.isEqual(placeholder, t_txt['extra'][0]) and utils.isEqual(count, t_txt['extra'][1])):
    #    t_txt = None

    if t_txt is None:
        fargs = {"t_id": t_id, "locale": current_locale, "default": default_txt, "count": count}
        ctx = {'t_id': t_id,
               'extra': (placeholder, count)}

        if placeholder:
            fargs["placeholder"] = placeholder

        if that:
            ctx["cmp"] = that
            client.call_func("translate", add_translation_component, ctx, **fargs)
        else:
            client.call_func("translate", add_translation, ctx, **fargs)
    else:
        default_txt = t_txt["text"]
    return default_txt

__pragma__("noiconv")
__pragma__("notconv")
__pragma__("nokwargs")
