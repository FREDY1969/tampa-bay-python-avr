# Parsing Design #

This covers the parsing of [Words](Word.md) up to and including IntermediateCode generation.



## Terminology ##

These terms are defined in this section:

  * **declaration** of a word
  * **defining** word
  * **kind** of a word
  * **call** to a word

### Declarations ###

A **declaration** creates a new word with a given name.

For this discussion, there are two kinds of words:

  * **defining** words
  * normal words (those that are not **defining** words)

**Defining** words are used to define normal words.  Thus, for example, the word _function_ is a **defining** word that is used to define the word _foo_ (a function), which is a normal word.  This is very much like the difference between class and instance.

The definition of both kinds of words is called a **declaration**.  Thus, the definition of the word _foo_ is a **declaration**, and the definition of the word _function_ is also a **declaration**.

We can say that the definition of _foo_ is a **function** declaration, or that the **kind** of _foo_ is **function**.

In the same spirit, we can say that the definition of the word _function_ is a **declaration** declaration, or that the **kind** of _function_ is **declaration**.

The word _declaration_ itself is a little strange because it's **kind** is also **declaration**.  This means that all words have a **kind**, which is another word.  And **declaration** is unique in being its own **kind**.

### Calls to a Word ###

In the above example, we have the words:

  * the **defining** word, _declaration_ (whose **kind** is **declaration**)
  * the **defining** word, _function_ (whose **kind** is **declaration**)
  * the normal word, _foo_ (whose **kind** is **function**)

Now suppose we add the following two words:

  * the **defining** word, _task_ (whose **kind** is **declaration**)
  * the normal word, _bar_ (whose **kind** is **task**)

And in the source file for bar (the body of the bar task), the word _foo_ appears.  We call this a **call** to foo.

## Goals ##

### User defined declarations ###

The first goal is to allow the user to define new kinds of declarations (ie, their own **defining** words), with perhaps new kinds of source files that require new kinds of parsing.

Given this capability, many of the basic built-in features of the language are themselves defined using this same mechanism.  For example, all of the following are defined using this mechanism:

  * tasks (functions with static [FunctionActivationRecords](FunctionActivationRecord.md))
  * functions (functions whose FunctionActivationRecord is allocated on the stack)
  * assembler functions (functions written in assembler, rather than ucl)
  * global variables
  * global constants

In addition to allowing for new kinds of source files, user defined declarations also allow the user defining one of these to create a set of questions that must be answered each time this declaration is used to declare a new word.

This QuestionsAndAnswers capability means that simple declarations do not require any source file (or syntax, or parser) at all.  Examples of this would be global variables and global constants.

The QuestionsAndAnswers capability also simplifies the syntax required when source files _are_ needed.  For example, the name and arguments of a function are specified by answering the questions associated with the _function_ declaration, rather than specified in the source file (which now contains only the body of the function).

### User defined syntax ###

The second goal is to allow the user to define new _statements_ in the ucl language that do interesting things when used within other functions.

This involves allowing the user to:

  * possibly define new reserved words
  * possibly define new syntax (grammar) for this statement
  * write the (python) code to compile a use of this statement (or call to this word) into IntermediateCode.

Given this capability, many of the basic built-in control statements are themselves defined using this same mechanism.  For example, all of the following are defined using this mechanism:

  * **if** statement
  * **while** statement
  * **for** statement
  * **repeat** statement
  * **with** statement


## Design ##

### Steps to Parsing ###

Parsing is handled at the [Package](Package.md) level; i.e., the Parsing step is carried out for the whole Package as a unit and produces a [Database](Database.md) for that Package.  Later, this might be broken out where the source file for each [Word](Word.md) can be parsed individually.

