'''Registry class for storing commonly referenced values within the GUI.'''

class Registry(object):
    def add(values={}):
        for key, value in values.iteritems():
            setattr(Registry, key, value)