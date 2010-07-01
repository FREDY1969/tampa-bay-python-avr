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
:080060000c9400000c94000058
:1000680011241fbecfefd8e0debfcdbf0e943d00f8
:02007800ffcfb8
:10007a002fed25b920e224b92fef28b920e027b9be
:10008a002fef2bb920e02ab920e838e0f894209322
:0c009a0061003093610078942fef30e299
:0800a60025b9232744e85ee1bf
:0800ae0041505040e9f7f8cf82
:00000001FF
'''

if target_blinky[-2] != '\r':
    target_blinky = target_blinky.replace('\n', '\r\n')

def test_compile(directory, del_db = True):
    os.chdir(directory)
    del_files(del_db)
    compile.do_compile(('.',), True)
    with open('flash.hex', 'rt', encoding='ascii', newline='') as f:
        return f.read()

