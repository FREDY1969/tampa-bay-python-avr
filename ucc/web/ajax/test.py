# test.py

"""An example module for handling ajax requests."""

def bar(session, data):
    print('== data ==', data)
    if 'foo' in data:
        return '200 OK', [], 'foo was set to {foo}'.format(**data)
    else:
        return '500 Server Error', [], 'foo was not set!'
