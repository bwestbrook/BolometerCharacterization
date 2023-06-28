import time
import shutil
import os

import simplejson
import numpy as np
import pickle as pkl
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.mpl_canvas import MplCanvas
from bd_lib.iv_curve_lib import IVCurveLib
from bd_lib.fourier_transform_spectroscopy import FourierTransformSpectroscopy
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

class ResonanceMeasurement(QtWidgets.QWidget, GuiBuilder, IVCurveLib, FourierTransformSpectroscopy):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, data_folder, dewar, ls_372_widget):
        '''
        '''
        super(ResonanceMeasurement, self).__init__()
        self.mplc = MplCanvas(self, screen_resolution, monitor_dpi)
        self.bands = self.ftsy_get_bands()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.ls_372_widget = ls_372_widget
        self.dewar = dewar
        with open(os.path.join('bd_settings', 'squids_settings.json'), 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh)
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)
        self.squid_gains = {
            '5': 1e-2,
            '50': 1e-1,
            '500': 1,
            }
        self.cold_bias_resistor_dict  = {
            '1': 20e-3, # 20mOhm
            '2': 250e-6, # 250microOhm
            }
        self.voltage_reduction_factor_dict  = {
            '1': 9.09e-8,
            '2': 4.28e-7,
            '3': 9.09e-7,
            '4': 1e-6,
            '5': 1e-4,
            '6': 1e-5,
            '7': 100,
            '8': 1e3,
            }
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.x_data = []
        self.x_stds = []
        self.y_data = []
        self.y_stds = []
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = os.path.join(data_folder, 'IV_Curves')
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        self.rm_populate()
        self.qthreadpool = QtCore.QThreadPool()
        self.rm_get_t_bath()
        with open(os.path.join('bd_resources', 'iv_collector_tool_tips.json'), 'r') as fh:
            tool_tips_dict = simplejson.load(fh)
        self.gb_add_tool_tips(self, tool_tips_dict)

    #########################################################
    # GUI and Input Handling
    #########################################################

    def rm_update_samples(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)

    def rm_update_squids_data(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'squids_settings.json'), 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh)

    def rm_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings

    def rm_populate(self):
        '''
        '''
        self.gb_initialize_panel('self')
        self.rm_configure_panel()

    def rm_configure_panel(self):
        '''
        '''

        self.hello_label = QtWidgets.QLabel('hello')
        self.layout().addWidget(self.hello_label, 0, 0, 1, 1)
        self.t_bath_lineedit = self.gb_make_labeled_lineedit('Set Tbath')
        self.layout().addWidget(self.t_bath_lineedit, 1, 0, 1, 1)

    def rm_get_t_bath(self):
        '''
        '''
        if not hasattr(self.ls_372_widget, 'channels'):
            return None
        channel_readout_info = self.ls_372_widget.channels.ls372_get_channel_value(6, reading='kelvin') # 6 is MXC
        if self.gb_is_float(channel_readout_info):
            temperature = '{0:.3f}'.format(float(channel_readout_info) * 1e3) # mK
        else:
            temperature = '300'
        self.t_bath_lineedit.setText(temperature)

    def rm_set_t_bath_power(self):
        '''
        '''
        power = float(self.t_bath_set_lineedit.text()) * 1e-3 #mW
        self.status_bar.showMessage('Setting T_bath power to  {0:.2f} mK'.format(power))
        new_settings = {
                'power': power,
                'polarity': 0,
                'analog_mode': 2,
                'input_channel': 6,
                'source': 1,
                'high_value': 0.5,
                'powerup_enable': 0,
                'filter_on': 1,
                'delay': 1,
                'low_value': 0,
                'manual_value': power
        }
        self.ls_372_widget.analog_outputs.ls372_set_open_loop_heater(0, new_settings, None)
