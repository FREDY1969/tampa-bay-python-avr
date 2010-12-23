'''Load configuration.'''

import sys, os
import configparser

def load():
    paths = os.path.expanduser('~')
    if sys.platform.startswith('win') or \
       sys.platform in ('os2', 'os2emx', 'riscos', 'atheos'):
        configFile = 'ucc.ini'
    else:
        configFile = '.ucc.ini'
    configPath = os.path.join(paths, configFile)
    if not os.path.exists(configPath):
        # This may need to be changed eventually to support zipped
        # installations of this compiler.
        defaultFile = os.path.join(os.path.dirname(__file__), 'ucc-default.ini')
        from distutils import file_util
        file_util.copy_file(defaultFile, configPath)
    config = configparser.RawConfigParser()
    config.read(configPath)
    return config
