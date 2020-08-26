import time
import os
import pylab as pl
import numpy as np
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class FTS(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, available_daqs, status_bar, screen_resolution, monitor_dpi):
        super(FTS, self).__init__()
        self.status_bar = status_bar
        self.available_daqs = available_daqs
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.fts_input_panel()

    def fts_input_panel(self):
        '''
        '''
        welcome_header_label = QtWidgets.QLabel('Welcome to FTS', self)
        self.layout().addWidget(welcome_header_label, 0, 0, 1, 1)
        # Stepper Motor Selection
        stepper_motor_header_label = QtWidgets.QLabel('Stepper Motor:', self)
        self.layout().addWidget(stepper_motor_header_label, 1, 0, 1, 1)
        stepper_motor_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(stepper_motor_combobox, 1, 1, 1, 1)
        for com_port in ['COM12']:
            stepper_motor_combobox.addItem(com_port)
        self.stepper_motor_settings_label = QtWidgets.QLabel('Stepper Settings', self)
        self.layout().addWidget(self.stepper_motor_settings_label, 1, 2, 1, 1)
        # DAQ Selection
        daq_header_label = QtWidgets.QLabel('DAQ:', self)
        self.layout().addWidget(daq_header_label, 2, 0, 1, 1)
        daq_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(daq_combobox, 2, 1, 1, 1)
        for channel in range(8):
            daq_combobox.addItem(str(channel))
        self.daq_settings_label = QtWidgets.QLabel('DAQ Settings', self)
        self.layout().addWidget(self.daq_settings_label, 2, 2, 1, 1)
        ######
        # Scan Params
        ######
        #Start Scan
        start_position_header_label = QtWidgets.QLabel('Start Position:', self)
        self.layout().addWidget(start_position_header_label, 3, 0, 1, 1)
        self.start_position_lineedit = QtWidgets.QLineEdit('-30000', self)
        self.start_position_lineedit.setValidator(QtGui.QIntValidator(-500000, 0, self.start_position_lineedit))
        self.start_position_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.layout().addWidget(self.start_position_lineedit, 3, 1, 1, 1)
        #End Scan
        end_position_header_label = QtWidgets.QLabel('End Position:', self)
        self.layout().addWidget(end_position_header_label, 4, 0, 1, 1)
        self.end_position_lineedit = QtWidgets.QLineEdit('30000', self)
        self.end_position_lineedit.setValidator(QtGui.QIntValidator(0, 300000, self.end_position_lineedit))
        self.end_position_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.layout().addWidget(self.end_position_lineedit, 4, 1, 1, 1)
        #Step size
        step_size_header_label = QtWidgets.QLabel('Step Size:', self)
        self.layout().addWidget(step_size_header_label, 5, 0, 1, 1)
        self.step_size_lineedit = QtWidgets.QLineEdit('500', self)
        self.step_size_lineedit.setValidator(QtGui.QIntValidator(1, 200000, self.step_size_lineedit))
        self.step_size_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.layout().addWidget(self.step_size_lineedit, 5, 1, 1, 1)
        #Scan Info size
        self.scan_info_label = QtWidgets.QLabel('Scan Info', self)
        self.layout().addWidget(self.scan_info_label, 6, 1, 1, 1)
        self.fts_update_scan_params()

    def fts_update_scan_params(self):
        '''
        '''
        end = float(self.end_position_lineedit.text())
        start = float(self.start_position_lineedit.text())
        step_size = float(self.step_size_lineedit.text())
        self.n_data_points = int((end - start) / step_size)
        self.scan_info_label.setText('N Data Points: {0}'.format(self.n_data_points))





