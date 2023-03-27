
import os
import pandas as pd
import pylab as pl
import numpy as np
import json
from pprint import pprint
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import *
from bd_lib.mpl_canvas import MplCanvas
from GuiBuilder.gui_builder import GuiBuilder, GenericClass
# Import Last

class WaferYield(QtWidgets.QWidget, GuiBuilder):
    '''
    '''

    def __init__(self, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(WaferYield, self).__init__()
        self.hi = 'hi'
        self.status_bar = status_bar
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.so_map_path = os.path.join('bd_histogram_data', 'LF_UFM_map.csv')
        self.so_resistance_key_path = os.path.join('bd_histogram_data', 'so_resistance_key_path.json')
        self.map_path_dict = {'SO': self.so_map_path}
        self.map_path = self.map_path_dict['SO']
        self.display_radius = 5.0 #mm
        self.dl_lf_pixel_avg_resistance_dict = {
            '1': 40.934000000000005,
            '10': 27.212666666666664,
            '11': 28.66916666666667,
            '12': 30.5415,
            '13': 34.144,
            '14': 29.392000000000007,
            '15': 27.188833333333335,
            '16': 23.858333333333334,
            '17': 21.90583333333333,
            '18': 23.9525,
            '19': 24.03575,
            '2': 35.1275,
            '20': 20.583333333333332,
            '21': 22.7705,
            '22': 25.38,
            '23': 18.70866666666667,
            '24': 17.346,
            '25': 18.61,
            '26': 16.7666,
            '27': 17.582333333333334,
            '28': 18.505666666666666,
            '29': 14.16475,
            '3': 40.501666666666665,
            '30': 12.027750000000001,
            '31': 11.471666666666666,
            '32': 12.415,
            '33': 15.15,
            '34': 8.793,
            '35': 8.334333333333335,
            '36': 9.057199999999998,
            '37': 9.6685,
            '4': 40.90375,
            '5': 33.958333333333336,
            '6': 35.57450000000001,
            '7': 33.5825,
            '8': 35.775,
            '9': 33.533}
        self.intra_pixel_resistance_dict = {
                '30B': 11.0,
                '30D': 8.5,
                '30T': 6.2,
                '40B': 4.5,
                '40D': 2.1,
                '40T': 0.0
            }
        self.intra_pixel_offsets = {
                '30B': (0.5 *np.sqrt(2), -0.5 *np.sqrt(2)),
                '30D': (0.5 *np.sqrt(2), 0.5 *np.sqrt(2)),
                '30T': (0, 1),
                '40B': (-0.5 *np.sqrt(2), 0.5 *np.sqrt(2)),
                '40D': (-0.5 *np.sqrt(2), -0.5 *np.sqrt(2)),
                '40T': (0, -1)
                }
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.wy_input_panel()

    def wy_set_df(self):
        '''
        '''
        wafer_type = self.wafer_type_combobox.currentText()
        self.map_path = self.map_path_dict[wafer_type]
        self.map_df = pd.read_csv(self.map_path)

    def wy_input_panel(self):
        '''
        '''
        self.wafer_type_combobox = self.gb_make_labeled_combobox(label_text='Wafer Type:')
        self.layout().addWidget(self.wafer_type_combobox, 0, 0, 1, 1)
        for wafer_type in self.map_path_dict:
            self.wafer_type_combobox.addItem(wafer_type)
        self.wafer_type_combobox.currentIndexChanged.connect(self.wy_set_df)
        self.wy_set_df()
        self.load_data_pushbutton = QtWidgets.QPushButton('Load')
        self.layout().addWidget(self.load_data_pushbutton, 0, 1, 1, 1)
        self.load_data_pushbutton.clicked.connect(self.wy_load)
        self.wafer_name_lineedit = self.gb_make_labeled_lineedit(label_text='Wafer Name')
        self.layout().addWidget(self.wafer_name_lineedit, 2, 0, 1, 1)
        self.replot_pushbutton = QtWidgets.QPushButton('Replot')
        self.replot_pushbutton.clicked.connect(self.wy_plot)
        self.layout().addWidget(self.replot_pushbutton, 2, 1, 1, 1)
        self.plot_label = QtWidgets.QLabel()
        self.layout().addWidget(self.plot_label, 3, 0, 1, 1)

    def wy_load(self):
        '''
        '''

        file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
        basename = os.path.basename(file_path)
        self.wafer_name_lineedit.setText(basename.split(' ')[0])
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r') as fh:
            self.df = pd.read_csv(file_path)
        self.wy_plot()
        #import ipdb;ipdb.set_trace()

    def check_bolo(self):
        '''
        '''
        with open(self.so_resistance_key_path, 'r') as fh:
            resistance_key_dict = json.load(fh)

    def wy_plot(self):
        '''
        '''
        all_xs = []
        all_ys = []
        all_resistances = []
        fig = pl.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        ax.set_aspect('equal')
        all_pixel_resistance_dict = {}
        all_pixel_resistance_small_dict = {}
        pixel_resistance_dict = {}
        info_dict = {}
        pixel_resistances = []
        intra_pixel_resistances = []
        for i in self.df.index:#[0:6]:
            x_center = self.map_df['x_mm'][i]
            y_center = self.map_df['y_mm'][i]
            tes_id = self.map_df['tes_id'][i]
            pixel = self.map_df['pixel'][i]
            resistance = self.df['R (kohms)'][i]
            info_dict[tes_id] = resistance
            x = x_center + self.intra_pixel_offsets[tes_id][0] * self.display_radius
            y = y_center + self.intra_pixel_offsets[tes_id][1] * self.display_radius
            if i % 6 == 0 and i > 0:
                prev_pixel = self.map_df['pixel'][i - 6]
                x_pos = x_center - 0.15 * self.display_radius
                y_pos = y_center - 0.15 * self.display_radius
                ax.text(x_pos, y_pos, 'P{0}'.format(pixel))
                info_dict.update({
                        'values': pixel_resistances,
                        'mean': np.mean(pixel_resistances),
                        'std': np.std(pixel_resistances)
                        })
                if len(pixel_resistances) == 6:
                    intra_pixel_resistance = np.asarray(pixel_resistances) - np.min(pixel_resistances)
                    intra_pixel_resistances.append(intra_pixel_resistance)
                all_pixel_resistance_dict[str(prev_pixel)] = info_dict
                all_pixel_resistance_small_dict[str(prev_pixel)] = info_dict['mean']
                self.wy_analyze_pixel(prev_pixel, pixel_resistances, info_dict)
                pixel_resistances = []
                info_dict = {}
            if resistance in ['open', 'Open']:
                resistance = 80
                label = None
                handles, labels = ax.get_legend_handles_labels()
                if "Open" not in labels:
                    label = "Open"
                ax.plot(x, y, 'o', ms=3, color='k', label=label)
            else:
                all_xs.append(x)
                all_ys.append(y)
                all_resistances.append(float(resistance))
                pixel_resistances.append(float(resistance))
            x_pos = x_center - 0.2 * self.display_radius
            y_pos = y_center - 0.2 * self.display_radius
            ax.text(x, y, '{0}'.format(tes_id), fontsize=6)
        #pprint(resistance_key_dict)
        intra_pixel_resistances = np.asarray(intra_pixel_resistances)
        pprint(all_pixel_resistance_small_dict)
        for i in range(6):
            intra_pixel_value = intra_pixel_resistances.T[i][np.abs(intra_pixel_resistances.T[i] - np.mean(intra_pixel_resistances.T[i])) < 1]
            #print(i, np.mean(intra_pixel_value))
        #import ipdb;ipdb.set_trace()
        cm = ax.scatter(np.asarray(all_xs), np.asarray(all_ys), s=100, c=np.asarray(all_resistances), cmap='jet')
        wafer_name = self.wafer_name_lineedit.text()
        ax.set_title('Resistance Heat Map for {0}'.format(wafer_name))
        ax.set_xlabel('X Pos (mm)')
        ax.set_ylabel('Y Pos (mm)')
        pl.legend()
        pl.colorbar(cm, label='Resitance (k$\Omega$)')
        pl.show()

    def wy_analyze_pixel(self, pixel, pixel_resistances, info_dict):
        '''
        '''
        nominal_average_resistance = self.dl_lf_pixel_avg_resistance_dict[str(pixel)]
        base_pixel_resistance = nominal_average_resistance - np.mean(list(self.intra_pixel_resistance_dict.values()))
        average_resistance = info_dict['mean']
        mean_deviation = np.abs(nominal_average_resistance - average_resistance)
        print()
        print(pixel, base_pixel_resistance)
        print(pixel, 'avg dev', mean_deviation)
        base_pixel_resistances = []
        for tes_id in self.intra_pixel_resistance_dict:
            expected_resistance = float(base_pixel_resistance) + float(self.intra_pixel_resistance_dict[tes_id])
            if info_dict[tes_id] in ['open', 'Open']:
                bolo_deviation = np.nan
            else:
                actual_resistance = float(info_dict[tes_id])
                bolo_deviation = actual_resistance - expected_resistance
            print(tes_id, bolo_deviation)
        #import ipdb;ipdb.set_trace()

if __name__ == '__main__':
    soy = SOYield()
