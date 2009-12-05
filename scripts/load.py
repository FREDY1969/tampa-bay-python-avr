#!/usr/bin/python

# load.py memory_type

import os
import sys
import optparse

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

from ucc.parser import load

class options_dict(dict):
    def __setattr__(self, key, value):
        if value is not None:
            self[key] = value

def run():
    optparser = optparse.OptionParser(
                  usage="usage: %s [options] [load_dir [memory_type]]" % 
                          os.path.basename(sys.argv[0]))

    optparser.add_option('--install_dir',
      help='the location of the arduino-xxxx directory downloaded from arduino.cc')
    optparser.add_option('--avrdude_port',
      help='the pseudo serial device on your PC that talks to the Arduino')
    optparser.add_option('--mcu',
      help='the microcontroller chip')
    optparser.add_option('--avr_dude_path',
      help='the subdirectory under --install_dir containing the avrdude program')
    optparser.add_option('--avr_config_path',
      help='the subdirectory under --install_dir containing avrdude.conf')
    optparser.add_option('--upload_rate',
      help='the upload baud rate')
    optparser.add_option('--avrdude_programmer',
      help='the download protocol to use')
    optparser.set_defaults()

    options, args = optparser.parse_args(values=options_dict())
    load.run(*args, **options)

if __name__ == '__main__':
    run()

