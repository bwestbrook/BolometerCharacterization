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

class NoiseAnalyzer(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(NoiseAnalyzer, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = os.path.join('Data', '{0}'.format(self.today_str))
        self.na_daq_panel()
        self.na_display_daq_settings()

    def na_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.na_display_daq_settings()

    def na_daq_panel(self):
        '''
        '''
        daq_header_label = QtWidgets.QLabel('DAQ Device:', self)
        self.layout().addWidget(daq_header_label, 0, 0, 1, 1)
        self.device_combobox = QtWidgets.QComboBox(self)
        for device in self.daq_settings:
            self.device_combobox.addItem(device)
        self.device_combobox.activated.connect(self.na_display_daq_settings)
        self.layout().addWidget(self.device_combobox, 0, 1, 1, 1)
        daq_1_header_label = QtWidgets.QLabel('DAQ Ch 1 Data:', self)
        self.layout().addWidget(daq_1_header_label, 1, 0, 1, 1)
        self.daq_1_combobox = QtWidgets.QComboBox(self)
        for daq in range(0, 4):
            self.daq_1_combobox.addItem(str(daq))
        self.daq_1_combobox.activated.connect(self.na_display_daq_settings)
        self.layout().addWidget(self.daq_1_combobox, 1, 1, 1, 1)
        # Chan 1
        self.channel_1_settings_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.channel_1_settings_label, 2, 0, 1, 2)
        # Chan 2
        # Sample Name
        sample_name_header_label = QtWidgets.QLabel('Sample Name:', self)
        self.layout().addWidget(sample_name_header_label, 3, 0, 1, 1)
        self.sample_name_lineedit = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.sample_name_lineedit, 3, 1, 1, 3)
        #self.integration_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int Time (s)')
        #self.integration_time_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.integration_time_lineedit))
        #self.layout().addWidget(self.integration_time_lineedit, 4, 1, 1, 1)
        self.noise_bin_low_edge_lineedit = self.gb_make_labeled_lineedit(label_text='Noise Bin Low Edge (Hz)')
        self.noise_bin_low_edge_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.noise_bin_low_edge_lineedit))
        self.layout().addWidget(self.noise_bin_low_edge_lineedit, 4, 0, 1, 1)

        self.noise_bin_high_edge_lineedit = self.gb_make_labeled_lineedit(label_text='Noise Bin High Edge (Hz)')
        self.noise_bin_high_edge_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.noise_bin_high_edge_lineedit))
        self.layout().addWidget(self.noise_bin_high_edge_lineedit, 4, 1, 1, 1)

        # Plot and Data Panel
        self.running_ts_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.running_ts_label, 5, 0, 1, 4)
        mean_1_header_label = QtWidgets.QLabel('Mean Ch 1:', self)
        self.layout().addWidget(mean_1_header_label, 6, 0, 1, 1)
        self.mean_1_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.mean_1_label, 6, 1, 1, 1)
        std_1_header_label = QtWidgets.QLabel('STD Ch 1:', self)
        self.layout().addWidget(std_1_header_label, 6, 2, 1, 1)
        self.std_1_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.std_1_label, 6, 3, 1, 1)

        self.running_std_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.running_std_label, 7, 0, 1, 4)

        # Buttons
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        start_pushbutton.clicked.connect(self.na_start_stop)
        self.layout().addWidget(start_pushbutton, 8, 0, 1, 4)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        save_pushbutton.clicked.connect(self.na_save)
        self.layout().addWidget(save_pushbutton, 9, 0, 1, 4)
        # Connect to functions after placing widgets
        self.daq_1_combobox.activated.connect(self.na_display_daq_settings)
        self.device_combobox.activated.connect(self.na_display_daq_settings)

    def na_display_daq_settings(self):
        '''
        '''
        self.device = self.device_combobox.currentText()
        self.channel_1 = self.daq_1_combobox.currentIndex()
        pprint(self.daq_settings)
        print(self.device, self.channel_1)
        print(self.device, self.channel_1)
        self.int_time_1 = self.daq_settings[self.device][str(self.channel_1)]['int_time']
        self.sample_rate_1 = self.daq_settings[self.device][str(self.channel_1)]['sample_rate']
        info_str_1 = 'Sample Rate (Hz): {0} :::: '.format(self.sample_rate_1)
        info_str_1 += 'Int Time (ms): {0}'.format(self.int_time_1)
        self.channel_1_settings_label.setText(info_str_1)

    ###########
    # Running
    ###########

    def na_start_stop(self):
        '''
        '''
        if 'Start' in self.sender().text():
            self.sender().setText('Stop')
            self.started = True
            self.na_collecter()
        else:
            self.sender().setText('Start')
            self.started = False

    def na_collecter(self):
        '''
        '''
        device = self.device_combobox.currentText()
        self.na_scan_file_name()
        signal_channels = [self.channel_1]
        while self.started:
            self.data_1, self.stds_1 = [], []
            data_dict = self.daq.get_data(signal_channels=signal_channels,
                                          int_time=self.int_time_1,
                                          sample_rate=self.sample_rate_1,
                                          device=device)
            ts_1 = data_dict[self.channel_1]['ts']
            mean_1 = data_dict[self.channel_1]['mean']
            min_1 = data_dict[self.channel_1]['min']
            max_1 = data_dict[self.channel_1]['max']
            std_1 = data_dict[self.channel_1]['std']
            self.mean_1_label.setText('{0:.5f}'.format(mean_1))
            self.std_1_label.setText('{0:.5f}'.format(std_1))
            self.data_1.extend(ts_1)
            self.stds_1.append(std_1)
            #save_path = self.na_index_file_name()
            #self.na_plot(running=True, save_path=save_path)
            #with open(save_path, 'w') as save_handle:
                #for i, data_1 in enumerate(self.data_1):
                    #line = '{0:.5f}, {1:.5f}\n'.format(self.data_1[i], self.data_2[i])
                    #save_handle.write(line)
            QtWidgets.QApplication.processEvents()
            self.repaint()

    def na_scan_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            folder_name = 'Noise_Scan_{0}'.format(str(i).zfill(3))
            self.folder_path = os.path.join(self.data_folder, folder_name)
            if not os.path.exists(self.folder_path):
                os.makedirs(self.folder_path)
                break

    def na_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}.txt'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.folder_path, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def na_save(self):
        '''
        '''
        save_path = self.na_index_file_name()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter=',*.txt,*.dat')[0]
        if len(save_path) > 0:
            with open(save_path, 'w') as save_handle:
                for i, data_1 in enumerate(self.data_1):
                    line = '{0:.5f}, {1:.5f}\n'.format(self.data_1[i], self.data_2[i])
                    save_handle.write(line)
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')
        self.na_plot()

    def na_plot(self, running=False, save_path=None):
        '''
        '''
        fig, ax1, ax2 = self.na_create_blank_fig(frac_screen_width=0.75, frac_screen_height=0.5,
                                                 left=0.12, right=0.98, top=0.9, bottom=0.13, aspect=None)
        ax1.plot(self.data_1)
        if running:
            temp_png_path = os.path.join('temp_files', 'temp_cr.png')
            fig.savefig(temp_png_path)
            image_to_display = QtGui.QPixmap(temp_png_path)
            self.running_plot_label.setPixmap(image_to_display)
            if save_path is not None:
                fig.savefig(save_path.replace('txt', 'png'))
            pl.close('all')

        else:
            title, okPressed = self.gb_quick_info_gather(title='Plot Title', dialog='What is the title of this plot?')
            ax1.set_title(title)
            pl.show()

    def na_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.8,
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
