from src import utils

from src.client import client, log

current_locale = "en_us"

_translations_d = {}


def add_translation(ctx, data, err):
    _translations_d.setdefault(current_locale, {})
    if not err:
        _translations_d[current_locale][ctx['t_id']] = {'text': data,
                                                        'placeholder': ctx['placeholder'],
                                                        'count': ctx['count'],
                                                        }


def add_translation_component(ctx, data, err):
    add_translation(ctx, data, err)
    if not err:
        ctx['cmp'].forceUpdate()

__pragma__("kwargs")
__pragma__("tconv")
__pragma__("iconv")


def tr(that, t_id, default_txt, placeholder=None, count=None):
    t_txt = None
    if t_id:
        t_txt = _translations_d.get(current_locale, {}).get(t_id)

    if t_id and t_txt and (placeholder is not None or count is not None):
        same = True
        if t_txt['count'] != count:
            same = False
        p_p = t_txt['placeholder']
        if p_p and placeholder:
            if len(p_p) != len(placeholder):
                same = False
            if same:
                for p in placeholder:
                    if not p in p_p:
                        same = False
                        break
                    if p_p[p] != placeholder[p]:
                        same = False
                        break

        elif txt['placeholder'] != placeholder:
            same = False

        if not same:
            t_txt = None

    if t_txt is None and t_id:
        fargs = {"t_id": t_id, "locale": current_locale, "default": default_txt, "count": count}
        ctx = {'t_id': t_id,
               'placeholder': placeholder,
               'count': count,
               }

        if placeholder:
            fargs["placeholder"] = placeholder

        if that:
            ctx["cmp"] = that
            client.call_func("translate", add_translation_component, ctx, **fargs)
        else:
            client.call_func("translate", add_translation, ctx, **fargs)
    elif t_txt:
        default_txt = t_txt["text"]
    log("{}:{}".format(t_id, default_txt))
    return default_txt

__pragma__("noiconv")
__pragma__("notconv")
__pragma__("nokwargs")
