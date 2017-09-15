import numpy as np

frequencies = ['90', '150', '220', '280']
pixels = ['Tetraplexer', 'Tetraplexer', 'Tetraplexer', 'Tetraplexer']

# Tetraplexer data from 2015/06/16 150/220 Only
# PLUS
# Tetraplexer data from 2015/06/16

dies = ['3_5', '3_5', '3_5', '3_5']
wafers = ['BW1_8', 'BW1_8', 'BW1_8', 'BW1_8']
dates = ['2015_06_16', '2015_06_16', '2015_06_16']

# Tetraplexer data from 2015/06/30
wafers = ['BW1_8', 'BW1_8', 'BW1_8', 'BW1_8']
dies = ['2_5', '2_5', '2_5', '2_5']
dates = ['2015_06_30', '2015_06_30', '2015_06_30', '2015_06_30']

selector = [1, 1, 1, 1]
selector = np.asarray(selector, dtype=bool)
dies = np.asarray(dies)[selector]
dates = np.asarray(dates)[selector]
pixels = np.asarray(pixels)[selector]
wafers = np.asarray(wafers)[selector]
frequencies = np.asarray(frequencies)[selector]
