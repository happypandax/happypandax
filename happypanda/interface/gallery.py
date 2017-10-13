"""
Gallery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from happypanda.core import message


def add_gallery(galleries: list=[], paths: list=[]):
    """
    Add galleries to the database.

    Args:
        galleries: list of gallery objects
        paths: list of paths to the galleries

    Returns:
        Gallery objects
    """
    return message.Message("works")


def scan_gallery(paths: list=[], add_after: bool=False,
                 ignore_exist: bool=True):
    """
    Scan folders for galleries

    Args:
        paths: list of paths to folders to scan for galleries
        add_after: add found galleries after scan
        ignore_exist: ignore existing galleries

    Returns:
        list of paths to the galleries
    """
    return message.Message("works")
