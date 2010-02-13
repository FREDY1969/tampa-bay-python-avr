#!/usr/bin/python

from __future__ import with_statement

import sys

def usage():
    sys.stderr.write("usage: peek.py file.hex\n")
    sys.exit(2)

if __name__ == "__main__":
    if len(sys.argv) != 2: usage()
    with open(sys.argv[1], 'r') as input:
        for line in input:
            templine = line[0:3] + ' ' + line[3:7] + ' ' + line[7:9] + '  ' 
            j = 9
            while j < len(line)-4:
                templine = templine + line[j+2:j+4] + line[j:j+2] + ' '
                j += 4
            print(templine)
