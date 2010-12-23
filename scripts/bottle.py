#!/usr/local/bin/python3.1

# bottle.py

"""Web based IDE for μCC project."""

#import argparse
import optparse
import sys

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

from ucc.bottle import server

def run():
    #argparser = argparse.ArgumentParser(description="Start the μCC IDE")
    #argparser.add_argument('package')
    #argparser.add_argument('--host', default='localhost', help="default localhost")
    #argparser.add_argument('--port', type=int, default=8080)

    optparser = optparse.OptionParser(
                  usage="usage: %prog [options] [[package_dir] package_name]")
    optparser.add_option('--host', default='localhost',
                         help="default: localhost")
    optparser.add_option('--port', type="int", default=8080,
                         help="default: 8080")

    options, args = optparser.parse_args()
    print("options", options)
    print("args", args)

    if len(args) == 1:
        server.start(options.host, options.port, None, args[0])
    elif len(args) > 2:
        parser.print_help()
        sys.stderr.write("too many arguments\n")
        sys.exit(2)
    else:
        server.start(options.host, options.port, *args)

if __name__ == '__main__':
    run()

