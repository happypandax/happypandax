"""
.Search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autodata:: happypanda.core.commands.search_cmd.Term
    :annotation: = NamedTuple

"""
import typing

from collections import namedtuple, ChainMap

from happypanda.common import hlogger, exceptions, utils, constants, config
from happypanda.core.command import Command, CommandEvent, CommandEntry, CParam
from happypanda.core.commands import database_cmd
from happypanda.core import db


log = hlogger.Logger(constants.log_ns_search + __name__)


def _get_search_options():
    return {
        config.search_option_all: 'all',
        config.search_option_case: 'case',
        config.search_option_desc: 'desc',
        config.search_option_regex: 'regex',
        config.search_option_whole: 'whole',
    }


def get_search_options(options={}):
    d_val = {}
    u_val = {}
    opt = _get_search_options()
    if isinstance(options, ChainMap):
        options = options.maps[0]
    for o in opt:
        d_val[opt[o]] = o.value
        if o.name in options:
            u_val[opt[o]] = options[o.name]
        elif opt[o] in options:
            u_val[opt[o]] = options[opt[o]]

    return ChainMap(u_val, d_val)


#: used to encapsulate a single term, e.g:
#: ``pages::>5`` where ``pages`` is the namespace,
#: ``>`` is the operator and ``5`` is the tag
Term = namedtuple("Term", ["namespace", "tag", "operator"])


class ParseTerm(Command):
    """
    Parse a single term

    By default, the following operators are parsed for:
    - '' to ''
    - '<' to 'less'
    - '>' to 'great'

    Args:
        term: a single term

    Returns:
        a namedtuple of namespace, tag and operator
    """

    parse: tuple = CommandEntry("parse",
                                CParam('term', str, "a single term"),
                                __doc="""
                                Called to parse the term into ``namespace``, ``tag`` and ``operator``
                                """,
                                __doc_return="""
                                a tuple of strings (namespace, tag, operator)
                                """)

    parsed = CommandEvent("parsed",
                          CParam('term', Term, "the parsed term"),
                          __doc="""
                          Emitted after a term has been parsed
                          """)

    def __init__(self):
        super().__init__()
        self.filter = ''
        self.term = None

    @parse.default()
    def _parse_term(term):
        s = term.split(':', 1)
        ns = s[0] if len(s) == 2 else ''
        tag = s[1] if len(s) == 2 else term
        operator = ''

        if tag.startswith('<'):
            operator = 'less'
        elif tag.startswith('>'):
            operator = 'great'
        return (ns, tag, operator)

    def main(self, term: str) -> Term:

        self.filter = term

        with self.parse.call(self.filter) as plg:
            t = plg.first_or_default()
            if not len(t) == 3:
                t = plg.default()
            self.term = Term(*t)

        self.parsed.emit(self.term)

        return self.term


