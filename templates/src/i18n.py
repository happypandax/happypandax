from src import utils

from src.client import client, log

_translations_d = {}


def add_translation(ctx, data, err):
    _translations_d.setdefault(ctx['locale'], {})
    if not err:
        _translations_d[ctx['locale']][ctx['t_id']] = {'text': data,
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
        curr_locale = utils.storage.get("locale", "unknown")
        if curr_locale:
            t_txt = _translations_d.get(curr_locale, {}).get(t_id)
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
        fargs = {"t_id": t_id, "default": default_txt, "count": count}
        ctx = {'t_id': t_id,
               'placeholder': placeholder,
               'count': count,
               'locale': curr_locale,
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
    return default_txt


__pragma__("noiconv")
__pragma__("notconv")
__pragma__("nokwargs")
