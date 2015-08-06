# create\_parsers #

This is the call graph for [create\_parsers](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/compiler/parse.py#53).

## [load\_word](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/compiler/parse.py#14) ##

Loads and initializes the word\_obj, which might be a Python class derived from [declaration](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#13), or an instance of one of these classes.

  * [declaration.load\_class](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#186) done once for the top-level `declaration` word
  * word\_kind.create\_subclass for each defining word (other than `declaration`)
    1. [declaration.create\_subclass](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#49)
      * [declaration.load\_class](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#186)
      * word\_kind.new\_syntax
        1. [declaration.new\_syntax](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#66) (empty stub)
  * word\_obj.create\_instance for each non-defining word
    1. [declaration.create\_instance](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#58)
    1. [singleton.create\_instance](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/singleton.py#17) Note the slight of hand here -- it's creating a subclass and passing it off as an instance!
      * word\_kind.create\_subclass (same subtree as above)
      * word\_kind.new\_syntax2
        1. [singleton.new\_syntax2](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/singleton.py#23) (empty stub)
        1. [macro.new\_syntax2](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/macro.py#11)

## [genparser.genparser](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/parser/genparser.py#13) ##

Called for each package, passed all of the new syntax (defined in macros) that applies to that package.  This generates a `parser.py` file in the package directory.

  * [parser\_init.parse](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/parser/parser_init.py#48)
    * MetaSyntax defined in [metaparser](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/parser/metaparser.py) and [metascanner](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/parser/metascanner.py).

## [helpers.import\_module](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/word/helpers.py#23) ##

Imports the new `parser.py` module.