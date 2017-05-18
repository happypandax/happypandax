
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

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)


def get_last(o):
    i = len(o)-1
    if i < 0:
        return None
    return o[i]

class HTML(object):
    '''Easily generate HTML.

    >>> print HTML('html', 'some text')
    <html>some text</html>
    >>> print HTML('html').p('some text')
    <html><p>some text</p></html>

    If a name is not passed in then the instance becomes a container for
    other tags that itself generates no tag:

    >>> h = HTML()
    >>> h.p('text')
    >>> h.p('text')
    print h
    <p>some text</p>
    <p>some text</p>

    '''
    newline_default_on = set('table ol ul dl'.split())

    def __init__(self, name=None, text=None, stack=None, newlines=True,
            escape=True):
        self._name = name
        self._content = []
        self._attrs = {}
        # insert newlines between content?
        if stack is None:
            stack = [self]
            self._top = True
            self._newlines = newlines
        else:
            self._top = False
            self._newlines = name in self.newline_default_on
        self._stack = stack
        if text is not None:
            self.text(text, escape)

    def __getattr__(self, name):
        # adding a new tag or newline
        if name == 'newline':
            e = '\n'
        else:
            e = self.__class__(name, stack=self._stack)
        if self._top:
            self._stack[-1:]._content.append(e)
        else:
            self._content.append(e)
        return e

    def __iadd__(self, other):
        if self._top:
            self._stack[-1:]._content.append(other)
        else:
            self._content.append(other)
        return self

    def text(self, text, escape=True):
        '''Add text to the document. If "escape" is True any characters
        special to HTML will be escaped.
        '''
        if escape:
            text = html_escape(text)
        # adding text
        if self._top:
            self._stack[-1:]._content.append(text)
        else:
            self._content.append(text)

    def raw_text(self, text):
        '''Add raw, unescaped text to the document. This is useful for
        explicitly adding HTML code or entities.
        '''
        return self.text(text, escape=False)

    def __call__(self, *content, **kw):
        if self._name == 'read':
            if len(content) == 1 and isinstance(content[0], int):
                raise TypeError('you appear to be calling read(%d) on '
                    'a HTML instance' % content)
            elif len(content) == 0:
                raise TypeError('you appear to be calling read() on a '
                    'HTML instance')

        # customising a tag with content or attributes
        escape = kw.pop('escape', True)
        if content:
            if escape:
                self._content = list(map(html_escape, content))
            else:
                self._content = content
        if 'newlines' in kw:
            # special-case to allow control over newlines
            self._newlines = kw.pop('newlines')
        for k in kw:
            if k == 'klass':
                self._attrs['class'] = html_escape(kw[k], True)
            else:
                self._attrs[k] = html_escape(kw[k], True)
        return self

    def __enter__(self):
        # we're now adding tags to me!
        self._stack.append(self)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        # we're done adding tags to me!
        self._stack.pop()

    def __repr__(self):
        return '<HTML %s 0x%x>' % (self._name, id(self))

    def _stringify(self, str_type):
        # turn me and my content into text
        join = '\n' if self._newlines else ''
        if self._name is None:
            return join.join(map(str_type, self._content))
        a = ['%s="%s"' % i for i in self._attrs.items()]
        l = [self._name] + a
        s = '<%s>%s' % (' '.join(l), join)
        if self._content:
            s += join.join(map(str_type, self._content))
            s += join + '</%s>' % self._name
        return s

    def __str__(self):
        return self._stringify(str)

    def __unicode__(self):
        return self._stringify(unicode)

    def __iter__(self):
        return iter([str(self)])


class XHTML(HTML):
    '''Easily generate XHTML.
    '''
    empty_elements = set('base meta link hr br param img area input col \
        colgroup basefont isindex frame'.split())

    def _stringify(self, str_type):
        # turn me and my content into text
        # honor empty and non-empty elements
        join = '\n' if self._newlines else ''
        if self._name is None:
            return join.join(map(str_type, self._content))
        a = ['%s="%s"' % i for i in self._attrs.items()]
        l = [self._name] + a
        s = '<%s>%s' % (' '.join(l), join)
        if self._content or not(self._name.lower() in self.empty_elements):
            s += join.join(map(str_type, self._content))
            s += join + '</%s>' % self._name
        else:
            s = '<%s />%s' % (' '.join(l), join)
        return s


class XML(XHTML):
    '''Easily generate XML.

    All tags with no contents are reduced to self-terminating tags.
    '''
    newline_default_on = set()          # no tags are special

    def _stringify(self, str_type):
        # turn me and my content into text
        # honor empty and non-empty elements
        join = '\n' if self._newlines else ''
        if self._name is None:
            return join.join(map(str_type, self._content))
        a = ['%s="%s"' % i for i in self._attrs.items()]
        l = [self._name] + a
        s = '<%s>%s' % (' '.join(l), join)
        if self._content:
            s += join.join(map(str_type, self._content))
            s += join + '</%s>' % self._name
        else:
            s = '<%s />%s' % (' '.join(l), join)
        return s

