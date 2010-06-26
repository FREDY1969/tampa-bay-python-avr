# session.py

"""A session object is just a place to dump session info.

Session info is simply stored as arbitrary attributes on the object.

This basically replaces the "registry" module in the old gui app, except here
the attributes are stored on an object instead of this module to allow for
multiple sessions in the future.

"""

class Session:
    pass
