#!/usr/bin/env python

# This script will call avrdude to load your flash.hex

import sys
import os
import glob
import subprocess

def usage():
    print >>sys.stderr, 'usage: load'
    sys.exit(2)

def run(
        load_path = '.',
        memory_type = 'flash',
        install_dir = None,
        avrdude_port = None,
        mcu = 'atmega328p',
        avr_dude_path = None,
        avr_config_path = None,
        avrdude_programmer = 'stk500v1',
        upload_rate='57600',
    ):
    
    # system dependent defaults
    
    if sys.platform == 'darwin': # Mac
        if avrdude_port is None:
            avrdude_port = '/dev/tty.usbserial*'
        avrdude_port = glob.glob(avrdude_port)[-1]
        if install_dir is None:
            install_dir = '/Applications/Arduino.app/Contents/Resources/Java/'
        if avr_dude_path is None:
            avr_dude_path = os.path.join('hardware', 'tools', 'avr', 'bin')
        if avr_config_path is None:
            avr_config_path = os.path.join('hardware', 'tools', 'avr', 'etc')
        
    elif sys.platform == 'win32':
        if avrdude_port is None:
            avrdude_port = 'COM3'
        if install_dir is None:
            install_dir = r'C:\Program Files\arduino-*'
        if avr_dude_path is None:
            avr_dude_path = os.path.join('hardware', 'tools', 'avr', 'bin')
        if avr_config_path is None:
            avr_config_path = os.path.join('hardware', 'tools', 'avr', 'etc')
        
    else: # some flavor of *nix...
        if avrdude_port is None:
            avrdude_port = '/dev/ttyUSB*'
        avrdude_port = glob.glob(avrdude_port)[-1]
        if install_dir is None:
            install_dir = os.environ['HOME'] + '/arduino-*'
        if avr_dude_path is None:
            avr_dude_path = os.path.join('hardware', 'tools')
        if avr_config_path is None:
            avr_config_path = os.path.join('hardware', 'tools')
    
    # call it
    
    subprocess.check_call(
        (
            os.path.join(glob.glob(install_dir)[-1], avr_dude_path, 'avrdude'),
            '-V',
            '-F',
            '-C', os.path.join(glob.glob(install_dir)[-1], avr_config_path,
                               'avrdude.conf'),
            '-p', mcu,
            '-P', avrdude_port,
            '-c', avrdude_programmer,
            '-b', upload_rate,
            '-U', memory_type + ':w:' + os.path.join(load_path,
                                                     memory_type + '.hex'),
        )
    )

if __name__ == '__main__':
    run(*sys.argv[1:])

