# hex_file.py

import os
import itertools

def write(words, package_dir, filetype):
    filename = os.path.join(package_dir, filetype + '.hex')
    with open(filename, 'w') as hex_file:
        generated_something = False
        for i in itertools.count():
            data_hex = ''.join(itertools.imap(
                                 lambda n: "%04x" % byte_reverse(n),
                                 itertools.islice(words, 8)))
            if not data_hex: break
            line = "%02x%04x00%s" % (len(data_hex)/2, i * 16, data_hex)
            hex_file.write(":%s%02x\r\n" % (line, check_sum(line)))
            generated_something = True
            if len(data_hex) < 32: break 
        hex_file.write(":00000001FF\r\n")
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