The steps to parse a Package are:

  1. Load all of the [Word Words](TwoObjectsForEachWord#Word_Word.md) in the [Package](Package.md) (and the Packages that this Package "uses") into memory.
    * A side effect of this is that all of the new syntax is identified.
  1. Gather up all of the new syntax and create a parser for this Package (this goes into a "parser.py" file in the Package's directory).
  1. Parse all of the Words in the Package to generate the SymbolTable and IntermediateCode in the [Database](Database.md) (replacing any prior information there on a Word by Word level).  The database is also stored in the Package directory as the file _ucc.db_.

**Note:** The compiler back-end will later take the SymbolTable and IntermediateCode from all of the Packages included in an [Installation](Package#Installation.md) and generate the machine code for all of it as a single unit.  Thus, while the compiler front-end is run at a [Package](Package.md) level, the compiler back-end is only run for the whole Installation (possibly made up of several Packages).  The compiler back-end is discussed elsewhere.

### Design of the API ###

The front-end of the compiler makes use of object-oriented dynamic binding capabilities to achieve the [goals](#Goals.md) stated above.

These capabilities are used for three purposes:

  1. to create and initialize the [Word Objects](TwoObjectsForEachWord#Word_Object.md) (both the class itself, as well as the instances of that class) that are used by the compiler front end
  1. to parse the source file associated with the declaration of each "norma" Word into an AbstractSyntaxTree stored in the [Database](Database.md)
  1. to translate the AbstractSyntaxTree into IntermediateCode for each call to the Word

All of these functions are handled by the **defining** Word.  Each **defining** Word is implemented as a Python class, and each "normal" Word is implemented as an instance of one of these classes (that class being it's **kind**).  In the above example, with:

  * the **defining** Word, _declaration_ (whose **kind** is **declaration**)
  * the **defining** Word, _function_ (whose **kind** is **declaration**)
  * the **defining** Word, _task_ (whose **kind** is **declaration**)
  * the "normal" Word, _foo_ (whose **kind** is **function**)
  * the "normal" Word, _bar_ (whose **kind** is **task**) containing a **call** to _foo_

there would be a Python class for _declaration_, _function_ and _task_ (the three **defining** Words), and an instance of the _function_ and _task_ classes for _foo_ and _bar_.  The source files for all **defining** Words are a .py file containing their class definition, while the source files for _foo_ and _bar_ are .ucl files.

Each class has methods to direct the following three kinds of activities:

  1. the creation of the new [Word Object](TwoObjectsForEachWord#Word_Object.md) to represent the [Word](Word.md) in the compiler
  1. the parsing of its instance's source files into an AbstractSyntaxTree
  1. the generation of IntermediateCode for **calls** to its instances

So in our example, the _function_ class must have methods to:

  * initialize the _function_ class, which represents itself.
  * initialize the instance, _foo_, of this _function_ class.
  * parse the source .ucl file for _foo_.
  * generate IntermediateCode in _bar_ for the call to the instance _foo_.

The API's for these are explained below.

### API for Creating New Word Objects in the Compiler ###

Each of these calls returns a two tuple: (new\_word, new\_syntax)

The new\_word is a [Word Object](TwoObjectsForEachWord#Word_Object.md) that may be a class or an instance.  It will be a class for **defining** Words, and an instance for "normal" Words.

The new\_syntax will be None if no new syntax is introduced by the Word.  Otherwise, new\_syntax is the two tuple: (rules, token\_dict).

Rules is a sequence of strings, each defining a new `raw_statement` in the language.  (See [SYNTAX](http://code.google.com/p/tampa-bay-python-avr/source/browse/ucc/parser/SYNTAX)).

Token\_dict is a dictionary mapping reserved words onto their token names (the token names are used in the rules).

#### To Create the Root **declaration** Class ####

We have a little problem getting our top-level **declaration** class (our _root_ **defining** Word) bootstrapped into the compiler (since it is its own **kind** and isn't loaded yet, so can't be used to load itself).

This special case uses:

```
>>> from ucclib.built_in import declaration  # this is the declaration module, not the class!

>>> new_word = declaration.load_class(ww)  # ww is instance of ucc.word.word.word class.
>>> new_syntax = None
```

This gives us our initial [Word Object](TwoObjectsForEachWord#Word_Object.md), which is the **kind** needed for the remaining **defining** Words.

Given the [Word Word](TwoObjectsForEachWord#Word_Word.md) that you want to create, you will also need the [Word Object](TwoObjectsForEachWord#Word_Object.md) for its **kind**.

You get the **kind** Word Object for the Word Word _ww_ as follows:

```
>>> kind_word = ww.kind_obj.symbol.word_obj  # ww.kind_obj is another Word Word
```

Then,

#### To Create a **Defining** Word ####

Then to initialize defining words:

```
>>> new_word, new_syntax = kind_word.create_subclass(ww)
```

New\_word will be a Word Object that issubclass of `kind_word`.

Note that because `kind_word` is a Python class, _create\_subclass_ must be a [classmethod](http://docs.python.org/library/functions.html#classmethod).

#### To Create a Normal Word ####

If the new word is a "normal" Word:

```
>>> new_word, new_syntax = kind_word.create_instance(ww)
```

New\_word will be a Word Object that isinstance of _kind\_word_.

Note that because `kind_word` is a Python class, _create\_instance_ must be a [classmethod](http://docs.python.org/library/functions.html#classmethod).

### API for Parsing a Source File ###

After all of the new\_syntax has been gathered together and a parser built for the package, the source files may be parsed as follows:

```
>>> if not isinstance(word_obj, type):
...     needs = word_obj.parse_file(parser, debug_flag)
```

Note that this is only done for "normal" Words, not **defining** Words -- which are classes (isinstance(word, type)).  The code for the **defining** Words is Python code, and we leave the parsing of those files to Python (dynamically importing these files to make this happen).

Also note that a connection to the [Database](Database.md) must be made first (not shown), since this call results in writing the AbstractSyntaxTree to the Database.

### API for Calls to an Instance ###

Each syntactic element recognized by the parser has a [Word](Word.md) associated with it (the function or operator being invoked) and a set of arguments.  (Some of these arguments may be statement lists, for example to the **if** word for its _true_ and _false_ legs).  Depending on how the syntactic element is used, one of a set of compile\_X methods are called on the Word Object to compile the **call** into IntermediateCode.  Examples of these compile\_X methods are:

  * compile\_value, used when the syntactic element is expected to simply produce a value, for example, as a parameter to an outer function call.
  * compile\_lvalue, used when the element is used on the left side of an assignment.  In this case, an address would be generated.  Not all words are capable of this!
  * compile\_cond, used when the element is used as a condition, for example, in an **if** or **while** statement.  In this case, the element may produce code that includes conditional branches to labels defined in the outer statement.
  * compile\_iter, used when the element is used in an iterator position (for example in a **for** statement).
  * compile\_statement, used when the element is used as a statement (where no return value is expected).
  * compile\_decl, used when the element is declaring a new word.  Not all words are capable of this either!

The choice of which method to call is specified in the grammar (see MetaSyntax).

These compile\_X methods generate and return the IntermediateCode that is stored in the [Database](Database.md).

Because instances (_foo_, not _function_, in our example above) are used in the AbstractSyntaxTree, these are normal methods on the _function_ class, not classmethods.