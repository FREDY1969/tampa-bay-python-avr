#!/bin/bash

# load file.hex

usage() {
    echo "usage: load" >&2
    exit 2
}

[ $# -eq 0 ] || usage

set -e

INSTALL_DIR=/home/bruce/arduino-0015
AVR_TOOLS_PATH=$INSTALL_DIR/hardware/tools
MCU=atmega328p
AVRDUDE_PORT=/dev/ttyUSB*
AVRDUDE_PROGRAMMER=stk500v1
UPLOAD_RATE=57600

AVRDUDE_FLAGS="-V -F -C $AVR_TOOLS_PATH/avrdude.conf -p $MCU -P $AVRDUDE_PORT -c $AVRDUDE_PROGRAMMER -b $UPLOAD_RATE"
AVRDUDE_WRITE_FLASH="-U flash:w:flash.hex"

AVRDUDE=$AVR_TOOLS_PATH/avrdude

$AVRDUDE $AVRDUDE_FLAGS $AVRDUDE_WRITE_FLASH
exit $?
