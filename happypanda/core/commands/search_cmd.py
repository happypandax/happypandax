from collections import namedtuple

from happypanda.common import hlogger, exceptions, utils, constants, config
from happypanda.core.command import Command, CommandEvent, CommandEntry
from happypanda.core.commands import database_cmd
from happypanda.core import db


log = hlogger.Logger(__name__)


def get_search_options():
    return {
        "case": config.search_option_case.value,
        "regex": config.search_option_regex.value,
        "whole": config.search_option_whole.value,
        "all": config.search_option_all.value,
        "desc": config.search_option_desc.value
    }

Term = namedtuple("Term", ["namespace", "tag", "operator"])


class ParseTerm(Command):
    """
    Parse a single term

    By default, the following operators are parsed for:
    - '' = ''
    - '<' = 'less'
    - '>' = 'great'

    Returns a namedtuple of strings: Term(namespace, tag, operator)
    """

    parse = CommandEntry("parse", tuple, str)
    parsed = CommandEvent("parsed", Term)

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
            t = plg.first()
            if not len(t) == 3:
                t = plg.default()

            self.term = Term(*t)

        self.parsed.emit(self.term)

        return self.term


class ParseSearch(Command):
    """
    Parse a search query

    Dividies term into ns:tag pieces, returns a tuple of ns:tag pieces
    """

    parse = CommandEntry("parse", tuple, str)
    parsed = CommandEvent("parsed", tuple)

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
    - Status
    - Grouping
    - Language
    - Category
    - Collection
    - Gallery
    - Title
    - GalleryUrl

    Returns a set with ids of matched model items
    """

    models = CommandEntry("models", tuple)

    match_model = CommandEntry("match_model", set, str, str, str, dict)
    matched = CommandEvent("matched", set)

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
                db.Status,
                db.Grouping,
                db.Language,
                db.Category,
                db.Collection,
                db.Gallery,
                db.Title,
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
    def _match_integer_column(session, parent_model, column, term, options, **kwargs):

        options.update(kwargs)

        return []

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

        s = constants.db_session()

        if term.namespace:
            lower_ns = term.namespace.lower()
            if lower_ns == 'path':
                ids.update(x[0] for x in s.query(parent_model.id).filter(match_string(db.Gallery.path,
                                                                                      term.tag,
                                                                                      options)).all())
            elif lower_ns in ("rating", "stars"):
                ids.update(x[0] for x in s.query(parent_model.id).filter(match_int(db.Gallery.rating,
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
            ids.update(x[0] for x in s.query(parent_model.id).
                       join(col_on_parent).
                       filter(match_string(child_model.name, term.tag, options)).all())
        return ids

    @match_model.default(capture=True)
    def _match_tags(parent_model, child_model, term, options,
                    capture=db.model_name(db.Taggable)):
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
        if term.namespace:
            col_ns = db.relationship_column(db.NamespaceTags, db.Namespace)
            items = q.join(col_on_parent).join(col_on_child).join(col_ns).join(col_tag).filter(db.and_op(
                match_string(db.Namespace.name, term.namespace, options, whole=True),
                match_string(db.Tag.name, term.tag, options))).all()
        else:
            items = q.join(col_on_parent).join(col_on_child).join(col_tag).filter(
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
            print()
            col_on_parent = db.relationship_column(parent_model, child_model)
            s = constants.db_session()
            ids.update(x[0] for x in s.query(parent_model.id).
                       join(col_on_parent).
                       join(child_model.names).
                       filter(match_string(db.AliasName.name, term.tag, options)).all())
        return ids

    @match_model.default(capture=True)
    def _match_namemixin(parent_model, child_model, term, options,
                         capture=[db.model_name(x) for x in _models() if issubclass(x, db.NameMixin)]):
        get_model = database_cmd.GetModelClass()
        parent_model = get_model.run(parent_model)
        child_model = get_model.run(child_model)
        match_string = PartialModelFilter._match_string_column
        term = ParseTerm().run(term)
        ids = set()

        if term.namespace.lower() == child_model.__name__.lower() or not term.namespace:
            col_on_parent = db.relationship_column(parent_model, child_model)
            s = constants.db_session()
            ids.update(x[0] for x in s.query(parent_model.id).join(col_on_parent).filter(match_string(child_model.name,
                                                                                                      term.tag,
                                                                                                      options)).all())
        return ids

    def main(self, model: db.Base, term: str) -> set:

        self.model = model
        model_name = db.model_name(self.model)
        self.term = term

        with self.models.call() as plg:
            for p in plg.all(default=True):
                self._supported_models.update(p)

        if self.model not in self._supported_models:
            raise exceptions.CommandError(utils.this_command(self),
                                          "Model '{}' is not supported".format(model))

        related_models = db.related_classes(model)

        sess = constants.db_session()

        model_count = sess.query(model).count()

        with self.match_model.call_capture(model_name, model_name, model_name, self.term, get_search_options()) as plg:
            for i in plg.all():
                self.matched_ids.update(i)
                if len(self.matched_ids) == model_count:
                    break

        has_all = False
        for m in related_models:
            if m in self._supported_models:
                with self.match_model.call_capture(db.model_name(m), model_name, db.model_name(m), self.term, get_search_options()) as plg:
                    for i in plg.all():
                        self.matched_ids.update(i)
                        if len(self.matched_ids) == model_count:
                            has_all = True
                            break
            if has_all:
                break

        self.matched.emit(self.matched_ids)

        return self.matched_ids


class ModelFilter(Command):
    """
    Perform a full search on database model
    Returns a set of ids of matched model items
    """

    separate = CommandEntry("separate", tuple, tuple)
    include = CommandEntry("include", set, str, set)
    exclude = CommandEntry("exclude", set, str, set)
    empty = CommandEntry("empty", set, str)

    included = CommandEvent("included", str, set)
    excluded = CommandEvent("excluded", str, set)
    matched = CommandEvent("matched", str, set)

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
    def _match(model_name, pieces):
        ""
        model = database_cmd.GetModelClass().run(model_name)
        partialfilter = PartialModelFilter()
        matched = set()

        for p in pieces:
            m = partialfilter.run(model, p)
            matched.update(m)

        return matched

    @include.default()
    def _include(model_name, pieces):
        return ModelFilter._match(model_name, pieces)

    @exclude.default()
    def _exclude(model_name, pieces):
        return ModelFilter._match(model_name, pieces)

    @empty.default()
    def _empty(model_name):
        model = database_cmd.GetModelClass().run(model_name)
        s = constants.db_session()
        return set(x[0] for x in s.query(model.id).all())

    def main(self, model: db.Base, search_filter: str) -> set:
        assert issubclass(model, db.Base)

        self._model = model
        model_name = db.model_name(self._model)

        if search_filter:

            self.parsesearchfilter = ParseSearch()

            pieces = self.parsesearchfilter.run(search_filter)

            options = get_search_options()

            include = set()
            exclude = set()

            with self.separate.call(pieces) as plg:

                for p in plg.all():
                    if len(p) == 2:
                        include.update(p[0])
                        exclude.update(p[1])

            with self.include.call(model_name, include) as plg:

                for i in plg.all():
                    if options.get("all"):
                        if self.included_ids:
                            self.included_ids.intersection_update(i)
                        else:
                            self.included_ids.update(i)
                    else:
                        self.included_ids.update(i)

            self.included.emit(model_name, self.included_ids)

            with self.exclude.call(model_name, exclude) as plg:

                for i in plg.all():
                    self.excluded_ids.update(i)

            self.excluded.emit(self._model.__name__, self.excluded_ids)

            self.matched_ids = self.included_ids
            self.matched_ids.difference_update(self.excluded_ids)

        else:

            with self.empty.call(model_name) as plg:
                for i in plg.all():
                    self.matched_ids.update(i)

        self.matched.emit(self._model.__name__, self.matched_ids)

        return self.matched_ids