class ParseSearch(Command):
    """
    Parse a search query.

    Dividies term into ns:tag pieces

    Args:
        search_filter: a search query

    Returns:
        a tuple of ns:tag pieces
    """

    parse: tuple = CommandEntry("parse",
                                CParam('terms', str, "a search query"),
                                __doc="""
                                Called to divide the search query as written into ``namespace:tag``(``str``) pieces
                                """,
                                __doc_return="""
                                a tuple of `namespace:tag``(``str``) pieces
                                """)

    parsed = CommandEvent("parsed",
                          CParam('pieces', tuple, "a tuple of `namespace:tag``(``str``) pieces"),
                          __doc="""
                          Emitted after the search query has been parsed
                          """)

    def __init__(self):
        super().__init__()
        self.filter = ''
        self.pieces = tuple()

    @parse.default()
    def _get_terms(term):

        # some variables we will use
        pieces = []
        piece = ''
        qoute_level = 0
        bracket_level = 0
        brackets_tags = {}
        current_bracket_ns = ''
        end_of_bracket = False
        blacklist = ['[', ']', '"', ',']

        for n, x in enumerate(term):
            # if we meet brackets
            if x == '[':
                bracket_level += 1
                brackets_tags[piece] = set()  # we want unique tags!
                current_bracket_ns = piece
            elif x == ']':
                bracket_level -= 1
                end_of_bracket = True

            # if we meet a double qoute
            if x == '"':
                if qoute_level > 0:
                    qoute_level -= 1
                else:
                    qoute_level += 1

            # if we meet a whitespace, comma or end of term and are not in a
            # double qoute
            if (x == ' ' or x == ',' or n == len(term) - 1) and qoute_level == 0:
                # if end of term and x is allowed
                if (n == len(term) - 1) and x not in blacklist and x != ' ':
                    piece += x
                if piece:
                    if bracket_level > 0 or end_of_bracket:  # if we are inside a bracket we put piece in the set
                        end_of_bracket = False
                        if piece.startswith(current_bracket_ns):
                            piece = piece[len(current_bracket_ns):]
                        if piece:
                            try:
                                brackets_tags[current_bracket_ns].add(piece)
                            except KeyError:  # keyerror when there is a closing bracket without a starting bracket
                                pass
                    else:
                        pieces.append(piece)  # else put it in the normal list
                piece = ''
                continue

            # else append to the buffers
            if x not in blacklist:
                if qoute_level > 0:  # we want to include everything if in double qoute
                    piece += x
                elif x != ' ':
                    piece += x

        # now for the bracket tags
        for ns in brackets_tags:
            for tag in brackets_tags[ns]:
                ns_tag = ns
                # if they want to exlucde this tag
                if tag[0] == '-':
                    if ns_tag[0] != '-':
                        ns_tag = '-' + ns
                    tag = tag[1:]  # remove the '-'

                # put them together
                ns_tag += tag

                # done
                pieces.append(ns_tag)

        return tuple(pieces)

    def main(self, search_filter: str) -> tuple:

        self.filter = search_filter

        pieces = set()

        with self.parse.call(search_filter) as plg:
            for p in plg.all(default=True):
                for x in p:
                    pieces.add(x)
        self.pieces = tuple(pieces)

        self.parsed.emit(self.pieces)

        return self.pieces


