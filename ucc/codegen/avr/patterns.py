# avr_patterns.py

patterns = [

    ['+', [True, 0, 63, None],   [],
      [[None, False, True], ['immed_word', True, False]],
      [['ADIW', '{right}', '{left_const}'],
      ]],

    ['+', [], [True, 0, 63, None],
      [['immed_word', True, False], [None, False, True]],
      [['ADIW', '{left}', '{right_const}'],
      ]],

    ['+', [True],   [],
      [[None, False, True], ['immed', True, False]],
      [['SUBI', 'lo_reg({right})', 'lo(-{left_const})'],
       ['SBCI', 'hi_reg({right})', 'hi(-{left_const})'],
      ]],

    ['+', [], [True],
      [['immed', True, False], [None, False, True]],
      [['SUBI', 'lo_reg({left})', 'lo(-{right_const})'],
       ['SBCI', 'hi_reg({left})', 'hi(-{right_const})'],
      ]],

    ['+', [False, None, None, False], [False],
      [['pair', True, False], ['pair', False, False]],
      [['ADD', 'lo_reg({left})', 'lo_reg({right})'],
       ['ADC', 'hi_reg({left})', 'hi_reg({right})'],
      ]],

    ['+', [False, None, None, True], [False],
      [['pair', False, False], ['pair', True, False]],
      [['ADD', 'lo_reg({right})', 'lo_reg({left})'],
       ['ADC', 'hi_reg({right})', 'hi_reg({left})'],
      ]],

]
