import time
import shutil
import os
import simplejson
import pickle as pkl
import numpy as np
import pylab as pl
import pandas as pd
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import *
from bd_lib.saving_manager import SavingManager
from bd_lib.mpl_canvas import MplCanvas
from bd_lib.fourier_transform_spectroscopy import FourierTransformSpectroscopy
from GuiBuilder.gui_builder import GuiBuilder, GenericClass
# Import Last

class RTCollector(QtWidgets.QWidget, GuiBuilder, FourierTransformSpectroscopy):

    def __init__(
            self,
            daq_settings,
            status_bar,
            screen_resolution,
            monitor_dpi,
            ls372_temp_widget,
            ls372_samples_widget,
            data_folder,
            dewar):
        '''
        '''
        super(RTCollector, self).__init__()
        self.today = datetime.now()
        self.start_time = datetime.now()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.mplc = MplCanvas(self, screen_resolution, monitor_dpi)
        time.sleep(0.05)
        time_delta = datetime.now() - self.today
        time_delta = time_delta.microseconds
        self.init_data = {
                0: {
                     'data': [0],
                     'stds': [0],
                     'directions': ['up'],
                     'time_deltas': [time_delta],
                     'temp_deltas': [1.0]
                    },
                1: {
                     'data': [0],
                     'stds': [0],
                     'directions': ['up'],
                     'time_deltas': [time_delta],
                     'temp_deltas': [1.0]
                    }
                }
        self.all_data_df = pd.DataFrame.from_dict(self.init_data)
        self.x_data = [0]
        self.x_stds = [0]
        self.y_data = [0]
        self.y_stds = [0]
        self.housekeeping_low_value = 0
        self.housekeeping_high_value = 10
        self.samples_low_value = 0
        self.samples_high_value = 10
        self.directions = ['down']
        self.x_fig = self.mplc.mplc_create_two_pane_plot(
                name='x_fig',
                left=0.12,
                right=0.93,
                wspace=0.8,
                hspace=0.4,
                bottom=0.2,
                top=0.93,
                frac_screen_height=0.2,
                frac_screen_width=0.26)
        self.y_fig = self.mplc.mplc_create_two_pane_plot(
                name='y_fig',
                left=0.12,
                right=0.93,
                wspace=0.8,
                hspace=0.4,
                bottom=0.2,
                top=0.93,
                frac_screen_height=0.2,
                frac_screen_width=0.26)
        self.xy_fig = self.mplc.mplc_create_fig_with_legend_axes(
                name='xy_fig',
                left=0.12,
                right=0.91,
                bottom=0.2,
                top=0.9,
                frac_screen_height=0.35,
                frac_screen_width=0.33,
                wspace=0.1,
                hspace=0.1)
        self.meta_data = {}
        self.daq = BoloDAQ()
        self.ls372_temp_widget = ls372_temp_widget
        self.ls372_samples_widget = ls372_samples_widget
        self.heater_resistance = 120.
        self.drift_direction = 'down'
        self.thermometer_index = 0
        with open(os.path.join('bd_settings', 'squids_settings.json'), 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh)
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)
        self.unit_dict = {
                'current': 'uA',
                'voltage': 'uV',
                'uA': 'current',
                'uV': 'voltage'
                }
        self.voltage_reduction_factor_dict  = {
            '1': 1,
            '2': 10,
            '3': 100,
            '4': 1e3,
            '5': 1e4,
            }
        self.thermometers = {
                'X... (576)': 0,
                'PT100 (MXC)': 6,
                'X110595 (Cu Box)': 9
                }
        self.lakeshore_thermometers = {
                'PT100 (MXC)': 6,
                'X110595 (Cu Box)': 9
                }
        self.active_daq_dict = {
                1: {
                    'active': True,
                    'plot': True,
                    'name': '',
                },
                2: {
                    'active': False,
                    'plot': False,
                    'name': '',
                },
                3:{
                    'active': False,
                    'plot': False,
                    'name': '',
                }
            }
        self.dewar = dewar
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.rtc_plot_panel = QtWidgets.QWidget(self)
        grid_2 = QtWidgets.QGridLayout()
        self.rtc_plot_panel.setLayout(grid_2)
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = os.path.join(data_folder, 'RT_Curves')
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        self.daq_collector = Collector(self, self.all_data_df)
        self.rtc_populate()
        if self.ls372_temp_widget is not None:
            self.status_bar.messageChanged.connect(self.rtc_update_panel)
        self.qthreadpool = QThreadPool()
        self.resize(self.minimumSizeHint())
        self.rtc_read_set_points()
        self.rtc_set_first_set_point()
        with open(os.path.join('bd_resources', 'rt_collector_tool_tips.json'), 'r') as fh:
            tool_tips_dict = simplejson.load(fh)
        self.gb_add_tool_tips(self, tool_tips_dict)

    #########################################################
    # GUI and Input Handling
    #########################################################

    def rtc_update_samples(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)
        self.rtc_update_sample_name()

    def rtc_populate(self):
        '''
        '''
        self.gb_initialize_panel('self')
        self.rtc_rt_config()
        self.rtc_lakeshore_panel()
        self.layout().addWidget(self.rtc_plot_panel, 6, 0, 20, 10)
        self.gb_initialize_panel('rtc_plot_panel')
        self.rtc_make_plot_panel()
        self.rtc_daq_panel()
        self.layout().setRowMinimumHeight(6, int(0.38 * self.screen_resolution.height()))
        daq_collector = Collector(self, self.all_data_df)
        if daq_collector.all_data_df is not None:
            daq_collector.rtc_plot_x_and_y()
            daq_collector.rtc_plot_xy(running=True)
            self.rtc_plot_running_from_disk()

    #############################################
    # DAQ Panel
    #############################################

    def rtc_daq_panel(self):
        '''
        '''
        # Device
        self.rtc_daq_combobox = self.gb_make_labeled_combobox(label_text='Device')
        for daq in self.daq_settings:
            self.rtc_daq_combobox.addItem(daq)
        self.layout().addWidget(self.rtc_daq_combobox, 1, 0, 1, 1)
        # DAQ X
        #self.daq_x_combobox = self.gb_make_labeled_combobox(label_text='DAQ_X:')
        #for daq in range(0, 8):
            #self.daq_x_combobox.addItem(str(daq))
        #self.layout().addWidget(self.daq_x_combobox, 1, 1, 1, 1)
        # DAQ Y
        #self.daq_y_combobox = self.gb_make_labeled_combobox(label_text='DAQ_Y:')
        #for daq in range(0, 8):
            #self.daq_y_combobox.addItem(str(daq))
        #self.layout().addWidget(self.daq_y_combobox, 1, 2, 1, 1)
        #self.daq_y_combobox.setCurrentIndex(1)
        self.rtc_daq_combobox.setCurrentIndex(0)
        self.layout().addWidget(self.rtc_daq_combobox, 0, 0, 1, 1)
        # Int time and sample rte
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int_Time (ms):')
        self.int_time_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.int_time_lineedit))
        self.layout().addWidget(self.int_time_lineedit, 0, 1, 1, 1)
        self.int_time_lineedit.setText('100')
        self.int_time = self.int_time_lineedit.text()
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample_Rate (Hz)')
        self.sample_rate_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.sample_rate_lineedit))
        self.layout().addWidget(self.sample_rate_lineedit, 0, 2, 1, 1)
        self.sample_rate_lineedit.setText('10000')
        self.sample_rate = self.sample_rate_lineedit.text()
        ## DAQ X
        self.daq_x_combobox = self.gb_make_labeled_combobox(label_text='DAQ_X:')
        for daq in range(0, 8):
            self.daq_x_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_x_combobox, 1, 0, 1, 1)
        # DAQ Y
        self.daq_y_combobox = self.gb_make_labeled_combobox(label_text='DAQ_Y:')
        for daq in self.active_daq_dict:
            self.daq_y_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_y_combobox, 1, 1, 1, 1)
        self.daq_y_checkbox = QtWidgets.QCheckBox('Active')
        self.layout().addWidget(self.daq_y_checkbox, 1, 2, 1, 1)
        self.daq_y_combobox.currentIndexChanged.connect(self.rtc_update_active_y_checkbox)
        self.daq_y_checkbox.stateChanged.connect(self.rtc_configure_y_channels)
        self.daq_y_combobox.setCurrentIndex(0)
        self.rtc_daq_combobox.setCurrentIndex(2)
        # Sample Configure 
        self.configure_channel_pushbutton = QtWidgets.QPushButton('Configure And Scan', self)
        self.layout().addWidget(self.configure_channel_pushbutton, 2, 1, 1, 1)
        self.configure_channel_pushbutton.resize(self.configure_channel_pushbutton.minimumSizeHint())
        self.configure_channel_pushbutton.clicked.connect(self.rtc_edit_lakeshore_channel)
        self.channel_combobox = self.gb_make_labeled_combobox(label_text='Channel')
        self.layout().addWidget(self.channel_combobox, 2, 0, 1, 1)
        for channel in range(1, 17):
            self.channel_combobox.addItem(str(channel))
        self.channel_combobox.addItem('SQUID')
        self.multi_channel_name_lineedit = self.gb_make_labeled_lineedit(label_text='MC Sample')
        self.layout().addWidget(self.multi_channel_name_lineedit, 2, 2, 1, 1)
        self.multi_channel_name_lineedit.returnPressed.connect(self.rtc_set_multichannel_name)
        # Sample Name
        self.exc_mode_label = self.gb_make_labeled_label(label_text='Lakeshore_Info:')
        self.exc_mode_label.setText('0 0 0 0 0')
        self.layout().addWidget(self.exc_mode_label, 4, 0, 1, 1)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample_Name:')
        self.layout().addWidget(self.sample_name_lineedit, 4, 1, 1, 2)
        if self.ls372_samples_widget is None:
            return
        self.ls372_samples_widget.channels.ls372_scan_channel(index=1)
        self.daq_y_checkbox.setChecked(True)

    #############################################
    # Lakeshore stuff for DR
    #############################################

    def rtc_lakeshore_panel(self):
        '''
        '''
        # Get Settings First
        if hasattr(self.ls372_temp_widget, 'analog_outputs'):
            self.housekeeping_low_value = self.ls372_temp_widget.analog_outputs.analog_output_aux.low_value # 0V = this value in K or Ohms
            self.housekeeping_high_value = self.ls372_temp_widget.analog_outputs.analog_output_aux.high_value # 10V = this value in K or Ohms
            self.samples_low_value = self.ls372_samples_widget.analog_outputs.analog_output_aux.low_value # 0V = this value in K or Ohms
            self.samples_high_value = self.ls372_samples_widget.analog_outputs.analog_output_aux.high_value # 10V = this value in K or Ohms
        # Temp Control
        self.temp_display_label = QtWidgets.QLabel('Temperature Scanning', self)
        self.temp_display_label.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(self.temp_display_label, 0, 3, 1, 2)
        self.temp_set_point_low_lineedit = self.gb_make_labeled_lineedit(label_text='SP_low (mK):', lineedit_text='140')
        self.temp_set_point_low_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.temp_set_point_low_lineedit))
        self.layout().addWidget(self.temp_set_point_low_lineedit, 1, 3, 1, 1)
        self.temp_set_point_high_lineedit = self.gb_make_labeled_lineedit(label_text='SP_high (mK):', lineedit_text='150')
        self.temp_set_point_high_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.temp_set_point_high_lineedit))
        self.layout().addWidget(self.temp_set_point_high_lineedit, 1, 4, 1, 1)
        self.refresh_set_point_pushbutton = QtWidgets.QPushButton('Refresh Temp', self)
        self.layout().addWidget(self.refresh_set_point_pushbutton, 1, 5, 1, 1)
        self.refresh_set_point_pushbutton.clicked.connect(self.rtc_scan_temp)
        ramp_on, ramp_value = True, ''
        if self.ls372_temp_widget is not None:
            ramp_on, ramp_value = self.ls372_temp_widget.temp_control.ls372_get_ramp()
        self.ramp_lineedit = self.gb_make_labeled_lineedit(label_text='Ramp (K/min): ')
        self.ramp_lineedit.setText('{0}'.format(ramp_value))
        self.ramp_lineedit.setValidator(QtGui.QDoubleValidator(0, 2, 3, self.ramp_lineedit))
        self.layout().addWidget(self.ramp_lineedit, 2, 3, 1, 1)
        self.set_ramp_pushbutton = QtWidgets.QPushButton('Set Ramp', self)
        self.layout().addWidget(self.set_ramp_pushbutton, 2, 4, 1, 1)
        self.set_ramp_pushbutton.clicked.connect(self.rtc_set_ramp)
        # Heater Config
        self.heater_config_label = QtWidgets.QLabel('Heater Configuration', self)
        self.layout().addWidget(self.heater_config_label, 0, 7, 1, 4)
        self.heater_config_label.setAlignment(Qt.AlignCenter)
        # P I D
        p, i, d = 0, 0, 0
        if self.ls372_temp_widget is not None:
            p, i, d = self.ls372_temp_widget.temp_control.ls372_get_pid()
        self.p_lineedit = self.gb_make_labeled_lineedit(label_text='P: ')
        self.p_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 2, self.p_lineedit))
        self.p_lineedit.setText(str(p))
        self.layout().addWidget(self.p_lineedit, 1, 7, 1, 1)
        self.i_lineedit = self.gb_make_labeled_lineedit(label_text='I: ')
        self.i_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 2, self.i_lineedit))
        self.i_lineedit.setText(str(i))
        self.layout().addWidget(self.i_lineedit, 1, 8, 1, 1)
        self.d_lineedit = self.gb_make_labeled_lineedit(label_text='D: ')
        self.d_lineedit.setValidator(QtGui.QDoubleValidator(-300, 300, 2, self.d_lineedit))
        self.d_lineedit.setText(str(d))
        self.layout().addWidget(self.d_lineedit, 1, 9, 1, 1)
        self.meta_data['P I D Settings'] = (p, i, d)
        # Heater Range
        if self.ls372_temp_widget is None:
            return None
        heater_value = self.ls372_temp_widget.temp_control.ls372_get_heater_value()
        current_range_index, current_range_value = self.ls372_temp_widget.temp_control.ls372_get_heater_range()
        self.heater_range_combobox = self.gb_make_labeled_combobox(label_text='Heater Range (mW)')
        self.layout().addWidget(self.heater_range_combobox, 2, 7, 1, 1)
        for range_index, range_value in self.ls372_temp_widget.temp_control.ls372_heater_range_dict.items():
            range_value_in_mw = 1e3 * self.heater_resistance * range_value ** 2
            self.heater_range_combobox.addItem('{0:.4f}'.format(range_value_in_mw))
            if int(range_index) == int(current_range_index):
                set_to_index = int(range_index)
                self.meta_data['Heater Range (A)'] = range_value
                self.meta_data['Heater Range (mW)'] = range_value_in_mw
        self.heater_range_combobox.setCurrentIndex(set_to_index)
        # Read and Write Settings
        update_ls372_heater_range_pushbutton = QtWidgets.QPushButton('Update Heater Range', self)
        update_ls372_heater_range_pushbutton.clicked.connect(self.rtc_edit_lakeshore_heater_range)
        self.layout().addWidget(update_ls372_heater_range_pushbutton, 2, 8, 1, 2)
        update_ls372_settings_pushbutton = QtWidgets.QPushButton('Update All Settings', self)
        update_ls372_settings_pushbutton.clicked.connect(self.rtc_edit_lakeshore_temp_control)
        self.layout().addWidget(update_ls372_settings_pushbutton, 3, 7, 1, 3)

        read_ls372_settings_pushbutton = QtWidgets.QPushButton('Get Lakeshore State', self)
        read_ls372_settings_pushbutton.clicked.connect(self.rtc_get_lakeshore_temp_control)
        self.layout().addWidget(read_ls372_settings_pushbutton, 4, 7, 1, 3)

        self.rtc_get_lakeshore_channel_info()
        self.thermometer_combobox.currentIndexChanged.connect(self.rtc_scan_new_lakeshore_channel)
        self.rtc_get_lakeshore_temp_control()

    def rtc_get_lakeshore_temp_control(self, pid=True, set_point=True):
        '''
        '''
        if not hasattr(self, 'lakeshore_state_label'):
            return None
        self.status_bar.showMessage('Getting Temp')
        current_temp = self.rtc_get_current_temp()
        self.status_bar.showMessage('Getting Set Point')
        active_set_point = self.rtc_get_active_set_point()# mK
        self.status_bar.showMessage('Getting Heater ')
        heater_current, heater_power = self.rtc_get_heater_state()
        lake_shore_state = 'Current temp {0:.3f}mK ::: Active Target {1:.3f}mK ::: Heater Power {2:.3f}mW'.format(current_temp, active_set_point * 1e3, heater_power * 1e3)
        self.lakeshore_state_label.setText(lake_shore_state)

    def rtc_get_lakeshore_pid(self):
        '''
        '''
        p, i, d = self.ls372_temp_widget.temp_control.ls372_get_pid()
        return p, i, d

    def rtc_set_ramp(self):
        '''
        '''
        if self.ls372_temp_widget is None:
            return None
        new_ramp = float(self.ramp_lineedit.text())
        self.ls372_temp_widget.temp_control.set_run_function('ls372_set_ramp', new_ramp)
        self.qthreadpool.start(self.ls372_temp_widget.temp_control)
        self.meta_data['Temp Ramp (K/min)'] = new_ramp

    def rtc_set_new_housekeeping_low_high_value(self):
        '''
        '''
        if self.ls372_temp_widget is None:
            return None
        low_value = float(self.new_housekeeping_low_value_lineedit.text())
        high_value = float(self.new_housekeeping_high_value_lineedit.text())
        data_source = 'kelvin'
        self.ls372_temp_widget.temp_control.ls372_set_analog_low_high_value(self.thermometer_index, data_source, low_value, high_value)
        self.housekeeping_high_value = high_value
        self.housekeeping_low_value = low_value

    def rtc_set_new_samples_low_high_value(self):
        '''
        '''
        if self.ls372_samples_widget is None:
            return None
        channel = self.channel_combobox.currentText()
        low_value = float(self.new_samples_low_value_lineedit.text())
        high_value = float(self.new_samples_high_value_lineedit.text())
        data_source = 'ohms'

        self.ls372_samples_widget.temp_control.ls372_set_analog_low_high_value(channel, data_source, low_value, high_value)
        self.samples_low_value = low_value
        self.samples_high_value = high_value

    def rtc_get_active_set_point(self):
        '''
        '''
        active_set_point = self.ls372_temp_widget.temp_control.ls372_get_temp_set_point()
        return active_set_point

    def rtc_get_current_temp(self):
        '''
        '''
        temp = np.nan
        if self.gb_is_float(self.ls372_temp_widget.channels.ls372_get_channel_value(self.thermometer_index, reading='kelvin')):
            temp = float(self.ls372_temp_widget.channels.ls372_get_channel_value(self.thermometer_index, reading='kelvin')) * 1e3
        return temp

    def rtc_get_heater_state(self):
        '''
        '''
        self.ls372_temp_widget.temp_control.set_run_function('ls372_get_heater_value')
        heater_current = self.ls372_temp_widget.temp_control.ls372_get_heater_value()
        heater_power = self.heater_resistance * heater_current ** 2 # in mW
        return heater_current, heater_power

    def rtc_scan_temp(self, clicked, x_data=[], x_stds=[]):
        '''
        '''
        if not self.gb_is_float(self.temp_set_point_low_lineedit.text()):
            return None
        if not self.gb_is_float(self.temp_set_point_high_lineedit.text()):
            return None
        x_data, x_stds = self.rtc_adjust_x_data(x_data, x_stds)
        if len(x_data) == 0:
            x_data, x_stds = self.rtc_adjust_x_data(self.x_data, self.x_stds)
        if len(x_data) == 0:
            return None
        current_temp = x_data[-1] * 1e3 #mK
        low_set_point = float(self.temp_set_point_low_lineedit.text())
        high_set_point = float(self.temp_set_point_high_lineedit.text())
        if current_temp > high_set_point - 1:
            self.drift_direction = 'down'
            new_target = low_set_point * 1e-3 #K
        elif current_temp < low_set_point + 1:
            self.drift_direction = 'up'
            new_target = high_set_point * 1e-3 #K
        elif self.drift_direction == 'up':
            new_target = high_set_point * 1e-3 #K
        elif self.drift_direction == 'down':
            new_target = low_set_point * 1e-3 #K
        self.ls372_temp_widget.temp_control.set_run_function('ls372_set_temp_set_point', new_target)
        self.qthreadpool.start(self.ls372_temp_widget.temp_control)
        self.status_bar.showMessage('Setting temperature {0} to {1} mK'.format(self.drift_direction, new_target * 1e3))

    def rtc_edit_lakeshore_heater_range(self):
        '''
        '''
        # Heater Range
        new_range_index = self.heater_range_combobox.currentIndex()
        self.ls372_temp_widget.channels.ls372_scan_channel(index=self.thermometer_index) # 6 is the MXC thermometer #10 is the Cu box
        self.ls372_temp_widget.temp_control.ls372_set_heater_range(new_range_index)
        self.status_bar.showMessage('Lakeshore Heater Ranges Set to {0}'.format(new_range_index))
        self.rtc_get_lakeshore_temp_control()

    def rtc_edit_lakeshore_temp_control(self):
        '''
        '''
        #PID Stuff
        new_p, new_i, new_d = float(self.p_lineedit.text()), float(self.i_lineedit.text()), float(self.d_lineedit.text())
        self.ls372_temp_widget.temp_control.ls372_set_pid(new_p, new_i, new_d)
        # Ramp 
        new_ramp = float(self.ramp_lineedit.text())
        self.ls372_temp_widget.temp_control.ls372_set_ramp(new_ramp)
        # Heater Range
        new_range_index = self.heater_range_combobox.currentIndex()
        self.ls372_temp_widget.channels.ls372_scan_channel(index=self.thermometer_index) # 6 is the MXC thermometer #10 is the Cu box
        self.ls372_temp_widget.temp_control.ls372_set_heater_range(new_range_index)
        self.status_bar.showMessage('Lakeshore configured')
        self.rtc_get_lakeshore_temp_control()

    def rtc_scan_new_lakeshore_channel(self):
        '''
        '''
        if self.ls372_temp_widget is None:
            return None
        thermometer = self.thermometer_combobox.currentText()
        self.thermometer_index = self.thermometers[thermometer]
        self.ls372_temp_widget.ls372_scan_channel(index=self.thermometer_index)
        self.ls372_temp_widget.analog_outputs.ls372_monitor_channel_aux_analog(self.thermometer_index, self.ls372_temp_widget.analog_outputs.analog_output_aux)

    def rtc_edit_lakeshore_channel(self):
        '''
        '''
        if self.ls372_samples_widget is None:
            return None
        channel = self.channel_combobox.currentText()
        ls_name = 'LS{0}'.format(channel.zfill(2))
        self.ls372_samples_widget.ls372_edit_channel(clicked=True, index=channel)
        self.ls372_samples_widget.channels.ls372_scan_channel(index=channel)
        self.ls372_samples_widget.analog_outputs.analog_output_aux.input_channel = channel
        self.ls372_samples_widget.analog_outputs.ls372_monitor_channel_aux_analog(channel, self.ls372_samples_widget.analog_outputs.analog_output_aux)

    def rtc_update_panel(self):
        '''
        '''
        self.rtc_get_lakeshore_channel_info()
        self.rtc_update_sample_name()

    def rtc_get_lakeshore_channel_info(self):
        '''
        '''
        if not hasattr(self, 'channel_combobox'):
            return None
        if self.channel_combobox.currentText() == 'SQUID':
            return None
        channel = self.channel_combobox.currentText()
        channel_info = 'Scanning {0} '.format(channel)
        channel_object = self.ls372_samples_widget.channels.__dict__['channel_{0}'.format(channel)]
        exc_mode = self.ls372_samples_widget.lakeshore372_command_dict['exc_mode'][channel_object.__dict__['exc_mode']]
        excitation = self.ls372_samples_widget.lakeshore372_command_dict['excitation'][exc_mode][channel_object.__dict__['excitation']]
        resistance_range = self.ls372_samples_widget.lakeshore372_command_dict['resistance_range'][channel_object.__dict__['resistance_range']]
        exc_info = '{0:.2f} {1} {2:.0f} (mOhms)'.format(excitation * 1e6, self.unit_dict[exc_mode], resistance_range * 1e3)
        self.exc_mode_label.setText(exc_info)
        y_correction_factor = (self.samples_high_value - self.samples_low_value) / 10 # divide out scaling of lakeshore
        y_correction_factor *= 1e3 # convet back to mOhm
        self.y_correction_lineedit.setText(str(y_correction_factor))

    def rtc_edit_lakeshore_aux_ouput(self):
        '''
        '''
        self.ls372_samples_widget.ls372_edit_analog_output(clicked=True, analog_output='aux')

    def rtc_update_ls372_widget(self, ls372_widget):
        '''
        '''
        self.ls372_widget = ls372_widget

    def rtc_rt_config(self):
        '''
        '''
        # Thermometers Serial 
        self.thermometer_combobox = self.gb_make_labeled_combobox(label_text='Thermometer:')
        for thermometer in self.thermometers:
            self.thermometer_combobox.addItem(thermometer)
        self.layout().addWidget(self.thermometer_combobox, 3, 3, 1, 2)
        self.y_label_combobox = self.gb_make_labeled_combobox(label_text='Y label:')
        y_labels = ['Resistance ($m\Omega$)', 'Arb Units']
        for y_label in y_labels:
            self.y_label_combobox.addItem(y_label)
        self.layout().addWidget(self.y_label_combobox, 4, 3, 1, 2)
        # Y Voltage Factor 
        self.y_correction_lineedit = self.gb_make_labeled_lineedit(label_text='Resistance Factor:', lineedit_text='100')
        self.layout().addWidget(self.y_correction_lineedit, 4, 5, 1, 1)
        self.y_correction_low_value_label = self.gb_make_labeled_label(label_text='')
        self.layout().addWidget(self.y_correction_low_value_label, 4, 7, 1, 1)
        self.y_correction_high_value_label = self.gb_make_labeled_label(label_text='')
        self.layout().addWidget(self.y_correction_high_value_label, 4, 8, 1, 1)


    def rtc_update_sample_name(self):
        '''
        '''
        if not hasattr(self, 'channel_combobox'):
            return None
        channel = self.channel_combobox.currentText()
        if channel != 'SQUID' and self.dewar != '576':
            sample_key = 'LS{0}'.format(channel.zfill(2))
            sample_name = self.samples_settings[sample_key]
            self.sample_name_lineedit.setText(sample_name)
        sample_name = self.sample_name_lineedit.text().replace(' ', '_').replace('__', '_')
        self.meta_data['Sample Name'] = sample_name

    #########################################################
    # Plotting
    #########################################################

    def rtc_make_plot_panel(self):
        '''
        '''
        # X
        self.x_time_stream_label = QtWidgets.QLabel('', self)
        self.x_time_stream_label.setAttribute(Qt.WA_TranslucentBackground)
        self.x_time_stream_label.setAlignment(Qt.AlignCenter)
        self.rtc_plot_panel.layout().addWidget(self.x_time_stream_label, 0, 0, 2, 1)
        self.x_data_label = QtWidgets.QLabel('X Data: X STD:', self)
        self.x_data_label.setAlignment(Qt.AlignCenter)
        self.rtc_plot_panel.layout().addWidget(self.x_data_label, 2, 0, 1, 1)

        # Lakeshore feedback X
        self.lakeshore_state_label = QtWidgets.QLabel('', self)
        self.lakeshore_state_label.setAlignment(Qt.AlignCenter)
        self.rtc_plot_panel.layout().addWidget(self.lakeshore_state_label, 3, 0, 1, 2)


        self.new_housekeeping_low_value_lineedit = self.gb_make_labeled_lineedit(label_text='Low Value (K=0V):')
        self.new_housekeeping_low_value_lineedit.setValidator(QtGui.QDoubleValidator(0, 10, 2, self.new_housekeeping_low_value_lineedit))
        self.rtc_plot_panel.layout().addWidget(self.new_housekeeping_low_value_lineedit, 0, 1, 1, 1)
        self.new_housekeeping_low_value_lineedit.setText(str(self.housekeeping_low_value))

        self.set_new_housekeeping_low_value_pushbutton = QtWidgets.QPushButton('Set Low')
        self.rtc_plot_panel.layout().addWidget(self.set_new_housekeeping_low_value_pushbutton, 0, 2, 1, 1)
        self.set_new_housekeeping_low_value_pushbutton.clicked.connect(self.rtc_set_new_housekeeping_low_high_value)

        self.new_housekeeping_high_value_lineedit = self.gb_make_labeled_lineedit(label_text='High Value (K=10V):')
        self.new_housekeeping_high_value_lineedit.setValidator(QtGui.QDoubleValidator(0, 10, 2, self.new_housekeeping_high_value_lineedit))
        self.rtc_plot_panel.layout().addWidget(self.new_housekeeping_high_value_lineedit, 1, 1, 1, 1)
        self.new_housekeeping_high_value_lineedit.setText(str(self.housekeeping_high_value))

        self.set_new_housekeeping_high_value_pushbutton = QtWidgets.QPushButton('Set High')
        self.rtc_plot_panel.layout().addWidget(self.set_new_housekeeping_high_value_pushbutton, 1, 2, 1, 1)
        self.set_new_housekeeping_high_value_pushbutton.clicked.connect(self.rtc_set_new_housekeeping_low_high_value)

        # Y
        self.y_time_stream_label = QtWidgets.QLabel('', self)
        self.y_time_stream_label.setAlignment(Qt.AlignCenter)
        self.y_time_stream_label.setAttribute(Qt.WA_TranslucentBackground)
        self.rtc_plot_panel.layout().addWidget(self.y_time_stream_label, 4, 0, 2, 1)
        self.y_time_stream_label_2 = QtWidgets.QLabel('', self)
        self.y_time_stream_label_2.setAlignment(Qt.AlignCenter)
        self.y_time_stream_label_2.setAttribute(Qt.WA_TranslucentBackground)
        self.rtc_plot_panel.layout().addWidget(self.y_time_stream_label_2, 4, 1, 2, 1)
        self.y_data_label = QtWidgets.QLabel('Y Data: Y STD:', self)
        self.y_data_label.setAlignment(Qt.AlignCenter)
        self.rtc_plot_panel.layout().addWidget(self.y_data_label, 6, 0, 1, 1)

        # Lakeshore feedback X
        self.new_samples_low_value_lineedit = self.gb_make_labeled_lineedit(label_text='Low Value (Ohms=0V):')
        self.new_samples_low_value_lineedit.setValidator(QtGui.QDoubleValidator(0, 10, 2, self.new_samples_low_value_lineedit))
        self.rtc_plot_panel.layout().addWidget(self.new_samples_low_value_lineedit, 4, 1, 1, 1)
        self.set_new_samples_low_value_pushbutton = QtWidgets.QPushButton('Set Low')
        self.rtc_plot_panel.layout().addWidget(self.set_new_samples_low_value_pushbutton, 4, 2, 1, 1)
        self.set_new_samples_low_value_pushbutton.clicked.connect(self.rtc_set_new_samples_low_high_value)
        self.new_samples_low_value_lineedit.setText(str(self.samples_low_value))

        self.new_samples_high_value_lineedit = self.gb_make_labeled_lineedit(label_text='High Value (Ohms=10V):')
        self.new_samples_high_value_lineedit.setValidator(QtGui.QDoubleValidator(0, 10, 2, self.new_samples_high_value_lineedit))
        self.rtc_plot_panel.layout().addWidget(self.new_samples_high_value_lineedit, 5, 1, 1, 1)
        self.set_new_samples_high_value_pushbutton = QtWidgets.QPushButton('Set High')
        self.rtc_plot_panel.layout().addWidget(self.set_new_samples_high_value_pushbutton, 5, 2, 1, 1)
        self.set_new_samples_high_value_pushbutton.clicked.connect(self.rtc_set_new_samples_low_high_value)
        self.new_samples_high_value_lineedit.setText(str(self.samples_high_value))

        # Main XY Scatter Plot
        self.xy_scatter_label = QtWidgets.QLabel('', self)
        self.xy_scatter_label.setAttribute(Qt.WA_TranslucentBackground)
        self.rtc_plot_panel.layout().addWidget(self.xy_scatter_label, 0, 3, 6, 4)

        # Sample Clip
        self.sample_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Sample_Clip Lo')
        self.sample_clip_lo_lineedit.setText(str(0))
        self.sample_clip_lo_lineedit.setValidator(QtGui.QIntValidator(0, 1000000, self.sample_clip_lo_lineedit))
        self.rtc_plot_panel.layout().addWidget(self.sample_clip_lo_lineedit, 0, 7, 1, 1)
        self.sample_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Sample_Clip Hi')
        self.sample_clip_hi_lineedit.setText(str(1000000))
        self.sample_clip_hi_lineedit.setValidator(QtGui.QIntValidator(0, 1000000, self.sample_clip_hi_lineedit))
        self.rtc_plot_panel.layout().addWidget(self.sample_clip_hi_lineedit, 0, 8, 1, 1)

        # Data Clip
        self.data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Clip_Lo (mK)')
        self.data_clip_lo_lineedit.setText(str(-1000.0))
        self.data_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(-1000, 4000, 5, self.data_clip_lo_lineedit))
        self.rtc_plot_panel.layout().addWidget(self.data_clip_lo_lineedit, 1, 7, 1, 1)
        self.data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Clip_Hi (mK)')
        self.data_clip_hi_lineedit.setText(str(100000.0))
        self.data_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(0, 4000, 5, self.data_clip_hi_lineedit))
        self.rtc_plot_panel.layout().addWidget(self.data_clip_hi_lineedit, 1, 8, 1, 1)

        # Rn Data Clip
        self.data_clip_rn_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Clip_Rn_Lo (mK)')
        self.data_clip_rn_lo_lineedit.setText(str(0.0))
        self.data_clip_rn_lo_lineedit.setValidator(QtGui.QDoubleValidator(0.1, 4000, 5, self.data_clip_rn_lo_lineedit))
        self.rtc_plot_panel.layout().addWidget(self.data_clip_rn_lo_lineedit, 2, 7, 1, 1)
        self.data_clip_rn_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Clip_Rn_Hi (mK)')
        self.data_clip_rn_hi_lineedit.setText(str(1000.0))
        self.data_clip_rn_hi_lineedit.setValidator(QtGui.QDoubleValidator(0.1, 4000, 5, self.data_clip_rn_hi_lineedit))
        self.rtc_plot_panel.layout().addWidget(self.data_clip_rn_hi_lineedit, 2, 8, 1, 1)

        # Clip Actions
        self.data_clip_lo_lineedit.returnPressed.connect(self.rtc_direct_plot)
        self.data_clip_hi_lineedit.returnPressed.connect(self.rtc_direct_plot)
        self.data_clip_rn_lo_lineedit.returnPressed.connect(self.rtc_direct_plot)
        self.data_clip_rn_hi_lineedit.returnPressed.connect(self.rtc_direct_plot)
        self.sample_clip_lo_lineedit.returnPressed.connect(self.rtc_direct_plot)
        self.sample_clip_hi_lineedit.returnPressed.connect(self.rtc_direct_plot)

        # Buttons and Controls
        self.start_pushbutton = QtWidgets.QPushButton('Start', self)
        self.start_pushbutton.clicked.connect(self.rtc_start_stop)
        self.rtc_plot_panel.layout().addWidget(self.start_pushbutton, 3, 7, 1, 1)
        self.start_pushbutton.resize(self.start_pushbutton.minimumSizeHint())
        self.rtc_update_sample_name()
        self.load_data_pushbutton = QtWidgets.QPushButton('Load')
        self.load_data_pushbutton.clicked.connect(self.rtc_load_data)
        self.rtc_plot_panel.layout().addWidget(self.load_data_pushbutton, 3, 8, 1, 1)
        self.plot_data_pushbutton = QtWidgets.QPushButton('Plot')
        self.plot_data_pushbutton.clicked.connect(self.rtc_direct_plot)
        self.rtc_plot_panel.layout().addWidget(self.plot_data_pushbutton, 4, 7, 1, 1)
        self.save_data_pushbutton = QtWidgets.QPushButton('Save')
        self.save_data_pushbutton.clicked.connect(self.rtc_save_plot)
        self.rtc_plot_panel.layout().addWidget(self.save_data_pushbutton, 4, 8, 1, 1)
        self.plot_y_combobox = self.gb_make_labeled_combobox(label_text='Plot?')
        for daq in self.active_daq_dict:
            self.plot_y_combobox.addItem(str(daq))
        self.plot_y_combobox.currentIndexChanged.connect(self.rtc_configure_y_plot_channels)
        self.rtc_plot_panel.layout().addWidget(self.plot_y_combobox, 5, 7, 1, 1)
        self.plot_y_active_checkbox = QtWidgets.QCheckBox('plot')
        self.plot_y_active_checkbox.setChecked(True)
        self.plot_y_active_checkbox.stateChanged.connect(self.rtc_update_active_plot_y_checkbox)
        self.rtc_plot_panel.layout().addWidget(self.plot_y_active_checkbox, 5, 8, 1, 1)
        self.transparent_plots_checkbox = QtWidgets.QCheckBox('Transparent?', self)
        self.rtc_plot_panel.layout().addWidget(self.transparent_plots_checkbox, 6, 7, 1, 1)
        self.transparent_plots_checkbox.setChecked(False)
        self.transparent_plots_checkbox.clicked.connect(self.rtc_direct_plot)
        self.smoothing_factor_combobox = self.gb_make_labeled_combobox(label_text='Smoothing Factor')
        for i in np.arange(0, 1, 0.005):
            self.smoothing_factor_combobox.addItem(str(i))
        self.rtc_plot_panel.layout().addWidget(self.smoothing_factor_combobox, 6, 8, 1, 1)
        self.smoothing_factor_combobox.currentIndexChanged.connect(self.rtc_direct_plot)

    #########################################################
    # Running
    #########################################################

    def rtc_update_active_plot_y_checkbox(self):
        '''
        '''
        plot_daq = int(self.plot_y_combobox.currentText())
        self.active_daq_dict[plot_daq]['plot'] = self.sender().isChecked()

    def rtc_configure_y_plot_channels(self):
        '''
        '''
        plot_daq = int(self.plot_y_combobox.currentText())
        self.plot_y_active_checkbox.setChecked(self.active_daq_dict[plot_daq]['plot'])

    def rtc_update_active_y_checkbox(self):
        '''
        '''
        daq = int(self.daq_y_combobox.currentText())
        self.daq_y_checkbox.setChecked(self.active_daq_dict[daq]['active'])
        name = self.active_daq_dict[daq]['name']
        self.multi_channel_name_lineedit.setText(name)

    def rtc_configure_y_channels(self):
        '''
        '''
        daq = int(self.daq_y_combobox.currentText())
        self.active_daq_dict[daq]['active'] = self.sender().isChecked()
        self.y_channels = []
        for daq, active_dict in self.active_daq_dict.items():
            if active_dict['active']:
                self.y_channels.append(daq)
        if len(self.y_channels) != 1:
            self.channel_combobox.setDisabled(True)
            self.configure_channel_pushbutton.setDisabled(True)
            self.multi_channel_name_lineedit.setDisabled(False)
        else:
            self.channel_combobox.setDisabled(False)
            self.configure_channel_pushbutton.setDisabled(False)
            self.multi_channel_name_lineedit.setDisabled(True)

    def rtc_set_multichannel_name(self):
        '''
        '''
        name = self.multi_channel_name_lineedit.text()
        daq = int(self.daq_y_combobox.currentText())
        self.active_daq_dict[daq]['name'] = name

    def rtc_collector(self, monitor=False):
        '''
        '''
        device = self.rtc_daq_combobox.currentText()
        self.x_data, self.x_stds = [], []
        self.y_data, self.y_stds = [], []
        x_channel = int(self.daq_x_combobox.currentText())
        signal_channels  = [x_channel] + self.y_channels
        int_time = self.int_time_lineedit.text()
        sample_rate = self.sample_rate_lineedit.text()
        thermometer = self.thermometer_combobox.currentText()
        voltage_reduction_factor = self.y_correction_lineedit.text()
        sample_name = self.sample_name_lineedit.text()
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=int_time,
                      sample_rate=sample_rate,
                      device=device)
        daq.signal_channels = signal_channels
        daq.screen_resolution = self.screen_resolution
        self.daq_collector = Collector(self, self.all_data_df)
        self.daq_collector.signals.data_ready.connect(self.rtc_plot_running_from_disk)
        self.daq_collector.signals.finished.connect(self.rtc_update_data)
        if self.dewar != '576':
            self.daq_collector.signals.check_scan.connect(self.rtc_scan_temp)
            self.daq_collector.signals.check_heater.connect(self.rtc_get_lakeshore_temp_control)
        self.daq_collector.add_daq(daq)
        self.qthreadpool.start(self.daq_collector)
        if self.ls372_temp_widget is not None:
            self.ls372_temp_widget.temp_control.ls372_set_monitor_channel(self.thermometer_index)
        i = 0
        while self.started:
            QtWidgets.QApplication.processEvents()
            if len(self.x_data) > 1:
                i += 1

    def rtc_set_first_set_point(self):
        '''
        '''
        if not hasattr(self.ls372_temp_widget, 'temp_control'):
            return None
        temperature = float(self.temp_set_point_high_lineedit.text()) * 1e-3 #K
        self.ls372_temp_widget.temp_control.ls372_set_ramp(0.1, use_ramp=0)
        self.ls372_temp_widget.temp_control.ls372_set_temp_set_point(temperature)
        self.rtc_set_ramp()


    def rtc_read_set_points(self):
        '''
        '''
        rt_set_points_path = os.path.join('bd_settings', 'rt_set_points.txt')
        with open(rt_set_points_path, 'r') as fh:
            set_low, set_high, thermometer = fh.read().split(', ')
        self.temp_set_point_low_lineedit.setText(set_low)
        self.temp_set_point_high_lineedit.setText(set_high)
        self.thermometer_combobox.setCurrentIndex(int(thermometer.strip()))

    def rtc_write_set_points(self):
        '''
        '''
        set_low = self.temp_set_point_low_lineedit.text()
        set_high = self.temp_set_point_high_lineedit.text()
        thermometer = self.thermometer_combobox.currentIndex()
        rt_set_points_path = os.path.join('bd_settings', 'rt_set_points.txt')
        with open(rt_set_points_path, 'w') as fh:
            fh.write('{0}, {1}, {2}'.format(set_low, set_high, thermometer))

    def rtc_start_stop(self):
        '''
        '''
        if self.dewar == '576':
            self.gb_quick_message('Running manual temp control in 576!', msg_type='Warning')
        elif self.heater_range_combobox.currentText() == '0.0000':
            self.gb_quick_message('Heater range is set to zero cannot regulate temp!', msg_type='Warning')
        self.rtc_write_set_points()
        if 'Start' in self.sender().text():
            self.start_time = datetime.now()
            self.sender().setText('Stop DAQ')
            self.started = True
            self.rtc_collector()
            self.data_clip_rn_lo_lineedit.setText('0')
            self.data_clip_rn_hi_lineedit.setText('10000')
            self.sample_clip_lo_lineedit.setText('0')
            self.sample_clip_hi_lineedit.setText('1000000')
            self.data_clip_lo_lineedit.setText('0')
            self.data_clip_hi_lineedit.setText('10000.0')
        else:
            self.daq_collector.stop()
            time.sleep(1)
            self.sender().setText('Start DAQ')
            self.started = False
            self.meta_data['n_samples'] = len(self.x_data)
            save_path = self.rtc_index_file_name()
            self.gb_save_meta_data(save_path, 'txt')
            self.rtc_save(save_path)
            QtWidgets.QApplication.processEvents()
            self.qthreadpool.clear()

    def rtc_get_first_active_daq(self):
        '''
        '''
        active_daqs = []
        for daq, daq_dict in self.active_daq_dict.items():
            if daq_dict['active']:
                active_daqs.append(daq)
        return active_daqs[0]

    def rtc_plot_running_from_disk(self):
        '''
        '''
        print('plotting')
        daq_channel_y = int(self.daq_y_combobox.currentText())
        first_active_daq = self.rtc_get_first_active_daq()
        #import ipdb;ipdb.set_trace()
        print(daq_channel_y)
        save_path = os.path.join('temp_files', 'temp_xy.png')
        image_to_display = QtGui.QPixmap(save_path)
        self.xy_scatter_label.setPixmap(image_to_display)
        save_path = os.path.join('temp_files', 'temp_x.png')
        image_to_display = QtGui.QPixmap(save_path)
        self.x_time_stream_label.setPixmap(image_to_display)
        save_path = os.path.join('temp_files', 'temp_y.png')
        image_to_display = QtGui.QPixmap(save_path)
        now = datetime.now()
        time_delta = now - self.start_time
        time_delta_seconds = time_delta.total_seconds()
        self.y_time_stream_label.setPixmap(image_to_display)
        if hasattr(self, 'daq_collector') and self.daq_collector.all_data_df is not None and hasattr(self.daq_collector, 'x_data_real') and hasattr(self.daq_collector, 'y_data_real'):
            rate = float(self.daq_collector.all_data_df[0]['data'].size) / time_delta_seconds
            x_data_text = 'X Data: {0:.4f} ::: X STD: {1:.4f} (raw) [{2}K=0V {3}K=10V]\n'.format(
                self.daq_collector.all_data_df[0]['data'][-1], self.daq_collector.all_data_df[0]['stds'][-1],
                self.housekeeping_low_value, self.housekeeping_high_value)
            x_data_text += 'X Data: {0:.2f} (mK)::: X STD: {1:.2f} (mK)'.format(self.daq_collector.x_data_real[-1], self.daq_collector.x_stds_real[-1])
            x_data_text += ' {0:.2f} minutes: {1:.2f} mk/min'.format(time_delta_seconds / 60.0, rate)
            self.x_data_label.setText(x_data_text)
            y_data_text = 'Y Data: {0:.4f} ::: Y STD: {1:.4f} (raw) [{2}Ohms=0V {3}Ohms=10V]\n'.format(

                self.daq_collector.all_data_df[first_active_daq]['data'][-1], self.daq_collector.all_data_df[first_active_daq]['stds'][-1],
                self.samples_low_value, self.samples_high_value)
            if len(self.daq_collector.y_data_real) > 0:
                y_data_text += 'Y Data: {0:.2f} (mOhms)::: Y STD: {1:.2f} (mOhms)\n'.format(self.daq_collector.y_data_real[-1], self.daq_collector.y_stds_real[-1])
                self.y_data_label.setText(y_data_text)

    ###################################################
    # Loading Saving and Plotting
    ###################################################

    def rtc_save_plot(self):
        '''
        '''
        save_path = os.path.join('temp_files', 'temp_xy.png')
        new_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', save_path, '')[0]
        new_path = new_path + '.png'
        shutil.copy(save_path, new_path)

    def rtc_load_old_data(self, save_path):
        '''
        '''
        x_data = []
        x_stds = []
        y_data = []
        y_stds = []
        directions = []
        with open(save_path, 'r') as fh:
            for line in fh.readlines():
                x_data.append(float(line.split(',')[0].strip()))
                x_stds.append(float(line.split(',')[1].strip()))
                y_data.append(float(line.split(',')[2].strip()))
                y_stds.append(float(line.split(',')[3].strip()))
                if len(line.split(',')) == 5:
                    directions.append(line.split(',')[4].strip())
        init_data = {
                0: {
                     'data': x_data,
                     'stds': x_stds,
                     'directions': directions,
                    },
                1: {
                     'data': y_data,
                     'stds': y_stds,
                     'directions': directions
                    }
                }
        self.daq_collector.all_data_df = pd.DataFrame.from_dict(init_data)
        self.all_data_df = self.daq_collector.all_data_df

    def rtc_load_data(self):
        '''
        '''
        save_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
        if len(save_path) == 0:
            return None
        self.meta_dict = self.gb_load_meta_data(save_path, 'txt')
        self.status_bar.showMessage(save_path)
        self.rtc_update_calibration_ranges()
        with open(save_path, 'r') as fh:
            try:
                self.daq_collector.all_data_df = pd.read_json(fh)
                self.all_data_df = self.daq_collector.all_data_df
                print(self.all_data_df)
                print(self.all_data_df.T.keys())
            except ValueError:
                self.rtc_load_old_data(save_path)
            if not 'directions' in self.daq_collector.all_data_df.T.keys():
                self.daq_collector.directions = ['up'] * len(self.daq_collector.all_data_df[0]['data'])
            else:
                self.daq_collector.directions = self.daq_collector.all_data_df[0]['directions']
            self.rtc_update_calibration_ranges()
            self.daq_collector.rtc_plot_x_and_y()
            self.daq_collector.rtc_plot_xy(running=True)
            self.rtc_plot_running_from_disk()

    def rtc_update_calibration_ranges(self):
        '''
        '''
        self.samples_low_value = float(self.new_samples_low_value_lineedit.text())
        self.samples_high_value = float(self.new_samples_high_value_lineedit.text())
        self.housekeeping_low_value = float(self.new_housekeeping_low_value_lineedit.text())
        self.housekeeping_high_value = float(self.new_housekeeping_high_value_lineedit.text())

    def rtc_direct_plot(self):
        '''
        '''
        self.daq_collector = Collector(
            self,
            self.all_data_df
            )
        self.rtc_update_calibration_ranges()
        self.daq_collector.rtc_plot_x_and_y()
        self.daq_collector.rtc_plot_xy(running=True)
        self.rtc_plot_running_from_disk()

    def rtc_update_data(self, all_data_df, directions):
        '''
        '''
        self.all_data_df = all_data_df
        self.directions = directions

    def rtc_get_linear_value(self, x, slope, offset):
        '''
        y = m * x + b
        '''
        return slope * x + offset

    def rtc_adjust_x_data(self, x_data=[], x_stds=[]):
        '''
        '''
        thermometer = self.thermometer_combobox.currentText()
        low_value = self.housekeeping_low_value
        high_value = self.housekeeping_high_value
        slope = (high_value - low_value) / 1e1 # K / V
        if thermometer in self.lakeshore_thermometers:
            if len(x_data) > 0:
                x_data = self.rtc_get_linear_value(np.asarray(x_data), slope, low_value)
                x_stds = np.asarray(x_stds) * slope
            else:
                x_data = []
                x_stds = []
        self.x_data_real = x_data #K
        self.x_stds_real = x_stds #K
        return x_data, x_stds

    def rtc_adjust_all_y_data(self):
        '''
        '''
        y_data = []
        y_stds = []
        if self.y_label_combobox.currentText() == 'Arb Units':
            for daq in self.daq_collector.daq.signal_channels[1:]:
                y_data = np.asarray(self.daq_collector.all_data_df[daq]['data'])
                y_data = y_data - np.min(y_data)
                y_stds = np.asarray(self.daq_collector.all_data_df[daq]['stds'])
                self.daq_collector.all_data_df[daq]['data'] = y_data
                self.daq_collector.all_data_df[daq]['stds'] = y_stds
        else:
            voltage_reduction_factor = float(self.y_correction_lineedit.text())
            low_value = self.samples_low_value
            high_value = self.samples_high_value
            slope = (high_value - low_value) / 1e1 # K / V
            for daq in self.daq_collector.all_data_df.keys()[1:]:
                y_data = self.rtc_get_linear_value(np.asarray(self.daq_collector.all_data_df[daq]['data']), slope, low_value) * 1e3 #mOhms
                y_stds = np.asarray(self.daq_collector.all_data_df[daq]['stds']) * slope * 1e3 #mOhms
                self.daq_collector.all_data_df[daq]['data'] = y_data
                self.daq_collector.all_data_df[daq]['stds'] = y_stds
        return y_data, y_stds

    def rtc_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            exc_mode = self.exc_mode_label.text()
            ramp_value = self.ramp_lineedit.text()
            ramp = '{0}'.format(ramp_value.replace('+', '')).replace('.', '_')
            excitation = self.exc_mode_label.text().split(' ')[0]
            sample_name = self.sample_name_lineedit.text().replace('-', '').replace(' ', '_').replace('__', '_')
            file_name = 'rvt_{0}_ramp_{1}_exc_{2}_scan_{3}.txt'.format(sample_name, ramp, excitation, str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def rtc_save(self, save_path=None):
        '''
        '''
        if self.sender().text() == 'Save' or save_path is None:
            save_path = self.rtc_index_file_name()
            save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter=',*.txt,*.dat')[0]
        if len(save_path) > 0:
            ss_save_path = save_path.replace('.txt', '_meta.png')
            screen = QtWidgets.QApplication.primaryScreen()
            screenshot = screen.grabWindow(self.winId())
            screenshot.save(ss_save_path, 'png')
            calibrated_save_path = save_path.replace('.txt', '_calibrated.txt')
            png_save_path = save_path.replace('.txt', '.png')
            shutil.copy(os.path.join('temp_files', 'temp_xy.png'), png_save_path)
            with open(save_path, 'w') as save_handle:
                self.daq_collector.all_data_df.to_json(save_handle)
            x_data, x_stds = self.rtc_adjust_x_data(self.daq_collector.all_data_df[0]['data'], self.daq_collector.all_data_df[0]['stds'])
            y_data, y_stds = self.rtc_adjust_all_y_data()
            self.daq_collector.all_data_df[0]['data'] = x_data
            self.daq_collector.all_data_df[0]['stds'] = x_stds
            with open(calibrated_save_path, 'w') as save_handle:
                self.daq_collector.all_data_df.to_json(save_handle)
            response = self.gb_quick_message('Put data in good data folder?', add_yes=True, add_no=True)
            good_data_folder = os.path.join(self.data_folder, 'good_data')
            if not os.path.exists(good_data_folder):
                os.makedirs(good_data_folder)
            if response == QtWidgets.QMessageBox.Yes:
                # Copy files
                #Data
                good_data_save_path = os.path.join(good_data_folder, os.path.basename(save_path))
                shutil.copy(save_path, good_data_save_path)
                #Json
                json_save_path = save_path.replace('txt', 'json')
                good_data_json_save_path = good_data_save_path.replace('txt', 'json')
                shutil.copy(json_save_path, good_data_json_save_path)
                #PNG
                png_save_path = os.path.join('temp_files', 'temp_xy.png')
                good_data_png_save_path = good_data_save_path.replace('txt', 'png')
                shutil.copy(png_save_path, good_data_png_save_path)
                #Calibrated Data
                good_calibrated_data_save_path = os.path.join(good_data_folder, os.path.basename(calibrated_save_path))
                shutil.copy(calibrated_save_path, good_calibrated_data_save_path)
                #Calibrated Data
                good_data_meta_save_path = good_data_save_path.replace('.txt', '_meta.png')
                shutil.copy(ss_save_path, good_data_meta_save_path)
            else:
                save_path = os.path.join('temp_files', 'temp_xy.png')
                shutil.copy(save_path, png_save_path)
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')
        #response = self.gb_quick_message('Open in pylab?', add_yes=True, add_no=True)
        #if response == QtWidgets.QMessageBox.Yes:
            #pl.show()