class PartialModelFilter(Command):
    """
    Perform a partial search on database model with a single term

    Accepts any term

    By default, the following models are supported:

    - User
    - NamespaceTags
    - Tag
    - Namespace
    - Artist
    - Circle
    - Parody
    - Status
    - Grouping
    - Language
    - Category
    - Collection
    - Gallery
    - Title
    - Url

    Args:
        model: a database model item
        term: a single term, like ``rating:5``
        match_options: search options, refer to :ref:`Settings`

    Returns:
        a ``set`` with ids of matched database model items
    """

    models: tuple = CommandEntry("models",
                                 __doc="""
                                 Called to get a tuple of supported database models
                                 """,
                                 __doc_return="""
                                 a tuple of database model items
                                 """)

    match_model: set = CommandEntry("match_model",
                                    CParam("parent_model_name", str, "name of parent database model"),
                                    CParam("child_model_name", str, "name of child database model"),
                                    CParam("term", str, "a single term"),
                                    CParam("options", ChainMap, "search options"),
                                    __capture=(str, "a database model name"),
                                    __doc="""
                                  Called to perform the matching on database items of the given model
                                  """,
                                    __doc_return="""
                                  a ``set`` of ids of the database items that match
                                  """)
    matched = CommandEvent("matched",
                           CParam("matched_ids", set, "a ``set`` of ids of the database items that match"),
                           __doc="""
                           Emitted at the end of the process
                           """
                           )

    def main(self, model: db.Base, term: str, match_options: dict = {}) -> typing.Set[int]:

        self.model = model
        model_name = db.model_name(self.model)
        self.term = term
        with self.models.call() as plg:
            for p in plg.all(default=True):
                self._supported_models.update(p)

        if self.model not in self._supported_models:
            raise exceptions.CommandError(utils.this_command(self),
                                          "Model '{}' is not supported".format(model))

        options = get_search_options(match_options)
        log.d("Match options", options)

        related_models = db.related_classes(model)

        sess = constants.db_session()

        model_count = sess.query(model).count()

        with self.match_model.call_capture(model_name, model_name, model_name, self.term, options) as plg:
            for i in plg.all_or_default():
                self.matched_ids.update(i)
                if len(self.matched_ids) == model_count:
                    break

        has_all = False
        for m in related_models:
            if m in self._supported_models:
                with self.match_model.call_capture(db.model_name(m), model_name, db.model_name(m), self.term, options) as plg:
                    for i in plg.all_or_default():
                        self.matched_ids.update(i)
                        if len(self.matched_ids) == model_count:
                            has_all = True
                            break
            if has_all:
                break

        self.matched.emit(self.matched_ids)

        return self.matched_ids

    def __init__(self):
        super().__init__()
        self.model = None
        self.term = ''
        self._supported_models = set()
        self.matched_ids = set()

    @models.default()
    def _models():
        return (db.Taggable,
                db.Artist,
                db.Circle,
                db.Parody,
                db.Status,
                db.Grouping,
                db.Language,
                db.Category,
                db.Collection,
                db.Gallery,
                db.Title,
                db.Namespace,
                db.Tag,
                db.NamespaceTags,
                db.Url)

    @staticmethod
    def _match_string_column(column, value, options, **kwargs):

        options.update(kwargs)

        expr = None

        if options.get("regex"):
            if options.get("case"):
                expr = column.regexp
            else:
                expr = column.iregexp
        else:
            if not options.get("whole"):
                value = '%' + value + '%'
            if options.get("case"):
                expr = column.like
            else:
                expr = column.ilike

        return expr(value)

    @staticmethod
    def _match_integer_column(column, value, options, **kwargs):

        options.update(kwargs)

        return None

    @match_model.default(capture=True)
    def _match_gallery(parent_model, child_model, term,
                       options, capture=db.model_name(db.Gallery)):
        get_model = database_cmd.GetModelClass()
        parent_model = get_model.run(parent_model)
        child_model = get_model.run(child_model)

        match_string = PartialModelFilter._match_string_column
        match_int = PartialModelFilter._match_integer_column
        term = ParseTerm().run(term)
        ids = set()

        col_on_parent = db.relationship_column(parent_model, child_model)
        s = constants.db_session()
        q = s.query(parent_model.id)
        if col_on_parent:
            q = q.join(col_on_parent)
        if term.namespace:
            lower_ns = term.namespace.lower()
            if lower_ns == 'path':
                ids.update(x[0] for x in q.filter(match_string(db.Gallery.path,
                                                               term.tag,
                                                               options)).all())
            elif lower_ns in ("rating", "stars"):
                ids.update(x[0] for x in q.filter(match_int(db.Gallery.rating,
                                                            term.tag,
                                                            options)).all())

        return ids

    @match_model.default(capture=True)
    def _match_title(parent_model, child_model, term, options,
                     capture=db.model_name(db.Title)):
        get_model = database_cmd.GetModelClass()
        parent_model = get_model.run(parent_model)
        child_model = get_model.run(child_model)

        match_string = PartialModelFilter._match_string_column
        term = ParseTerm().run(term)
        ids = set()

        if term.namespace.lower() == 'title' or not term.namespace:

            col_on_parent = db.relationship_column(parent_model, child_model)

            s = constants.db_session()
            q = s.query(parent_model.id)
            if col_on_parent:
                q = q.join(col_on_parent)
            ids.update(x[0] for x in q.filter(match_string(child_model.name, term.tag, options)).all())
        return ids

    @match_model.default(capture=True)
    def _match_tags(parent_model, child_model, term, options,
                    capture=[db.model_name(x) for x in (db.Taggable, db.NamespaceTags)]):
        get_model = database_cmd.GetModelClass()
        parent_model = get_model.run(parent_model)
        child_model = get_model.run(child_model)

        match_string = PartialModelFilter._match_string_column
        term = ParseTerm().run(term)
        ids = set()

        col_on_parent = db.relationship_column(parent_model, child_model)
        col_on_child = db.relationship_column(child_model, db.NamespaceTags)
        col_tag = db.relationship_column(db.NamespaceTags, db.Tag)
        s = constants.db_session()
        q = s.query(parent_model.id)
        if col_on_parent and parent_model != child_model:
            q = q.join(col_on_parent)
        if col_on_child and parent_model != child_model:
            q = q.join(col_on_child)
        if term.namespace:
            col_ns = db.relationship_column(db.NamespaceTags, db.Namespace)
            items = q.join(col_ns).join(col_tag).filter(db.and_op(
                match_string(db.Namespace.name, term.namespace, options, whole=True),
                match_string(db.Tag.name, term.tag, options))).all()
        else:
            items = q.join(col_tag).filter(
                match_string(db.Tag.name, term.tag, options)).all()

        ids.update(x[0] for x in items)
        return ids

    @match_model.default(capture=True)
    def _match_artist(parent_model, child_model, term, options,
                      capture=db.model_name(db.Artist)):
        get_model = database_cmd.GetModelClass()
        parent_model = get_model.run(parent_model)
        child_model = get_model.run(child_model)

        match_string = PartialModelFilter._match_string_column
        term = ParseTerm().run(term)
        ids = set()

        if term.namespace.lower() == 'artist' or not term.namespace:
            col_on_parent = db.relationship_column(parent_model, child_model)

            s = constants.db_session()
            q = s.query(parent_model.id)
            if col_on_parent:
                q = q.join(col_on_parent)
            ids.update(
                x[0] for x in q.join(
                    child_model.names).filter(
                    match_string(
                        db.ArtistName.name,
                        term.tag,
                        options)).all())
        return ids

    @match_model.default(capture=True)
    def _match_parody(parent_model, child_model, term, options,
                      capture=db.model_name(db.Parody)):
        get_model = database_cmd.GetModelClass()
        parent_model = get_model.run(parent_model)
        child_model = get_model.run(child_model)

        match_string = PartialModelFilter._match_string_column
        term = ParseTerm().run(term)
        ids = set()

        if term.namespace.lower() == 'parody' or not term.namespace:
            col_on_parent = db.relationship_column(parent_model, child_model)

            s = constants.db_session()
            q = s.query(parent_model.id)
            if col_on_parent:
                q = q.join(col_on_parent)
            ids.update(
                x[0] for x in q.join(
                    child_model.names).filter(
                    match_string(
                        db.ParodyName.name,
                        term.tag,
                        options)).all())
        return ids

    @match_model.default(capture=True)
    def _match_namemixin(parent_model, child_model, term, options,
                         capture=[db.model_name(x) for x in _models() if issubclass(x, (db.NameMixin, db.Url))]):
        get_model = database_cmd.GetModelClass()
        parent_model = get_model.run(parent_model)
        child_model = get_model.run(child_model)
        match_string = PartialModelFilter._match_string_column
        term = ParseTerm().run(term)
        ids = set()

        if term.namespace.lower() == child_model.__name__.lower() or not term.namespace:
            col_on_parent = db.relationship_column(parent_model, child_model)
            s = constants.db_session()
            q = s.query(parent_model.id)
            if col_on_parent:
                q = q.join(col_on_parent)
            ids.update(x[0] for x in q.filter(match_string(child_model.name,
                                                           term.tag,
                                                           options)).all())
        return ids


