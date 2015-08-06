# Two Objects for Each Word #

The way that [Words](Word.md) are used internally requires two different classes, as they have different purposes and lifetimes.

## Word Word ##

The first class is [ucc.word.word.word](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/word/word.py#86), instances of this class are called _word words_ in the code (because of the "word.word" in the import needed for them).  These are often simply abbreviated _ww_.  This is a "one size fits all" class used for all Words in the system (both **defining** Words and "normal" Words).

This class deals with the XML file associated with each Word and is used by both the GUI and the compiler.  It knows the **kind** of each Word, and the name of each Word's source file (if any).

The GUI creates these, reading in all of the XML files, and is responsible for updating the XML files when the user changes answers to questions (for example).  (See QuestionsAndAnswers).

The compiler uses these to refer to the answers that it needs, but doesn't update them.  Instead, it creates temporary shadow "word objects" for each "word word" that it uses.  (Note that the GUI reads in all Words in a [Package](Package.md), while the compiler only deals with the actual Words needed by the [Installation](Package#Installation.md).  The Installation may not use all of the Words in a library (for example).

## Word Object ##

Only the compiler creates and uses these.

There are two kinds of "word objects":

  1. Python classes defined in a [Package](Package.md) that are derived from [ucclib.built\_in.declaration.declaration](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucclib/built_in/declaration.py).  These are the **defining** Words.
  1. Instances of these classes.  These are the "normal" Words.

These are the Words that provide the hooks for the user to extend the language to suite his needs by writing his own subclasses of the **declaration** class.

All of these classes appear in individual [Packages](Package.md), rather than in the main "ucc" directory.

See ParsingDesign for their APIs and usage.