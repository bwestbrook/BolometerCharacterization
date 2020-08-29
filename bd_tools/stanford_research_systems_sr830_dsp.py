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

class StanfordResearchSystemsSR830DSP(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, available_daqs, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(StanfordResearchSystemsSR830DSP, self).__init__()
        self.status_bar = status_bar
        self.available_daqs = available_daqs
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        test_widget = QtWidgets.QLabel('SRS ', self)
        self.layout().addWidget(test_widget, 1, 0, 1, 1)

    def bd_close_lock_in(self):
        self.lock_in_popup.close()

    def bd_sr830_dsp(self):
        if not hasattr(self, 'lock_in'):
            self.lock_in = LockIn()
        if not hasattr(self, 'lock_in_popup'):
            self.gb_create_popup_window('lock_in_popup')
        else:
            self.gb_initialize_panel('lock_in_popup')
        self.gb_build_panel(settings.lock_in_popup_build_dict)
        for combobox_widget, entry_list in self.lock_in_combobox_entry_dict.items():
            self.gb_populate_combobox(combobox_widget, entry_list)
        # Set current values to gui
        #time_constant_index = self.lock_in._get_current_time_constant()
        #getattr(self, '_lock_in_popup_lock_in_time_constant_combobox').setCurrentIndex(time_constant_index)
        getattr(self, '_lock_in_popup_lock_in_sensitivity_range_combobox').setCurrentIndex(22)
        self.lock_in_popup.showMaximized()
        self.lock_in_popup.setWindowTitle('SR830 DSP')
        self.repaint()

    def bd_change_lock_in_sensitivity_range(self):
        if 'combobox' in str(self.sender().whatsThis()):
            new_value = int(getattr(self, '_lock_in_popup_lock_in_sensitivity_range_combobox').currentText())
            self.lock_in._change_lock_in_sensitivity_range(setting=new_value)
        elif 'down' in str(self.sender().whatsThis()):
            self.lock_in._change_lock_in_sensitivity_range(direction='down')
        else:
            self.lock_in._change_lock_in_sensitivity_range(direction='up')

    def bd_change_lock_in_time_constant(self):
        if 'combobox' in str(self.sender().whatsThis()):
            new_value = int(getattr(self, '_lock_in_popup_lock_in_time_constant_combobox').currentText())
            self.lock_in._change_lock_in_time_constant(setting=new_value)
        elif 'down' in str(self.sender().whatsThis()):
            self.lock_in._change_lock_in_time_constant(direction='down')
        else:
            self.lock_in._change_lock_in_time_constant(direction='up')

    def bd_zero_lock_in_phase(self):
        self.lock_in._zero_lock_in_phase()