class ModelFilter(Command):
    """
    Perform a full search on database model

    Args:
        model: a database model item
        search_filter: a search query
        match_options: search options, refer to :ref:`Settings`

    Returns:
        a set of ids of matched database model items
    """

    separate: tuple = CommandEntry("separate",
                                   CParam("pieces", tuple, "a tuple of terms"),
                                   __doc="""
                                   Called to separate terms that include and terms that exclude from eachother
                                   """,
                                   __doc_return="""
                                   a tuple of two tuples where the first tuple contains terms that include
                                   and the second contains terms that exclude
                                   """
                                   )
    include: set = CommandEntry("include",
                                CParam("model_name", str, "name of a database model"),
                                CParam("pieces", set, "a set of terms"),
                                CParam("options", ChainMap, "search options"),
                                __doc="""
                                Called to match database items of the given model to include in the final results
                                """,
                                __doc_return="""
                                a ``set`` of ids of the database items that match
                                """
                                )
    exclude: set = CommandEntry("exclude",
                                CParam("model_name", str, "name of a database model"),
                                CParam("pieces", set, "a set of terms"),
                                CParam("options", ChainMap, "search options"),
                                __doc="""
                                Called to match database items of the given model to exclude in the final results
                                """,
                                __doc_return="""
                                a ``set`` of ids of the database items that match
                                """
                                )
    empty: set = CommandEntry("empty",
                              CParam("model_name", str, "name of a database model"),
                              __doc="""
                                Called when the search query is empty
                                """,
                              __doc_return="""
                                a ``set`` of ids of the database items that match when a search query is empty
                                """)

    included = CommandEvent("included",
                            CParam("model_name", str, "name of a database model"),
                            CParam("matched_ids", set, "a ``set`` of ids of the database items that match for inclusion"),
                            __doc="""
                            Emitted after the match
                            """)

    excluded = CommandEvent("excluded",
                            CParam("model_name", str, "name of a database model"),
                            CParam("matched_ids", set, "a ``set`` of ids of the database items that match for exclusion"),
                            __doc="""
                            Emitted after the match
                            """)

    matched = CommandEvent("matched",
                           CParam("model_name", str, "name of a database model"),
                           CParam("matched_ids", set, "a ``set`` of ids of the database items that match"),
                           __doc="""
                            Emitted at the end of the process with the final results
                            """)

    def main(self, model: db.Base, search_filter: str, match_options: dict = {}) -> typing.Set[int]:
        assert issubclass(model, db.Base)

        self._model = model
        model_name = db.model_name(self._model)

        if search_filter:

            self.parsesearchfilter = ParseSearch()

            pieces = self.parsesearchfilter.run(search_filter)

            options = get_search_options(match_options)

            include = set()
            exclude = set()

            with self.separate.call(pieces) as plg:

                for p in plg.all(True):
                    if len(p) == 2:
                        include.update(p[0])
                        exclude.update(p[1])

            if options.get("all"):
                for n, p in enumerate(include):
                    with self.include.call(model_name, {p}, options) as plg:
                        for i in plg.all_or_default():
                            if n != 0:
                                self.included_ids.intersection_update(i)
                            else:
                                self.included_ids.update(i)
            else:
                with self.include.call(model_name, include, options) as plg:

                    for n, i in enumerate(plg.all_or_default()):
                        self.included_ids.update(i)

            self.included.emit(model_name, self.included_ids)

            with self.exclude.call(model_name, exclude, options) as plg:

                for i in plg.all_or_default():
                    self.excluded_ids.update(i)

            self.excluded.emit(self._model.__name__, self.excluded_ids)

            self.matched_ids = self.included_ids
            self.matched_ids.difference_update(self.excluded_ids)

        else:

            with self.empty.call(model_name) as plg:
                for i in plg.all_or_default():
                    self.matched_ids.update(i)

        self.matched.emit(self._model.__name__, self.matched_ids)

        return self.matched_ids

    def __init__(self):
        super().__init__()
        self._model = None
        self.parsesearchfilter = None
        self.included_ids = set()
        self.excluded_ids = set()
        self.matched_ids = set()

    @separate.default()
    def _separate(pecies):

        include = []
        exclude = []

        for p in pecies:
            if p.startswith('-'):
                exclude.append(p[1:])  # remove '-' at the start
            else:
                include.append(p)

        return tuple(include), tuple(exclude)

    @staticmethod
    def _match(model_name, pieces, options):
        ""
        model = database_cmd.GetModelClass().run(model_name)
        partialfilter = PartialModelFilter()
        matched = set()

        for p in pieces:
            m = partialfilter.run(model, p, options)
            matched.update(m)

        return matched

    @include.default()
    def _include(model_name, pieces, options):
        return ModelFilter._match(model_name, pieces, options)

    @exclude.default()
    def _exclude(model_name, pieces, options):
        return ModelFilter._match(model_name, pieces, options)

    @empty.default()
    def _empty(model_name):
        model = database_cmd.GetModelClass().run(model_name)
        s = constants.db_session()
        return set(x[0] for x in s.query(model.id).all())
