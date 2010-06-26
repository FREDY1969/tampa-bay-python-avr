# test.py

"""An example module for handling ajax requests."""

def bar(session, **kwarg):
    if 'foo' in kwarg:
        return ('200 OK', [], 'foo was set to {}'.format(kwarg['foo']))
    else:
        return ('500 Server Error', [], 'foo was not set!')
    
