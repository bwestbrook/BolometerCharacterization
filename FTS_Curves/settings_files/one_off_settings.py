import numpy as np

# DSDp Triplexer data from 2015/06/16
frequencies = ['150']
pixels = ['PB2']
dies = ['Corner']
wafers = ['AS7-20']
dates = ['2016_03_25']
selector = [1]

selector = np.asarray(selector, dtype=bool)

dies = np.asarray(dies)[selector]
dates = np.asarray(dates)[selector]
pixels = np.asarray(pixels)[selector]
frequencies = np.asarray(frequencies)[selector]
