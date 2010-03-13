# debug.py

'''Print out debug messages.'''

CSI="\x1b["
RED = CSI+'31;1;5m'
GREEN = CSI+'32;1m'
BLUE = CSI+'94;1m'
ENDC = CSI+'0m'

def trace(string):
    print('  '+string)

def warn(string):
    print(colorize('  '+string, RED))

def success(string):
    print(colorize('  '+string, GREEN))

def notice(string):
    print(colorize('  '+string, BLUE))

def header(string=None, color=None):
    if string: string = ' %s ' % string
    string = '\n'+string.upper().center(78, '=')
    if color:
        print(colorize(string, color))
    else:
        print(colorize(string))

def colorize(string=None, color=BLUE):
    return color+string+ENDC