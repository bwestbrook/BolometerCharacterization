import time
import shutil
import os
import simplejson
import pickle as pkl
import numpy as np
import pandas as pd
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import *
from bd_lib.saving_manager import SavingManager
from bd_lib.mpl_canvas import MplCanvas
from GuiBuilder.gui_builder import GuiBuilder, GenericClass
# Import Last

class RTCollector(QtWidgets.QWidget, GuiBuilder):

    def __init__(
            self,
            daq_settings,
            status_bar,
            screen_resolution,
            monitor_dpi,
            ls372_temp_widget,
            ls372_samples_widget,
            data_folder):
        '''
        '''
        super(RTCollector, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.mplc = MplCanvas(self, screen_resolution, monitor_dpi)
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
                left=0.16,
                right=0.98,
                wspace=0.45,
                hspace=0.2,
                bottom=0.25,
                top=0.88,
                frac_screen_height=0.15,
                frac_screen_width=0.23)
        self.y_fig = self.mplc.mplc_create_two_pane_plot(
                name='y_fig',
                left=0.16,
                right=0.98,
                wspace=0.45,
                hspace=0.2,
                bottom=0.25,
                top=0.88,
                frac_screen_height=0.15,
                frac_screen_width=0.23)
        self.xy_fig = self.mplc.mplc_create_fig_with_legend_axes(
                name='xy_fig',
                left=0.12,
                right=0.95,
                bottom=0.2,
                top=0.9,
                frac_screen_height=0.35,
                frac_screen_width=0.35,
                wspace=0.1,
                hspace=0.25)

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
                'X110595 (Cu Box)': 10
                }
        self.lakeshore_thermometers = {
                'PT100 (MXC)': 6,
                'X110595 (Cu Box)': 10
                }
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.rtc_plot_panel = QtWidgets.QWidget(self)
        grid_2 = QtWidgets.QGridLayout()
        self.rtc_plot_panel.setLayout(grid_2)
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = data_folder
        self.saving_manager = SavingManager(self, self.data_folder, self.rtc_save, 'RT')
        daq_collector = Collector(self)
        self.rtc_populate()
        if self.ls372_temp_widget is not None:
            self.status_bar.messageChanged.connect(self.rtc_update_panel)
        self.qthreadpool = QThreadPool()
        self.resize(self.minimumSizeHint())
        self.rtc_read_set_points()
        self.rtc_set_first_set_point()

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
        daq_collector = Collector(self)
        daq_collector.rtc_plot_x_and_y()
        daq_collector.rtc_plot_xy()
        self.rtc_plot_running_from_disk()

    #############################################
    # DAQ Panel
    #############################################

    def rtc_daq_panel(self):
        '''
        '''
        self.daq_label = QtWidgets.QLabel('Configure DAQ and Samples', self)
        self.layout().addWidget(self.daq_label, 0, 0, 1, 3)
        self.daq_label.setAlignment(Qt.AlignCenter)
        # Device
        self.rtc_daq_combobox = self.gb_make_labeled_combobox(label_text='Device')
        for daq in self.daq_settings:
            self.rtc_daq_combobox.addItem(daq)
        self.layout().addWidget(self.rtc_daq_combobox, 1, 0, 1, 1)
        # DAQ X
        self.daq_x_combobox = self.gb_make_labeled_combobox(label_text='DAQ_X:')
        for daq in range(0, 8):
            self.daq_x_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_x_combobox, 1, 1, 1, 1)
        # DAQ Y
        self.daq_y_combobox = self.gb_make_labeled_combobox(label_text='DAQ_Y:')
        for daq in range(0, 8):
            self.daq_y_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_y_combobox, 1, 2, 1, 1)
        self.daq_y_combobox.setCurrentIndex(1)
        self.rtc_daq_combobox.setCurrentIndex(1)
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int_Time (ms):')
        self.int_time_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.int_time_lineedit))
        self.layout().addWidget(self.int_time_lineedit, 2, 0, 1, 1)
        self.int_time_lineedit.setText('100')
        self.int_time = self.int_time_lineedit.text()
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample_Rate (Hz)')
        self.sample_rate_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e5, 2, self.sample_rate_lineedit))
        self.layout().addWidget(self.sample_rate_lineedit, 2, 1, 1, 1)
        self.sample_rate_lineedit.setText('10000')
        self.sample_rate = self.sample_rate_lineedit.text()
        # Sample Configure 
        configure_channel_pushbutton = QtWidgets.QPushButton('Configure And Scan', self)
        self.layout().addWidget(configure_channel_pushbutton, 3, 1, 1, 2)
        configure_channel_pushbutton.resize(configure_channel_pushbutton.minimumSizeHint())
        configure_channel_pushbutton.clicked.connect(self.rtc_edit_lakeshore_channel)
        self.channel_combobox = self.gb_make_labeled_combobox(label_text='Channel')
        self.layout().addWidget(self.channel_combobox, 3, 0, 1, 1)
        for channel in range(1, 17):
            self.channel_combobox.addItem(str(channel))
        self.channel_combobox.addItem('SQUID')
        # Sample Name
        self.exc_mode_label = self.gb_make_labeled_label(label_text='Lakeshore_Info:')
        self.exc_mode_label.setText('0 0 0 0 0')
        self.layout().addWidget(self.exc_mode_label, 4, 0, 1, 1)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample_Name:')
        self.layout().addWidget(self.sample_name_lineedit, 4, 1, 1, 2)
        if self.ls372_samples_widget is None:
            return
        self.ls372_samples_widget.channels.ls372_scan_channel(index=1)

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
        update_ls372_settings_pushbutton = QtWidgets.QPushButton('Update Settings', self)
        update_ls372_settings_pushbutton.clicked.connect(self.rtc_edit_lakeshore_temp_control)
        update_ls372_settings_pushbutton.resize(update_ls372_settings_pushbutton.minimumSizeHint())
        self.layout().addWidget(update_ls372_settings_pushbutton, 2, 8, 1, 2)

        read_ls372_settings_pushbutton = QtWidgets.QPushButton('Get Lakeshore State', self)
        read_ls372_settings_pushbutton.clicked.connect(self.rtc_get_lakeshore_temp_control)
        read_ls372_settings_pushbutton.resize(read_ls372_settings_pushbutton.minimumSizeHint())
        self.layout().addWidget(read_ls372_settings_pushbutton, 3, 7, 1, 3)

        self.rtc_get_lakeshore_channel_info()
        self.thermometer_combobox.setCurrentIndex(0)
        self.thermometer_combobox.currentIndexChanged.connect(self.rtc_scan_new_lakeshore_channel)
        self.thermometer_combobox.setCurrentIndex(1)
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
        new_ramp = float(self.ramp_lineedit.text())
        self.ls372_temp_widget.temp_control.set_run_function('ls372_set_ramp', new_ramp)
        self.qthreadpool.start(self.ls372_temp_widget.temp_control)
        self.meta_data['Temp Ramp (K/min)'] = new_ramp

    def rtc_set_new_housekeeping_low_high_value(self):
        '''
        '''
        low_value = float(self.new_housekeeping_low_value_lineedit.text())
        high_value = float(self.new_housekeeping_high_value_lineedit.text())
        data_source = 'kelvin'
        self.ls372_temp_widget.temp_control.ls372_set_analog_low_high_value(self.thermometer_index, data_source, low_value, high_value)
        self.housekeeping_high_value = high_value
        self.housekeeping_low_value = low_value

    def rtc_set_new_samples_low_high_value(self):
        '''
        '''
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
        current_temp = x_data[-1]
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
        thermometer = self.thermometer_combobox.currentText()
        self.thermometer_index = self.thermometers[thermometer]
        self.ls372_temp_widget.ls372_scan_channel(index=self.thermometer_index)
        self.ls372_temp_widget.analog_outputs.ls372_monitor_channel_aux_analog(self.thermometer_index, self.ls372_temp_widget.analog_outputs.analog_output_aux)

    def rtc_edit_lakeshore_channel(self):
        '''
        '''
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
        self.thermometer_combobox.setCurrentIndex(1)
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
        if channel != 'SQUID':
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
        print(self.housekeeping_low_value)
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
        self.data_clip_lo_lineedit.setText(str(0.0))
        self.data_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(0, 4000, 5, self.data_clip_lo_lineedit))
        self.rtc_plot_panel.layout().addWidget(self.data_clip_lo_lineedit, 1, 7, 1, 1)
        self.data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Clip_Hi (mK)')
        self.data_clip_hi_lineedit.setText(str(10000.0))
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
        self.data_clip_lo_lineedit.returnPressed.connect(self.rtc_plot_running_from_disk)
        self.data_clip_hi_lineedit.returnPressed.connect(self.rtc_plot_running_from_disk)
        self.sample_clip_lo_lineedit.returnPressed.connect(self.rtc_plot_running_from_disk)
        self.sample_clip_hi_lineedit.returnPressed.connect(self.rtc_plot_running_from_disk)

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
        self.transparent_plots_checkbox = QtWidgets.QCheckBox('Transparent?', self)
        self.rtc_plot_panel.layout().addWidget(self.transparent_plots_checkbox, 5, 7, 1, 1)
        self.transparent_plots_checkbox.setChecked(False)



    #########################################################
    # Running
    #########################################################

    def rtc_collector(self, monitor=False):
        '''
        '''
        device = self.rtc_daq_combobox.currentText()
        self.x_data, self.x_stds = [], []
        self.y_data, self.y_stds = [], []
        x_channel = self.daq_x_combobox.currentText()
        y_channel = self.daq_y_combobox.currentText()
        signal_channels  = [x_channel, y_channel]
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
        self.daq_collector = Collector(self)
        self.daq_collector.signals.data_ready.connect(self.rtc_plot_running_from_disk)
        self.daq_collector.signals.check_scan.connect(self.rtc_scan_temp)
        self.daq_collector.signals.check_heater.connect(self.rtc_get_lakeshore_temp_control)
        self.daq_collector.signals.finished.connect(self.rtc_update_data)
        self.daq_collector.add_daq(daq)
        self.qthreadpool.start(self.daq_collector)
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
        rt_set_points_path = os.path.join('bd_resources', 'rt_set_points.txt')
        with open(rt_set_points_path, 'r') as fh:
            set_low, set_high = fh.read().split(', ')
        self.temp_set_point_low_lineedit.setText(set_low)
        self.temp_set_point_high_lineedit.setText(set_high)

    def rtc_write_set_points(self):
        '''
        '''
        set_low = self.temp_set_point_low_lineedit.text()
        set_high = self.temp_set_point_high_lineedit.text()
        rt_set_points_path = os.path.join('bd_resources', 'rt_set_points.txt')
        with open(rt_set_points_path, 'w') as fh:
            fh.write('{0}, {1}'.format(set_low, set_high))

    def rtc_start_stop(self):
        '''
        '''
        if self.heater_range_combobox.currentText() == '0.0000':
            self.gb_quick_message('Heater range is set to zero cannot regulate temp!', msg_type='Warning')
            return None
        self.rtc_write_set_points()
        if 'Start' in self.sender().text():
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
            self.sender().setText('Start DAQ')
            self.started = False
            self.meta_data['n_samples'] = len(self.x_data)
            save_path = self.rtc_index_file_name()
            notes, okPressed = self.gb_quick_info_gather(title='Good data?', dialog='Data Notes')
            self.meta_data['notes'] = notes
            with open(save_path.replace('txt', 'json'), 'w') as json_handle:
                simplejson.dump(self.meta_data, json_handle)
            self.rtc_save(save_path)
            QtWidgets.QApplication.processEvents()
            self.qthreadpool.clear()

    def rtc_plot_running_from_disk(self):
        '''
        '''
        save_path = os.path.join('temp_files', 'temp_xy.png')
        image_to_display = QtGui.QPixmap(save_path)
        self.xy_scatter_label.setPixmap(image_to_display)
        save_path = os.path.join('temp_files', 'temp_x.png')
        image_to_display = QtGui.QPixmap(save_path)
        self.x_time_stream_label.setPixmap(image_to_display)
        save_path = os.path.join('temp_files', 'temp_y.png')
        image_to_display = QtGui.QPixmap(save_path)
        self.y_time_stream_label.setPixmap(image_to_display)
        if hasattr(self, 'daq_collector'):
            x_data_text = 'X Data: {0:.4f} ::: X STD: {1:.4f} (raw) [{2}K=0V {3}K=10V]\n'.format(
                self.daq_collector.x_data[-1], self.daq_collector.x_stds[-1],
                self.housekeeping_low_value, self.housekeeping_high_value)
            x_data_text += 'X Data: {0:.2f} (mK)::: X STD: {1:.2f} (mK)\n'.format(self.daq_collector.x_data_real[-1], self.daq_collector.x_stds_real[-1])
            self.x_data_label.setText(x_data_text)
            y_data_text = 'Y Data: {0:.4f} ::: Y STD: {1:.4f} (raw) [{2}Ohms=0V {3}Ohms=10V]\n'.format(
                self.daq_collector.y_data[-1], self.daq_collector.y_stds[-1],
                self.samples_low_value, self.samples_high_value)
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

    def rtc_load_data(self):
        '''
        '''
        save_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
        self.status_bar.showMessage(save_path)
        x_data, x_stds, y_data, y_stds, directions = [], [], [], [], []
        lines = []
        with open(save_path, 'r') as fh:
            for line in fh.readlines():
                items = line.split(',')
                x = float(items[0].strip())
                x_std = float(items[1].strip())
                y = float(items[2].strip())
                if len(items[3].split(' ')) > 1:
                    y_std = float(items[3].strip())
                    direction = items[4].strip()
                elif len(items) == 5:
                    direction = items[4].strip()
                else:
                    direction = 'up'
                x_data.append(x)
                x_stds.append(x_std)
                y_data.append(y)
                y_stds.append(y_std)
                directions.append(direction)
                lines.append(line)
                self.status_bar.showMessage(line)
        self.rtc_update_data(
            np.asarray(x_data),
            np.asarray(x_stds),
            np.asarray(y_data),
            np.asarray(y_stds),
            directions
            )

        self.x_data = x_data
        self.x_stds = x_stds
        self.y_data = y_data
        self.y_stds = y_stds
        self.directions = directions
        self.rtc_direct_plot()


    def rtc_direct_plot(self):
        '''
        '''
        daq_collector = Collector(
            self,
            x_data=self.x_data,
            x_stds=self.x_stds,
            y_data=self.y_data,
            y_stds=self.y_stds,
            directions=self.directions
            )
        daq_collector.rtc_plot_xy()
        self.rtc_plot_running_from_disk()

    def rtc_update_data(self, x_data, x_stds, y_data, y_stds, directions):
        '''
        '''
        self.x_data = x_data
        self.x_stds = x_stds
        self.y_data = y_data
        self.y_stds = y_stds
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
                x_data = self.rtc_get_linear_value(np.asarray(self.x_data), slope, low_value)
                x_stds = np.asarray(x_stds) * slope
            else:
                x_data = self.rtc_get_linear_value(np.asarray(self.x_data), slope, low_value)
                x_stds = np.asarray(self.x_stds) * slope
        self.x_data_real = x_data #mK
        self.x_stds_real = x_stds #mK
        return x_data, x_stds

    def rtc_adjust_y_data(self):
        '''
        '''
        y_data = []
        y_stds = []
        if self.y_label_combobox.currentText() == 'Arb Units':
            y_data = np.asarray(self.y_data) - np.min(self.y_data)
            y_stds = np.asarray(self.y_stds)
        else:
            voltage_reduction_factor = float(self.y_correction_lineedit.text())
            low_value = self.samples_low_value
            high_value = self.samples_high_value
            slope = (high_value - low_value) / 1e1 # K / V
            y_data = self.rtc_get_linear_value(np.asarray(self.y_data), slope, low_value) * 1e3 #mOhms
            y_stds = np.asarray(self.y_stds) * slope * 1e3 #mOhms
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
            file_name = 'RvT_{0}_Ramp_{1}_Exc_{2}_Scan_{3}.txt'.format(sample_name, ramp, excitation, str(i).zfill(3))
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
        print('saving', self.x_data)
        if len(self.x_data) == 0:
            self.gb_quick_message('Warning! data error setting trace in terminal', msg_type='Warning')
            self.x_data = self.daq_collector.x_data
            self.x_stds = self.daq_collector.x_stds
            self.y_data = self.daq_collector.y_data
            self.y_stds = self.daq_collector.y_stds
            self.directions = self.daq_collector.directions
            #import ipdb;ipdb.set_trace()

        if len(save_path) > 0:
            ss_save_path = save_path.replace('.txt', '_meta.png')
            screen = QtWidgets.QApplication.primaryScreen()
            screenshot = screen.grabWindow(self.winId())
            screenshot.save(ss_save_path, 'png')
            calibrated_save_path = save_path.replace('.txt', '_calibrated.txt')
            png_save_path = save_path.replace('.txt', '.png')
            shutil.copy(os.path.join('temp_files', 'temp_xy.png'), png_save_path)
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}, {4}\n'.format(self.x_data[i], self.x_stds[i], self.y_data[i], self.y_stds[i], self.directions[i])
                    save_handle.write(line)
            x_data, x_stds = self.rtc_adjust_x_data()
            y_data, y_stds = self.rtc_adjust_y_data()
            with open(calibrated_save_path, 'w') as save_handle:
                for i, x_i in enumerate(x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}, {4}\n'.format(x_data[i], x_stds[i], y_data[i], y_stds[i], self.directions[i])
                    save_handle.write(line)
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
            x_data=[0],
            x_stds=[0],
            y_data=[0],
            y_stds=[0],
            directions=['down']
            ):
        '''
        '''
        super(Collector, self).__init__()
        self.transparent_plots = False
        self.signals = CollectorSignals()
        self.monitor_dpi = 96
        self.rtc = rtc
        self.x_data = x_data
        self.x_stds = x_stds
        self.y_data = y_data
        self.y_stds = y_stds
        self.directions = directions

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
        self.y_data, self.y_stds = [], []
        self.directions = []
        self.x_channel = signal_channels[0]
        self.y_channel = signal_channels[1]
        self.int_time = self.daq.int_time
        self.sample_rate = self.daq.sample_rate
        self.transparent_plots = self.rtc.transparent_plots_checkbox.isChecked()
        while self.rtc.started:
            data_dict = self.daq.run()
            sleep_time = float(self.daq.int_time) / 1e3
            time.sleep(sleep_time)
            x_ts = data_dict[self.x_channel]['ts']
            x_mean = data_dict[self.x_channel]['mean']
            x_min = data_dict[self.x_channel]['min']
            x_max = data_dict[self.x_channel]['max']
            x_std = data_dict[self.x_channel]['std']
            y_ts = data_dict[self.y_channel]['ts']
            y_mean = data_dict[self.y_channel]['mean']
            y_min = data_dict[self.y_channel]['min']
            y_max = data_dict[self.y_channel]['max']
            y_std = data_dict[self.y_channel]['std']
            self.x_data.append(x_mean)
            self.x_stds.append(x_std)
            self.y_data.append(y_mean)
            self.y_stds.append(y_std)
            self.transparent_plots = self.rtc.transparent_plots_checkbox.isChecked()
            self.directions.append(self.rtc.drift_direction)
            self.rtc_plot_running()
            self.signals.data_ready.emit() #data_dict)
            if i % 15 == 0 and i % 60 != 0:
                self.signals.check_scan.emit(False, [self.x_data[-1]], [self.x_stds[-1]])
            if i % 60 == 0:
                self.signals.check_heater.emit()
            i += 1
        self.signals.finished.emit(self.x_data, self.x_stds, self.y_data, self.y_stds, self.directions)

    def rtc_plot_running(self):
        '''
        '''
        self.rtc_plot_x_and_y()
        self.rtc_plot_xy(running=True)


    def rtc_adjust_x_data_point(self, x):
        '''
        '''
        thermometer = self.rtc.thermometer_combobox.currentText()
        if not hasattr(self.rtc.ls372_temp_widget, 'analog_outputs'):
            high_value = 1e2
            low_value = 0
        else:
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
        if not hasattr(self.rtc.ls372_temp_widget, 'analog_outputs'):
            high_value = 1e2
            low_value = 0
        else:
            low_value = self.rtc.housekeeping_low_value
            high_value = self.rtc.housekeeping_high_value
        # high_value 00 #0 to 10K is 0 to 1V

        if thermometer in self.rtc.lakeshore_thermometers:
            slope = (high_value - low_value) / 1e1 # Y range / 10V
            x_data = self.rtc.rtc_get_linear_value(np.asarray(self.x_data), slope, low_value) * 1e3 #mK
            x_stds = np.asarray(self.x_stds) * slope
        self.x_data_real = x_data #mK
        self.x_stds_real = x_stds #mK
        return x_data, x_stds

    def rtc_adjust_y_data_point(self, y):
        '''
        '''
        low_value = self.rtc.samples_low_value
        high_value = self.rtc.samples_high_value
        slope = (high_value - low_value) / 10 # K/ V
        adjusted_y = self.rtc.rtc_get_linear_value(y, slope, low_value) * 1e3 #mOhms
        return adjusted_y

    def rtc_adjust_y_data(self):
        '''
        '''
        y_data = []
        y_stds = []
        voltage_reduction_factor = 1.0
        if self.rtc.y_label_combobox.currentText() == 'Arb Units':
            y_data = np.asarray(self.y_data) - np.min(self.y_data)
            y_stds = np.asarray(self.y_stds)
        else:
            low_value = self.rtc.samples_low_value
            high_value = self.rtc.samples_high_value
            slope = (high_value - low_value) / 10 # K/ V
            y_data = self.rtc.rtc_get_linear_value(np.asarray(self.y_data), slope, low_value) * 1e3 #mOhms
            y_stds = np.asarray(self.y_stds) * slope * 1e3 #mOhms
        self.y_data_real = y_data
        self.y_stds_real = y_stds
        return y_data, y_stds

    def rtc_plot_x_and_y(self):
        '''
        '''
        change_indicies = list(np.where(np.asarray(self.directions[:-1]) != np.asarray(self.directions[1:]))[0])
        change_indicies.append(-1)
        fig_x = self.rtc.x_fig
        ax_x = fig_x.get_axes()[0]
        ax2_x = fig_x.get_axes()[1]
        ax2_x.plot([0, 10], [self.rtc.housekeeping_low_value, self.rtc.housekeeping_high_value], 'k', alpha=0.5)
        ax2_x.set_xlabel('(V)', fontsize=8)
        ax2_x.set_ylabel('(K)', fontsize=8)
        ax_x.set_ylabel('X ($V$)', fontsize=8)
        fig_y = self.rtc.y_fig
        ax_y = fig_y.get_axes()[0]
        ax2_y = fig_y.get_axes()[1]
        ax2_y.plot([0, 10], [self.rtc.samples_low_value, self.rtc.samples_high_value], 'k', alpha=0.5)
        ax2_y.set_xlabel('(V)', fontsize=8)
        ax2_y.set_ylabel('($\Omega$)', fontsize=8)
        ax_y.set_ylabel('Y ($V$)', fontsize=8)
        label = None
        if hasattr(self, 'daq') and len(self.x_data) > 1:
            label_str = 'DAQ {0} Sample {1}'.format(self.x_channel, len(self.x_data))
            label = label_str
        for i, change_index in enumerate(change_indicies):
            if i == 0:
                drift_start_index = 0
            drift_end_index = change_index
            color = 'r'
            if len(self.directions) > 0:
                if self.directions[change_index] == 'down':
                    color = 'b'
            ax_x.errorbar(
                    range(len(self.x_data))[drift_start_index:drift_end_index],
                    self.x_data[drift_start_index:drift_end_index],
                    yerr=self.x_stds[drift_start_index:drift_end_index],
                    marker='.', ms=0.5, color=color, alpha=0.75,
                    linestyle='None', label=label)
            scaled_x_point = self.rtc_adjust_x_data_point(self.x_data[-1])
            ax2_x.plot(self.x_data[-1], scaled_x_point, '*', ms=3)
            ax_y.errorbar(
                    range(len(self.x_data))[drift_start_index:drift_end_index],
                    self.y_data[drift_start_index:drift_end_index],
                    yerr=self.y_stds[drift_start_index:drift_end_index],
                    marker='.', ms=0.5, color=color, alpha=0.75,
                    linestyle='None', label=label)
            scaled_y_point = self.rtc_adjust_y_data_point(self.y_data[-1]) * 1e-3 #back to K
            ax2_y.plot(self.y_data[-1], scaled_y_point, '*', ms=3)
            drift_start_index = change_index
        handles, labels = ax_x.get_legend_handles_labels()
        if len(handles) > 0:
            label_str = 'DAQ {0} Sample {1}'.format(self.x_channel, len(self.x_data))
            labels[0] = label_str
            #ax_x.legend(handles[:1], labels[:1], loc='best')
        save_path = os.path.join('temp_files', 'temp_x.png')
        fig_x.savefig(save_path, transparent=self.transparent_plots)
        handles, labels = ax_y.get_legend_handles_labels()
        if len(handles) > 0:
            label_str = 'DAQ {0} Sample {1}'.format(self.x_channel, len(self.x_data))
            labels[0] = label_str
            #ax_y.legend(handles[:1], labels[:1], loc='best')
        save_path = os.path.join('temp_files', 'temp_y.png')
        fig_y.savefig(save_path, transparent=self.transparent_plots)

    def rtc_plot_xy(self, running=False, file_name=''):
        '''
        '''
        if len(self.x_data) == 0:
            return None
        fig = self.rtc.xy_fig
        ax = fig.get_axes()[0]
        y_label = self.rtc.y_label_combobox.currentText()
        if running:
            y_data, y_stds = self.rtc_adjust_y_data()
            x_data, x_stds = self.rtc_adjust_x_data()
            if np.mean(y_data) > 1e3:
                y_data *= 1e-3
                y_stds *= 1e-3
                y_label = y_label.replace('$m','$')
            fig = self.rtc_plot_drifts(fig, x_data, x_stds, y_data, y_stds)
            ax.set_xlabel('Temperature ($mK$)', fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
            save_path = os.path.join('temp_files', 'temp_xy.png')
            fig.savefig(save_path, transparent=self.transparent_plots)
        else:
            self.y_data, self.y_stds = self.rtc_adjust_y_data()
            self.x_data, self.x_stds = self.rtc_adjust_x_data()
            fig = self.rtc_plot_drifts(fig, self.x_data, self.x_stds, self.y_data, self.y_stds)
            print(self.x_data)
            ax.tick_params(axis='x', labelsize=16)
            ax.tick_params(axis='y', labelsize=16)
            ax.set_xlabel('Temperature ($mK$)', fontsize=14)
            ax.set_ylabel(y_label, fontsize=12)
            save_path = os.path.join('temp_files', 'temp_xy.png')
            fig.savefig(save_path, transparent=self.transparent_plots)

    def rtc_get_rn_and_tc(self):
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
        y_data = np.asarray(self.y_data[sample_clip_lo:sample_clip_hi])
        x_data = np.asarray(x_data[sample_clip_lo:sample_clip_hi])
        x_data_selector = np.where(np.logical_and(data_clip_lo < x_data, x_data < data_clip_hi))
        y_data = y_data[x_data_selector]
        x_data = x_data[x_data_selector]
        if len(x_data) == 0:
            normal_resistance = np.nan
            transition_temperature = np.nan
            half_rn = np.nan
        elif self.rtc.y_label_combobox.currentText() == 'Arb Units':
            offset_array = np.asarray(y_data) - np.min(y_data)
            rn_data_selector = np.where(np.logical_and(data_clip_rn_lo < x_data, x_data < data_clip_rn_hi))
            normal_resistance = np.mean(y_data[rn_data_selector])
            normal_resistance = np.max(offset_array)
            half_rn = 0.5 * normal_resistance
            tc_idx = (np.abs(offset_array - half_rn)).argmin()
            transition_temperature = np.asarray(x_data)[tc_idx]
        else:
            rn_data_selector = np.where(np.logical_and(data_clip_rn_lo < x_data, x_data < data_clip_rn_hi))
            normal_resistance = np.mean(y_data[rn_data_selector])
            half_rn = 0.5 * normal_resistance
            tc_idx = (np.abs(np.asarray(y_data) - half_rn)).argmin()
            transition_temperature = np.asarray(x_data)[tc_idx]
            normal_resistance = self.rtc_adjust_y_data_point(normal_resistance)
            half_rn = self.rtc_adjust_y_data_point(y_data[tc_idx])
        units = '$m\Omega$'
        if normal_resistance > 1e3:
            normal_resistance *= 1e-3
            half_rn *= 1e-3
            units = units.replace('$m', '$')
        scan_info = '$R_n$ ({0}): {1:.2f}\n'.format(units, normal_resistance)
        scan_info += '$T_c$ (mK): {0:.2f}\n'.format(transition_temperature)
        scan_info += 'Exc: {0:.2f} {1}\n'.format(float(excitation), unit)
        scan_info += 'Ramp: {0} K/min\n'.format(ramp_value)
        scan_info += 'Sensor: {0}\n'.format(thermometer)
        return transition_temperature, normal_resistance, half_rn, scan_info

    def rtc_plot_drifts(self, fig, x_data, x_stds, y_data, y_stds):
        '''
        '''
        if len(self.x_data) == 0:
            return fig
        if not self.rtc.gb_is_float(self.rtc.sample_clip_lo_lineedit.text()):
            return fig
        if not self.rtc.gb_is_float(self.rtc.sample_clip_hi_lineedit.text()):
            return fig
        if not self.rtc.gb_is_float(self.rtc.data_clip_lo_lineedit.text()):
            return fig
        if not self.rtc.gb_is_float(self.rtc.data_clip_hi_lineedit.text()):
            return fig
        ax_plot = fig.get_axes()[0]
        ax_plot.cla()
        ax_legend = fig.get_axes()[1]
        ax_legend.cla()
        ax_legend.set_axis_off()
        sample_name = self.rtc.sample_name_lineedit.text()
        # Analyze Tc
        transition_temperature, normal_resistance, half_rn, label = self.rtc_get_rn_and_tc()
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
        plot_x_data = x_data[sample_clip_lo:sample_clip_hi]
        plot_x_stds = x_stds[sample_clip_lo:sample_clip_hi]
        plot_y_data = y_data[sample_clip_lo:sample_clip_hi]
        plot_y_stds = y_stds[sample_clip_lo:sample_clip_hi]
        for i, change_index in enumerate(change_indicies):
            if i == 0:
                drift_start_index = 0
            drift_end_index = change_index
            color = 'r'

            if len(selected_directions) > 0:
                if selected_directions[change_index] == 'down':
                    color = 'b'
            if change_index == -1:
                final_plot_x_data = plot_x_data[drift_start_index:]
                final_plot_x_stds = plot_x_stds[drift_start_index:]
                final_plot_y_data = plot_y_data[drift_start_index:]
                final_plot_y_stds = plot_x_stds[drift_start_index:]
            else:
                final_plot_x_data = plot_x_data[drift_start_index:change_index]
                final_plot_x_stds = plot_x_stds[drift_start_index:change_index]
                final_plot_y_data = plot_y_data[drift_start_index:change_index]
                final_plot_y_stds = plot_x_stds[drift_start_index:change_index]
            selector = np.where(np.logical_and(data_clip_lo < final_plot_x_data, final_plot_x_data < data_clip_hi))

            rn_selector = np.where(np.logical_and(data_clip_rn_lo < final_plot_x_data, final_plot_x_data < data_clip_rn_hi))

            hndls, lbls = ax_plot.get_legend_handles_labels()
            if '$R_n$' in lbls:
                ax_plot.plot(final_plot_x_data[rn_selector], np.ones(len(final_plot_x_data[rn_selector])) * normal_resistance,
                             color='k', lw=5, alpha=0.4)
            else:
                ax_plot.plot(final_plot_x_data[rn_selector], np.ones(len(final_plot_x_data[rn_selector])) * normal_resistance,
                             color='k', lw=5, alpha=0.4, label='$R_n$')
            ax_plot.errorbar(final_plot_x_data[selector], final_plot_y_data[selector],
                             xerr=final_plot_x_stds[selector], yerr=final_plot_y_stds[selector],
                             marker='x', ms=0.75, color=color, alpha=0.75,
                             linestyle='-')
            tc_label = None
            if i == 0:
                tc_label = '$T_c$'
            ax_plot.plot(transition_temperature, half_rn, '*', ms=25, color='g', label=tc_label)
            drift_start_index = change_index
            handles, labels = ax_plot.get_legend_handles_labels()
            if len(final_plot_x_data[selector]) > 0 and not 'up' in labels:
                ax_plot.plot(final_plot_x_data[selector][-1], final_plot_y_data[selector][-1], linestyle=None,
                             marker='*', ms=0.75, color='r', alpha=0.75, label='up')
                ax_plot.plot(final_plot_x_data[selector][-1], final_plot_y_data[selector][-1], linestyle=None,
                             marker='*', ms=0.75, color='b', alpha=0.75, label='down')
        hndls, lbls = ax_plot.get_legend_handles_labels()
        frameon = not self.transparent_plots
        ax_legend.legend(handles, labels, loc='best', frameon=frameon, title=label, numpoints=1)
        ax_plot.set_title(sample_name, fontsize=14)
        return fig


class CollectorSignals(QObject):
    '''
    This collects the data and sends signals back to the cod e
    '''

    data_ready = pyqtSignal()
    check_scan = pyqtSignal(bool, list, list)
    check_heater = pyqtSignal()
    finished = pyqtSignal(list, list, list, list, list)
    temp_ready = pyqtSignal(float)
