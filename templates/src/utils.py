from org.transcrypt.stubs.browser import __pragma__
__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = localStorage = sessionStorage = None
Date = None
__pragma__('noskip')

query_string = require("query-string")
marked = require("marked")
moment = require("moment")
isEqual = require('lodash/isEqual')
stringify = require('json-stable-stringify')

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


random_string = __pragma__('js', '{}',
                           """
    function random_string(length) {
    var text = "";
    var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for(var i = 0; i < length; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
    }""")

interval_func = __pragma__('js', '{}',
                           """
    function interval_func(fn, interval) {
        function f() {
            fn();
            return setTimeout(f, interval);
        }
        return f();
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

storage_available = __pragma__('js', '{}',
                               """
function storageAvailable(type) {
    try {
        var storage = window[type],
            x = '__storage_test__';
        storage.setItem(x, x);
        storage.removeItem(x);
        return true;
    }
    catch(e) {
        return e instanceof DOMException && (
            // everything except Firefox
            e.code === 22 ||
            // Firefox
            e.code === 1014 ||
            // test name field too, because code might not be present
            // everything except Firefox
            e.name === 'QuotaExceededError' ||
            // Firefox
            e.name === 'NS_ERROR_DOM_QUOTA_REACHED') &&
            // acknowledge QuotaExceededError only if there's something already stored
            storage.length !== 0;
    }
}
                               """)

visibility_keys = __pragma__('js', '{}',
                             """
    function visibility_keys() {
    var hidden, visibilityChange;

    if (typeof document.hidden !== "undefined") { // Opera 12.10 and Firefox 18 and later support
      hidden = "hidden";
      visibilityChange = "visibilitychange";
    } else if (typeof document.msHidden !== "undefined") {
      hidden = "msHidden";
      visibilityChange = "msvisibilitychange";
    } else if (typeof document.webkitHidden !== "undefined") {
      hidden = "webkitHidden";
      visibilityChange = "webkitvisibilitychange";
    }

    return {'hidden':hidden, 'visibilitychange':visibilityChange};
    }
                               """)


defined = __pragma__('js', '{}',
                     """
    function defined(v) {
        return !(v === undefined);
    }""")

remove_key = __pragma__('js', '{}',
                        """
    function remove_key(o, k) {
        delete o[k];
        return o;
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


def scroll_to_element(el):
    if el:
        el.scrollIntoView({'behavior': 'smooth'})


def is_same_machine():
    return document.getElementById('root').dataset.machine == "True"


def get_version():
    return document.getElementById('root').dataset.version


moment.locale(get_locale())


class Storage:

    __pragma__("kwargs")

    def __init__(self, storage_type="localStorage"):
        self.dummy = {}
        self.enabled = storage_available(storage_type)
        if storage_type == "localStorage":
            self.lstorage = localStorage
        else:
            self.lstorage = sessionStorage

    def get(self, key, default=None, local=False):
        if self.enabled and not local:
            r = self.lstorage.getItem(key)
            if r is None and default is not None:
                r = default
            elif r == "undefined":
                r = None
            elif r:
                r = JSON.parse(r)  # can't handle empty strings
            else:
                r = None  # raise KeyError?
        else:
            r = self.dummy.get(key, default)
        return r

    def set(self, key, value, local=False):
        if self.enabled and not local:
            if value == js_undefined:  # convert undefined to null
                value = None
            self.lstorage.setItem(key, JSON.stringify(value))
        else:
            self.dummy[key] = value

    def clear(self, local=False):
        if self.enabled:
            self.lstorage.js_clear()
        if local:
            self.dummy.clear()

    def remove(self, key, local=False):
        if self.enabled and not local:
            self.lstorage.removeItem(key)
        else:
            self.dummy.pop(key, True)
    __pragma__("nokwargs")


storage = Storage()
session_storage = Storage("sessionStorage")

__pragma__("kwargs")


def either(a, b=None):
    if a == None:  # noqa: E711
        return b
    return a


__pragma__("nokwargs")


def JSONCopy(obj):
    return JSON.parse(JSON.stringify(obj))
