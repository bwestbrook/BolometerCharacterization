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

class AgilentE3634A(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(AgilentE3634A, self).__init__()
        self.status_bar = status_bar
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        test_widget = QtWidgets.QLabel('adfadfasdf', self)
        self.layout().addWidget(test_widget, 1, 0, 1, 1)

    # Power Supply Agilent E3634A

    def bd_close_power_supply(self):
        self.power_supply_popup.close()

    def bd_e3634a(self):
        if not hasattr(self, 'ps'):
            self.ps = PowerSupply()
        if not hasattr(self, 'power_supply_popup'):
            self.gb_create_popup_window('power_supply_popup')
        else:
            self.gb_initialize_panel('power_supply_popup')
        self.gb_build_panel(settings.power_supply_popup_build_dict)
        #for combobox_widget, entry_list in self.power_supply_combobox_entry_dict.items():
            #self.gb_populate_combobox(combobox_widget, entry_list)
        #voltage_to_set, voltage_to_set_str = self.ps.get_voltage()
        #if voltage_to_set < 0:
            #voltage_to_set, voltage_to_set_str = 0.0, '0.0'
        #self.set_ps_voltage(voltage_to_set=voltage_to_set)
        #getattr(self, '_power_supply_popup_set_voltage_lineedit').setText(voltage_to_set_str)
        self.power_supply_popup.showMaximized()
        self.power_supply_popup.setWindowTitle('Agilent E3634 A')
        self.repaint()

    def bd_set_ps_voltage(self, voltage_to_set=None):
        if voltage_to_set is None or type(voltage_to_set) is bool:
            voltage_to_set = getattr(self, '_power_supply_popup_set_voltage_lineedit').text()
        if self.is_float(voltage_to_set, enforce_positive=True):
            self.ps.apply_voltage(float(voltage_to_set))
            set_voltage, set_voltage_str = self.ps.get_voltage()
            if float(voltage_to_set) < 10:
                getattr(self, '_power_supply_popup_which_squid_label').setText('SQUID 1')
            else:
                getattr(self, '_power_supply_popup_which_squid_label').setText('SQUID 2')
            getattr(self, '_power_supply_popup_set_voltage_label').setText(set_voltage_str)
            getattr(self, '_power_supply_popup_voltage_control_dial').setSliderPosition(int(voltage_to_set))

    def bd_set_ps_voltage_dial(self):
        dial_value = float(getattr(self, '_power_supply_popup_voltage_control_dial').value())
        getattr(self, '_power_supply_popup_test2_label').setText(str(dial_value))
        self.set_ps_voltage(dial_value)
