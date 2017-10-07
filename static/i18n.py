from client import client

current_locale = "en_us"

_translations_d = {}

def add_translation(t_id, data, err):
    _translations_d.setdefault(current_locale, {})
    if not err:
        _translations_d[current_locale][t_id] = data

def add_translation_component(ctx, data, err):
    add_translation(ctx['t_id'], data, err)
    if not err:
        ctx['cmp'].forceUpdate()

def tr(that, t_id, default_txt):
    if t_id:
        t_txt = _translations_d.get(current_locale, {}).get(t_id)
        if t_txt is None:
            fargs = {"t_id":t_id, "locale":current_locale, "default":default_txt}
            if that:
                client.call_func("translate", add_translation_component, {'cmp':that, 't_id':t_id}, **fargs)
            else:
                client.call_func("translate", add_translation, t_id, **fargs)
        else:
            default_txt = t_txt
    return default_txt
