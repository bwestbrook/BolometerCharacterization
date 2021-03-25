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
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = os.path.join('S:', 'Daily_Data', '{0}'.format(self.today_str))
        self.cr_daq_panel()

    def cr_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings

    def cr_daq_panel(self):
        '''
        '''
        # Device Select 
        self.device_combobox = self.gb_make_labeled_combobox('DAQ Device: ')
        for device in self.daq_settings:
            self.device_combobox.addItem(device)
        self.device_combobox.setCurrentIndex(1)
        self.layout().addWidget(self.device_combobox, 0, 0, 1, 1)
        # Sample Rate
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz): ')
        self.sample_rate_lineedit.setText('5000')
        self.sample_rate_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e7, 1, self.sample_rate_lineedit))
        self.layout().addWidget(self.sample_rate_lineedit, 0, 1, 1, 1)
        # Int Time 
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Integration Time (ms): ')
        self.int_time_lineedit.setText('1000')
        self.int_time_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e6, 1, self.int_time_lineedit))
        self.layout().addWidget(self.int_time_lineedit, 0, 2, 1, 1)
        self.daq_1_combobox = self.gb_make_labeled_combobox(label_text='Ch 1 DAQ: ')
        # DAQ Ch Select 
        for daq in range(0, 4):
            self.daq_1_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_1_combobox, 1, 0, 1, 1)
        self.daq_2_combobox = self.gb_make_labeled_combobox(label_text='Ch 2 DAQ: ')
        for daq in range(0, 4):
            self.daq_2_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_2_combobox, 1, 1, 1, 1)
        self.daq_2_combobox.setCurrentIndex(1)
        self.daq_3_combobox = self.gb_make_labeled_combobox(label_text= 'CH 3 DAQ: ')
        for daq in range(0, 4):
            self.daq_3_combobox.addItem(str(daq))
        self.daq_3_combobox.setCurrentIndex(2)
        self.layout().addWidget(self.daq_3_combobox, 1, 2, 1, 1)
        # Sample Name
        sample_name_header_label = QtWidgets.QLabel('Sample Name:', self)
        self.layout().addWidget(sample_name_header_label, 3, 0, 1, 1)
        self.sample_name_lineedit = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.sample_name_lineedit, 3, 1, 1, 3)
        # Plot
        self.running_plot_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.running_plot_label, 4, 0, 1, 5)
        # Data Panel Ch 1
        self.mean_1_label = QtWidgets.QLabel('Mean 1: ', self)
        self.layout().addWidget(self.mean_1_label, 5, 0, 1, 1)
        self.std_1_label = QtWidgets.QLabel('STD 1: ', self)
        self.layout().addWidget(self.std_1_label, 5, 1, 1, 1)
        # Data Panel Ch 2
        self.mean_2_label = QtWidgets.QLabel('Mean 2: ', self)
        self.layout().addWidget(self.mean_2_label, 6, 0, 1, 1)
        self.std_2_label = QtWidgets.QLabel('STD 2: ', self)
        self.layout().addWidget(self.std_2_label, 6, 1, 1, 1)
        # Data Panel Ch 3
        self.mean_3_label = QtWidgets.QLabel('Mean 3: ', self)
        self.layout().addWidget(self.mean_3_label, 7, 0, 1, 1)
        self.std_3_label = QtWidgets.QLabel('STD 3: ', self)
        self.layout().addWidget(self.std_3_label, 7, 1, 1, 1)
        # Buttons
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        start_pushbutton.clicked.connect(self.cr_start_stop)
        self.layout().addWidget(start_pushbutton, 8, 0, 1, 4)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        save_pushbutton.clicked.connect(self.cr_save)
        self.layout().addWidget(save_pushbutton, 9, 0, 1, 4)

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
        ch_1 = self.daq_1_combobox.currentText()
        ch_2 = self.daq_2_combobox.currentText()
        ch_3 = self.daq_3_combobox.currentText()
        int_time = float(self.int_time_lineedit.text())
        sample_rate = float(self.sample_rate_lineedit.text())
        self.cr_scan_file_name()
        signal_channels = [ch_1, ch_2, ch_3]

        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=int_time,
                      sample_rate=sample_rate,
                      device=device)
        while self.started:
            data_dict = daq.run()
            self.data_1, self.stds_1 = [], []
            self.data_2, self.stds_2 = [], []
            self.data_3, self.stds_3 = [], []
