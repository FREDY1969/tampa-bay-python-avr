Declaration [Words](Word.md) may define questions that must be answered when that word is used to define a new word.

It is important that both questions (essentially the metadata for answers) and answers are stored in a text format that can be merged by VCS tools (like mercurial).  This nixes the use of a database to store questions and answers.

The text format should produce merge conflicts where reporting a merge conflict makes sense, and not produce merge conflicts where reporting a merge conflict doesn't make sense.  Specifically, if two different developers add a new value to the same list, that should _not_ produce a merge conflict.

We will also need a way to update all of the sets of answers for a given question when the definition for that question changes.

Finally, whether questions also store GUI information (like what widget to use to ask the question, what label to use, help text, the position of widgets on the screen, or whatever) is up to the GUI developer(s).  For example, the GUI developer may allow the person creating the questions to use a GUI widget layout tool and store the output of the tool with the question.  But the format of this layout information should also be textual and mergable with reasonable merge conflicts.

So to meet these goals, we've chosen an XML format.  The routines to read and write this XML are in the ucc/word directory:

```
>>> from ucc.word import word
>>> word = word.read_word('word_name', 'package/directory')
>>> word.write_xml('package/directory')
```

Each **word** object has the following attributes:

  * name (python name)
  * label (name in GUI)
  * defining (True or False)
  * kind (name of defining word used to define this word)
  * answers (dict mapping question\_name to "answers", where "answers" can be: None, an _answer_ object or a list of _answer_ objects.
  * questions (list of _question_ objects)

**Words** also have a get\_answer('question\_name') method.

Both _answer_ objects and _question_ objects are also defined in ucc/word.

![http://groups.google.com/group/tampa-bay-python-avr/web/QuestionsAndAnswers.png](http://groups.google.com/group/tampa-bay-python-avr/web/QuestionsAndAnswers.png)

# Question #

Questions are defined recursively.  The bottom-level (leaf) questions are called _atoms_, and groups of questions are called _molecules_.

Any question, atom or molecule, may be have a min and max number of occurrences specified.  A min of 0, max of 1 indicates an optional question (doesn't have to be answered).  A min of 0, max of infinite indicates a repeating question that may not have any answers.  A min of 1, max of infinite indicates a repeating question that requires at least one answer, etc.

In addition, the order of the repetitions may or may not be important.  Thus, where multiple answers are allowed, there is also the option to allow the user to reorder the answers or not (where this makes sense).

## Atoms ##

An atom is an indivisible piece of information.  They are not composed of smaller questions.

  1. bool
    * Can choose what words to use for "True" and "False" (e.g., "On" and "Off", "High" and "Low", "Yes" and "No", etc).
  1. int
    * Can be decimal, hex or binary.
    * All forms may have a range of valid values, which is specified using parenthesis to exclude the listed value and square brackets to include it.  Examples:
      * `(3-10]` means greater than 3 and less than or equal to 10.
      * `[3-10)` means greater than or equal to 3 and less than 10.
      * `(3-10)` means greater than 3 and less than 10.
      * `[3-10]` means greater than or equal to 3 and less than or equal to 10.
    * Hex and binary have a length in bytes.
  1. rational
    * These are exact numbers, expressed as a ratio.  All forms of input have a '/' character in them (here `[]` means optional, `+` means 1 or more, `*` means 0 or more, and `decimal` means any decimal digit 0-9):
      * `[-][decimal+.]decimal+/decimal+`
        * For example: 2.1/2 means "2 and one half".
      * `[-]decimal*.decimal+/`
        * Here the denominator is understood to be `10**num_digits_after_decimal_pt`.
        * For example: 2.5/ is the same as 2.5/10.  2.54/ is the same as 2.54/100, etc.
  1. real
    * These are approximate numbers.  This uses the standard notation for floating point numbers.
  1. string
    * These are utf-8 encoded.
    * No quoting is required.
    * Standard Python escapes are supported.

### XML Format ###

The XML Format for atomic questions is:

```
<question>
    <name>python name</name>
    <label>user name</label>
    <type>bool|number|int|rational|real|string</type>
    <min>int</min>                <!-- optional -->
    <max>int|infinite</max>       <!-- optional -->
    <orderable>True</orderable>   <!-- optional -->
    <validation>                  <!-- optional -->
        <validator type="regex" value="expression" flags="re_compile_flags_as_int" />
        <validatar type="range" minvalue="0" maxvalue="1024" />
    </validation>
</question>
```

## Molecules ##

Molecules are groups of other questions (either atoms and/or other molecules).  Here, the other subordinate questions are indicated by Q1, Q2, etc.

  1. series `Q1, Q2, ...`: represents a series of questions that must be asked.
  1. choice `Tag1: [Q1], Tag2: [Q2], ...`: means that the user picks one of the tags and then answers the associated question (if any).
    * If none of the tags have questions, this is like an C **enum**.
    * This may be set up as either single selection or multiple selection.  But if multiple selection, each tag may only be specified at most once.

### XML Format ###

A series is represented as:

```
<questions>
    <name>series-name</name>
    <label>My Series</label>
    <min>int</min>                <!-- optional -->
    <max>int|infinite</max>       <!-- optional -->
    <orderable>True</orderable>   <!-- optional -->
    <question> ... </question> ...
</questions>
```

A choice is represented as:

```
<question>
    <name>on-is</name>
    <label>On is represented as</label>
    <type>choice|multichoice</type>
    <default>1</default>          <!-- optional -->
    <min>int</min>                <!-- optional -->
    <max>int|infinite</max>       <!-- optional -->
    <orderable>True</orderable>   <!-- optional -->
    <options>
        <option name="HIGH" value="1">
            <questions>
                <question> ... </question> ...
            </questions>
        </option>
        <option name="LOW" value="0" />
    </options>
 </question>

```

# Answer #

Answers to questions are represented in Python as follows.

## Atoms ##

  1. bool -- using a Python bool.
  1. int -- using a Python int.
  1. rational -- using a Python Fraction (from the [fractions](http://docs.python.org/library/fractions.html) module in the standard library).
  1. real -- using our own number class.
  1. string -- using a Python str.

## Molecules ##

  1. optional -- using `None` if unanswered, otherwise the undecorated answer to the subordinate question.  (`None` is not otherwise a valid value for an answer).
  1. repeat -- using a dict if it has a key and the order doesn't matter, otherwise a tuple.
  1. series -- using an instance of `object` with the subordinate answers stored as attributes under the tag names.
  1. choice
    * if the tag is a number, it is encoded as a number; otherwise as a str.
    * for single selection choices:
      * if the chosen choice has no subordinate answer, then just the tag value.
      * otherwise: the tuple (tag, subordinate\_answer)
    * for multiple selection choices:
      * if none of the possible choices have subordinate questions:
        * if all tags are integers between 0 and 15, use a int with the tags stored as a bit map.
        * otherwise, use a frozenset of tags.
      * otherwise, use a dict with the tags as keys and subordinate answers as values.  Individual tags that don't have subordinate questions have `None` as their value.

### XML Format ###

#### Atomic Answers ####

The XML format for atomic answers is:

```
<answer name="pin-number" type="bool|number|int|rational|real|string" value="2" />
```

If the answer is repeatable, then there may be several of these with the same _name_, and each will have a _repeated="True"_ attribute.

```
<answer name="pin-number" type="bool|number|int|rational|real|string" value="3" repeated="True" />
```

If the answer is optional and not specified, the _type_ and _value_ attributes are omitted.

```
<answer name="pin-number" />
```

The _repeated_ attribute is still required if more than one answer is allowed:

```
<answer name="pin-number" repeated="True" />
```

#### Molecule Answers ####

The answer for a series is:

```
<answers name="series-name" repeated="True|False">
    <answer ...> ... </answer> ...
</answers>
```

While the answer for a choice is:

```
<answer name="on-is" type="choice|multichoice" repeated="True|False">
    <options>
        <option value="1">
            <answers>
                <answer ...> ... </answer> ...
            </answers>
        </option>
        <option value="2" />
    </options>
</answer>
```