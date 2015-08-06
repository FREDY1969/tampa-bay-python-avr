# parse\_needed\_words #

This is the call graph for [parse\_needed\_words](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/compiler/parse.py#109).

The overall plan here is very simple, it starts by placing the [startup](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/startup.asm) [Word](Word.md) on a todo list.

It then calls parse\_word on each item in the todo list.  Each call returns the Words need by that function.  Words that have already been parsed are deleted from this list, and the rest are added to the todo list.

This repeats until the todo list is empty.

## [parse\_word](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/compiler/parse.py#86) ##

This returns the words needed by this word so that only the needed words are compiled.

To do this, it calls the `parse_file` method on the [Word Object](http://code.google.com/p/tampa-bay-python-avr/wiki/TwoObjectsForEachWord#Word_Object), passing the `parser.py` module for the [Package](Package.md) that it's in.

Currently, there are three implementations of `parse_file`:

  1. [declaration.parse\_file](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#83) this is just an empty stub (as a default for words that don't have text files associated with them).
  1. [high\_level\_word.parse\_file](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#145)
    * [parse.parse\_file](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/parser/parse.py#10) passing the `parser.py` module
    * [ast.prepare\_args](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/database/ast.py#300)
      * [ast.ast.prepare](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/database/ast.py#164)
        * [declaration.get\_method](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#95) looks up `prepare_<expect>` method.  If not found, returns the `prepare_generic` method.
        * word\_obj.prepare`_<expect>`
          1. [word.prepare\_generic](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py#133)
            * word\_obj.update\_expect
            * [ast.ast.prepare\_args](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/database/ast.py#196) recurses on arguments to the word
            * word\_obj.update\_types
            * word\_obj.macro\_expand
    * [ast.save\_word](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/database/ast.py#346) writes the AbstractSyntaxTree to the [Database](Database.md)
  1. [assembler\_word.parse\_file](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/assembler_word.py#16) (ignores `parser.py` passed to it)
    * [parse\_asm](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/assembler_word.py#98)
    * [assembler.block.write](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/database/assembler.py#83) writes the assembler to the [Database](Database.md)
    * [assembler\_word.labels\_used](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/assembler_word.py#40)