#            data_dict = self.daq.get_data(signal_channels=signal_channels,
                                          #device=device)
            ts_1 = data_dict[ch_1]['ts']
            mean_1 = data_dict[ch_1]['mean']
            min_1 = data_dict[ch_1]['min']
            max_1 = data_dict[ch_1]['max']
            std_1 = data_dict[ch_1]['std']

            ts_2 = data_dict[ch_2]['ts']
            mean_2 = data_dict[ch_2]['mean']
            min_2 = data_dict[ch_2]['min']
            max_2 = data_dict[ch_2]['max']
            std_2 = data_dict[ch_2]['std']

            ts_3 = data_dict[ch_3]['ts']
            mean_3 = data_dict[ch_3]['mean']
            min_3 = data_dict[ch_3]['min']
            max_3 = data_dict[ch_3]['max']
            std_3 = data_dict[ch_3]['std']

            self.mean_1_label.setText('Mean 1: {0:.5f}'.format(mean_1))
            self.std_1_label.setText('STD 1: {0:.5f}'.format(std_1))
            self.mean_2_label.setText('Mean 2: {0:.5f}'.format(mean_2))
            self.std_2_label.setText('STD 2: {0:.5f}'.format(std_2))
            self.mean_3_label.setText('Mean 3: {0:.5f}'.format(mean_3))
            self.std_3_label.setText('STD 3: {0:.5f}'.format(std_3))

            self.data_1.extend(ts_1)
            self.stds_1.append(std_1)
            self.data_2.extend(ts_2)
            self.stds_2.append(std_2)
            self.data_3.extend(ts_3)
            self.stds_3.append(std_3)
            save_path = self.cr_index_file_name()
            self.cr_plot(running=True, save_path=save_path)
            with open(save_path, 'w') as save_handle:
                for i, data_1 in enumerate(self.data_1):
                    line = '{0:.6f}, {1:.6f}, {2:.6f}\n'.format(self.data_1[i], self.data_2[i], self.data_3[i])
                    save_handle.write(line)
            QtWidgets.QApplication.processEvents()
            self.repaint()

    def cr_scan_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            folder_name = 'CR_Scan_{0}'.format(str(i).zfill(3))
            self.folder_path = os.path.join(self.data_folder, folder_name)
            if not os.path.exists(self.folder_path):
                os.makedirs(self.folder_path)
                break

    def cr_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}.txt'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.folder_path, file_name)
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

    def cr_plot(self, running=False, save_path=None):
        '''
        '''
        fig, ax1, ax2, ax3 = self.cr_create_blank_fig(frac_screen_width=0.8, frac_screen_height=0.5,
                                                      left=0.12, right=0.98, top=0.9, bottom=0.13, aspect=None, n_axes=3)
        #ax1.errorbar(range(len(self.data_1)), self.data_1, yerr=self.stds_1, marker='.', linestyle='-')
        #ax2.errorbar(range(len(self.data_2)), self.data_2, yerr=self.stds_2, marker='.', linestyle='-')
        ax1.plot(self.data_1)
        ax2.plot(self.data_2)
        ax3.plot(self.data_3)
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
        if n_axes == 3:
            ax1 = fig.add_subplot(311, label='ch 1')
            ax2 = fig.add_subplot(312, label='ch 2')
            ax3 = fig.add_subplot(313, label='ch 3')
            return fig, ax1, ax2, ax3
        elif n_axes == 2:
            ax1 = fig.add_subplot(211, label='ch 1')
            ax2 = fig.add_subplot(212, label='ch 2')
            return fig, ax1, ax2
        else:
            ax = fig.add_subplot(111)
            return fig, ax
