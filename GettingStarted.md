## Groups/Administrative ##

  * If you haven't already, join [TamPyBay](http://groups.google.com/group/tampybay) google group.  This is just for general Python stuff.
  * Join the [Tampa Bay Python AVR](http://groups.google.com/group/tampa-bay-python-avr) google group.  This is for discussion on the compiler project.
  * Join the [tampa-bay-python-avr](http://code.google.com/p/tampa-bay-python-avr/) google code project.  You will need to request membership permission to push changesets to the main repository.  Send an email to [tampa-bay-python-avr@googlegroups.com](mailto:tampa-bay-python-avr@googlegroups.com) if you would like membership.  Note: You can clone the repo and look at the wiki without being a member.

## System Setup ##

  1. Get Python 3.1 or later on whatever box you want to run it on (real or virtual).  The compiler is targeted for Linux/Mac/Windows.
  1. Install [mercurial](http://mercurial.selenic.com/) (this does NOT need to be on Python 3).  You need to create a ~/.hgrc file with your username in it.  If you decide to do this on Windows, also read WindowsUsers1 (important!).
```
[ui]
username = Bruce Frederiksen <your.email@someplace.com>
```
  1. Install [doctest-tools](http://code.google.com/p/doctest-tools/) from google code.  I don't think that [pip](http://pypi.python.org/pypi/pip/0.6.3)  works yet on Python 3, but [easy\_install](http://pypi.python.org/pypi/setuptools/0.6c11) does if you install the [distribute](http://pypi.python.org/pypi/distribute/) package.  You need version 1.0a3 or later of doctest-tools.  Make sure you use the python3 version of easy\_install, e.g.:
```
$ easy_install-3.1 doctest-tools
```
  1. Install the [bottle](http://pypi.python.org/pypi/bottle) web framework and [mako](http://pypi.python.org/pypi/) html templates.  You can use easy\_install for these too.
  1. If you want to load the programs you compile into an arduino (even if not your own), install the [arduino software](http://arduino.cc/en/Main/Software).  We only need the avrdude program, which you might be able to get by itself without the rest of the arduino baggage (if you want to play and explore that option for us)?

## Reference ##

  * Download the [ATmega328P datasheet](http://atmel.com/dyn/resources/prod_documents/doc8271.pdf) for future reference (it's a pdf file).  It's over 500 pages.  If that's intimidating, go [here](https://docs.google.com/Doc?docid=0AcS32tQHvYDrZGdmdGI3OGpfMTZrMnBjbTZkeg&hl=en) for a roadmap that will guide you with what parts are important and what parts can be skipped (which is most of the document!).  If you're not so interested in the hardware, you probably won't need this very much, but it still might be good to have it just in case...
  * Download the [AVR Instruction Set](http://www.atmel.com/atmel/acrobat/doc0856.pdf) manual (another pdf).  Again for future reference, just in case.

## Project Setup ##

  1. Create a directory where you'll keep the compiler source code.  Call it whatever you like.
```
$ mkdir avr_compiler
$ cd avr_compiler
```
  1. I strongly suggest (at least) two clones in this directory.  The first is just a copy of the repo from google.  You will **never** do work directly in this clone.  We generally call this "google", but you can call it what you want:
```
$ hg clone -U https://tampa-bay-python-avr.googlecode.com/hg/ google
```
  1. The second clone is where you do your work.  Many people call this one "working", but again, call it what you want:
```
$ hg clone google working
```
  1. Create the machine database (this is a static database that describes the AVR processor).
```
$ cd working
$ scripts/make_machine_db.py avr atmega328p
```
  1. Take a look at our (still unfinished) IDE:
```
$ scripts/bottle.py
```
  1. There are three examples.  Washer is the largest.  It was the first, and only serves as example code without intending to ever actually be used.  Blinky is a simple program written in AVR assembler to blink an LED.  Blinky2 is another version written in our high-level language.  You can compile and run both of these.
    1. To compile blinky:
```
$ scripts/compile.py examples/blinky
```
    1. To peek at the flash.hex file that it generated (which is what avrdude loads into the Arduino):
```
$ scripts/peek.py examples/blinky/flash.hex
```
    1. To load the flash.hex file onto the Arduino (and run it):
```
$ scripts/load.py examples/blinky
```
  1. Finally, run the unit test suite (just to see how it works too) and sound off if it doesn't work!  (The testall\_31.py program comes with the doctest-tools package):
```
$ testall_31.py
```