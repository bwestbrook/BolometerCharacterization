import numpy as np

frequencies = ['40', '60', '90']
pixels = ['LF_Triplexer', 'LF_Triplexer', 'LF_Triplexer']




# LF Triplexer data from 2015/07/13
wafers = ['BW1_8', 'BW1_8', 'BW1_8', 'BW1_8']
dies = ['3_6', '3_6', '3_6']
dates = ['2016_01_18', '2016_01_18', '2016_01_18']

# LF Triplexer data from 2015/07/13
wafers = ['BW1_8', 'BW1_8', 'BW1_8', 'BW1_8']
dies = ['3_6', '3_6', '3_6']
dates = ['2015_07_13', '2015_07_13', '2015_07_13']

selector = [1, 1, 1]
selector = np.asarray(selector, dtype=bool)

dies = np.asarray(dies)[selector]
dates = np.asarray(dates)[selector]
pixels = np.asarray(pixels)[selector]
wafers = np.asarray(wafers)[selector]
frequencies = np.asarray(frequencies)[selector]
