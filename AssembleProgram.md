# assemble\_program #

This is the call graph for [assemble\_program](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/assemble.py#64).

Translates the assembler into machine code and generates the .hex file(s).

  * [assemble.assign\_labels](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/assemble.py#11)
  * [assemble.assemble](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/assemble.py#38)
    * [assemble.assemble\_word](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/assemble.py#48)
      * asm\_inst.assemble
        1. [inst1.assemble](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/asm_inst.py#327)
        1. [inst2.assemble](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/asm_inst.py#344)
        1. [bytes.assemble](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/asm_inst.py#374)
        1. [int8.assemble](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/asm_inst.py#387)
        1. [int16.assemble](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/asm_inst.py#395)
        1. [int32.assemble](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/asm_inst.py#405)
        1. [zeroes.assemble](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/asm_inst.py#418)
  * [hex\_file.write](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/hex_file.py#6)