import numpy as np

# DSDp Triplexer data from 2015/06/16
frequencies = ['350']
pixels = ['DsDp']
wafers = ['BW1_8']
dies = ['5_4']
dates = ['2015_06_10']
selector = [1]

selector = np.asarray(selector, dtype=bool)

dies = np.asarray(dies)[selector]
dates = np.asarray(dates)[selector]
pixels = np.asarray(pixels)[selector]
frequencies = np.asarray(frequencies)[selector]
