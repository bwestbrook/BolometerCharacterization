import time
import os
import simplejson
import pylab as pl
import numpy as np
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class CosmicRays(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(CosmicRays, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = available_daqs
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = './Data/{0}'.format(self.today_str)
        self.cr_daq_panel()
        self.cr_display_daq_settings()

    def cr_daq_panel(self):
        '''
        '''
        daq_header_label = QtWidgets.QLabel('DAQ Device:', self)
        self.layout().addWidget(daq_header_label, 0, 0, 1, 1)
        self.device_combobox = QtWidgets.QComboBox(self)
        for device in self.daq_settings:
            self.device_combobox.addItem(device)
        self.layout().addWidget(self.device_combobox, 0, 1, 1, 1)
        daq_1_header_label = QtWidgets.QLabel('DAQ Ch 1 Data:', self)
        self.layout().addWidget(daq_1_header_label, 1, 0, 1, 1)
        self.daq_1_combobox = QtWidgets.QComboBox(self)
        for daq in range(0, 4):
            self.daq_1_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_1_combobox, 1, 1, 1, 1)
        daq_1_header_label = QtWidgets.QLabel('DAQ Ch 1 Data:', self)
        self.layout().addWidget(daq_1_header_label, 1, 2, 1, 1)
        self.daq_2_combobox = QtWidgets.QComboBox(self)
        for daq in range(0, 4):
            self.daq_2_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_2_combobox, 1, 3, 1, 1)
        # Chan 1
        self.channel_1_settings_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.channel_1_settings_label, 2, 0, 1, 2)
        # Chan 2
        self.channel_2_settings_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.channel_2_settings_label, 2, 2, 1, 2)
        # Sample Name
        sample_name_header_label = QtWidgets.QLabel('Sample Name:', self)
        self.layout().addWidget(sample_name_header_label, 3, 0, 1, 1)
        self.sample_name_lineedit = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.sample_name_lineedit, 3, 1, 1, 3)
        # Plot and Data Panel
        self.running_plot_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.running_plot_label, 4, 0, 1, 4)
        mean_1_header_label = QtWidgets.QLabel('Mean Ch 1:', self)
        self.layout().addWidget(mean_1_header_label, 5, 0, 1, 1)
        self.mean_1_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.mean_1_label, 5, 1, 1, 1)
        std_1_header_label = QtWidgets.QLabel('STD Ch 1:', self)
        self.layout().addWidget(std_1_header_label, 5, 2, 1, 1)
        self.std_1_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.std_1_label, 5, 3, 1, 1)
        mean_2_header_label = QtWidgets.QLabel('Mean Ch 2:', self)
        self.layout().addWidget(mean_2_header_label, 6, 0, 1, 1)
        self.mean_2_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.mean_2_label, 6, 1, 1, 1)
        std_2_header_label = QtWidgets.QLabel('STD Ch 2:', self)
        self.layout().addWidget(std_2_header_label, 6, 2, 1, 1)
        self.std_2_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.std_2_label, 6, 3, 1, 1)
        # Buttons
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        start_pushbutton.clicked.connect(self.cr_start_stop)
        self.layout().addWidget(start_pushbutton, 7, 0, 1, 4)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        save_pushbutton.clicked.connect(self.cr_save)
        self.layout().addWidget(save_pushbutton, 8, 0, 1, 4)
        # Connect to functions after placing widgets
        self.daq_1_combobox.activated.connect(self.cr_display_daq_settings)
        self.daq_2_combobox.activated.connect(self.cr_display_daq_settings)
        self.device_combobox.activated.connect(self.cr_display_daq_settings)

    def cr_update_daq(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'daq_settings.json'), 'r') as json_handle:
            self.daq_settings = simplejson.load(json_handle)

    def cr_display_daq_settings(self):
        '''
        '''
        self.cr_update_daq()
        self.device = self.device_combobox.currentText()
        self.channel_1 = self.daq_1_combobox.currentIndex()
        self.channel_2 = self.daq_2_combobox.currentIndex()
        self.int_time_1 = self.daq_settings[self.device][str(self.channel_1)]['int_time']
        self.int_time_2 = self.daq_settings[self.device][str(self.channel_1)]['int_time']
        self.sample_rate_1 = self.daq_settings[self.device][str(self.channel_1)]['sample_rate']
        self.sample_rate_2 = self.daq_settings[self.device][str(self.channel_1)]['sample_rate']
        info_str_1 = 'Sample Rate (Hz): {0} :::: '.format(self.sample_rate_1)
        info_str_1 += 'Int Time (ms): {0}'.format(self.int_time_1)
        info_str_2 = 'Sample Rate (Hz): {0} ::: '.format(self.sample_rate_2)
        info_str_2 += 'Int Time (ms): {0}'.format(self.int_time_2)
        self.channel_1_settings_label.setText(info_str_1)
        self.channel_2_settings_label.setText(info_str_2)

    ###########
    # Running
    ###########

    def cr_start_stop(self):
        '''
        '''
        if 'Start' in self.sender().text():
            self.sender().setText('Stop')
            self.started = True
            self.cr_collecter()
        else:
            self.sender().setText('Start')
            self.started = False

    def cr_collecter(self):
        '''
        '''
        device = self.device_combobox.currentText()
        self.data_1, self.stds_1 = [], []
        self.data_2, self.stds_2 = [], []
        while self.started:
            ts_1, mean_1, min_1, max_1, std_1 = self.daq.get_data(signal_channel=self.channel_1,
                                                                  int_time=self.int_time_1,
                                                                  sample_rate=self.sample_rate_1,
                                                                  device=device)
            ts_2, mean_2, min_2, max_2, std_2 = self.daq.get_data(signal_channel=self.channel_2,
                                                                  int_time=self.int_time_2,
                                                                  sample_rate=self.sample_rate_2,
                                                                  device=device)
            self.mean_1_label.setText('{0:.5f}'.format(mean_1))
            self.std_1_label.setText('{0:.5f}'.format(std_1))
            self.mean_2_label.setText('{0:.5f}'.format(mean_2))
            self.std_2_label.setText('{0:.5f}'.format(std_2))
            self.data_1.extend(ts_1)
            self.stds_1.append(std_1)
            self.data_2.extend(ts_2)
            self.stds_2.append(std_2)
            self.cr_plot(running=True)
            QtWidgets.QApplication.processEvents()
            self.repaint()

    def cr_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}.txt'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def cr_save(self):
        '''
        '''
        save_path = self.cr_index_file_name()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter=',*.txt,*.dat')[0]
        if len(save_path) > 0:
            with open(save_path, 'w') as save_handle:
                for i, data_1 in enumerate(self.data_1):
                    line = '{0:.5f}, {1:.5f}\n'.format(self.data_1[i], self.data_2[i])
                    save_handle.write(line)
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')
        self.cr_plot()

    def cr_plot(self, running=False):
        '''
        '''
        fig, ax1, ax2 = self.cr_create_blank_fig(frac_screen_width=0.75, frac_screen_height=0.5,
                                                 left=0.12, right=0.98, top=0.9, bottom=0.13, aspect=None)
        #ax1.errorbar(range(len(self.data_1)), self.data_1, yerr=self.stds_1, marker='.', linestyle='-')
        #ax2.errorbar(range(len(self.data_2)), self.data_2, yerr=self.stds_2, marker='.', linestyle='-')
        ax1.plot(self.data_1)
        ax2.plot(self.data_2)
        if running:
            temp_png_path = os.path.join('temp_files', 'temp_cr.png')
            fig.savefig(temp_png_path)
            image_to_display = QtGui.QPixmap(temp_png_path)
            self.running_plot_label.setPixmap(image_to_display)
            os.remove(temp_png_path)
        else:
            title, okPressed = self.gb_quick_info_gather(title='Plot Title', dialog='What is the title of this plot?')
            ax1.set_title(title)
            pl.show()

    def cr_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.8,
                             left=0.13, right=0.98, top=0.95, bottom=0.08, n_axes=2,
                             aspect=None):
        if frac_screen_width is None and frac_screen_height is None:
            fig = pl.figure()
        else:
            width = (frac_screen_width * self.screen_resolution.width()) / self.monitor_dpi
            height = (frac_screen_height * self.screen_resolution.height()) / self.monitor_dpi
            fig = pl.figure(figsize=(width, height))
        fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
        if n_axes == 2:
            ax1 = fig.add_subplot(211, label='ch 1')
            ax2 = fig.add_subplot(212, label='ch 2')
            return fig, ax1, ax2
        else:
            ax = fig.add_subplot(111)
            return fig, ax
