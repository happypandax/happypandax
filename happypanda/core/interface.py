from gevent import monkey
monkey.patch_all()
import code, sys

## CORE ##

def interactive():
    
    # exception trick to pick up the current frame
    try:
        raise None
    except:
        frame = sys.exc_info()[2].tb_frame.f_back

    # evaluate commands in current namespace
    namespace = frame.f_globals.copy()
    namespace.update(frame.f_locals)

    code.interact("======== Start Happypanda Debugging ========", local=namespace)

## DATABASE ##



## GALLERY ##

def fetchGallery(offset=None, from_gallery_id=None):
    """
    Fetch galleries from the database.
    Params:
        offset -- where to start fetching from, an int
        from_gallery -- which gallery id(index) to start fetching from, an int
    Returns:
        Gallery objects
    """
    pass

def addGallery(gallery_boject=None, paths=None):
    """
    Add galleries to the database.
    Params:
        galleries -- list of gallery objects parsed from XML
        Returns: Status

        paths -- list of paths to the galleries
        Returns: Gallery objects
    """
    pass

def scanGallery(paths=[], add_after=False, ignore_exist=True):
    """
    Scan folders for galleries
    Params:
        paths -- list of paths to folders to scan for galleries
        add_after -- add found galleries after scan
        ignore_exist -- ignore existing galleries
    Returns:
        Paths to the galleries
    """
    pass


