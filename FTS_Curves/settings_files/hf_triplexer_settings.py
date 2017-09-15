import numpy as np

frequencies = ['220', '280', '350']
pixels = ['HF_Triplexer', 'HF_Triplexer', 'HF_Triplexer']
wafers = ['BW1_8', 'BW1_8', 'BW1_8']



# HF Triplexer data from 2015/05/27
dies = ['5_4', '5_4', '5_4']
dates = ['2015_05_27', '2015_05_27', '2015_05_27']

# HF Triplexer data from 2015/07/10
dies = ['3_6', '3_6', '3_6']
dies = ['5_4', '5_4', '5_4']
dates = ['2015_07_10', '2015_07_10', '2015_07_10']

selector = [1, 1, 1]
selector = np.asarray(selector, dtype=bool)

dies = np.asarray(dies)[selector]
dates = np.asarray(dates)[selector]
pixels = np.asarray(pixels)[selector]
wafers = np.asarray(wafers)[selector]
frequencies = np.asarray(frequencies)[selector]

pos_for_40 = 35
pos_for_60 = 50
pos_for_90 = 82
pos_for_150 = 123
pos_for_220 = 190
pos_for_280 = 245
pos_for_350 = 308
