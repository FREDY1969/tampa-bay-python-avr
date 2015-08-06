The Python import mechanism is probably Python's weakest feature.  By adopting the following practices, we should avoid trouble down the road.

## PYTHONPATH ##

Because we want to allow programmers to work with several hg clones of the project, we should **not** set the `PYTHONPATH` env variable (or set up a `.pth` file) to tell Python where our code lives.

Instead, I've created a `setpath.py` module in `ucc/gui` that will automatically add the proper directory to the Python path each time the program is run.

All that needs to done is `import setpath` before any other ucc modules.  This needs to be done only **once** by the top-level gui module.  It should _not_ be imported by any other module.

This will allow us to switch back and forth between different hg clones and run the program without confusing Python about what directory to import the modules from each time.

## How to import modules ##

In order to avoid importing the same module twice by two different paths (which causes _really_ strange errors), we should always use a full path on our imports:

> `from ucc.gui import foobar`

rather than just:

> `import foobar`

even if the module importing foobar is in the ucc/gui directory itself.

## Executable Python Programs ##

The mechanism to set the path properly for executable programs that need to import ucc modules is to place the following two lines before any ucc imports:

```
>>> import setpath
>>> setpath.setpath(__file__)
```