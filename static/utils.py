query_string = require("query-string")
moment = require("moment")

syntax_highlight = __pragma__('js', '{}',
                              """
    function syntax_highlight(json) {
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
            var cls = 'json-number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'json-key';
                } else {
                    cls = 'json-string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'json-boolean';
            } else if (/null/.test(match)) {
                cls = 'json-null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
    }""")

poll_func = __pragma__('js', '{}',
                       """
    function poll_func(fn, timeout, interval) {
    var startTime = (new Date()).getTime();
    interval = interval || 1000;
    var canPoll = true;

    (function p() {
        canPoll = ((new Date).getTime() - startTime ) <= timeout;
        if (!fn() && canPoll)  { // ensures the function exucutes
            setTimeout(p, interval);
        }
    })();
    }""")

poll_func_stagger = __pragma__('js', '{}',
                       """
    function poll_func(fn, timeout, interval) {
    var startTime = (new Date()).getTime();
    interval = interval || 1000;
    var canPoll = true;

    (function p() {
        canPoll = ((new Date).getTime() - startTime ) <= timeout;
        interval = fn()
        if (interval && canPoll)  { // ensures the function exucutes
            setTimeout(p, interval);
        }
    })();
    }""")

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}


def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c, c) for c in text)

defined = __pragma__('js', '{}',
                       """
    function defined(v) {
        return !(v === undefined);
    }""")

def get_locale():
    return window.navigator.userLanguage or window.navigator.language

def query_to_string(obj):
    return query_string.stringify(obj)

__pragma__("kwargs")
def query_to_obj(query=None, location_obj=None):
    if not query:
        l = location_obj or location
        query = l.search
    return query_string.parse(query)
__pragma__("nokwargs")

__pragma__("kwargs")
__pragma__("iconv")
def get_query(key, default=None, query=None, location_obj=None):
    q = {}
    q.update(query_to_obj(query, location_obj=location_obj))
    if key in q:
        return q[key]
    return default
__pragma__("noiconv")
__pragma__("nokwargs")

__pragma__("kwargs")
__pragma__("tconv")
def go_to(history_obj, url="", query={}, state=None, push=True, keep_query=True, location_obj=None):
    if not url:
        l = location_obj or location
        url = l.pathname
    q = {}
    if keep_query:
        q.update(query_to_obj())
    q.update(query)

    if q:
        url += "?" + query_to_string(q, location_obj=location_obj)
    if push:
        history_obj.push(url, state)
    else:
        history_obj.js_replace(url, state)
__pragma__("notconv")
__pragma__("nokwargs")

__pragma__("kwargs")
__pragma__("tconv")
def build_url(url="", query={}, keep_query=True, location_obj=None):
    if not url:
        l = location_obj or location
        url = l.pathname
    q = {}
    if keep_query:
        q.update(query_to_obj())
    q.update(query)

    if q:
        url += "?" + query_to_string(q, location_obj=location_obj)
    return url
__pragma__("notconv")
__pragma__("nokwargs")

moment.locale(get_locale())

