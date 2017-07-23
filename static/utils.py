__pragma__('alias', 'S', '$')  # JQuery

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


def get_locale():
    return window.navigator.userLanguage or window.navigator.language


class Grid:
    __pragma__('kwargs')

    def __init__(self, container_el, child_el, **kwargs):
        self._grid = S(container_el)
        self._options = {
            'itemSelector': child_el,
        }
        self._options.update(kwargs)
        self._grid.packery(self._options)
    __pragma__('nokwargs')

    def reload(self):
        "Reload all items in node"
        self._grid.packery('reloadItems')

    def layout(self):
        self._grid.packery()

    def append(self, items):
        self._grid.packery("appended", items)

    def add(self, items):
        self._grid.packery("addItems", items)


class URLManipulator:

    __pragma__('kwargs')

    def __init__(self, url=None):
        if url:
            self.uri = URI(url)
        else:
            self.uri = URI()
    __pragma__('nokwargs')

    def path(self):
        return self.uri.pathname()

    def go(self, url):
        "Add state to History"
        history.pushState(null, null, url)
