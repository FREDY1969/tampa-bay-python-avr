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
        for address, bytes in split(words, 16):
            data_hex = ''.join("{:02x}".format(n) for n in bytes)
            line = "{:02x}{:04x}00{}" \
                     .format(len(data_hex)//2, address, data_hex)
            hex_file.write(":{}{:02x}\n".format(line, check_sum(line)))
            generated_something = True
        hex_file.write(":00000001FF\n")
    if not generated_something:
        os.remove(filename)

def split(it, size = 16):
    r'''Generates address, bytes where len(bytes) <= size.

    'it' is a sequence of (address, byte).

    Terminates bytes if there are any jumps in the address produced by it.

        >>> tuple(split(()))
        ()
        >>> tuple(split((x, x) for x in range(1, 30)))
        ((1, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]), (17, [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]))
    '''
    first_address = None
    last_address = None
    bytes = []
    for address, byte in it:
        if first_address is None:
            first_address = address
            bytes = [byte]
        elif last_address + 1 != address or len(bytes) >= size:
            if bytes: yield first_address, bytes
            first_address = address
            bytes = [byte]
        else:
            bytes.append(byte)
        last_address = address
    if bytes: yield first_address, bytes

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

