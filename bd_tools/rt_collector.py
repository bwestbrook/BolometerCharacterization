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
from bd_lib.saving_manager import SavingManager
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class RTCollector(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, ls372_temp_widget, ls372_samples_widget):
        '''
        '''
        super(RTCollector, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
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
        self.data_folder = os.path.join('Data', '{0}'.format(self.today_str))
        self.saving_manager = SavingManager(self, self.data_folder)
        self.rtc_populate()
        self.rtc_plot_running()

    #########################################################
    # GUI and Input Handling
    #########################################################

    def rtc_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.rtc_display_daq_settings()

    def rtc_populate(self):
        '''
        '''
        self.gb_initialize_panel('self')
        self.layout().addWidget(self.rtc_plot_panel, 17, 0, 1, 16)
        self.gb_initialize_panel('rtc_plot_panel')
        self.rtc_add_common_widgets()
        self.rtc_daq_panel()
        self.rtc_rt_config()
        if self.ls372_temp_widget is not None:
            self.rtc_lakeshore_panel()
        self.rtc_make_plot_panel()
        self.rtc_display_daq_settings()
        self.rtc_plot_running()

    #############################################
    # Lakeshore stuff for DR
    #############################################

    def rtc_lakeshore_panel(self):
        '''
        '''
        # Temp Control
        self.temp_display_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.temp_display_label, 0, 5, 1, 1)
        self.temp_set_point_lineedit = QtWidgets.QLineEdit('0.001', self)
        self.temp_set_point_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.temp_set_point_lineedit))
        self.layout().addWidget(self.temp_set_point_lineedit, 0, 6, 1, 1)
        temp_set_point_pushbuton = QtWidgets.QPushButton('Set New', self)
        temp_set_point_pushbuton.clicked.connect(self.rtc_update_set_point)
        self.layout().addWidget(temp_set_point_pushbuton, 0, 7, 1, 1)
        set_point = self.ls372_temp_widget.temp_control.ls372_get_temp_set_point()
        self.temp_set_point_lineedit.setText('{0:.4f}'.format(set_point * 1e3))
        mxc_temp = float(self.ls372_temp_widget.channels.ls372_get_channel_value(6, reading='kelvin')) * 1e3
        self.temp_display_label.setText('Current Temp {0:.3f}mK (Set) | {1:.3f}mK (Act)'.format(set_point * 1e3, mxc_temp))
        ramp_on, ramp_value = self.ls372_temp_widget.temp_control.ls372_get_ramp()
        self.ramp_lineedit = self.gb_make_labeled_lineedit(label_text='Ramp (K/min): ')
        self.ramp_lineedit.setText('{0}'.format(ramp_value))
        self.ramp_lineedit.setValidator(QtGui.QDoubleValidator(0, 2, 3, self.ramp_lineedit))
        self.layout().addWidget(self.ramp_lineedit, 1, 5, 1, 2)
        set_ramp_pushbutton = QtWidgets.QPushButton('Set Ramp', self)
        self.layout().addWidget(set_ramp_pushbutton, 1, 7, 1, 1)
        set_ramp_pushbutton.clicked.connect(self.rtc_update_ramp)
        # PID Config
        p, i, d = self.ls372_temp_widget.temp_control.ls372_get_pid()
        self.p_lineedit = self.gb_make_labeled_lineedit(label_text='P: ')
        self.p_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 2, self.p_lineedit))
        self.p_lineedit.setText(str(p))
        self.layout().addWidget(self.p_lineedit, 2, 5, 1, 1)
        self.i_lineedit = self.gb_make_labeled_lineedit(label_text='I: ')
        self.i_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 2, self.i_lineedit))
        self.i_lineedit.setText(str(i))
        self.layout().addWidget(self.i_lineedit, 2, 6, 1, 1)
        self.d_lineedit = self.gb_make_labeled_lineedit(label_text='D: ')
        self.d_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 2, self.d_lineedit))
        self.d_lineedit.setText(str(d))
        self.layout().addWidget(self.d_lineedit, 2, 7, 1, 1)
        self.pid_header_label = QtWidgets.QLabel('', self)
        self.pid_header_label.setText( 'P:{0} ::: I:{1} ::: D:{2} '.format(p, i, d))
        self.layout().addWidget(self.pid_header_label, 3, 7, 1, 1)
        # Heater Range
        heater_value = self.ls372_temp_widget.temp_control.ls372_get_heater_value()
        current_range_index, current_range_value = self.ls372_temp_widget.temp_control.ls372_get_heater_range()
        self.heater_range_header_label = QtWidgets.QLabel('Heater Value {0:.5f} (A)'.format(heater_value), self)
        self.layout().addWidget(self.heater_range_header_label, 3, 5, 1, 1)
        self.heater_range_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.heater_range_combobox, 3, 6, 1, 1)
        for range_index, range_value in self.ls372_temp_widget.temp_control.ls372_heater_range_dict.items():
            self.heater_range_combobox.addItem(str(range_value))
            if int(range_index) == int(current_range_index):
                set_to_index = int(range_index)
        self.heater_range_combobox.setCurrentIndex(set_to_index)
        # Read and Write Settings
        read_ls372_settings_pushbutton = QtWidgets.QPushButton('Read Settings', self)
        read_ls372_settings_pushbutton.clicked.connect(self.rtc_get_lakeshore_temp_control)
        self.layout().addWidget(read_ls372_settings_pushbutton, 4, 5, 1, 3)
        update_ls372_settings_pushbutton = QtWidgets.QPushButton('Update Settings', self)
        update_ls372_settings_pushbutton.clicked.connect(self.rtc_edit_lakeshore_temp_control)
        self.layout().addWidget(update_ls372_settings_pushbutton, 5, 5, 1, 3)
        # Control Buttons
        configure_channel_pushbutton = QtWidgets.QPushButton('Configure', self)
        self.layout().addWidget(configure_channel_pushbutton, 6, 6, 1, 2)
        configure_channel_pushbutton.clicked.connect(self.rtc_edit_lakeshore_channel)
        self.channel_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.channel_combobox, 6, 5, 1, 1)
        #self.ls372_samples_widget.scan_channel(1)
        for channel in range(1, 17):
            self.channel_combobox.addItem(str(channel))
        set_aux_analog_out_pushbutton = QtWidgets.QPushButton('Set Analog Out', self)
        set_aux_analog_out_pushbutton.clicked.connect(self.rtc_edit_lakeshore_aux_ouput)
        self.layout().addWidget(set_aux_analog_out_pushbutton, 7, 6, 1, 2)
        aux_analog_label = QtWidgets.QLabel('1', self)
        self.layout().addWidget(aux_analog_label, 7, 5, 1, 1)

    def rtc_get_lakeshore_temp_control(self):
        '''
        '''
        p, i, d = self.ls372_temp_widget.temp_control.ls372_get_pid()
        self.pid_header_label.setText( 'P:{0} ::: I:{1} ::: D:{2} '.format(p, i, d))
        self.status_bar.showMessage('Retreived temp control parameters')

    def rtc_update_set_point(self):
        '''
        '''
        new_set_point = float(self.temp_set_point_lineedit.text()) * 1e-3
        self.ls372_temp_widget.temp_control.ls372_set_temp_set_point(new_set_point)
        self.rtc_check_set_point()

    def rtc_update_ramp(self):
        '''
        '''
        new_ramp = float(self.ramp_lineedit.text())
        self.ls372_temp_widget.temp_control.ls372_set_ramp(new_ramp)

    def rtc_check_set_point(self):
        '''
        '''
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
        self.ls372_temp_widget.channels.ls372_scan_channel(6) # 6 is the MXC thermometer
        self.ls372_temp_widget.channels.ls372_scann
        self.status_bar.showMessage('Set new temp control parameters and scanning the MXC with temp Lakeshore')

    def rtc_scan_lakeshore_channel(self):
        '''
        '''
        channel = self.channel_combobox.currentText()
        self.ls372_samples_widget.ls372_scan_channel(clicked=True, index=channel)

    def rtc_edit_lakeshore_channel(self):
        '''
        '''
        channel = self.channel_combobox.currentText()
        self.ls372_samples_widget.ls372_edit_channel(clicked=True, index=channel)

    def rtc_edit_lakeshore_aux_ouput(self):
        '''
        '''
        self.ls372_samples_widget.ls372_edit_analog_output(clicked=True, analog_output='aux')

    def rtc_display_daq_settings(self):
        '''
        '''
        daq = self.rtc_daq_combobox.currentText()
        self.x_channel = self.daq_x_combobox.currentIndex()
        self.y_channel = self.daq_y_combobox.currentIndex()
        # X
        self.int_time_x = self.daq_settings[daq][str(self.x_channel)]['int_time']
        self.sample_rate_x = self.daq_settings[daq][str(self.x_channel)]['sample_rate']
        daq_settings_x_info = 'Int Time (ms): {0}\n'.format(self.int_time_x)
        daq_settings_x_info += 'Sample Rate (Hz): {0}'.format(str(self.sample_rate_x))
        self.daq_settings_x_label.setText(daq_settings_x_info)
        # Y
        self.int_time_y = self.daq_settings[daq][str(self.y_channel)]['int_time']
        self.sample_rate_y = self.daq_settings[daq][str(self.y_channel)]['sample_rate']
        daq_settings_y_info = 'Int Time (ms): {0}\n'.format(self.int_time_y)
        daq_settings_y_info += 'Sample Rate (Hz): {0}'.format(str(self.sample_rate_y))
        self.daq_settings_y_label.setText(daq_settings_y_info)

    def rtc_daq_panel(self):
        '''
        '''
        # Device
        rtc_daq_header_label = QtWidgets.QLabel('DAQ Device:', self)
        self.layout().addWidget(rtc_daq_header_label, 0, 0, 1, 1)
        self.rtc_daq_combobox = QtWidgets.QComboBox(self)
        for daq in self.daq_settings:
            self.rtc_daq_combobox.addItem(daq)
        self.layout().addWidget(self.rtc_daq_combobox, 0, 1, 1, 3)
        # DAQ Y
        daq_x_header_label = QtWidgets.QLabel('DAQ Ch X Data:', self)
        self.layout().addWidget(daq_x_header_label, 1, 0, 1, 1)
        self.daq_x_combobox = QtWidgets.QComboBox(self)
        for daq in range(0, 8):
            self.daq_x_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_x_combobox, 1, 1, 1, 1)
        self.daq_settings_x_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.daq_settings_x_label, 2, 1, 1, 1)
        # DAQ Y
        daq_y_header_label = QtWidgets.QLabel('DAQ Ch Y Data:', self)
        self.layout().addWidget(daq_y_header_label, 1, 2, 1, 1)
        self.daq_y_combobox = QtWidgets.QComboBox(self)
        for daq in range(0, 8):
            self.daq_y_combobox.addItem(str(daq))
        self.layout().addWidget(self.daq_y_combobox, 1, 3, 1, 1)
        self.daq_settings_y_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.daq_settings_y_label, 2, 3, 1, 1)
        self.daq_y_combobox.currentIndexChanged.connect(self.rtc_display_daq_settings)
        self.daq_x_combobox.currentIndexChanged.connect(self.rtc_display_daq_settings)
        self.rtc_daq_combobox.currentIndexChanged.connect(self.rtc_display_daq_settings)

    def rtc_rt_config(self):
        '''
        '''
        # GRT Serial 
        grt_serial_header_label = QtWidgets.QLabel('GRT SERIAL:', self)
        self.layout().addWidget(grt_serial_header_label, 3, 0, 1, 1)
        self.x_correction_combobox = QtWidgets.QComboBox(self)
        for grt_serial in ['Lakeshore']:
            self.x_correction_combobox.addItem(grt_serial)
        self.layout().addWidget(self.x_correction_combobox, 3, 1, 1, 1)
        # Y Voltage Factor 
        y_voltage_factor_header_label = QtWidgets.QLabel('Resistance Voltage Factor', self)
        self.layout().addWidget(y_voltage_factor_header_label, 3, 2, 1, 1)
        self.y_correction_combobox = QtWidgets.QComboBox(self)
        for index, voltage_reduction_factor in self.voltage_reduction_factor_dict.items():
            self.y_correction_combobox.addItem('{0}'.format(voltage_reduction_factor))
        self.layout().addWidget(self.y_correction_combobox, 3, 3, 1, 1)
        # Data Clip
        data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo (mK)')
        data_clip_lo_lineedit.setText(str(0.0))
        self.layout().addWidget(data_clip_lo_lineedit, 4, 0, 1, 1)
        self.data_clip_lo_lineedit = data_clip_lo_lineedit
        data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi (mK)')
        data_clip_hi_lineedit.setText(str(1000.0))
        self.layout().addWidget(data_clip_hi_lineedit, 4, 2, 1, 1)
        self.data_clip_hi_lineedit = data_clip_hi_lineedit

    def rtc_add_common_widgets(self):
        '''
        '''
        start_row = 5
        row = start_row
        # Sample Name
        self.sample_name_combobox = QtWidgets.QComboBox(self)
        for sample in self.samples_settings:
            self.sample_name_combobox.addItem(sample)
        self.sample_name_combobox.activated.connect(self.rtc_update_sample_name)
        self.layout().addWidget(self.sample_name_combobox, row, 3, 1, 1)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name')
        self.layout().addWidget(self.sample_name_lineedit, row, 0, 1, 2)
        row += 1
        # Buttons
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        start_pushbutton.clicked.connect(self.rtc_start_stop)
        self.layout().addWidget(start_pushbutton, row, 0, 1, 4)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        save_pushbutton.clicked.connect(self.rtc_save)
        row += 1
        self.layout().addWidget(save_pushbutton, row, 0, 1, 4)
        row += 1
        spacer_label = QtWidgets.QLabel(' ', self)
        self.layout().addWidget(spacer_label, row, 0, 3, 4)
        self.rtc_update_sample_name(0)

    def rtc_update_sample_name(self, index):
        '''
        '''
        sample_key = self.sample_name_combobox.currentText()
        sample_name = self.samples_settings[sample_key]
        self.sample_name_lineedit.setText(sample_name)

    def rtc_update_squid_calibration(self, index):
        '''
        '''
        squid_key = self.y_correction_combobox.currentText()
        calibration_value = self.squid_calibration_dict[squid_key]
        self.squid_calibration_lineedit.setText(calibration_value)

    def rtc_update_ls372_widget(self, ls372_widget):
        '''
        '''
        self.ls372_widget = ls372_widget

    #########################################################
    # Plotting
    #########################################################

    def rtc_make_plot_panel(self):
        '''
        '''
        # X
        self.x_time_stream_label = QtWidgets.QLabel('', self)
        self.x_time_stream_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.rtc_plot_panel.layout().addWidget(self.x_time_stream_label, 17, 0, 1, 1)
        self.x_data_label = QtWidgets.QLabel('X Data: X STD:', self)
        self.rtc_plot_panel.layout().addWidget(self.x_data_label, 18, 0, 1, 1)

        # Y
        self.y_time_stream_label = QtWidgets.QLabel('', self)
        self.y_time_stream_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.rtc_plot_panel.layout().addWidget(self.y_time_stream_label, 19, 0, 1, 1)
        self.y_data_label = QtWidgets.QLabel('Y Data: Y STD:', self)
        self.rtc_plot_panel.layout().addWidget(self.y_data_label, 20, 0, 1, 1)

        # XY
        self.xy_scatter_label = QtWidgets.QLabel('', self)
        self.xy_scatter_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.xy_scatter_label.setFixedWidth(0.75 * self.screen_resolution.width())
        self.rtc_plot_panel.layout().addWidget(self.xy_scatter_label, 17, 1, 4, 1)

    #########################################################
    # Running
    #########################################################

    def rtc_start_stop(self):
        '''
        '''
        if 'Start' in self.sender().text():
            self.sender().setText('Stop DAQ')
            self.started = True
            self.rtc_collecter()
        else:
            self.sender().setText('Start DAQ')
            self.started = False
            self.saving_manager.auto_save()

    def rtc_collecter(self, monitor=False):
        '''
        '''
        device = self.rtc_daq_combobox.currentText()
        self.x_data, self.x_stds = [], []
        self.y_data, self.y_stds = [], []
        i = 0
        while self.started:
            x_ts, x_mean, x_min, x_max, x_std = self.daq.get_data(signal_channel=self.x_channel,
                                                                  int_time=self.int_time_x,
                                                                  sample_rate=self.sample_rate_x,
                                                                  device=device)
            y_ts, y_mean, y_min, y_max, y_std = self.daq.get_data(signal_channel=self.y_channel,
                                                                  int_time=self.int_time_y,
                                                                  sample_rate=self.sample_rate_y,
                                                                  device=device)
            self.x_data_label.setText('X Mean: {0:.5f} ::: X STD: {0:.5f}'.format(x_mean, x_std))
            self.y_data_label.setText('Y Mean: {0:.5f} ::: Y STD: {0:.5f}'.format(y_mean, y_std))
            self.x_data.append(x_mean)
            self.x_stds.append(x_std)
            self.y_data.append(y_mean)
            self.y_stds.append(y_std)
            self.rtc_plot_running()
            if i % 25 == 0 and monitor:
                mxc_temp = float(self.ls372_temp_widget.channels.ls372_get_channel_value(6, reading='kelvin')) * 1e3
                heater_value = self.ls372_temp_widget.temp_control.ls372_get_heater_value()
                set_point = self.ls372_temp_widget.temp_control.ls372_get_temp_set_point()
                self.heater_range_header_label.setText('Heater Value {0:.5f} (A)'.format(heater_value))
                self.temp_display_label.setText('Current Temp {0:.3f}mK (Set) | {1:.3f}mK (Act)'.format(set_point * 1e3, mxc_temp))
            QtWidgets.QApplication.processEvents()
            i += 1
            self.repaint()

    ###################################################
    # Saving and Plotting
    ###################################################

    def rtc_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}.txt'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def rtc_auto_save(self):
        '''
        '''

    def rtc_save(self):
        '''
        '''
        save_path = self.rtc_index_file_name()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter=',*.txt,*.dat')[0]
        if len(save_path) > 0:
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_data[i], self.x_stds[i], self.y_data[i], self.y_stds[i])
                    save_handle.write(line)
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')
        self.rtc_plot_xy()

    def rtc_plot_running(self):
        '''
        '''
        self.rtc_plot_x()
        self.rtc_plot_y()
        self.rtc_plot_xy(running=True)

    def rtc_plot_x(self):
        '''
        '''
        fig, ax = self.rtc_create_blank_fig(frac_screen_width=0.4, frac_screen_height=0.18, left=0.12, top=0.98)
        ax.set_xlabel('Sample', fontsize=14)
        ax.set_ylabel('X ($V$)', fontsize=14)
        label = 'DAQ {0}'.format(self.x_channel)
        ax.errorbar(range(len(self.x_data)), self.x_data, self.x_stds, marker='.', linestyle='None', label=label)
        pl.legend(loc='best', fontsize=14)
        fig.savefig('temp_x.png', transparent=True)
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_x.png')
        self.x_time_stream_label.setPixmap(image_to_display)

    def rtc_plot_y(self):
        '''
        '''
        fig, ax = self.rtc_create_blank_fig(frac_screen_width=0.4, frac_screen_height=0.18, left=0.12, top=0.98)
        ax.set_xlabel('Sample', fontsize=14)
        ax.set_ylabel('Y ($V$)', fontsize=14)
        label = 'DAQ {0}'.format(self.y_channel)
        ax.errorbar(range(len(self.y_data)), self.y_data, self.y_stds, marker='.', linestyle='None', label=label)
        pl.legend(loc='best', fontsize=14)
        fig.savefig('temp_y.png', transparent=True)
        pl.close('all')
        image_to_display = QtGui.QPixmap('temp_y.png')
        self.y_time_stream_label.setPixmap(image_to_display)

    def rtc_plot_xy(self, running=False):
        '''
        '''
        fig, ax = self.rtc_create_blank_fig(frac_screen_width=0.75, frac_screen_height=0.55, left=0.08, bottom=0.08, top=0.95)
        y_data, y_stds = self.rtc_adjust_y_data()
        x_data, x_stds = self.rtc_adjust_x_data()
        ax.set_xlabel('Temperature ($mK$)', fontsize=14)
        ax.set_ylabel('Resistance ($m\Omega$)', fontsize=14)
        data_clip_lo = float(self.data_clip_lo_lineedit.text())
        data_clip_hi = float(self.data_clip_hi_lineedit.text())
        selector =  np.where(np.logical_and(data_clip_lo < x_data, x_data < data_clip_hi))
        sample_name = self.sample_name_lineedit.text()
        ax.errorbar(x_data[selector], y_data[selector], xerr=x_stds[selector], yerr=y_stds[selector], marker='.', linestyle='-', label=sample_name)
        if running:
            ax.set_xlabel('Temperature ($mK$)', fontsize=14)
            ax.set_ylabel('Resistance ($m\Omega$)', fontsize=14)
            ax.set_title(sample_name, fontsize=14)
            pl.legend(loc='best', fontsize=14)
            fig.savefig('temp_xy.png', transparent=True)
            pl.close('all')
            image_to_display = QtGui.QPixmap('temp_xy.png')
            self.xy_scatter_label.setPixmap(image_to_display)
        else:
            ax.set_xlabel('Temperature ($mK$)', fontsize=18)
            ax.set_ylabel('Resistance ($m\Omega$)', fontsize=18)
            ax.set_title(sample_name, fontsize=18)
            pl.show()

    def rtc_adjust_x_data(self):
        '''
        '''
        x_data = []
        x_stds = []
        grt_serial = self.x_correction_combobox.currentText()
        if grt_serial == 'Lakeshore':
            x_data = np.asarray(self.x_data) * 100
            x_stds = np.asarray(self.x_stds) * 100
        return x_data, x_stds

    def rtc_adjust_y_data(self):
        '''
        '''
        y_data = []
        y_stds = []
        voltage_reduction_factor = float(self.y_correction_combobox.currentText())
        y_data = np.asarray(self.y_data) * voltage_reduction_factor
        y_stds = np.asarray(self.y_stds) * voltage_reduction_factor
        return y_data, y_stds

    def bd_final_rt_plot(self):
        '''
        '''
        meta_data = self.bd_get_all_meta_data(popup='xy_collector')
        plot_params = self.bd_get_all_params(meta_data, settings.xy_collector_plot_params, 'xy_collector')
        rtc = RTCurve([])
        invert = getattr(self, '_xy_collector_popup_invert_output_checkbox').isChecked()
        normal_res = str(getattr(self, '_xy_collector_popup_sample_res_lineedit').text())
        if self.gb_is_float(normal_res, enforce_positive=True):
            normal_res = float(normal_res)
        else:
            normal_res = np.nan
        pprint(plot_params)
        title = '{0} R vs. T'.format(plot_params['sample_name'])
        label = '{0}-{1}'.format(plot_params['sample_name'], plot_params['sample_drift_direction'])
        data_clip_lo = float(plot_params['data_clip_lo'])
        data_clip_hi = float(plot_params['data_clip_hi'])
        if len(self.xdata) > 2:
            xlim_range = data_clip_hi - data_clip_lo
            xlim = (data_clip_lo - 0.01 * xlim_range, data_clip_hi + 0.01 * xlim_range)
            input_dict = {'invert': invert, 'normal_res': normal_res, 'label': label,
                          'title': title, 'xlim': xlim}
            sample_res_vector = rtc.normalize_squid_output(self.ydata, input_dict)
            selector = np.logical_and(np.asarray(self.xdata) > data_clip_lo, np.asarray(self.xdata) < data_clip_hi)
            self.active_fig = rtc.plot_rt_curves(np.asarray(self.xdata)[selector], np.asarray(sample_res_vector)[selector],
                                                 in_millikelvin=True, fig=None, input_dict=input_dict)
            self.temp_plot_path = './temp_files/temp_rt_png.png'
            self.active_fig.savefig(self.temp_plot_path)
        self.bd_adjust_final_plot_popup('RT', xlabel='Sample Temp (mK)', ylabel='Sample Res ($\Omega$)', title=title)

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
        ax.tick_params(axis='x', labelsize=16)
        ax.tick_params(axis='y', labelsize=16)
        return fig, ax
