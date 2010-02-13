# task.py

r'''A task may be suspended.

This includes coroutines_ and `green threads`_.

A task (unlike a `function`) may call other tasks.

Both tasks and functions may call other functions.

.. _coroutines: http://en.wikipedia.org/wiki/Coroutine
.. _green threads: http://en.wikipedia.org/wiki/Green_thread
'''

from ucclib.built_in import declaration

class task(declaration.high_level_word):
    pass

