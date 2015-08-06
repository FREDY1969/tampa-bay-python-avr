# [Word Object](http://code.google.com/p/tampa-bay-python-avr/wiki/TwoObjectsForEachWord#Word_Object).compile #

Compiles the AbstractSyntaxTree into IntermediateCode.

There are currently three implementations of this:

  1. [word.compile](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#102) empty stub for default action
  1. [high\_level\_word.compile](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#160)
    * [ast.compile\_args](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/database/ast.py#334)
      * [arg.compile](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/database/ast.py#215)
        * word\_object.compile`_<expect>`
          1. [high\_level\_word.compile\_value](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#171)
          1. [high\_level\_word.compile\_statement](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#182)
          1. [operator.compile\_value](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/operator.py#18)
          1. [input\_pin.compile\_condition](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/input_pin.py#51)
          1. [input\_pin.compile\_value](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/input_pin.py#20)
          1. [set\_output\_bit.compile\_statement](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/set_output_bit.py#15)
          1. [clear\_output\_bit.compile\_statement](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/clear_output_bit.py#19)
          1. [set.compile\_statement](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/set.py#13)
          1. [var.compile\_value](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/var.py#22)
  1. [var.compile](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/var.py#10)