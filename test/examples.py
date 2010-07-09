# examples.py

r'''Helper functions for blinky tests.
'''

import os, sys
from scripts import compile

def del_file(filename):
    if os.path.exists(filename):
        os.remove(filename)

def del_files(del_db = True):
    del_file('flash.hex')
    del_file('parser.py')
    del_file('parser.pyc')
    del_file('parser_tables.py')
    del_file('parser_tables.pyc')
    if (del_db): del_file('ucc.db')

os.chdir(sys.path[0])
os.chdir('examples')

target_blinky = ''':100000000c9434000c9400000c9400000c9400003c
:100010000c9400000c9400000c9400000c94000060
:100020000c9400000c9400000c9400000c94000050
:100030000c9400000c9400000c9400000c94000040
:100040000c9400000c9400000c9400000c94000030
:100050000c9400000c9400000c9400000c94000020
:100060000c9400000c94000011241fbecfefd8e0c8
:10007000debfcdbf0e943d00ffcf2fed25b920e2ae
:1000800024b92fef28b920e027b92fef2bb920e0b2
:100090002ab920e838e0f894209361003093610099
:1000a00078942fef30e225b9232744e85ee14150f0
:0600b0005040e9f7f8cf13
:00000001FF
'''

if target_blinky[-2] != '\r':
    target_blinky = target_blinky.replace('\n', '\r\n')

target_blinky2 = ''':10000000hi mom!
'''

if target_blinky2[-2] != '\r':
    target_blinky2 = target_blinky2.replace('\n', '\r\n')

def test_compile(directory, del_db = True):
    os.chdir(directory)
    del_files(del_db)
    compile.do_compile(('.',), True)
    with open('flash.hex', 'rt', encoding='ascii', newline='') as f:
        return f.read()

