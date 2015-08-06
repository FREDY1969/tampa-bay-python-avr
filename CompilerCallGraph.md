# Legend #

Bullet lists represent standard calls to functions.  These may be normal functions or calls to methods on objects.

Numbered lists represent the different possible methods that might be called (depending on the type of the object).  Each numbered list is subordinate to the bullet list item for the method call.  Each individual numbered list item (representing a single method) then has the calls that it makes as a bullet list under that number.

# Compile Call Graph #

The function that is called to compile the [Installation](Package#Installation.md) is simply [compile.run](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/compiler/compile.py#13).

There are six basic steps to the compilation process:

## CreateParsers ##

The [create\_parsers](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/compiler/parse.py#53) function creates a parser.py module for each [Package](Package.md).

## ParseNeededWords ##

The [parse\_needed\_words](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/compiler/parse.py#109) function parses the source text files for all of the [Words](Word.md) needed by this [Installation](Package#Installation.md) and generates the [AbstractSyntaxTree](AbstractSyntaxTree.md).

## WordObjCompile ##

Calls the `compile` method on the [Word Object](http://code.google.com/p/tampa-bay-python-avr/wiki/TwoObjectsForEachWord#Word_Object) to compile the AbstractSyntaxTree into IntermediateCode.

## Optimize ##

This optimizes the IntermediateCode.

The [optimize](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/compiler/optimize.py#5) function is currently just an empty stub.  It is a "Release 2" feature.

## GenAssembler ##

The [gen\_assembler](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/codegen/codegen.py#11) function translates the IntermediateCode into assembler.

## AssembleProgram ##

The [assemble\_program](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/assembler/assemble.py#64) function translates the assembler into machine code and generates the .hex file(s).