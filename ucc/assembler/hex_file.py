# hex_file.py

import os
import itertools

def write(words, package_dir, filetype):
    r'''Writes words to .hex file in package_dir.

    'words' is a sequence of (starting_address, byte sequence).
    '''
    filename = os.path.join(package_dir, filetype + '.hex')
    with open(filename, 'wt', encoding='ascii', newline='\r\n') as hex_file:
        generated_something = False
        for address, bytes in words:
            bytes_iter = iter(bytes)
            for i in itertools.count():
                data_hex = ''.join(map(
                                     lambda n: "%02x" % n,
                                     itertools.islice(bytes_iter, 16)))
                if not data_hex: break
                line = "%02x%04x00%s" % \
                         (len(data_hex)//2, address + i * 16, data_hex)
                hex_file.write(":%s%02x\n" % (line, check_sum(line)))
                generated_something = True
                if len(data_hex) < 32: break 
        hex_file.write(":00000001FF\n")
    if not generated_something:
        os.remove(filename)

def byte_reverse(n):
    r'''Reverses the two bytes in a 16 bit number.

    >>> hex(byte_reverse(0x1234))
    '0x3412'
    '''
    return ((n << 8) & 0xff00) | (n >> 8)

def check_sum(data):
    r'''Calculates the .hex checksum.

    >>> hex(check_sum('100000000C9445010C9467110C9494110C946D01'))
    '0x9f'
    >>> hex(check_sum('10008000202D2068656C70202874686973206F75'))
    '0x56'
    '''
    sum = 0
    for i in range(0, len(data), 2):
        sum += int(data[i:i+2], 16)
    return (256 - (sum & 0xff)) & 0xFF

