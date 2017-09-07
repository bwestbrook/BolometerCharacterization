import numpy as np
# Hyrbrid Triplexer data from 2015/07/13

# All band in all pixels
frequency_list = [['40', '60', '90'],
                  ['90', '150', '220', '280'],
                  ['220', '280', '350']]

wafer_list = [['BW1_8', 'BW1_8', 'BW1_8'],
              ['BW1_8', 'BW1_8', 'BW1_8', 'BW1_8'],
              ['BW1_8', 'BW1_8', 'BW1_8']]


pixel_list = [['LF_Triplexer', 'LF_Triplexer', 'LF_Triplexer'],
              ['Tetraplexer', 'Tetraplexer', 'Tetraplexer', 'Tetraplexer'],
              ['HF_Triplexer', 'HF_Triplexer', 'HF_Triplexer']]

date_list = [['2015_07_13', '2015_07_13', '2015_07_13'],
             ['2015_06_30', '2015_06_30', '2015_06_30', '2015_06_30'],
             ['2015_07_10', '2015_07_10', '2015_07_10']]

die_list = [['3_6', '3_6', '3_6'],
            ['2_5', '2_5', '2_5', '2_5'],
            ['3_6', '3_6', '3_6']]

selector = np.asarray([[0, 0, 0],
                       [1, 0, 1]])

#For Co-plotting back to back runs of same frequency

# All band in all pixels
frequency_list = [['40', '60', '90'],
                  ['40', '60', '90']]

wafer_list = [['BW1_8', 'BW1_8', 'BW1_8'],
              ['BW1_8', 'BW1_8', 'BW1_8']]


pixel_list = [['LF_Triplexer', 'LF_Triplexer', 'LF_Triplexer'],
              ['LF_Triplexer', 'LF_Triplexer', 'LF_Triplexer']]

date_list = [['2015_07_13', '2015_07_13', '2015_07_13'],
             ['2016_01_18', '2016_01_18', '2016_01_18']]

die_list = [['3_6', '3_6', '3_6'],
            ['3_6', '3_6', '3_6']]

selector = np.asarray([[1, 1, 1],
                       [1, 1, 1]])

#Using this selector we created a well ordered set of lists

frequencies, pixels, dies, wafers, dates = [], [], [], [], []

pos_for_40 = 38
pos_for_60 = 58
pos_for_90 = 86
pos_for_150 = 133
pos_for_220 = 193
pos_for_280 = 248
pos_for_350 = 308


for i, selection_row in enumerate(selector):
    selection_row = np.asarray(selection_row, dtype=bool)
    frequencies.extend(np.asarray(frequency_list[i])[selection_row])
    dies.extend(np.asarray(die_list[i])[selection_row])
    wafers.extend(np.asarray(wafer_list[i])[selection_row])
    dates.extend(np.asarray(date_list[i])[selection_row])
    pixels.extend(np.asarray(pixel_list[i])[selection_row])
