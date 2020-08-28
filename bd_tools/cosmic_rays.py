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

    def __init__(self, available_daqs, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(CosmicRays, self).__init__()
        self.status_bar = status_bar
        self.available_daqs = available_daqs
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.cr_daq_panel()
        self.cr_display_daq_settings()

    def cr_daq_panel(self):
        '''
        '''
        daq_header_label = QtWidgets.QLabel('DAQ Device:', self)
        self.layout().addWidget(daq_header_label, 0, 0, 1, 1)
        self.device_combobox = QtWidgets.QComboBox(self)
        for device in self.available_daqs:
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
        # Connect to functions after placing widgets
        self.daq_1_combobox.activated.connect(self.cr_display_daq_settings)
        self.daq_2_combobox.activated.connect(self.cr_display_daq_settings)
        self.device_combobox.activated.connect(self.cr_display_daq_settings)

    def cr_update_daq(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'daq_settings.json'), 'r') as json_handle:
            self.available_daqs = simplejson.load(json_handle)

    def cr_display_daq_settings(self):
        '''
        '''
        self.cr_update_daq()
        self.device = self.device_combobox.currentText()
        self.channel_1 = self.daq_1_combobox.currentIndex()
        self.channel_2 = self.daq_2_combobox.currentIndex()
        self.int_time_1 = self.available_daqs[self.device][str(self.channel_1)]['int_time']
        self.int_time_2 = self.available_daqs[self.device][str(self.channel_1)]['int_time']
        self.sample_rate_1 = self.available_daqs[self.device][str(self.channel_1)]['sample_rate']
        self.sample_rate_2 = self.available_daqs[self.device][str(self.channel_1)]['sample_rate']
        info_str_1 = 'Sample Rate (Hz): {0} :::: '.format(self.sample_rate_1)
        info_str_1 += 'Int Time (ms): {0}'.format(self.int_time_1)
        info_str_2 = 'Sample Rate (Hz): {0} ::: '.format(self.sample_rate_2)
        info_str_2 += 'Int Time (ms): {0}'.format(self.int_time_2)
        self.channel_1_settings_label.setText(info_str_1)
        self.channel_2_settings_label.setText(info_str_2)

