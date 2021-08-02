import time
import shutil
import os
import simplejson
import pylab as pl
import numpy as np
from copy import copy
from datetime import datetime
from pprint import pprint
from scipy.signal import medfilt2d
from scipy.optimize import leastsq, curve_fit
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class PolarizationEfficiency(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, csm_widget, srs_widget, sk_widget, data_folder):
        '''
        '''
        super(PolarizationEfficiency, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.srs_widget = srs_widget
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.csm_widget = csm_widget
        self.sk_widget = sk_widget
        self.pe_update_samples()
        self.daq = BoloDAQ()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid_2 = QtWidgets.QGridLayout()
        self.pe_plot_panel = QtWidgets.QWidget(self)
        self.layout().addWidget(self.pe_plot_panel, 0, 2, 20, 1)
        self.pe_plot_panel.setLayout(grid_2)
        self.pe_plot_panel.setFixedWidth(0.7 * screen_resolution.width())
        self.pe_configure_input_panel()
        self.pe_configure_plot_panel()
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = data_folder
        self.start_pause = 5.0
        self.status_bar.showMessage('Ready')
        self.y_fit = []
        self.angles = []
        self.x_data = []
        self.x_stds = []
        self.y_data = []
        self.y_stds = []
        self.pe_plot_time_stream([0], -1, 1.0)
        self.pe_plot(running=True)

    #################################################
    # Gui Config
    #################################################

    def pe_update_samples(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)

    def pe_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.pe_update_scan_params()

    def pe_update_source_type(self):
        '''
        '''
        source_type = self.source_type_combobox.currentText()
        if source_type in ['LN2', 'Heater']:
            self.source_frequency_lineedit.setDisabled(True)
            self.source_power_lineedit.setDisabled(True)
            self.source_angle_lineedit.setDisabled(True)
            self.source_temp_lineedit.setDisabled(False)
            self.source_frequency_lineedit.setText('Thermal')
            if source_type == 'LN2':
                self.source_temp_lineedit.setText('77')
        else:
            self.source_frequency_lineedit.setDisabled(False)
            self.source_power_lineedit.setDisabled(False)
            self.source_angle_lineedit.setDisabled(False)
            self.source_temp_lineedit.setDisabled(True)
            self.source_temp_lineedit.setText('')
            self.source_frequency_lineedit.setText('')

    def pe_update_sample_name(self):
        '''
        '''
        sample_key = self.sample_name_combobox.currentText()
        sample_name = self.samples_settings[sample_key]
        self.sample_name_lineedit.setText(sample_name)

    def pe_configure_input_panel(self):
        '''
        '''
        # DAQ (Device + Channel) Selection
        self.device_combobox = self.gb_make_labeled_combobox(label_text='Device:')
        self.layout().addWidget(self.device_combobox, 0, 0, 1, 1)
        for device in self.daq_settings:
            self.device_combobox.addItem(device)
        self.daq_combobox = self.gb_make_labeled_combobox(label_text='DAQ:')
        self.layout().addWidget(self.daq_combobox, 0, 1, 1, 1)
        for channel in sorted([int(x) for x in self.daq_settings[device]]):
            self.daq_combobox.addItem(str(channel))
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int Time (ms):')
        self.layout().addWidget(self.int_time_lineedit, 1, 0, 1, 1)
        self.int_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.int_time_lineedit))
        self.int_time_lineedit.setText('500')
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz):')
        self.layout().addWidget(self.sample_rate_lineedit, 1, 1, 1, 1)
        self.sample_rate_lineedit.setText('5000')
        self.sample_rate_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.sample_rate_lineedit))
        #Pause Time 
        self.pause_time_lineedit = self.gb_make_labeled_lineedit(label_text='Pause Time (ms):', lineedit_text='1500')
        self.pause_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.pause_time_lineedit))
        self.layout().addWidget(self.pause_time_lineedit, 2, 0, 1, 2)
        # Stepper Motor Selection
        if self.csm_widget is not None:
            stepper_motor_header_label = QtWidgets.QLabel('Stepper Motor:', self)
            self.layout().addWidget(stepper_motor_header_label, 3, 0, 1, 1)
            self.stepper_motor_label = QtWidgets.QLabel(self.csm_widget.com_port, self)
            self.layout().addWidget(self.stepper_motor_label, 3, 1, 1, 1)
            self.stepper_settings_label = QtWidgets.QLabel('Stepper Settings', self)
            self.layout().addWidget(self.stepper_settings_label, 4, 0, 1, 1)
        ######
        # Scan Params
        ######
        #Start Scan
        self.start_angle_lineedit = self.gb_make_labeled_lineedit(label_text='Start Angle (degs):', lineedit_text='0')
        self.start_angle_lineedit.setValidator(QtGui.QIntValidator(-1, 1, self.start_angle_lineedit))
        self.start_angle_lineedit.textChanged.connect(self.pe_update_scan_params)
        self.layout().addWidget(self.start_angle_lineedit, 5, 0, 1, 1)
        #End Scan
        self.end_angle_lineedit = self.gb_make_labeled_lineedit(label_text='End Angle (degs):', lineedit_text='180')
        self.end_angle_lineedit.setValidator(QtGui.QIntValidator(0, 720, self.end_angle_lineedit))
        self.end_angle_lineedit.textChanged.connect(self.pe_update_scan_params)
        self.layout().addWidget(self.end_angle_lineedit, 5, 1, 1, 1)
        #Grid Angle Interval
        self.angle_interval_lineedit = self.gb_make_labeled_lineedit(label_text='Grid Angle Interval (degs):', lineedit_text='10')
        self.angle_interval_lineedit.textChanged.connect(self.pe_update_scan_params)
        self.angle_interval_lineedit.setValidator(QtGui.QIntValidator(1, 90, self.angle_interval_lineedit))
        self.layout().addWidget(self.angle_interval_lineedit, 6, 0, 1, 1)

        # Voltage Bias
        self.voltage_bias_lineedit = self.gb_make_labeled_lineedit(label_text='Voltage Bias (uV):')
        self.voltage_bias_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 3, self.voltage_bias_lineedit))
        self.layout().addWidget(self.voltage_bias_lineedit, 6, 1, 1, 1)
        #Scan Type (Grid or Monchromatic Horn)
        self.scan_type_combobox = self.gb_make_labeled_combobox(label_text='Scan Type')
        for scan_type in ['Horn', 'Grid']:
            self.scan_type_combobox.addItem(scan_type)
        self.layout().addWidget(self.scan_type_combobox, 7, 0, 1, 1)
        #Angle Step size (Changes grid vs Sigma Koki)
        self.angle_per_step_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.angle_per_step_label, 7, 1, 1, 1)
        self.scan_type_combobox.currentIndexChanged.connect(self.pe_update_scan_params)
        # Source Type
        self.source_type_combobox = self.gb_make_labeled_combobox(label_text='Source Type')
        for source_type in ['Analyzer', 'LN2', 'Heater']:
            self.source_type_combobox.addItem(source_type)
        self.source_type_combobox.currentIndexChanged.connect(self.pe_update_source_type)
        self.layout().addWidget(self.source_type_combobox, 8, 0, 1, 1)

        self.modulation_frequency_lineedit = self.gb_make_labeled_lineedit(label_text='Modulation Frequency (Hz)', lineedit_text='12')
        self.modulation_frequency_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 3, self.modulation_frequency_lineedit))
        self.layout().addWidget(self.modulation_frequency_lineedit, 8, 1, 1, 1)
        # Source Temp
        self.source_temp_lineedit = self.gb_make_labeled_lineedit(label_text='Source Temp (K):')
        self.source_temp_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 3, self.source_temp_lineedit))
        self.layout().addWidget(self.source_temp_lineedit, 9, 0, 1, 1)
        # Source Frequency
        self.source_frequency_lineedit = self.gb_make_labeled_lineedit(label_text='Source Frequency (GHz):')
        self.source_frequency_lineedit.setValidator(QtGui.QDoubleValidator(0, 1000, 3, self.source_frequency_lineedit))
        self.layout().addWidget(self.source_frequency_lineedit, 9, 1, 1, 1)
        # Source Power
        self.source_power_lineedit = self.gb_make_labeled_lineedit(label_text='Source Power (dBm):')
        self.source_power_lineedit.setValidator(QtGui.QDoubleValidator(-1e3, 1e3, 5, self.source_power_lineedit))
        self.layout().addWidget(self.source_power_lineedit, 10, 0, 1, 1)
        # Source Angle
        self.source_angle_lineedit = self.gb_make_labeled_lineedit(label_text='Source Angle (degs):')
        self.source_angle_lineedit.setValidator(QtGui.QDoubleValidator(0, 360, 2, self.source_angle_lineedit))
        self.layout().addWidget(self.source_angle_lineedit, 10, 1, 1, 1)
        self.set_source_angle_pushbutton = QtWidgets.QPushButton('Set Angle', self)
        self.layout().addWidget(self.set_source_angle_pushbutton, 11, 0, 1, 1)
        self.set_source_angle_pushbutton.clicked.connect(self.pe_set_source_angle)
        self.set_source_angle_home_pushbutton = QtWidgets.QPushButton('Set Angle Home', self)
        self.layout().addWidget(self.set_source_angle_home_pushbutton, 11, 1, 1, 1)
        self.set_source_angle_pushbutton.clicked.connect(self.sk_widget.sk_set_home)
        #Scan Info size
        self.scan_info_label = QtWidgets.QLabel('Scan Info', self)
        self.layout().addWidget(self.scan_info_label, 12, 0, 1, 2)
        self.sample_name_combobox = self.gb_make_labeled_combobox(label_text='Sample Name:')
        self.layout().addWidget(self.sample_name_combobox, 13, 0, 1, 1)
        for sample in self.samples_settings:
            self.sample_name_combobox.addItem(sample)
        self.sample_name_combobox.setCurrentIndex(5)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name:')
        self.layout().addWidget(self.sample_name_lineedit, 13, 1, 1, 1)
        self.sample_name_combobox.activated.connect(self.pe_update_sample_name)
        self.sample_name_combobox.currentIndexChanged.connect(self.pe_update_sample_name)
        # Zero Lock in
        self.zero_lock_in_checkbox = QtWidgets.QCheckBox('Zero Lock In?', self)
        self.zero_lock_in_checkbox.setChecked(True)
        self.layout().addWidget(self.zero_lock_in_checkbox, 14, 0, 1, 1)
        self.reverse_scan_checkbox = QtWidgets.QCheckBox('Reverse Scan?', self)
        self.reverse_scan_checkbox.setChecked(False)
        self.layout().addWidget(self.reverse_scan_checkbox, 14, 1, 1, 1)
        #####
        # Control Buttons 
        ######
        self.start_pushbutton = QtWidgets.QPushButton('Start', self)
        self.layout().addWidget(self.start_pushbutton, 15, 0, 1, 2)
        self.start_pushbutton.clicked.connect(self.pe_start_stop_scan)

        self.load_pushbutton = QtWidgets.QPushButton('Load', self)
        self.layout().addWidget(self.load_pushbutton, 16, 0, 1, 2)
        self.load_pushbutton.clicked.connect(self.pe_load)

        self.save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.layout().addWidget(self.save_pushbutton, 17, 0, 1, 2)
        self.save_pushbutton.clicked.connect(self.pe_save)

        if self.csm_widget is None:
            self.start_pushbutton.setDisabled(True)

    def pe_configure_plot_panel(self):
        '''
        '''
        self.pe_plot_label = QtWidgets.QLabel('', self.pe_plot_panel)
        self.pe_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.pe_plot_panel.layout().addWidget(self.pe_plot_label, 0, 0, 1, 4)
        self.time_stream_plot_label = QtWidgets.QLabel('', self.pe_plot_panel)
        self.time_stream_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.pe_plot_panel.layout().addWidget(self.time_stream_plot_label, 1, 0, 1, 4)
        self.data_mean_label = QtWidgets.QLabel('Data Mean (V):', self.pe_plot_panel)
        self.pe_plot_panel.layout().addWidget(self.data_mean_label, 2, 0, 1, 1)
        self.data_std_label = QtWidgets.QLabel('Data STD (V)', self.pe_plot_panel)
        self.pe_plot_panel.layout().addWidget(self.data_std_label, 2, 1, 1, 1)
        self.data_summary_label = QtWidgets.QLabel('', self.pe_plot_panel)
        self.pe_plot_panel.layout().addWidget(self.data_summary_label, 3, 0, 1, 2)
        self.data_time_stream = QtWidgets.QLabel('', self.pe_plot_panel)

    def bd_get_simulated_data(self, datatype, current_position, noise=10):
        '''
        noise is in percent and is of the max-min of data
        '''
        in_degs = current_position*np.pi/180
        dev = (np.random.randn()-0.5)*2/100*noise
        simulated_data = np.sin(in_degs) + dev
        return simulated_data

    #################################################
    # Scanning
    #################################################

    def pe_set_source_angle(self, clicked, set_to_position_deg=None):
        '''
        '''
        if set_to_position_deg is None:
            set_to_position_deg = float(self.source_angle_lineedit.text())
        self.sk_widget.sk_set_position(clicked, set_to_position_deg=set_to_position_deg)

    def pe_update_scan_params(self):
        '''
        '''
        if len(self.end_angle_lineedit.text()) == 0 or len(self.start_angle_lineedit.text()) == 0:
            return None
        if len(self.angle_interval_lineedit.text()) == 0:
            return None
        if int(self.end_angle_lineedit.text()) < int(self.start_angle_lineedit.text()):
            return None
        if int(self.angle_interval_lineedit.text()) == 0:
            return None
        end_angle = int(self.end_angle_lineedit.text())
        start_angle = int(self.start_angle_lineedit.text())
        angle_interval = int(self.angle_interval_lineedit.text())
        if self.scan_type_combobox.currentText() == 'Grid':
            angle_per_step = 0.0035 # mDeg
        else:
            angle_per_step = 0.005 # mDeg
        stepper_motor_steps_data_point = angle_interval / angle_per_step
        scan_positions = np.arange(start_angle, end_angle, angle_interval)
        n_data_points = len(scan_positions)
        info_string = 'N Data Points: {0} ::: '.format(n_data_points)
        info_string += 'Angle Per Step {0:.1f} ::: '.format(angle_per_step)
        info_string += 'Stepper Motor Steps Per Data Point {0}'.format(stepper_motor_steps_data_point)
        self.scan_info_label.setText(info_string)
        self.pe_setup_stepper()

    def pe_setup_stepper(self):
        '''
        '''
        sm_com_port = self.stepper_motor_label.text()
        self.status_bar.showMessage('Setting up serial connection to stepper motor on {0}'.format(sm_com_port))
        QtWidgets.QApplication.processEvents()
        sm_settings_str = ''
        if self.csm_widget is not None:
            for setting, value in self.csm_widget.stepper_settings_dict.items():
                sm_settings_str += ' '.join([x.title() for x in setting.split('_')])
                sm_settings_str += ' {0} ::: '.format(value)
            self.stepper_settings_label.setText(sm_settings_str)

    def pe_start_stop_scan(self):
        '''
        '''
        if self.sender().text() == 'Start':
            self.y_fit = []
            self.pe_update_scan_params()
            self.sender().setText('Stop')
            self.started = True
            self.pe_scan()
        else:
            self.y_fit = []
            self.sender().setText('Start')
            self.started = False
            self.pe_save()

    def pe_convert_angles_to_stepper_motor_positions(self, scan_angles):
        '''
        '''
        scan_type = self.scan_type_combobox.currentText()
        if scan_type == 'Grid':
            angle_per_step = 0.0032 # deg
            set_position = self.csm_widget.csm_set_position
        else:
            angle_per_step = 0.005 # deg
            set_position = self.sk_widget.sk_set_position
        stepper_motor_positions = [float(x) / angle_per_step  for x in scan_angles]
        return stepper_motor_positions, set_position

    def pe_scan(self):
        '''
        '''
        pause_time = int(self.pause_time_lineedit.text())
        device = self.device_combobox.currentText()
        signal_channel = self.daq_combobox.currentText()
        int_time = int(self.int_time_lineedit.text())
        sample_rate = float(self.sample_rate_lineedit.text())
        scan_type = self.scan_type_combobox.currentText()
        start_angle = int(self.start_angle_lineedit.text())
        end_angle = int(self.end_angle_lineedit.text())
        angle_interval = int(self.angle_interval_lineedit.text())
        scan_angles = range(start_angle, end_angle + angle_interval, angle_interval)
        start_angle = scan_angles[0]
        n_data_points = len(scan_angles)
        stepper_motor_positions, set_position = self.pe_convert_angles_to_stepper_motor_positions(scan_angles)
        start_position = stepper_motor_positions[0]
        signal_channels = [signal_channel]
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=int_time,
                      sample_rate=sample_rate,
                      device=device)
        while self.started:
            t_start = datetime.now()
            self.angles = []
            self.x_data, self.x_stds = [], []
            self.y_data, self.y_stds = [], []
            if self.reverse_scan_checkbox.isChecked():
                stepper_motor_positions = list(reversed(stepper_motor_positions))
            for i, position in enumerate(stepper_motor_positions):
                set_position(clicked=False, position=int(position))
                if i == 0:
                    self.status_bar.showMessage('Waiting {0}s for grid to move to start position'.format(self.start_pause))
                    QtWidgets.QApplication.processEvents()
                    time.sleep(self.start_pause) # wait for motor to reach starting point
                time.sleep(pause_time * 1.5e-3)
                if self.zero_lock_in_checkbox.isChecked():
                    self.srs_widget.srs_zero_lock_in_phase()
                time.sleep(pause_time * 1e-3)
                # Gather Data and Append to Vector then plot
                self.x_data.append(position)
                self.x_stds.append(2) # guesstimated < 2 step error in position
                data_dict = daq.run()
                data_time_stream = data_dict[signal_channel]['ts']
                mean = data_dict[signal_channel]['mean']
                min_ = data_dict[signal_channel]['min']
                max_ = data_dict[signal_channel]['max']
                std = data_dict[signal_channel]['std']
                self.y_data.append(mean)
                self.y_stds.append(std)
                pol_eff_str = ''
                scan_angle = scan_angles[i]
                self.angles.append(scan_angle)
                if np.abs(scan_angle - start_angle) > 90:
                    self.x_fit = []
                    self.y_fit = []
                    normalized_amplitude = self.y_data / np.max(self.y_data)
                    initial_fit_params = self.pe_moments(self.x_data, np.asarray(self.y_data), angle_interval)
                    try:
                        fit_params = self.pe_fit_sine(self.x_data, np.asarray(self.y_data), initial_fit_params)
                        for x_val in range(int(start_position), int(position), 100):
                            fit_val = self.pe_test_sine(x_val, fit_params[0], fit_params[1], fit_params[2], fit_params[3])
                            angle_ = (self.x_data[i] /fit_params[1]) * 2 * np.pi
                            self.y_fit.append(fit_val)
                            self.x_fit.append(x_val)
                        pol_eff_fit = np.min(self.y_fit) / np.max(self.y_fit) * 1e2 # is a pct
                        pol_eff_data = np.min(self.y_data) / np.max(self.y_data) * 1e2 # is a pct
                        pol_eff_str = 'Pol Eff: {0:.2f}% (Fit) Pol Eff: {1:.2f}% (Data)'.format(pol_eff_fit, pol_eff_data)
                    except RuntimeError:
                        fit_params = initial_fit_params
                pct_finished = 1e2 * float(i + 1) / float(len(scan_angles))
                self.status_bar.progress_bar.setValue(np.ceil(pct_finished))
                self.pe_plot_time_stream(data_time_stream, min_, max_)
                self.pe_plot(running=True, pol_eff_str=pol_eff_str)
                pol_eff_str += 'Min: {0} Max:{1}'.format(np.min(self.y_data), np.max(self.y_data))
                self.data_mean_label.setText('{0:.6f}'.format(mean))
                self.data_std_label.setText('{0:.6f}'.format(std))
                self.data_summary_label.setText(pol_eff_str)
                # Compute and report time diagnostics
                t_now = datetime.now()
                t_elapsed = t_now - t_start
                t_elapsed = t_elapsed.seconds + t_elapsed.microseconds * 1e-6
                t_average = t_elapsed / float(i + 1)
                steps_remain = n_data_points - i
                t_remain = t_average * steps_remain
                status_message = 'Elapsed Time(s): {0:.1f} Remaining Time (s): {1:.1f} ::: Current Angle (deg) {2} ::: (Step {3} of {4})'.format(t_elapsed, t_remain, scan_angle, i, n_data_points)
                self.status_bar.showMessage(status_message)
                QtWidgets.QApplication.processEvents()
                if not self.started:
                    break
                elif i + 1 == n_data_points:
                    self.started = False
        self.pe_save()
        self.sender().setText('Start')
        self.started = False
        set_position(clicked=False, position=int(stepper_motor_positions[1]))

    ###################################################################
    # Saving and Plotting
    ###################################################################

    def pe_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            if self.reverse_scan_checkbox.isChecked():
                file_name = '{0}_{1}_Reversed.dat'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            else:
                file_name = '{0}_{1}.dat'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def pe_load(self):
        '''
        '''
        save_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Pol data', '.txt')[0]
        self.x_data, self.x_stds, self.y_data, self.y_stds = [], [], [], []
        with open(save_path, 'r') as fh:
            lines = fh.readlines()
            for line in lines:
                x_data = float(line.split(', ')[0].strip())
                x_std = float(line.split(', ')[1].strip())
                y_data = float(line.split(', ')[2].strip())
                y_std = float(line.split(', ')[3].strip())
                self.x_data.append(x_data)
                self.x_stds.append(x_std)
                self.y_data.append(y_data)
                self.y_stds.append(y_std)
        self.pe_plot()

    def pe_save(self):
        '''
        '''
        save_path = self.pe_index_file_name()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter='*.txt')[0]
        if len(save_path) > 0:
            self.gb_save_meta_data(save_path, 'txt')
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_data[i], self.x_stds[i], self.y_data[i], self.y_stds[i])
                    save_handle.write(line)
            if 'txt' in save_path:
                shutil.copy(os.path.join('temp_files', 'temp_pol.png'), save_path.replace('txt', 'png'))
            else:
                shutil.copy(os.path.join('temp_files', 'temp_pol.png'), save_path.replace('dat', 'png'))
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')

    def pe_plot_time_stream(self, ts, min_, max_):
        '''
        '''
        fig, ax, ax_twin = self.pe_create_blank_fig(left=0.15, frac_screen_width=0.6, frac_screen_height=0.25, top=0.9, bottom=0.21, n_axes=1)
        ax.plot(ts)
        ax.set_xlabel('Samples', fontsize=14)
        ax.set_ylabel('($V$)', fontsize=14)
        fig.savefig(os.path.join('temp_files', 'temp_ts.png'), transparent=True)
        pl.close('all')
        image = QtGui.QPixmap(os.path.join('temp_files', 'temp_ts.png'))
        self.time_stream_plot_label.setPixmap(image)

    def pe_plot(self, running=False, pol_eff_str=None):
        '''
        '''
        pl.close('all')
        fig, ax, ax_twin = self.pe_create_blank_fig(left=0.15, bottom=0.2, frac_screen_width=0.6, frac_screen_height=0.5, n_axes=1, twin_yaxis=True)
        ax.set_xlabel('Degrees ($^\circ$)', fontsize=10)
        ax.set_ylabel('Amplitude', fontsize=10)
        title = 'Polarization Efficiency'
        if len(self.sample_name_lineedit.text()) > 0:
            title += ' {0}'.format(self.sample_name_lineedit.text())
        ax.set_title(title, fontsize=14)
        ax_twin.errorbar(self.x_data, self.y_data, yerr=self.y_stds, xerr=self.x_stds, marker='.', linestyle='-', color='k', label='data')
        ax.plot(self.angles, self.y_data, marker='.', linestyle='-', color='k')
        if len(self.y_fit) > 0:
            if pol_eff_str is not None:
                ax_twin.plot(self.x_fit, self.y_fit, color='r', linestyle='-', label=pol_eff_str)
            else:
                ax_twin.plot(self.x_fit, self.y_fit, color='r', linestyle='-', label='fit')
            fit_to_subtract = np.interp(self.x_data, self.x_fit, self.y_fit)
            residual = np.asarray(self.y_data) - np.asarray(fit_to_subtract)
            pct_residual = 1e2 * np.max(np.abs(residual)) / np.max(self.y_data)
            label = 'Residual {0:.2f}/{1:.2f}/{2:.2f} (pk/data_max / %)'.format(np.max(np.abs(residual)), np.max(self.y_data), pct_residual)
            ax_twin.plot(self.x_data, residual, color='g', linestyle='-', label='Residual')
        pl.legend()
        fig.savefig(os.path.join('temp_files', 'temp_pol.png'), transparent=True)
        image = QtGui.QPixmap(os.path.join('temp_files', 'temp_pol.png'))
        self.pe_plot_label.setPixmap(image)
        if not running and False:
            angle_interval = int(self.angle_interval_lineedit.text())
            initial_fit_params = self.pe_moments(self.x_data, np.asarray(self.y_data), angle_interval)
            fit_params = self.pe_fit_sine(self.x_data, np.asarray(self.y_data), initial_fit_params)
            self.y_fit = []
            self.x_fit = []
            for x_val in np.arange(0, 360, 2):
                fit_val = self.pe_test_sine(x_val, fit_params[0], fit_params[1], fit_params[2], fit_params[3])
                angle_ = (x_val /fit_params[1]) * 2 * np.pi
                self.y_fit.append(fit_val)
                self.x_fit.append(x_val)
            pol_eff_fit = np.min(self.y_fit) / np.max(self.y_fit) * 1e2 # is a pct
            pol_eff_data = np.min(self.y_data) / np.max(self.y_data) * 1e2 # is a pct
            pol_eff_str = 'Pol Eff: {0:.2f}% (Fit) Pol Eff: {1:.2f}% (Data)'.format(pol_eff_fit, pol_eff_data)

    def pe_angle_to_position(self, angle):
        '''
        '''
        position = angle * 1e-3
        return position

    def pe_position_to_angle(self, position):
        '''
        '''
        angle = position * 1e3
        return angle

    def pe_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.8,
                             left=0.08, right=0.98, top=0.95, bottom=0.08, n_axes=2,
                             aspect=None, twin_yaxis=False):
        if frac_screen_width is None and frac_screen_height is None:
            fig = pl.figure()
        else:
            width = (frac_screen_width * self.screen_resolution.width()) / self.monitor_dpi
            height = (frac_screen_height * self.screen_resolution.height()) / self.monitor_dpi
            fig = pl.figure(figsize=(width, height))
        fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
        if n_axes == 2:
            ax1 = fig.add_subplot(211, label='int')
            ax2 = fig.add_subplot(212, label='spec')
            return fig, ax1, ax2
        else:
            ax = fig.add_subplot(111)
            ax_twin = None
            if twin_yaxis:
                ax_twin = ax.twiny()
            return fig, ax, ax_twin

    ##################################################
    ## Fitting Utilities
    ##################################################

    def pe_arbitrary_sine(self, amplitude, period, y_offset):
        def arb_sine(x):
            value = amplitude*np.sin(x * period) ** 2 + y_offset
            return value
        return arb_sine

    def pe_test_sine(self, x_val, amplitude, period, phase, y_offset=0.0):
        if period is None:
            return np.nan
        period = float(period)
        y_offset = float(y_offset)
        #value = amplitude * np.sin((2.5 * x_val / period) * 2 * np.pi + phase) + y_offset
        value = amplitude * np.sin((x_val / period) * 2 * np.pi + phase) + y_offset
        return value

    def pe_moments(self, raw_angle, data, degsperstep):
        if len(data) == 0:
            return None, None, None
        try:
            amplitude = (np.max(data) - np.min(data)) / 2.0
        except ValueError:
            import ipdb;ipdb.set_trace()
        y_offset = np.min(data) + amplitude
        radsperstep = degsperstep * (np.pi / 180.0)
        period_in_stepper_steps = 2 * np.abs(raw_angle[data.argmax()] - raw_angle[data.argmin()])
        period = period_in_stepper_steps
        period = 120000
        phase = 0.0
        return amplitude, period, phase, y_offset

    def pe_fit_sine(self, x_data, y_data, fit_params):
        fit_params = curve_fit(self.pe_test_sine, x_data, y_data, p0=fit_params)
        return fit_params[0]
