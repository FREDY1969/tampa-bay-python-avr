# blinky2_b.tst

Test the blinky2 example:

>>> import examples

>>> test2 = examples.test_compile('blinky2', False)
>>> test2 == examples.target_blinky2 or test2 == examples.target_blinky2_alt
True
