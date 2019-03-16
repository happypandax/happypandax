FAQ
========================================

File Support
-------------------------------------
In addition to folders with loose files, the following file extensions are accepted for import within HPX by default:

- **Archive Formats**
- ZIP = ``.zip``
- RAR = ``.rar``
- CBR = ``.cbr``
- CBZ = ``.cbz``
- TAR GZ = ``.tar.gz`` or ``.tgz``
- TARBZ2 = ``.tar.bz2`` or ``.tbz``
- TARXZ = ``.tar.xz`` or ``.txz``

- **Image formats**
- JPG = ``.jpg``
- JPEG = ``.jpeg``
- BMP = ``.bmp``
- PNG = ``.png``
- GIF = ``.gif``

It is possible to add support for additional file extensions with plugins

Scanning for galleries
-------------------------------------

In addition to regular paths to folders, the scanner also supports some special syntax for more fine-grained control of the import process.

The following tokens can be used in a path, these shall be called component-tokens:

- ``{collection}`` - to specify that this part in the path is a collection
- ``{grouping}`` or ``{series}`` - to specify that this part in the path is a grouping
- ``{artist}`` - to specify that this part in the path is the artist name
- ``{gallery}`` - to specify that this part in the path is a gallery

For regex, these tokens are available:

- ``{re:"<regex here>"}`` - to match a part in the path that satisfies the given expression *(replace ``<regex here>`` with the actual expression)*
- ``{re:'<regex here>' <omponent>}`` - where ``<component>`` is one of the component-tokens above. This token is basically a combination of the regex token and a component-token.

For glob patterns, or more general name matching, this token is available:

- ``{"<pattern here>"}`` - to match a part in the path that satisfies the given glob pattern or name

A special wild-card token is also available:

- ``*`` - to match anything

These tokens make the scanner pretty flexible and able to work on most, if not all, possible directory structures.

Learn best by example:

Suppose our collection is structured like this:

    root\
        - col A\ 
            - series A\
                - gallery C
                - gallery D
        - col B\ 
            - gallery A
        - col C\ 
            - gallery **B**
        - gallery ABC


If we want to add ``gallery C`` and ``gallery D`` put in the same series and collection we write:

- ``root/{collection}/{series}/{gallery}``

This tells the scanner the following:

- Treat every folder found in ``root/`` as collections
- Next, treat the folders found in those collections as series'
- Lastly, in those series, treat every folders or files as galleries

This will add ``gallery C`` and ``gallery D`` grouped under the same series and collection.
The scanner will ignore ``col B``, ``col C`` and ``gallery ABC`` because, according to the the path given, no galleries were found inside them.

If we want to add ``gallery A`` and ``gallery B``, we just write:

- ``root/{collection}/{gallery}``

Same as before, just now without the ``{series}`` token. There is no need for all tokens to be present but there must always be a ``{gallery}`` token **at the very end** of the path.
The scanner will add one automatically if none is provided, so these to paths are actually equal:

- ``root/{gallery}`` and ``root/``

These two will both add ``gallery ABC`` as a gallery. ``col A``, ``col B`` and ``col C`` are matched too but these don't *qualify* as galleries so the scanner will ignore them.

The order of item-tokens can be arbitrary except ``{gallery}``, which always must be last:

- ``root/{gallery}/{collection}/{series}`` -- ERROR
- ``root/{series}/{collection}/{gallery}`` -- OK

The wild-card can be used to match a folder unconditionally without treating it as a special item:

- ``root/{collection}/*/{gallery}``

This will add ``gallery C`` and ``gallery D`` put in the same collection but not series, because no token for it was provided.

If we want to only add ``gallery C`` and not ``gallery D``, we can use regex to, for example, only match names that contain the letter ``C``:

- ``root/{collection}/{series}/{re:".*C.*" gallery}``

This will only add ``gallery C``.
We can also use it to match folders without specifying an item. For example, if we want to match ``gallery A`` and not ``gallery B``:

- ``root/{re:".*B.*"}/{gallery}``

This will add ``gallery A`` and not ``gallery B``.

A simpler way would be using a glob-pattern:

- ``root/{"*B*"}/{gallery}``
- 
This will also add ``gallery A`` and not ``gallery B``.

You may ask, **what if we want to just add all galleries?**. It is possible to do so in conjunction with the setting ``scan.transparent_nested_folders``.
If we're not interested in specifying collection and grouping, we could just write:

- ``root/{gallery}``

This will add all the galleries if ``scan.transparent_nested_folders`` is set to true. But if we're interested in specifying the different kind of items, we'll have to do it in passes. Think smartly.

Lastly, item-tokens are only allowed to appear once in the path.