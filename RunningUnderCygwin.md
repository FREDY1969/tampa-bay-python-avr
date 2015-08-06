#Quickstart guide for running the project under Cygwin

# Fresh Install of Cywgin #

Install the following Cygwin Packages:

All -> Database -> Sqlite3

All -> Python -> python (version 2.5.2-1 at time of writing)

# Install Python Pmw package #
The package is available here:

http://sourceforge.net/projects/pmw/files/Pmw/Pmw.1.3.2/Pmw.1.3.2.tar.gz/download

# Copy it to Cygwin dir: /home/Dan/PyAVR/Pmw

# In Windows explorer (for me) this is: C:\cygwin\home\Dan\PyAVR\Pmw

```
$ gunzip Pmw.1.3.2.tar.gz
$ tar -xf Pmw.1.3.2.tar
$ cd Pmw.1.3.2/src
Dan@moe ~/PyAVR/Pmw/Pmw.1.3.2/src
$ python setup.py install
```

# Use Mercurial (Hg) to check out the code from Google Code #
```
Dan@moe ~
$ mkdir PyAVR
$ cd PyAVR

Dan@moe ~
$ hg clone https://tampa-bay-python-avr.googlecode.com/hg/ shared-code
requesting all changes
adding changesets
adding manifests
adding file changes
added 93 changesets with 523 changes to 256 files
updating working directory
112 files updated, 0 files merged, 0 files removed, 0 files unresolved

Dan@moe ~
hg clone https://tampa-bay-python-avr.googlecode.com/hg/ working-code

$ cd working-code

$ db_update/create_db examples/washer

$ python ucc/gui/tk_gui.py examples/washer
```
et voila!