class LakeShore372(QRunnable):
    '''
    This is the backend for controlling the Lakeshore so it can be run as a tread
    '''

class Collector(QRunnable):
    '''
    This collects the data and sends signals back to the code once the latest plots ready
    '''
    def __init__(
            self,
            rtc,
            all_data_df
            ):
        '''
        '''
        super(Collector, self).__init__()
        self.transparent_plots = False
        self.signals = CollectorSignals()
        self.monitor_dpi = 96
        self.rtc = rtc
        self.x_channel = 0
        self.colors = ['r', 'm', 'y', 'b', 'k', 'g']
        self.all_data_df = all_data_df
        if 'directions' in self.all_data_df.T.keys():
            self.directions = self.all_data_df.T['directions'][0]
        else:
            self.directions = ['up'] * len(self.all_data_df[0]['data'])

    def add_daq(self, daq):
        '''
        '''
        self.daq = daq
        self.screen_resolution = daq.screen_resolution

    @pyqtSlot()
    def stop(self):
        self.rtc.started = False

    @pyqtSlot()
    def run(self):
        '''
        '''
        i = 0
        signal_channels  = self.daq.signal_channels
        self.rtc.x_fig.get_axes()[0].cla()
        self.rtc.x_fig.get_axes()[1].cla()
        self.rtc.y_fig.get_axes()[0].cla()
        self.rtc.y_fig.get_axes()[1].cla()
        self.rtc.xy_fig.get_axes()[0].cla()
        self.x_data, self.x_stds = [], []
        basic_dict = {
                'data': np.asarray([]), 'stds': np.asarray([]),
                'time_deltas': np.asarray([]), 'temp_deltas': np.asarray([]),
                'directions': np.asarray([])}
        data_frame_dict = {}
        for signal_channel in self.daq.signal_channels:
            data_frame_dict[signal_channel] = basic_dict
        self.all_data_df = pd.DataFrame.from_dict(data_frame_dict)
        self.y_data, self.y_stds = [], []
        self.directions = []
        self.time_deltas = []
        self.temp_deltas = []
        self.x_channel = signal_channels[0]
        self.int_time = self.daq.int_time
        self.sample_rate = self.daq.sample_rate
        self.transparent_plots = self.rtc.transparent_plots_checkbox.isChecked()
        while self.rtc.started:
            data_dict = self.daq.run()
            sleep_time = float(self.daq.int_time) / 1e3
            time.sleep(sleep_time)
            data_point_df = pd.DataFrame.from_dict(data_dict)
            self.transparent_plots = self.rtc.transparent_plots_checkbox.isChecked()
            self.directions.append(self.rtc.drift_direction)
            if len(self.directions) > 1:
                last_time = self.rtc.start_time
                time_now = datetime.now()
                time_delta = time_now - last_time
                time_delta = time_delta.microseconds
                temp_delta = self.all_data_df[0]['data'] - data_point_df[0]['mean']
                self.time_deltas.append(time_delta)
                #self.temp_deltas.append(temp_delta[0])
            for signal_channel in self.daq.signal_channels:
                mean = data_point_df[signal_channel]['mean']
                std = data_point_df[signal_channel]['std']
                self.all_data_df[signal_channel]['data'] = np.insert(
                        self.all_data_df[signal_channel]['data'],
                        self.all_data_df[signal_channel]['data'].size,
                        mean)
                self.all_data_df[signal_channel]['stds'] = np.insert(
                        self.all_data_df[signal_channel]['stds'],
                        self.all_data_df[signal_channel]['stds'].size,
                        std)
                self.all_data_df[signal_channel]['directions'] = self.directions
                self.all_data_df[signal_channel]['time_deltas'] = self.time_deltas
                self.all_data_df[signal_channel]['temp_deltas'] = self.temp_deltas
            last_time = datetime.now()
            self.rtc_plot_running()
            self.signals.data_ready.emit() #data_dict)
            if i % 15 == 0 and i % 60 != 0:
                self.signals.check_scan.emit(False, [self.all_data_df[0]['data'][-1]], [self.all_data_df[0]['stds'][-1]])
            if i % 60 == 0:
                self.signals.check_heater.emit()
            i += 1
        self.signals.finished.emit(self.all_data_df, self.directions)

    def rtc_plot_running(self):
        '''
        '''
        self.rtc_plot_x_and_y()
        self.rtc_plot_xy(running=True)


    def rtc_adjust_x_data_point(self, x):
        '''
        '''
        thermometer = self.rtc.thermometer_combobox.currentText()
        low_value = self.rtc.housekeeping_low_value
        high_value = self.rtc.housekeeping_high_value
        if thermometer in self.rtc.lakeshore_thermometers:
            slope = (high_value - low_value) / 1e1 # Y range / 10V
            adjusted_x = self.rtc.rtc_get_linear_value(x, slope, low_value)#
        else:
            adjusted_x = np.nan
        return adjusted_x


    def rtc_adjust_x_data(self):
        '''
        '''
        x_data = []
        x_stds = []
        thermometer = self.rtc.thermometer_combobox.currentText()
        low_value = self.rtc.housekeeping_low_value
        high_value = self.rtc.housekeeping_high_value
        if thermometer in self.rtc.lakeshore_thermometers:
            slope = (high_value - low_value) / 1e1 # Y range / 10V
            x_data = self.rtc.rtc_get_linear_value(np.asarray(self.all_data_df[0]['data']), slope, low_value) * 1e3 #mK
            x_stds = np.asarray(self.all_data_df[0]['data']) * slope
        if type(x_data) == np.float64:
            x_data = np.asarray([x_data])
            x_stds = np.asarray([x_stds])
        self.x_data_real = x_data #mK
        self.x_stds_real = x_stds #mK
        return x_data[:-1], x_stds[:-1]

    def rtc_adjust_y_data_point(self, y):
        '''
        '''
        low_value = self.rtc.samples_low_value
        high_value = self.rtc.samples_high_value
        slope = (high_value - low_value) / 10 # K/ V
        adjusted_y = self.rtc.rtc_get_linear_value(y, slope, low_value) * 1e3 #mOhms
        return adjusted_y

    def rtc_adjust_y_data(self, daq):
        '''
        '''
        y_data = []
        y_stds = []
        voltage_reduction_factor = 1.0
        if self.rtc.y_label_combobox.currentText() == 'Arb Units':
            y_data = np.asarray(self.all_data_df[daq]['data']) - np.min(self.all_data_df[daq]['data'])
            y_stds = np.asarray(self.all_data_df[daq]['stds'])
        else:
            low_value = self.rtc.samples_low_value
            high_value = self.rtc.samples_high_value
            slope = (high_value - low_value) / 10 # K/ V
            y_data = self.rtc.rtc_get_linear_value(np.asarray(self.all_data_df[daq]['data']), slope, low_value) * 1e3 #mOhms
            y_stds = np.asarray(self.all_data_df[daq]['stds']) * slope * 1e3 #mOhms
        if type(y_data) == np.float64:
            y_data = np.asarray([y_data])
            y_stds = np.asarray([y_stds])
        self.y_data_real = y_data[:-1]
        self.y_stds_real = y_stds[:-1]
        return y_data[:-1], y_stds[:-1]

    def rtc_plot_x_and_y(self):
        '''
        '''
        if not hasattr(self, 'all_data_df'):
            return None
        change_indicies = list(np.where(np.asarray(self.directions[:-1]) != np.asarray(self.directions[1:]))[0])
        change_indicies.append(-1)
        fig_x = self.rtc.x_fig
        ax_x = fig_x.get_axes()[0]
        ax_x_twinx = fig_x.get_axes()[1]
        ax_x.set_yticks(np.linspace(ax_x.get_ybound()[0], ax_x.get_ybound()[1], 4))
        ax_x_twinx.set_yticks(np.linspace(ax_x_twinx.get_ybound()[0], ax_x_twinx.get_ybound()[1], 4))
        ax2_x = fig_x.get_axes()[2]
        ax_x.cla()
        ax_x_twinx.cla()
        ax2_x.cla()
        ax2_x.plot([0, 10], [self.rtc.housekeeping_low_value, self.rtc.housekeeping_high_value], 'k', alpha=0.5)
        ax2_x.set_xlabel('(V)', fontsize=8)
        ax2_x.set_ylabel('(K)', fontsize=8)
        ax_x.set_xlabel('Sample', fontsize=8)
        ax_x.set_ylabel('X_DAQ_OUT ($V$)', fontsize=8)
        ax_x_twinx.set_ylabel('(mK)', fontsize=8)
        fig_y = self.rtc.y_fig
        ax_y = fig_y.get_axes()[0]
        ax_y_twinx = fig_y.get_axes()[1]
        ax_y.set_yticks(np.linspace(ax_y.get_ybound()[0], ax_y.get_ybound()[1], 4))
        #ax_y_twinx.set_yticks(np.linspace(ax_y_twinx.get_ybound()[0], ax_y_twinx.get_ybound()[1], 4))
        ax2_y = fig_y.get_axes()[2]
        ax_y.cla()
        ax_y_twinx.cla()
        ax2_y.cla()
        ax2_y.plot([0, 10], [self.rtc.samples_low_value, self.rtc.samples_high_value], 'k', alpha=0.5)
        ax2_y.set_xlabel('(V)', fontsize=8)
        ax2_y.set_ylabel('($\Omega$)', fontsize=8)
        ax_y.set_xlabel('Sample', fontsize=8)
        ax_y.set_ylabel('Y_DAQ_OUT ($V$)', fontsize=8)
        ax_y_twinx.set_ylabel('(m$\Omega$)', fontsize=8)
        label = None
        try:
            if hasattr(self, 'daq') and self.all_data_df[0]['data'].size > 1:
                label_str = 'DAQ {0} Sample {1}'.format(self.x_channel, len(self.all_data_df[0]['data']))
                label = label_str
        except TypeError:
            import ipdb;ipdb.set_trace()
        for i, change_index in enumerate(change_indicies):
            if i == 0:
                drift_start_index = 0
            drift_end_index = change_index
            color = 'r'
            if len(self.directions) > 0:
                if self.directions[change_index] == 'down':
                    color = 'b'
            if type(self.all_data_df[0]['data']) == list or self.all_data_df[0]['data'].size <= 1:
                pass
            else:
                x_data = self.all_data_df[0]['data'][drift_start_index:drift_end_index]
                x_stds = self.all_data_df[0]['stds'][drift_start_index:drift_end_index]
                if change_index == -1:
                    x_range = range(drift_start_index, drift_start_index + len(x_data))
                else:
                    x_range = range(drift_start_index, drift_end_index)
                ax_x.errorbar(x_range, x_data, yerr=x_stds, marker='.', ms=0.5, color=color, alpha=0.75, linestyle='None', label=label)
                x_data, x_stds = self.rtc.rtc_adjust_x_data(x_data, x_stds)
                #ax_x_twinx.plot(range(len(x_data)), np.asarray(x_data) * 1e3, #mK
                        #marker='x', ms=0.5, color=color, alpha=0.0,
                        #linestyle='None', label=label)
                scaled_x_point = self.rtc_adjust_x_data_point(self.all_data_df[0]['data'][-1])
                ax2_x.plot(self.all_data_df[0]['data'][-1], scaled_x_point, '*', ms=3)
                for y_channel in self.all_data_df.keys()[1:]:
                    y_data = self.all_data_df[y_channel]['data'][drift_start_index:drift_end_index]
                    yerr = self.all_data_df[y_channel]['stds'][drift_start_index:drift_end_index]
                    y_range = x_range #range(drift_start_index, drift_start_index + len(y_data)),
                    if self.directions[change_index] == 'down':
                        color = self.colors[y_channel + 2]
                    else:
                        color = self.colors[y_channel - 1]
                    ax_y.errorbar(
                            y_range,
                            y_data, yerr=yerr,
                            marker='.', ms=0.5, color=color, alpha=0.75,
                            linestyle='None', label=str(y_channel))
                    temp_y_data, temp_y_stds = self.rtc_adjust_y_data(y_channel)
                    temp_x_data = range(drift_start_index, drift_start_index + len(y_data) - 1)
                    if len(temp_x_data) != len(temp_y_data):
                        temp_x_data = range(drift_start_index, drift_start_index + len(y_data))
                    ax_y_twinx.plot(
                            temp_x_data,
                            temp_y_data[drift_start_index:drift_start_index + len(temp_x_data)],
                            marker='x', ms=0.5, color=color, alpha=0.0,
                            linestyle='None', label=str(y_channel))
                    scaled_y_point = self.rtc_adjust_y_data_point(self.all_data_df[y_channel]['data'][-1]) * 1e-3 #back to K
                    ax2_y.plot(self.all_data_df[y_channel]['data'][-1], scaled_y_point, '*', color=self.colors[y_channel - 1], ms=3)
                drift_start_index = change_index
        handles, labels = ax_x.get_legend_handles_labels()
        if len(handles) > 0:
            label_str = 'DAQ {0} Sample {1}'.format(self.x_channel, len(self.all_data_df[0]['data']))
            labels[0] = label_str
        save_path = os.path.join('temp_files', 'temp_x.png')
        fig_x.savefig(save_path, transparent=self.transparent_plots)
        handles, labels = ax_y.get_legend_handles_labels()
        if len(handles) > 0:
            label_str = 'DAQ {0} Sample {1}'.format(self.x_channel, len(self.all_data_df[0]['data']))
            labels[0] = label_str
        save_path = os.path.join('temp_files', 'temp_y.png')
        fig_y.savefig(save_path, transparent=self.transparent_plots)

    def rtc_plot_xy(self, running=False, file_name=''):
        '''
        '''
        if not hasattr(self, 'all_data_df'):
            return None
        if type(self.all_data_df[0]['data']) == list or self.all_data_df[0]['data'].size == 0:
            return None
        fig = self.rtc.xy_fig
        ax = fig.get_axes()[0]
        ax.cla()
        y_label = self.rtc.y_label_combobox.currentText()
        x_label = 'Temperature ($mK$)'
        print('run', running)
        if running:
            x_data, x_stds = self.rtc_adjust_x_data()
            print(x_data, x_stds)
            for i, daq in enumerate(self.all_data_df.keys()[1:]):
                if self.rtc.active_daq_dict[daq]['plot']:
                    y_data, y_stds = self.rtc_adjust_y_data(daq)
                    if np.mean(y_data) > 1e3:
                        y_data *= 1e-3
                        y_stds *= 1e-3
                        y_label = y_label.replace('$m','$')
                    if np.mean(x_data) > 1e3:
                        x_data *= 1e-3
                        x_stds *= 1e-3
                        x_label = x_label.replace('$m','$')
                    fig = self.rtc_plot_drifts(fig, x_data, x_stds, y_data, y_stds, daq)
                    ax.set_xlabel(x_label, fontsize=12)
                    ax.set_ylabel(y_label, fontsize=12)
                    #import ipdb;ipdb.set_trace()
            save_path = os.path.join('temp_files', 'temp_xy.png')
            fig.savefig(save_path, transparent=self.transparent_plots)
        else:
            self.x_data, self.x_stds = self.rtc_adjust_x_data()
            fig = self.rtc_plot_drifts(fig, self.x_data, self.x_stds, self.y_data, self.y_stds)
            fig.set_canvas(pl.gcf().canvas)
            ax.tick_params(axis='x', labelsize=16)
            ax.tick_params(axis='y', labelsize=16)
            ax.set_xlabel('Temperature ($mK$)', fontsize=14)
            ax.set_ylabel(y_label, fontsize=12)
            save_path = os.path.join('temp_files', 'temp_xy.png')
            fig.savefig(save_path, transparent=self.transparent_plots)
            if hasattr(self, 'daq'):
                for daq in self.daq.signal_channels[1:]:
                    self.y_data, self.y_stds = self.rtc_adjust_y_data()
                    fig = self.rtc_plot_drifts(fig, self.x_data, self.x_stds, self.y_data, self.y_stds, daq)
                    ax.tick_params(axis='x', labelsize=16)
                    ax.tick_params(axis='y', labelsize=16)
                    ax.set_xlabel('Temperature ($mK$)', fontsize=14)
                    ax.set_ylabel(y_label, fontsize=12)
                save_path = os.path.join('temp_files', 'temp_xy.png')
                fig.savefig(save_path, transparent=self.transparent_plots)

    def rtc_bin_smooth_data(self, x_data, y_data, smoothing_factor=0.01):
        '''
        '''
        if smoothing_factor == 0.0:
            return vector
        xy = zip(*sorted(zip(x_data, y_data), key=lambda pair: pair[0]))
        import ipdb;ipdb.set_trace()
        for i, value in enumerate(sorted(vector)):
            low_index = i
            hi_index = i + N
            if hi_index > len(vector) - 1:
                hi_index = len(vector) - 1
            averaged_value = np.mean(vector[low_index:hi_index])
            if np.isnan(averaged_value):
                np.put(averaged_vector, i, 0.0)
            else:
                np.put(averaged_vector, i, averaged_value)
        return averaged_vector


    def rtc_get_rn_and_tc(self, daq):
        '''
        '''
        sample_clip_lo = int(self.rtc.sample_clip_lo_lineedit.text())
        sample_clip_hi = int(self.rtc.sample_clip_hi_lineedit.text())
        data_clip_lo = float(self.rtc.data_clip_lo_lineedit.text())
        data_clip_hi = float(self.rtc.data_clip_hi_lineedit.text())
        x_data, x_stds = self.rtc_adjust_x_data()
        #y_data, y_stds = self.rtc_adjust_y_data()
        if self.rtc.gb_is_float(self.rtc.data_clip_rn_lo_lineedit.text()):
            data_clip_rn_lo = float(self.rtc.data_clip_rn_lo_lineedit.text())
        else:
            data_clip_rn_lo = 0.0
        if self.rtc.gb_is_float(self.rtc.data_clip_rn_hi_lineedit.text()):
            data_clip_rn_hi = float(self.rtc.data_clip_rn_hi_lineedit.text())
        else:
            data_clip_rn_hi = 1000.0
        excitation = self.rtc.exc_mode_label.text().split(' ')[0]
        unit = self.rtc.exc_mode_label.text().split(' ')[1]
        ramp_value = self.rtc.ramp_lineedit.text().replace('+', '')
        thermometer = self.rtc.thermometer_combobox.currentText()
        y_data = np.asarray(self.all_data_df[daq]['data'][sample_clip_lo:sample_clip_hi])
        smoothing_factor = 0.1
        if hasattr(self.rtc, 'smoothing_factor_combobox'):
            smoothing_factor = float(self.rtc.smoothing_factor_combobox.currentText())
            if smoothing_factor > 0:
                y_data = self.rtc.ftsy_running_mean(y_data, smoothing_factor=smoothing_factor)
                #y_data = self.rtc_bin_smooth_data(x_data, y_data, smoothing_factor=smoothing_factor)
        x_data = np.asarray(x_data[sample_clip_lo:sample_clip_hi])
        x_data_selector = np.where(np.logical_and(data_clip_lo < x_data, x_data < data_clip_hi))
        y_data = y_data[x_data_selector]
        x_data = x_data[x_data_selector]
        if len(x_data) == 0:
            normal_resistance = np.nan
            transition_temperature = np.nan
            half_rn = np.nan
        elif self.rtc.y_label_combobox.currentText() == 'Arb Units':
            y_data = np.asarray(y_data) - np.min(y_data)
            rn_data_selector = np.where(np.logical_and(data_clip_rn_lo < x_data, x_data < data_clip_rn_hi))
            normal_resistance = np.mean(y_data[rn_data_selector])
            half_rn = 0.5 * normal_resistance
            tc_idx = (np.abs(y_data - half_rn)).argmin()
            transition_temperature = np.asarray(x_data)[tc_idx]
        else:
            rn_data_selector = np.where(np.logical_and(data_clip_rn_lo < x_data, x_data < data_clip_rn_hi))
            normal_resistance = np.mean(y_data[rn_data_selector])
            half_rn = 0.5 * normal_resistance
            tc_idx = (np.abs(np.asarray(y_data) - half_rn)).argmin()
            transition_temperature = np.asarray(x_data)[tc_idx]
            normal_resistance = self.rtc_adjust_y_data_point(normal_resistance)
            half_rn = 0.5 * normal_resistance
            #half_rn = self.rtc_adjust_y_data_point(y_data[tc_idx])
        units = '$m\Omega$'
        if normal_resistance > 1e3:
            normal_resistance *= 1e-3
            half_rn *= 1e-3
            units = units.replace('$m', '$')
        t_units = '$mK$'
        if transition_temperature > 1e3:
            transition_temperature *= 1e-3
            t_units = t_units.replace('$m', '$')
        scan_info = '$R_n$ ({0}): {1:.2f} {2}\n'.format(units, normal_resistance, daq)
        scan_info += '$T_c$ ({0}): {1:.2f} {2}\n'.format(t_units, transition_temperature, daq)
        scan_info += 'Exc: {0:.2f} {1}\n'.format(float(excitation), unit)
        scan_info += 'Ramp: {0} K/min\n'.format(ramp_value)
        scan_info += 'Sensor: {0}\n'.format(thermometer)
        return transition_temperature, normal_resistance, half_rn, scan_info, units, t_units

    def rtc_plot_drifts(self, fig, x_data, x_stds, y_data, y_stds, daq):
        '''
        '''
        #import ipdb;ipdb.set_trace()
        if self.all_data_df[0]['data'].size == 0:
            return fig
        if not self.rtc.gb_is_float(self.rtc.sample_clip_lo_lineedit.text()):
            return fig
        if not self.rtc.gb_is_float(self.rtc.sample_clip_hi_lineedit.text()):
            return fig
        if not self.rtc.gb_is_float(self.rtc.data_clip_lo_lineedit.text()):
            return fig
        if not self.rtc.gb_is_float(self.rtc.data_clip_hi_lineedit.text()):
            return fig
        if len(x_data) == 0:
            return fig
        ax_plot = fig.get_axes()[0]
        ax_legend = fig.get_axes()[1]
        ax_legend.set_axis_off()
        sample_name = self.rtc.sample_name_lineedit.text()
        # Analyze Tc
        transition_temperature, normal_resistance, half_rn, label, units, t_units = self.rtc_get_rn_and_tc(daq)
        sample_clip_lo = int(self.rtc.sample_clip_lo_lineedit.text())
        sample_clip_hi = int(self.rtc.sample_clip_hi_lineedit.text())
        data_clip_lo = float(self.rtc.data_clip_lo_lineedit.text())
        data_clip_hi = float(self.rtc.data_clip_hi_lineedit.text())
        if self.rtc.gb_is_float(self.rtc.data_clip_rn_lo_lineedit.text()):
            data_clip_rn_lo = float(self.rtc.data_clip_rn_lo_lineedit.text())
        else:
            data_clip_rn_lo = 0.0
        if self.rtc.gb_is_float(self.rtc.data_clip_rn_hi_lineedit.text()):
            data_clip_rn_hi = float(self.rtc.data_clip_rn_hi_lineedit.text())
        else:
            data_clip_rn_hi = 1000.0
        selected_directions = np.asarray(self.directions)[sample_clip_lo:sample_clip_hi]
        change_indicies = list(np.where(selected_directions[:-1] != selected_directions[1:])[0])
        change_indicies.append(-1)
        smoothing_factor = 0.1
        if hasattr(self.rtc, 'smoothing_factor_combobox'):
            smoothing_factor = float(self.rtc.smoothing_factor_combobox.currentText())
            if smoothing_factor > 0:
                y_data = self.rtc.ftsy_running_mean(y_data, smoothing_factor=smoothing_factor)
                x_data = x_data[:-1]
                y_data = y_data[:-1]
        plot_x_data = x_data[sample_clip_lo:sample_clip_hi]
        plot_x_stds = x_stds[sample_clip_lo:sample_clip_hi]
        plot_y_data = y_data[sample_clip_lo:sample_clip_hi]
        plot_y_stds = y_stds[sample_clip_lo:sample_clip_hi]
        for i, change_index in enumerate(change_indicies):
            if i == 0:
                drift_start_index = 0
            drift_end_index = change_index
            color = self.colors[daq - 1]
            if len(selected_directions) > 0:
                if selected_directions[change_index] == 'down':
                    color = self.colors[daq + 2]
            if change_index == -1:
                final_plot_x_data = plot_x_data[drift_start_index:]
                final_plot_x_stds = plot_x_stds[drift_start_index:]
                final_plot_y_data = plot_y_data[drift_start_index:]
                final_plot_y_stds = plot_y_stds[drift_start_index:]
            else:
                final_plot_x_data = plot_x_data[drift_start_index:change_index]
                final_plot_x_stds = plot_x_stds[drift_start_index:change_index]
                final_plot_y_data = plot_y_data[drift_start_index:change_index]
                final_plot_y_stds = plot_y_stds[drift_start_index:change_index]
            selector = np.where(np.logical_and(data_clip_lo < final_plot_x_data, final_plot_x_data < data_clip_hi))

            rn_selector = np.where(np.logical_and(data_clip_rn_lo < final_plot_x_data, final_plot_x_data < data_clip_rn_hi))

            hndls, lbls = ax_plot.get_legend_handles_labels()
            if '$R_n$' in lbls:
                ax_plot.plot(final_plot_x_data[rn_selector], np.ones(len(final_plot_x_data[rn_selector])) * normal_resistance,
                             color='k', lw=5, alpha=0.4)
            else:
                ax_plot.plot(final_plot_x_data[rn_selector], np.ones(len(final_plot_x_data[rn_selector])) * normal_resistance,
                             color='k', lw=5, alpha=0.4, label='$R_n$')
            print()
            print(final_plot_x_data[selector], final_plot_y_data[selector])
            ax_plot.errorbar(final_plot_x_data[selector], final_plot_y_data[selector],
                             xerr=final_plot_x_stds[selector], yerr=final_plot_y_stds[selector],
                             marker='x', ms=0.75, color=color, alpha=0.75,
                             linestyle='-')
            rn_label = None
            tc_label = None
            name = self.rtc.active_daq_dict[daq]['name']
            if i == 0:
                rn_label = '{0}: $R_n$ {1:.2f} {2}'.format(name, normal_resistance, units)
                tc_label = '{0}: $T_c$ {1:.2f} {2}'.format(name, transition_temperature, t_units)
            ax_plot.plot(final_plot_x_data[rn_selector], np.ones(len(final_plot_x_data[rn_selector])) * normal_resistance,
                         color='k', lw=5, alpha=0.4, label=rn_label)
            ax_plot.errorbar(final_plot_x_data[selector], final_plot_y_data[selector],
                             xerr=final_plot_x_stds[selector], yerr=final_plot_y_stds[selector],
                             marker='x', ms=0.75, color=color, alpha=0.75, linestyle='-')
            if not (np.isnan(normal_resistance) or np.isnan(transition_temperature)):
                print(normal_resistance, transition_temperature)
                ax_plot.plot(transition_temperature, half_rn, '*', ms=25, color='g', label=tc_label)
            drift_start_index = change_index
            handles, labels = ax_plot.get_legend_handles_labels()
            if len(final_plot_x_data[selector]) > 0 and '{0} up'.format(name) not in labels:
                ax_plot.plot(final_plot_x_data[selector][-1], final_plot_y_data[selector][-1], linestyle=None,
                             marker='*', ms=0.75, color=self.colors[daq - 1], alpha=0.75, label='{0} up'.format(name))
                ax_plot.plot(final_plot_x_data[selector][-1], final_plot_y_data[selector][-1], linestyle=None,
                             marker='*', ms=0.75, color=self.colors[daq + 2], alpha=0.75, label='{0} down'.format(name))
        handles, labels = ax_plot.get_legend_handles_labels()
        frameon = not self.transparent_plots
        ax_legend.legend(handles, labels, loc='best', frameon=frameon, numpoints=1)
        if len(self.all_data_df.keys()[1:]) > 1:
            sample_name = 'Multi Channel RT'
        ax_plot.set_title(sample_name, fontsize=14)
        return fig


class CollectorSignals(QObject):
    '''
    This collects the data and sends signals back to the cod e
    '''

    data_ready = pyqtSignal()
    check_scan = pyqtSignal(bool, list, list)
    check_heater = pyqtSignal()
    finished = pyqtSignal(pd.DataFrame, list)
    temp_ready = pyqtSignal(float)
