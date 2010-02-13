'''Load configuration.'''

import sys, os
import ConfigParser

def load():
    paths = os.path.expanduser('~')
    #import pprint
    #pprint.pprint(paths)
    if sys.platform.startswith('win') or \
       sys.platform in ('os2', 'os2emx', 'riscos', 'atheos'):
        configFile = 'ucc.ini'
    else:
        configFile = '.ucc.ini'
    configPath = os.path.join(paths, configFile)
    if not os.path.exists(configPath):
        # This may need to be changed eventually to support zipped
        # installations of this compiler.
        defaultFile = os.path.join(sys.path[0], 'ucc', 'ucc-default.ini')
        from distutils import file_util
        file_util.copy_file(defaultFile, configPath)
    config = ConfigParser.RawConfigParser()
    config.read(configPath)
    return config