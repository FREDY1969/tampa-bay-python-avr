# blinky2_a.tst

Test the blinky2 example:

>>> import examples

>>> test1 = examples.test_compile('blinky2', True)
>>> test1 == examples.target_blinky2 or test1 == examples.target_blinky2_alt
True
