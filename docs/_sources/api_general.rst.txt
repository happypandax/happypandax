General
#######################################

Database
----------------------------------------

Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Collection** -> **Grouping** -> **Gallery** -> **Page**

.. note::

    **Grouping** is not actually a direct descendant of **Collection** as can be seen below,
    but it is sometimes helpful to think of it as such.

Recommended Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Collection
***************************************

Conventions (e.g. ``C90``), magazines (e.g. ``Girls forM``),
tankōbon's or a compilation of related/personal galleries

Grouping
***************************************

Think of this as a namespace for related galleries. It is ideal for grouping
multi-series galleries, so you use this as the series name. Since tankōbon's also sometimes feature
a complete series, you can use this for that too. It is not recommended to put tankōbon in both
**Collection** and here. Choose one and stick to it to avoid confusion.
**Gallery**'s ``number`` field is used in the context of a **Grouping**.

GalleryFilter
***************************************

Think of this as those *smart-playlists* in music applications. It's a compilation of galleries put
together by the user either manually or through automatic search filtering. If you've used the old
Happypanda then you've should already be familiar with this. In old HP they were called gallery lists.
Recommended usage is "anything". It could range from your favorite fetishes to a shortcut for a
search filter you're tired of always typing in.

Gallery
***************************************

A single chapter, then you group these chapters under a **Grouping** to form a complete series.

Special Notes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Gallery
***************************************

- A **Gallery** can have multiple **Title**, **Artist** and **Parody**
- A **Gallery** can be in multiple **Collection** and **GalleryFilter**
- A **Gallery** can only be in **one** **Grouping**
- A **Gallery** will *always* be in a **Grouping**

Tags
***************************************

**Gallery** and **Page** are the only taggable items.
**Collection** and **Grouping** are *not* taggable, but they can display, and are searchable through tags of their children **Gallery**.

Alias
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

 ...

Parent
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

 ...


.. note::
    *You can right-click on the image and choose "Show image" to view it in its full dimensions*

.. image:: _static/schema.png

Asynchronous Commands
----------------------------------------

.. autoclass:: happypanda.core.command.CommandState
   :members:

Exceptions
----------------------------------------

