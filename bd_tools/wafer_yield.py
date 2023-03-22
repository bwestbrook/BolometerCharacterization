
import os
import pandas as pd
import pylab as pl
import numpy as np
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
        self.map_path_dict = {'SO': self.so_map_path}
        self.map_path = self.map_path_dict['SO']
        self.display_radius = 5.0 #mm
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
        self.plot_label = QtWidgets.QLabel()
        self.layout().addWidget(self.plot_label, 2, 0, 1, 1)

    def wy_load(self):
        '''
        '''

        file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r') as fh:
            df = pd.read_csv(file_path)
        #import ipdb;ipdb.set_trace()
        all_xs = []
        all_ys = []
        all_resistances = []
        fig = pl.figure()
        ax = fig.add_subplot(111)
        for i in df.index:#[0:6]:
            x_center = self.map_df['x_mm'][i]
            y_center = self.map_df['y_mm'][i]
            tes_id = self.map_df['tes_id'][i]
            pixel = self.map_df['pixel'][i]
            resistance = df['R (kohms)'][i]
            x = x_center + self.intra_pixel_offsets[tes_id][0] * self.display_radius
            y = y_center + self.intra_pixel_offsets[tes_id][1] * self.display_radius
            if resistance == 'open':
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
            if i % 6 == 0:
                #print(pixel, tes_id, x_center, y_center, x, y)
                x_pos = x_center - 0.15 * self.display_radius
                y_pos = y_center - 0.15 * self.display_radius
                ax.text(x_pos, y_pos, 'P{0}'.format(pixel))
                #ax.plot(x_center, y_center, 'o', ms=16, color='k', alpha=0.3)
            x_pos = x_center - 0.2 * self.display_radius
            y_pos = y_center - 0.2 * self.display_radius
            ax.text(x, y, '{0}'.format(tes_id), fontsize=6)
        #import ipdb;ipdb.set_trace()
        cm = ax.scatter(np.asarray(all_xs), np.asarray(all_ys), s=100, c=np.asarray(all_resistances), cmap='jet')
        ax.set_xlabel('X Pos (mm)')
        ax.set_ylabel('Y Pos (mm)')
        ax.set_title('Resistance Heat Map for DL-LF-r1-005E')
        pl.legend()
        pl.colorbar(cm, label='Resitance (k$\Omega$)')
        pl.show()


if __name__ == '__main__':
    soy = SOYield()
