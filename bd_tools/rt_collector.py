import time
import shutil
import os
import simplejson
import matplotlib
matplotlib.use('Agg')
import pylab as pl
import pickle as pkl
import numpy as np
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import *
from bd_lib.saving_manager import SavingManager
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class RTCollector(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, ls372_temp_widget, ls372_samples_widget, data_folder):
        '''
        '''
        super(RTCollector, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.meta_data = {}
        self.daq = BoloDAQ()
        self.le_width = int(0.1 * self.screen_resolution.width())
        self.ls372_temp_widget = ls372_temp_widget
        self.ls372_samples_widget = ls372_samples_widget
        with open(os.path.join('bd_settings', 'squids_settings.json'), 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh)
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)
        self.voltage_reduction_factor_dict  = {
            '1': 1,
            '2': 10,
            '3': 100,
            '4': 1e3,
            '5': 1e4,
            }
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.rtc_plot_panel = QtWidgets.QWidget(self)
        grid_2 = QtWidgets.QGridLayout()
        self.rtc_plot_panel.setLayout(grid_2)
        self.x_data = []
        self.x_stds = []
        self.y_data = []
        self.y_stds = []
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = data_folder
        self.saving_manager = SavingManager(self, self.data_folder, self.rtc_save, 'RT')
        self.rtc_populate()
        #self.rtc_plot_running()
        if self.ls372_temp_widget is not None:
            self.status_bar.messageChanged.connect(self.rtc_update_panel)
        self.qthreadpool = QThreadPool()

    #########################################################
    # GUI and Input Handling
    #########################################################

    def rtc_update_samples(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)
        self.rtc_update_sample_name()

    def rtc_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.rtc_display_daq_settings()

    def rtc_populate(self):
        '''
        '''
        self.gb_initialize_panel('self')
        self.rtc_rt_config()
        if self.ls372_temp_widget is not None:
            self.rtc_lakeshore_panel()
            self.layout().addWidget(self.rtc_plot_panel, 0, 4, 20, 1)
        else:
            self.layout().addWidget(self.rtc_plot_panel, 0, 2, 13, 1)
        self.gb_initialize_panel('rtc_plot_panel')
        self.rtc_add_common_widgets()
        self.rtc_daq_panel()
        self.rtc_make_plot_panel()
        self.rtc_display_daq_settings()
        #self.rtc_plot_running()

    #############################################
    # Lakeshore stuff for DR
    #############################################

    def rtc_lakeshore_panel(self):
        '''
        '''
        # Temp Control
        self.temp_display_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.temp_display_label, 11, 0, 1, 1)
        self.temp_set_point_lineedit = QtWidgets.QLineEdit('0.001', self)
        self.temp_set_point_lineedit.setFixedWidth(self.le_width)
        self.temp_set_point_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.temp_set_point_lineedit))
        self.layout().addWidget(self.temp_set_point_lineedit, 11, 1, 1, 1)
        temp_set_point_pushbuton = QtWidgets.QPushButton('Set New', self)
        temp_set_point_pushbuton.setFixedWidth(self.le_width)
        temp_set_point_pushbuton.clicked.connect(self.rtc_set_temp_set_point)
        self.layout().addWidget(temp_set_point_pushbuton, 11, 2, 1, 1)
        set_point = self.ls372_temp_widget.temp_control.ls372_get_temp_set_point()
        self.temp_set_point_lineedit.setText('{0:.4f}'.format(set_point * 1e3))
        if self.gb_is_float(self.ls372_temp_widget.channels.ls372_get_channel_value(6, reading='kelvin')):
            mxc_temp = float(self.ls372_temp_widget.channels.ls372_get_channel_value(6, reading='kelvin'))
        else:
            mxc_temp = np.nan
        self.temp_display_label.setText('Set P: {0:.3f} mK\nAct: {1:.3f} mK'.format(set_point * 1e3, mxc_temp))
        ramp_on, ramp_value = self.ls372_temp_widget.temp_control.ls372_get_ramp()
        self.meta_data['Temp Ramp (K/min)'] = ramp_value
        self.ramp_lineedit = self.gb_make_labeled_lineedit(label_text='Ramp (K/min): ')
        self.ramp_lineedit.setFixedWidth(2 * self.le_width)
        self.ramp_lineedit.setText('{0}'.format(ramp_value))
        self.ramp_lineedit.setValidator(QtGui.QDoubleValidator(12, 2, 3, self.ramp_lineedit))
        self.layout().addWidget(self.ramp_lineedit, 12, 0, 1, 2)
        set_ramp_pushbutton = QtWidgets.QPushButton('Set Ramp', self)
        set_ramp_pushbutton.setFixedWidth(self.le_width)
        self.layout().addWidget(set_ramp_pushbutton, 12, 2, 1, 1)
        set_ramp_pushbutton.clicked.connect(self.rtc_set_ramp)
        # PID Config
        p, i, d = self.ls372_temp_widget.temp_control.ls372_get_pid()
        self.p_lineedit = self.gb_make_labeled_lineedit(label_text='P: ')
        self.p_lineedit.setFixedWidth(0.5 * self.le_width)
        self.p_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 2, self.p_lineedit))
        self.p_lineedit.setText(str(p))
        self.layout().addWidget(self.p_lineedit, 13, 0, 1, 1)
        self.i_lineedit = self.gb_make_labeled_lineedit(label_text='I: ')
        self.i_lineedit.setFixedWidth(0.5 * self.le_width)
        self.i_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 2, self.i_lineedit))
        self.i_lineedit.setText(str(i))
        self.layout().addWidget(self.i_lineedit, 13, 1, 1, 1)
        self.d_lineedit = self.gb_make_labeled_lineedit(label_text='D: ')
        self.d_lineedit.setFixedWidth(0.5 * self.le_width)
        self.d_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 2, self.d_lineedit))
        self.d_lineedit.setText(str(d))
        self.layout().addWidget(self.d_lineedit, 13, 2, 1, 1)
        self.pid_header_label = QtWidgets.QLabel('', self)
        self.pid_header_label.setText( 'P:{0} ::: I:{1} ::: D:{2} '.format(p, i, d))
        self.layout().addWidget(self.pid_header_label, 14, 2, 1, 1)
        self.meta_data['P I D Settings'] = (p, i, d)
        # Heater Range
        heater_value = self.ls372_temp_widget.temp_control.ls372_get_heater_value()
        current_range_index, current_range_value = self.ls372_temp_widget.temp_control.ls372_get_heater_range()
        self.heater_range_header_label = QtWidgets.QLabel('Heater Value {0:.5f} (A)'.format(heater_value), self)
        self.layout().addWidget(self.heater_range_header_label, 14, 0, 1, 1)
        self.heater_range_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.heater_range_combobox, 14, 1, 1, 1)
        for range_index, range_value in self.ls372_temp_widget.temp_control.ls372_heater_range_dict.items():
            self.heater_range_combobox.addItem(str(range_value))
            if int(range_index) == int(current_range_index):
                set_to_index = int(range_index)
                self.meta_data['Heater Range (A)'] = range_value
        self.heater_range_combobox.setCurrentIndex(set_to_index)
        # Read and Write Settings
        read_ls372_settings_pushbutton = QtWidgets.QPushButton('Read Settings', self)
        read_ls372_settings_pushbutton.clicked.connect(self.rtc_get_lakeshore_temp_control)
        self.layout().addWidget(read_ls372_settings_pushbutton, 15, 0, 1, 3)
        update_ls372_settings_pushbutton = QtWidgets.QPushButton('Update Settings', self)
        update_ls372_settings_pushbutton.clicked.connect(self.rtc_edit_lakeshore_temp_control)
        self.layout().addWidget(update_ls372_settings_pushbutton, 16, 0, 1, 3)
        # Control Buttons
        configure_channel_pushbutton = QtWidgets.QPushButton('Configure And Scan', self)
        self.layout().addWidget(configure_channel_pushbutton, 17, 1, 1, 2)
        configure_channel_pushbutton.clicked.connect(self.rtc_edit_lakeshore_channel)
        self.channel_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.channel_combobox, 17, 0, 1, 1)
        for channel in range(1, 17):
            self.channel_combobox.addItem(str(channel))
        self.ls372_samples_widget.channels.ls372_scan_channel(1)
        set_aux_analog_out_pushbutton = QtWidgets.QPushButton('Set Analog Out', self)
        set_aux_analog_out_pushbutton.clicked.connect(self.rtc_edit_lakeshore_aux_ouput)
        self.layout().addWidget(set_aux_analog_out_pushbutton, 18, 1, 1, 2)
        self.scanned_channel_info_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.scanned_channel_info_label, 19, 0, 1, 2)
        self.rtc_get_lakeshore_channel_info()

    def rtc_get_lakeshore_temp_control(self):
        '''
        '''
        self.rtc_get_lakeshore_pid()

    def rtc_get_lakeshore_pid(self):
        '''
        '''
        self.ls372_temp_widget.temp_control.set_run_function('ls372_get_pid')
        self.qthreadpool.start(self.ls372_temp_widget.temp_control)
        self.ls372_temp_widget.signals.pid_ready_connect(self.rtc_display_pid)
        #p, i, d = self.ls372_temp_widget.temp_control.ls372_get_pid()

    def rtc_display_pid(self, p, i, d):
        '''
        '''
        print(p, i, d)
        self.pid_header_label.setText( 'P:{0} ::: I:{1} ::: D:{2} '.format(p, i, d))
        self.meta_data['P I D Settings'] = (p, i, d)

    def rtc_set_temp_set_point(self):
        '''
        '''
        new_set_point = float(self.temp_set_point_lineedit.text()) * 1e-3
        print('afdaf')
        self.ls372_temp_widget.temp_control.set_run_function('ls372_set_temp_set_point', new_set_point)
        self.qthreadpool.start(self.ls372_temp_widget.temp_control)
        #self.ls372_temp_widget.temp_ready.connect(self.rtc_get_temp_set_point)

    def rtc_set_ramp(self):
        '''
        '''
        new_ramp = float(self.ramp_lineedit.text())
        self.ls372_temp_widget.temp_control.set_run_function('ls372_set_ramp', new_ramp)
        self.qthreadpool.start(self.ls372_temp_widget.temp_control)
        self.meta_data['Temp Ramp (K/min)'] = new_ramp
        self.rtc_update_sample_name()

    def rtc_get_temp_set_point(self):
        '''
        '''
        print(self.ls372_temp_widget.channels.ls372_get_channel_value(6, reading='kelvin'))
        mxc_temp = float(self.ls372_temp_widget.channels.ls372_get_channel_value(6, reading='kelvin')) * 1e3
        heater_value = self.ls372_temp_widget.temp_control.ls372_get_heater_value()
        set_point = self.ls372_temp_widget.temp_control.ls372_get_temp_set_point()
        self.heater_range_header_label.setText('Heater Value {0:.5f} (A)'.format(heater_value))
        self.temp_display_label.setText('Current Temp {0:.3f}mK (Set) | {1:.3f}mK (Act)'.format(set_point * 1e3, mxc_temp))

    def rtc_edit_lakeshore_temp_control(self):
        '''
        '''
        #PID Stuff
        new_p, new_i, new_d = float(self.p_lineedit.text()), float(self.i_lineedit.text()), float(self.d_lineedit.text())
        self.ls372_temp_widget.temp_control.ls372_set_pid(new_p, new_i, new_d)
        p, i, d = self.ls372_temp_widget.temp_control.ls372_get_pid()
        self.pid_header_label.setText( 'P:{0} ::: I:{1} ::: D:{2} '.format(p, i, d))
        # Ramp 
        new_ramp = float(self.ramp_lineedit.text())
        self.ls372_temp_widget.temp_control.ls372_set_ramp(new_ramp)
        ramp_on, ramp_value = self.ls372_temp_widget.temp_control.ls372_get_ramp()
        self.ramp_lineedit.setText(str(ramp_value))
        #Temp set point 
        set_point = self.ls372_temp_widget.temp_control.ls372_get_temp_set_point()
        new_set_point = float(self.temp_set_point_lineedit.text()) * 1e-3
        self.ls372_temp_widget.temp_control.ls372_set_temp_set_point(new_set_point)
        # Update with read out values
        mxc_temp = float(self.ls372_temp_widget.channels.ls372_get_channel_value(6, reading='kelvin')) * 1e3
        self.temp_display_label.setText('Current Temp {0:.3f}mK (Set) | {1:.3f}mK (Act)'.format(set_point * 1e3, mxc_temp))
        # Heater Range
        new_range_index = self.heater_range_combobox.currentIndex()
        self.ls372_temp_widget.temp_control.ls372_set_heater_range(new_range_index)
        range_index, range_value = self.ls372_temp_widget.temp_control.ls372_get_heater_range()
        self.meta_data['Heater Range (A)'] = range_value
        self.ls372_temp_widget.channels.ls372_scan_channel(6) # 6 is the MXC thermometer
        self.status_bar.showMessage('Set new temp control parameters and scanning the MXC with temp Lakeshore')

    def rtc_edit_lakeshore_channel(self):
        '''
        '''
        channel = self.channel_combobox.currentText()
        self.sample_name_combobox.setCurrentIndex(int(channel) - 1)
        self.rtc_update_sample_name()
        self.ls372_samples_widget.ls372_edit_channel(clicked=True, index=channel)
        self.ls372_samples_widget.channels.ls372_scan_channel(channel)
        self.ls372_samples_widget.analog_outputs.analog_output_aux.input_channel = channel
        self.ls372_samples_widget.analog_outputs.ls372_monitor_channel_aux_analog(channel, self.ls372_samples_widget.analog_outputs.analog_output_aux)
        self.meta_data['Scanned Channel'] = channel

    def rtc_update_panel(self):
        '''
        '''
        self.rtc_get_lakeshore_channel_info()
        self.rtc_update_sample_name()

    def rtc_get_lakeshore_channel_info(self):
        '''
        '''
        channel = self.channel_combobox.currentText()
        channel_info = 'Scanning {0} '.format(channel)
        channel_object = self.ls372_samples_widget.channels.__dict__['channel_{0}'.format(channel)]
        exc_mode = self.ls372_samples_widget.lakeshore372_command_dict['exc_mode'][channel_object.__dict__['exc_mode']]
        excitation = self.ls372_samples_widget.lakeshore372_command_dict['excitation'][exc_mode][channel_object.__dict__['excitation']]
        resistance_range = self.ls372_samples_widget.lakeshore372_command_dict['resistance_range'][channel_object.__dict__['resistance_range']]
        channel_info += 'Exc Type: {0} '.format(exc_mode)
        channel_info += 'Excitation: {0} '.format(excitation)
        channel_info += 'Range: {0} '.format(resistance_range)
        self.meta_data['Exc Mode'] = exc_mode
        if exc_mode == 'current':
            self.meta_data['Excitation (A)'] = excitation
        else:
            self.meta_data['Excitation (V)'] = excitation
        self.meta_data['Resistance Range (Ohms)'] = resistance_range
        high_value = self.ls372_samples_widget.analog_outputs.analog_output_aux.high_value # 10V = this value in K
        low_value = self.ls372_samples_widget.analog_outputs.analog_output_aux.low_value # 0V = this value in K
        y_correction_factor = (high_value - low_value) / 10 # divide out scaling of lakeshore
        y_correction_factor *= 1e3 # convet back to mV
        self.y_correction_lineedit.setText(str(y_correction_factor))
        self.scanned_channel_info_label.setText(channel_info)

    def rtc_edit_lakeshore_aux_ouput(self):
        '''
        '''
        self.ls372_samples_widget.ls372_edit_analog_output(clicked=True, analog_output='aux')

    def rtc_update_ls372_widget(self, ls372_widget):
        '''
        '''
        self.ls372_widget = ls372_widget

    #############################################
    # DAQ Panel
    #############################################

    def rtc_display_daq_settings(self):
        '''
        '''
        daq = self.rtc_daq_combobox.currentText()
        self.x_channel = self.daq_x_combobox.currentIndex()
        self.y_channel = self.daq_y_combobox.currentIndex()
        self.meta_data['daq_x_channel'] = self.x_channel
        self.meta_data['daq_y_channel'] = self.y_channel
        # X
        self.int_time_x = self.daq_settings[daq][str(self.x_channel)]['int_time']
        self.sample_rate_x = self.daq_settings[daq][str(self.x_channel)]['sample_rate']
        self.meta_data['daq_x_int_time (ms)'] = self.int_time_x
        self.meta_data['daq_x_sample_rate (Hz)'] = self.sample_rate_x
        daq_settings_x_info = 'DAQ X: Int Time (ms): {0} ::: '.format(self.int_time_x)
        daq_settings_x_info += 'Sample Rate (Hz): {0}'.format(str(self.sample_rate_x))
        self.daq_settings_x_label.setText(daq_settings_x_info)
        # Y
        self.int_time_y = self.daq_settings[daq][str(self.y_channel)]['int_time']
        self.sample_rate_y = self.daq_settings[daq][str(self.y_channel)]['sample_rate']
        self.meta_data['daq_y_int_time (ms)'] = self.int_time_y
        self.meta_data['daq_y_sample_rate (Hz)'] = self.sample_rate_y
        daq_settings_y_info = 'DAQ Y: Int Time (ms): {0} ::: '.format(self.int_time_y)
        daq_settings_y_info += 'Sample Rate (Hz): {0}'.format(str(self.sample_rate_y))
        self.daq_settings_y_label.setText(daq_settings_y_info)

    def rtc_daq_panel(self):
        '''
        '''
        # Device
        self.rtc_daq_combobox = self.gb_make_labeled_combobox(label_text='DAQ Device:', width=self.le_width)
        for daq in self.daq_settings:
            self.rtc_daq_combobox.addItem(daq)
        self.layout().addWidget(self.rtc_daq_combobox, 0, 0, 1, 3)
        # DAQ X
        self.daq_x_combobox = self.gb_make_labeled_combobox(label_text='DAQ Ch X Data:', width=self.le_width)
        for daq in range(0, 8):
            self.daq_x_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_x_combobox, 1, 0, 1, 3)
        self.daq_settings_x_label = QtWidgets.QLabel('', self)
        self.daq_settings_x_label.setAlignment(Qt.AlignRight)
        self.layout().addWidget(self.daq_settings_x_label, 2, 0, 1, 3)
        # DAQ Y
        self.daq_y_combobox = self.gb_make_labeled_combobox(label_text='DAQ Ch Y Data:', width=self.le_width)
        for daq in range(0, 8):
            self.daq_y_combobox.addItem(str(daq))
        self.daq_y_combobox.setCurrentIndex(1)
        self.layout().addWidget(self.daq_y_combobox, 3, 0, 1, 3)
        self.daq_settings_y_label = QtWidgets.QLabel('', self)
        self.daq_settings_y_label.setAlignment(Qt.AlignRight)
        self.layout().addWidget(self.daq_settings_y_label, 4, 0, 1, 3)
        self.daq_y_combobox.setCurrentIndex(1)
        self.daq_y_combobox.currentIndexChanged.connect(self.rtc_display_daq_settings)
        self.daq_x_combobox.currentIndexChanged.connect(self.rtc_display_daq_settings)
        self.rtc_daq_combobox.currentIndexChanged.connect(self.rtc_display_daq_settings)
        self.rtc_daq_combobox.setCurrentIndex(1)

    def rtc_rt_config(self):
        '''
        '''
        # GRT Serial 
        self.x_correction_combobox = self.gb_make_labeled_combobox(label_text='GRT Serial:', width=self.le_width)
        for grt_serial in ['Lakeshore']:
            self.x_correction_combobox.addItem(grt_serial)
        self.layout().addWidget(self.x_correction_combobox, 5, 0, 1, 3)
        # Y Voltage Factor 
        self.y_correction_lineedit = self.gb_make_labeled_lineedit(label_text='Resistance Correction Factor:', width=self.le_width)
        self.layout().addWidget(self.y_correction_lineedit, 6, 0, 1, 3)
        # Data Clip
        self.data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo (mK)', width=self.le_width)
        self.data_clip_lo_lineedit.setText(str(0.0))
        self.data_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(-1e18, 1e18, 5, self.data_clip_lo_lineedit))
        self.layout().addWidget(self.data_clip_lo_lineedit, 7, 0, 1, 3)
        self.data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi (mK)', width=self.le_width)
        self.data_clip_hi_lineedit.setText(str(1000.0))
        self.data_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(-1e18, 1e18, 5, self.data_clip_hi_lineedit))
        self.meta_data['data_clip_lo (mK)'] = '0.0'
        self.meta_data['data_clip_hi (mK)'] = '1000.0'
        self.layout().addWidget(self.data_clip_hi_lineedit, 8, 0, 1, 3)
        self.data_clip_lo_lineedit.editingFinished.connect(lambda: self.rtc_update_plot_range(self.data_clip_lo_lineedit, 'data_clip_lo (mK)'))
        self.data_clip_lo_lineedit.returnPressed.connect(lambda: self.rtc_update_plot_range(self.data_clip_lo_lineedit, 'data_clip_lo (mK)'))
        self.data_clip_hi_lineedit.editingFinished.connect(lambda: self.rtc_update_plot_range(self.data_clip_hi_lineedit, 'data_clip_hi (mK)'))
        self.data_clip_hi_lineedit.returnPressed.connect(lambda: self.rtc_update_plot_range(self.data_clip_hi_lineedit, 'data_clip_hi (mK)'))

    def rtc_update_plot_range(self, line_edit, clip_key):
        '''
        '''
        new_clip_value = line_edit.text()
        if clip_key == 'data_clip_lo (mK)':
            self.meta_data['data_clip_lo (mK)'] = new_clip_value
        elif clip_key == 'data_clip_hi (mK)':
            self.meta_data['data_clip_hi (mK)'] = new_clip_value


    def rtc_add_common_widgets(self):
        '''
        '''
        # Sample Name
        self.sample_name_combobox = self.gb_make_labeled_combobox(label_text='Select Sample', width=self.le_width)
        for sample in sorted(self.samples_settings):
            self.sample_name_combobox.addItem(str(sample))
        self.sample_name_combobox.activated.connect(self.rtc_update_sample_name)
        self.layout().addWidget(self.sample_name_combobox, 9, 0, 1, 3)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name')
        self.layout().addWidget(self.sample_name_lineedit, 10, 0, 1, 3)
        # Buttons
        self.start_pushbutton = QtWidgets.QPushButton('Start', self)
        self.start_pushbutton.clicked.connect(self.rtc_start_stop)
        self.layout().addWidget(self.start_pushbutton, 21, 0, 1, 5)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        save_pushbutton.clicked.connect(self.rtc_save)
        self.layout().addWidget(save_pushbutton, 22, 0, 1, 5)
        self.rtc_update_sample_name()

    def rtc_update_sample_name(self):
        '''
        '''
        sample_key = self.sample_name_combobox.currentText()
        sample_name = self.samples_settings[sample_key]
        self.sample_name_lineedit.setText(sample_name)
        sample_name = self.sample_name_lineedit.text().replace('-', '').replace(' ', '_').replace('__', '_')
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
        self.rtc_plot_panel.layout().addWidget(self.x_time_stream_label, 0, 0, 1, 1)
        self.x_data_label = QtWidgets.QLabel('X Data: X STD:', self)
        self.x_data_label.setAlignment(Qt.AlignCenter)
        self.rtc_plot_panel.layout().addWidget(self.x_data_label, 1, 0, 1, 1)
        # Y
        self.y_time_stream_label = QtWidgets.QLabel('', self)
        self.y_time_stream_label.setAlignment(Qt.AlignCenter)
        self.y_time_stream_label.setAttribute(Qt.WA_TranslucentBackground)
        self.rtc_plot_panel.layout().addWidget(self.y_time_stream_label, 0, 1, 1, 1)
        self.y_data_label = QtWidgets.QLabel('Y Data: Y STD:', self)
        self.y_data_label.setAlignment(Qt.AlignCenter)
        self.rtc_plot_panel.layout().addWidget(self.y_data_label, 1, 1, 1, 1)
        # XY
        self.xy_scatter_label = QtWidgets.QLabel('', self)
        self.xy_scatter_label.setAttribute(Qt.WA_TranslucentBackground)
        self.rtc_plot_panel.layout().addWidget(self.xy_scatter_label, 2, 0, 1, 2)

    #########################################################
    # Running
    #########################################################

    def rtc_collecter(self, monitor=False):
        '''
        '''
        device = self.rtc_daq_combobox.currentText()
        self.x_data, self.x_stds = [], []
        self.y_data, self.y_stds = [], []
        signal_channels  = [self.x_channel, self.y_channel]
        self.int_time = self.int_time_x
        self.sample_rate = self.sample_rate_x
        i = 0
        grt_serial = self.x_correction_combobox.currentText()
        self.meta_data['grt_serial'] = grt_serial
        voltage_reduction_factor = self.y_correction_lineedit.text()
        self.meta_data['voltage_reduction_factor'] = float(voltage_reduction_factor)
        sample_name = self.sample_name_lineedit.text()
        self.meta_data['sample_name'] = sample_name
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=self.int_time,
                      sample_rate=self.sample_rate,
                      device=device)
        daq.signal_channels = signal_channels
        daq.screen_resolution = self.screen_resolution
        self.daq_collector = Collector(daq, self.meta_data, self.started)
        self.daq_collector.signals.data_ready.connect(self.rtc_plot_running)
        self.daq_collector.signals.finished.connect(self.rtc_update_data)
        self.qthreadpool.start(self.daq_collector)
        while self.started:
            QtWidgets.QApplication.processEvents()
            if len(self.daq_collector.x_data) > 1:
                x_data_text = 'X Data: {0:.4f} ::: X STD: {1:.4f} (raw)\n'.format(self.daq_collector.x_data[-1], self.daq_collector.x_stds[-1])
                x_data_text += 'X Data: {0:.2f} (mK)::: X STD: {1:.2f} (mK)\n'.format(self.daq_collector.x_data_real[-1], self.daq_collector.x_stds_real[-1])
                self.x_data_label.setText(x_data_text)
                y_data_text = 'Y Data: {0:.4f} ::: Y STD: {1:.4f} (raw)\n'.format(self.daq_collector.y_data[-1], self.daq_collector.y_stds[-1])
                y_data_text += 'Y Data: {0:.2f} (mOhms)::: Y STD: {1:.2f} (mOhms)\n'.format(self.daq_collector.y_data_real[-1], self.daq_collector.y_stds_real[-1])
                self.y_data_label.setText(y_data_text)

    def rtc_start_stop(self):
        '''
        '''
        if 'Start' in self.sender().text():
            self.sender().setText('Stop DAQ')
            self.started = True
            #with open('temp.pkl', 'rb') as fh:
                #data_dict = pkl.load(fh)
            #data_dict = pkl.loads(data_dict)
            #self.qthreadpool.start(
            self.rtc_collecter()
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

    def rtc_plot_running(self):
        '''
        '''
        image_to_display = QtGui.QPixmap('temp_xy.png')
        self.xy_scatter_label.setPixmap(image_to_display)
        image_to_display = QtGui.QPixmap('temp_x.png')
        self.x_time_stream_label.setPixmap(image_to_display)
        image_to_display = QtGui.QPixmap('temp_y.png')
        self.y_time_stream_label.setPixmap(image_to_display)

    ###################################################
    # Saving and Plotting
    ###################################################

    def rtc_update_data(self, x_data, x_stds, y_data, y_stds):
        '''
        '''
        self.x_data = x_data
        self.x_stds = x_stds
        self.y_data = y_data
        self.y_stds = y_stds

    def rtc_adjust_x_data(self):
        '''
        '''
        x_data = []
        x_stds = []
        grt_serial = self.x_correction_combobox.currentText()
        self.meta_data['grt_serial'] = grt_serial
        if grt_serial == 'Lakeshore':
            x_data = np.asarray(self.x_data) * 100
            x_stds = np.asarray(self.x_stds) * 100
        return x_data, x_stds

    def rtc_adjust_y_data(self):
        '''
        '''
        y_data = []
        y_stds = []
        voltage_reduction_factor = float(self.y_correction_lineedit.text())
        self.meta_data['voltage_reduction_factor'] = voltage_reduction_factor
        y_data = np.asarray(self.y_data) * voltage_reduction_factor
        y_stds = np.asarray(self.y_stds) * voltage_reduction_factor
        return y_data, y_stds


    def rtc_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            exc_mode = str(self.meta_data['Exc Mode'])
            ramp_value = str(self.meta_data['Temp Ramp (K/min)'])
            ramp = '{0}'.format(ramp_value.replace('+', '')).replace('.', '_')
            if exc_mode == 'current':
                excitation = float(self.meta_data['Excitation (A)']) * 1e6
                excitation = '{0:.2f}uA'.format(excitation).replace('.', '_').replace(' ', '_')
            else:
                excitation = float(self.meta_data['Excitation (V)']) * 1e6
                excitation = '{0:.2f}uA'.format(excitation).replace('.', '_').replace(' ', '_')
            sample_name = self.sample_name_lineedit.text().replace('-', '').replace(' ', '_').replace('__', '_')
            file_name = 'RvT_{0}_Ramp_{1}_Exc_{2}_Scan_{3}.txt'.format(sample_name, ramp, excitation, str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def rtc_save(self, save_path=None):
        '''
        '''
        if save_path is None:
            save_path = self.rtc_index_file_name()
            save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter=',*.txt,*.dat')[0]
        if len(save_path) > 0:
            calibrated_save_path = save_path.replace('.txt', '_calibrated.txt')
            png_save_path = save_path.replace('.txt', '.png')
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_data[i], self.x_stds[i], self.y_data[i], self.y_stds[i])
                    save_handle.write(line)
            x_data, x_stds = self.rtc_adjust_x_data()
            y_data, y_stds = self.rtc_adjust_y_data()
            with open(calibrated_save_path, 'w') as save_handle:
                for i, x_i in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(x_data[i], x_stds[i], y_data[i], y_stds[i])
                    save_handle.write(line)
            response = self.gb_quick_message('Put data in good data folder?', add_yes=True, add_no=True)
            good_data_folder = os.path.join(self.data_folder, 'good_data')
            if not os.path.exists(good_data_folder):
                os.makedirs(good_data_folder)
            if response == QtWidgets.QMessageBox.Yes:
                good_data_save_path = os.path.join(good_data_folder, os.path.basename(save_path))
                good_data_save_png_path = good_data_save_path.replace('txt', 'png')
                good_calibrated_data_save_path = os.path.join(good_data_folder, os.path.basename(calibrated_save_path))
                #self.rtc_plot_xy(file_name=good_data_save_path.replace('txt', 'png'))
                shutil.copy('temp_xy.png', good_data_save_png_path)
                shutil.copy(save_path, good_data_save_path)
                shutil.copy(calibrated_save_path, good_calibrated_data_save_path)
            else:
                shutil.copy('temp_xy.png', png_save_path)
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
    def __init__(self, daq, meta_data, started):
        '''
        '''
        super(Collector, self).__init__()
        self.signals = CollectorSignals()
        self.screen_resolution = daq.screen_resolution
        self.daq = daq
        self.monitor_dpi = 96
        self.meta_data = meta_data
        self.daq_started = started

    @pyqtSlot()
    def stop(self):
        self.daq_started = False

    @pyqtSlot()
    def run(self):
        '''
        '''
        i = 0
        self.x_data, self.x_stds = [], []
        self.y_data, self.y_stds = [], []
        signal_channels  = self.daq.signal_channels
        self.x_channel = signal_channels[0]
        self.y_channel = signal_channels[1]
        self.int_time = self.daq.int_time
        self.sample_rate = self.daq.sample_rate
        i += 1
        while self.daq_started:
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
            #self.x_data_label.setText('X Mean: {0:.5f} ::: X STD: {0:.5f}'.format(x_mean, x_std))
            #self.y_data_label.setText('Y Mean: {0:.5f} ::: Y STD: {0:.5f}'.format(y_mean, y_std))
            self.x_data.append(x_mean)
            self.x_stds.append(x_std)
            self.y_data.append(y_mean)
            self.y_stds.append(y_std)
            self.signals.data_ready.emit() #data_dict)
            self.rtc_plot_running(data_dict)
        self.signals.finished.emit(self.x_data, self.x_stds, self.y_data, self.y_stds)

    def rtc_plot_running(self, data_dict):
        '''
        '''
        self.rtc_plot_x()
        self.rtc_plot_y()
        self.rtc_plot_xy(running=True)

    def rtc_plot_x(self):
        '''
        '''
        fig, ax = self.rtc_create_blank_fig(frac_screen_width=0.275, frac_screen_height=0.15, left=0.2, bottom=0.20, top=0.98)
        ax.set_xlabel('Sample', fontsize=8)
        ax.set_ylabel('X ($V$)', fontsize=8)
        label = 'DAQ {0}'.format(self.x_channel)
        ax.errorbar(range(len(self.x_data)), self.x_data, self.x_stds, marker='.', ms=0.5, color='b', alpha=0.75, linestyle='None', label=label)
        pl.legend(loc='best', fontsize=8)
        fig.savefig('temp_x.png', transparent=True)
        fig.savefig('temp_x.png', transparent=False)
        pl.close('all')

    def rtc_plot_y(self):
        '''
        '''
        fig, ax = self.rtc_create_blank_fig(frac_screen_width=0.275, frac_screen_height=0.15, left=0.2, bottom=0.20, top=0.98)
        ax.set_xlabel('Sample', fontsize=8)
        ax.set_ylabel('Y ($V$)', fontsize=8)
        label = 'DAQ {0}'.format(self.y_channel)
        ax.errorbar(range(len(self.y_data)), self.y_data, self.y_stds, marker='.', ms=0.5, color='b', alpha=0.75, linestyle='None', label=label)
        pl.legend(loc='best', fontsize=8)
        fig.savefig('temp_y.png', transparent=True)
        fig.savefig('temp_y.png', transparent=False)
        pl.close('all')

    def rtc_plot_xy(self, running=False, file_name=''):
        '''
        '''
        if len(self.x_data) == 0:
            return None
        sample_name = self.meta_data['Sample Name']
        exc_mode = self.meta_data['Exc Mode']
        ramp_value = self.meta_data['Temp Ramp (K/min)']
        if exc_mode == 'current':
            excitation = self.meta_data['Excitation (A)']
            scan_info = 'Exc {0:.2f} uA  Ramp: {1} K/min'.format(float(excitation) * 1e6, ramp_value)
        else:
            excitation = self.meta_data['Excitation (V)']
            scan_info = 'Exc {0:.2f} uV  Ramp: {1} K/min'.format(float(excitation) * 1e6, ramp_value)
        label = '{0}\n{1}'.format(sample_name, scan_info)
        data_clip_lo = float(self.meta_data['data_clip_lo (mK)'])
        data_clip_hi = float(self.meta_data['data_clip_hi (mK)'])
        if running:
            fig, ax = self.rtc_create_blank_fig(frac_screen_width=0.55, frac_screen_height=0.4, left=0.08, bottom=0.16, top=0.92)
            y_data, y_stds = self.rtc_adjust_y_data()
            x_data, x_stds = self.rtc_adjust_x_data()
            selector =  np.where(np.logical_and(data_clip_lo < x_data, x_data < data_clip_hi))
            ax.errorbar(x_data[selector], y_data[selector], xerr=x_stds[selector], yerr=y_stds[selector], marker='.', ms=0.75, color='k', alpha=0.75, linestyle='-', label=label)
        else:
            fig, ax = self.rtc_create_blank_fig(frac_screen_width=0.55, frac_screen_height=0.4, left=0.12, bottom=0.16, top=0.92)
            self.y_data, self.y_stds = self.rtc_adjust_y_data()
            self.x_data, self.x_stds = self.rtc_adjust_x_data()
            selector =  np.where(np.logical_and(data_clip_lo < self.x_data, self.x_data < data_clip_hi))
            ax.errorbar(self.x_data[selector], self.y_data[selector], xerr=self.x_stds[selector], yerr=self.y_stds[selector], marker='.', linestyle='-', label=label)
        if running:
            ax.set_xlabel('Temperature ($mK$)', fontsize=14)
            ax.set_ylabel('Resistance ($m\Omega$)', fontsize=14)
            ax.set_title(sample_name, fontsize=14)
            pl.legend(loc='best', fontsize=14)
            fig.savefig('temp_xy.png', transparent=True)
            fig.savefig('temp_xy.png', transparent=False)
            pl.close('all')
        else:
            ax.tick_params(axis='x', labelsize=16)
            ax.tick_params(axis='y', labelsize=16)
            ax.set_xlabel('Temperature ($mK$)', fontsize=18)
            ax.set_ylabel('Resistance ($m\Omega$)', fontsize=18)
            ax.set_title(sample_name, fontsize=18)
            pl.legend(loc='best', fontsize=14)
            fig.savefig(file_name, transparent=False)

    def rtc_adjust_x_data(self):
        '''
        '''
        x_data = []
        x_stds = []
        grt_serial = self.meta_data['grt_serial']
        if grt_serial == 'Lakeshore':
            x_data = np.asarray(self.x_data) * 100
            x_stds = np.asarray(self.x_stds) * 100
        self.x_data_real = x_data
        self.x_stds_real = x_stds
        return x_data, x_stds

    def rtc_adjust_y_data(self):
        '''
        '''
        y_data = []
        y_stds = []
        voltage_reduction_factor = self.meta_data['voltage_reduction_factor']
        y_data = np.asarray(self.y_data) * voltage_reduction_factor
        y_stds = np.asarray(self.y_stds) * voltage_reduction_factor
        self.y_data_real = y_data
        self.y_stds_real = y_stds
        return y_data, y_stds

    def rtc_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.25,
                             left=0.15, right=0.98, top=0.9, bottom=0.23, multiple_axes=False,
                             aspect=None):
        if frac_screen_width is None and frac_screen_height is None:
            fig = pl.figure()
        else:
            width = (frac_screen_width * self.screen_resolution.width()) / self.monitor_dpi
            height = (frac_screen_height * self.screen_resolution.height()) / self.monitor_dpi
            fig = pl.figure(figsize=(width, height))
        if not multiple_axes:
            if aspect is None:
                ax = fig.add_subplot(111)
            else:
                ax = fig.add_subplot(111, aspect=aspect)
        else:
            ax = None
        fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
        ax.tick_params(axis='x', labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        return fig, ax

class CollectorSignals(QObject):
    '''
    This collects the data and sends signals back to the cod e
    '''

    data_ready = pyqtSignal()
    finished = pyqtSignal(list, list, list, list)
    temp_ready = pyqtSignal(float)
