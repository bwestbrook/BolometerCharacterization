import time
import simplejson
import shutil
import os
import pylab as pl
import numpy as np
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.fourier_transform_spectroscopy import FourierTransformSpectroscopy
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass
from bd_tools.configure_stepper_motor import ConfigureStepperMotor

class FourierTransformSpectrometer(QtWidgets.QWidget, GuiBuilder, FourierTransformSpectroscopy):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, csm_widget, srs_widget, data_folder):
        '''
        '''
        super(FourierTransformSpectrometer, self).__init__()
        self.bands = self.ftsy_get_bands()
        self.optical_elements = self.ftsy_get_optical_elements()
        self.status_bar = status_bar
        self.srs_widget = srs_widget
        self.csm_widget = csm_widget
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid_2 = QtWidgets.QGridLayout()
        self.fts_configure_input_panel()
        self.fts_configure_plot_panel()
        self.data_folder = data_folder
        self.start_pause = 5.0
        self.status_bar.showMessage('Ready')
        self.x_data = []
        self.x_stds = []
        self.y_data = []
        self.y_stds = []
        self.fts_plot()
        self.started = False
        self.fts_update_samples()
        self.fts_plot_time_stream([0], -1.0, 1.0)
        self.fts_update_sample_name(0)

    #################################################
    # Gui Config
    #################################################

    def fts_update_samples(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)

    def fts_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.fts_update_scan_params()

    def fts_update_sample_name(self, index):
        '''
        '''
        sample_name = self.samples_settings[str(index + 1)]
        self.sample_name_lineedit.setText(sample_name)

    def fts_configure_input_panel(self):
        '''
        '''
        welcome_header_label = QtWidgets.QLabel('Welcome to FTS', self)
        self.layout().addWidget(welcome_header_label, 0, 0, 1, 2)
        # DAQ (Device + Channel) Selection
        device_header_label = QtWidgets.QLabel('Device:', self)
        self.layout().addWidget(device_header_label, 1, 0, 1, 1)
        self.device_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.device_combobox, 1, 1, 1, 1)
        for device in self.daq_settings:
            self.device_combobox.addItem(device)
        daq_header_label = QtWidgets.QLabel('DAQ:', self)
        self.layout().addWidget(daq_header_label, 2, 0, 1, 1)
        self.daq_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.daq_combobox, 2, 1, 1, 1)
        for channel in sorted([int(x) for x in self.daq_settings[device]]):
            self.daq_combobox.addItem(str(channel))
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int Time (ms): ')
        self.int_time_lineedit.setText('500')
        self.layout().addWidget(self.int_time_lineedit, 3, 0, 1, 1)
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz): ')
        self.sample_rate_lineedit.setText('5000')
        self.layout().addWidget(self.sample_rate_lineedit, 3, 1, 1, 1)
        # Stepper Motor Selection
        self.stepper_motor_label = self.gb_make_labeled_label(label_text = 'Stepper Motor:')
        self.stepper_motor_label = QtWidgets.QLabel(self.csm_widget.com_port, self)
        self.layout().addWidget(self.stepper_motor_label, 4, 0, 1, 1)
        self.stepper_settings_label = self.gb_make_labeled_label(label_text = 'Stepper Settings:')
        self.layout().addWidget(self.stepper_settings_label, 5, 0, 1, 1)
        ######
        # Scan Params
        ######
        #Pause Time 
        self.pause_time_lineedit = self.gb_make_labeled_lineedit(label_text='Pause Time (ms):')
        self.pause_time_lineedit.setText('700')
        self.pause_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.pause_time_lineedit))
        self.layout().addWidget(self.pause_time_lineedit, 6, 0, 1, 1)
        #Start Scan
        self.start_position_lineedit = self.gb_make_labeled_lineedit(label_text='Start Position:')
        self.start_position_lineedit.setText('-300000')
        self.start_position_lineedit.setValidator(QtGui.QIntValidator(-600000, 0, self.start_position_lineedit))
        self.start_position_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.layout().addWidget(self.start_position_lineedit, 7, 0, 1, 1)
        #End Scan
        self.end_position_lineedit = self.gb_make_labeled_lineedit(label_text='End Position:')
        self.end_position_lineedit.setValidator(QtGui.QIntValidator(0, 300000, self.end_position_lineedit))
        self.end_position_lineedit.setText('300000')
        self.end_position_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.layout().addWidget(self.end_position_lineedit, 8, 0, 1, 1)
        #Mirror Interval 
        self.mirror_interval_lineedit = self.gb_make_labeled_lineedit(label_text='Mirror Interval (steps):')
        self.mirror_interval_lineedit.setText('500')
        self.mirror_interval_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.mirror_interval_lineedit.setValidator(QtGui.QIntValidator(1, 200000, self.mirror_interval_lineedit))
        self.layout().addWidget(self.mirror_interval_lineedit, 9, 0, 1, 1)
        #Step size (Fixed for Bill's FTS right now)
        distance_per_step_header_label = QtWidgets.QLabel('Distance Per Step (nm):', self)
        self.layout().addWidget(distance_per_step_header_label, 10, 0, 1, 1)
        self.distance_per_step_combobox = QtWidgets.QComboBox(self)
        for distance_per_step in ['250.39']:
            self.distance_per_step_combobox.addItem(distance_per_step)
        self.distance_per_step_combobox.activated.connect(self.fts_update_scan_params)
        self.layout().addWidget(self.distance_per_step_combobox, 10, 1, 1, 1)
        #Scan Info size
        self.scan_info_label = QtWidgets.QLabel('Scan Info', self)
        self.layout().addWidget(self.scan_info_label, 11, 1, 1, 1)
        self.fts_update_scan_params()
        self.sample_select_combobox = self.gb_make_labeled_combobox(label_text='Sample Select:')
        self.layout().addWidget(self.sample_select_combobox, 12, 0, 1, 1)
        for i in range(6):
            self.sample_select_combobox.addItem(str(i + 1))
        self.sample_select_combobox.activated.connect(self.fts_update_sample_name)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name:')
        self.layout().addWidget(self.sample_name_lineedit, 12, 1, 1, 1)
        # Zero Lockin
        self.zero_lock_in_checkbox = QtWidgets.QCheckBox('Zero Lock in?', self)
        self.layout().addWidget(self.zero_lock_in_checkbox, 13, 0, 1, 1)
        self.zero_lock_in_checkbox.setChecked(True)
        ######
        # Control Buttons 
        ######
        self.start_pushbutton = QtWidgets.QPushButton('Start', self)
        self.layout().addWidget(self.start_pushbutton, 14, 0, 1, 2)
        self.start_pushbutton.clicked.connect(self.fts_start_stop_scan)
        self.save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.layout().addWidget(self.save_pushbutton, 15, 0, 1, 2)
        self.save_pushbutton.clicked.connect(self.fts_save)
        self.load_pushbutton = QtWidgets.QPushButton('Load', self)
        self.load_pushbutton.clicked.connect(self.fts_load)
        self.layout().addWidget(self.load_pushbutton, 16, 0, 1, 2)
        self.replot_pushbutton = QtWidgets.QPushButton('Replot', self)
        self.layout().addWidget(self.replot_pushbutton, 17, 0, 1, 2)
        self.replot_pushbutton.clicked.connect(self.fts_plot)

    def fts_configure_plot_panel(self):
        '''
        '''
        self.int_spec_plot_label = QtWidgets.QLabel('', self)
        self.int_spec_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.layout().addWidget(self.int_spec_plot_label, 0, 4, 7, 2)
        # Time stream 
        self.time_stream_plot_label = QtWidgets.QLabel('', self)
        self.time_stream_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.layout().addWidget(self.time_stream_plot_label, 7, 4, 5, 2)
        # Mean 
        self.data_mean_label = QtWidgets.QLabel('Data Mean (V):', self)
        self.layout().addWidget(self.data_mean_label, 12, 4, 1, 1)
        # STD
        self.data_std_label = QtWidgets.QLabel('Data STD (V):', self)
        self.layout().addWidget(self.data_std_label, 12, 5, 1, 1)
        self.optical_elements_combobox = self.gb_make_labeled_combobox(label_text='Optical Elements')
        for optical_element in self.optical_elements:
            self.optical_elements_combobox.addItem(optical_element)
        self.layout().addWidget(self.optical_elements_combobox, 13, 4, 1, 1)
        self.optical_elements_combobox.activated.connect(self.fts_show_active_optical_elements)
        self.optical_element_active_checkbox = QtWidgets.QCheckBox('Active', self)
        self.optical_element_active_checkbox.clicked.connect(self.fts_update_active_optical_elements)
        self.layout().addWidget(self.optical_element_active_checkbox, 13, 5, 1, 1)
        self.bands_combobox = self.gb_make_labeled_combobox(label_text='Detector Band')
        self.smoothing_factor_lineedit = self.gb_make_labeled_lineedit(label_text='Smoothing Factor:')
        self.smoothing_factor_lineedit.setText('0.01')
        self.smoothing_factor_lineedit.returnPressed.connect(self.fts_plot)
        self.layout().addWidget(self.smoothing_factor_lineedit, 14, 5, 1, 1)
        for band in self.bands:
            self.bands_combobox.addItem(band)
        self.layout().addWidget(self.bands_combobox, 14, 4, 1, 1)
        self.bands_combobox.activated.connect(self.fts_plot)
        self.data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo (GHz):')
        self.data_clip_lo_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.data_clip_lo_lineedit))
        self.data_clip_lo_lineedit.returnPressed.connect(self.fts_plot)
        self.data_clip_lo_lineedit.setText('0.0')
        self.layout().addWidget(self.data_clip_lo_lineedit, 15, 4, 1, 1)
        self.data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi (GHz):')
        self.data_clip_hi_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.data_clip_hi_lineedit))
        self.data_clip_hi_lineedit.returnPressed.connect(self.fts_plot)
        self.data_clip_hi_lineedit.setText('600.0')
        self.layout().addWidget(self.data_clip_hi_lineedit, 15, 5, 1, 1)
        self.voltage_bias_lineedit = self.gb_make_labeled_lineedit(label_text='Bias Voltage (uV):')
        self.voltage_bias_lineedit.setValidator(QtGui.QDoubleValidator(0, 25000, 3, self.voltage_bias_lineedit))
        self.layout().addWidget(self.voltage_bias_lineedit, 16, 4, 1, 1)
        self.heater_voltage_lineedit = self.gb_make_labeled_lineedit(label_text='Heater Voltage (V):')
        self.heater_voltage_lineedit.setValidator(QtGui.QDoubleValidator(0, 150, 2, self.heater_voltage_lineedit))
        self.layout().addWidget(self.heater_voltage_lineedit, 16, 5, 1, 1)

    def fts_show_active_optical_elements(self):
        '''
        '''
        optical_element = self.optical_elements_combobox.currentText()
        active = self.optical_elements[optical_element]['Active']
        self.optical_element_active_checkbox.setChecked(active)
        self.fts_plot()

    def fts_update_active_optical_elements(self):
        '''
        '''
        optical_element = self.optical_elements_combobox.currentText()
        self.optical_elements[optical_element]['Active'] = self.optical_element_active_checkbox.isChecked()
        if self.optical_elements[optical_element]['Active']:
            self.status_bar.showMessage('{0} is Active'.format(optical_element))
        self.fts_plot()

    #################################################
    # Scanning
    #################################################

    def fts_update_scan_params(self):
        '''
        '''
        end = int(self.end_position_lineedit.text())
        start = int(self.start_position_lineedit.text())
        mirror_interval = int(self.mirror_interval_lineedit.text())
        distance_per_step = float(self.distance_per_step_combobox.currentText())
        pause_time = float(self.pause_time_lineedit.text())
        if mirror_interval > 0:
            self.n_data_points = int((end - start) / mirror_interval)
        else:
            self.n_data_points = np.nan
        total_distance = self.n_data_points * distance_per_step * mirror_interval
        min_distance = distance_per_step * mirror_interval
        if min_distance > 0 and total_distance > 0:
            min_distance *= 1e-9 # from nm to m
            total_distance *= 1e-9 # from nm to m
            nyquist_distance = 4 * min_distance
            max_frequency = ((2.99792458 * 10 ** 8) / nyquist_distance) / (10 ** 9) # GHz
            resolution = ((2.99792458 * 10 ** 8) / total_distance) / (10 ** 9) # GHz
            resolution = '{0:.2f} GHz'.format(resolution)
            max_frequency = '{0:.2f} GHz'.format(max_frequency)
            info_string = 'N Data Points: {0} ::: '.format(self.n_data_points)
            info_string += 'Resolution: {0} ::: Max Frequency (GHz): {1}'.format(resolution, max_frequency)
        else:
            info_string = ''
        self.scan_settings_dict = {
             'end': end,
             'start': start,
             'mirror_interval': mirror_interval,
             'distance_per_step': distance_per_step,
             'pause_time': pause_time,
             'n_data_points': self.n_data_points
            }
        self.scan_info_label.setText(info_string)
        device = self.device_combobox.currentText()
        daq = self.daq_combobox.currentText()
        self.scan_settings_dict.update({'device': device, 'daq': daq})
        daq_settings = str(self.daq_settings[device][daq])
        daq_settings_str = ''
        self.scan_settings_dict.update(self.daq_settings[device][daq])
        self.fts_setup_stepper()

    def fts_setup_stepper(self):
        '''
        '''
        sm_com_port = self.stepper_motor_label.text()
        self.scan_settings_dict.update({'sm_com_port': sm_com_port})
        self.status_bar.showMessage('Setting up serial connection to stepper motor on {0}'.format(sm_com_port))
        QtWidgets.QApplication.processEvents()
        sm_settings_str = ''
        #self.scan_settings_dict.update(self.csm_widget.stepper_settings_dict)
        for setting, value in self.csm_widget.stepper_settings_dict.items():
            sm_settings_str += ' '.join([x.title() for x in setting.split('_')])
            sm_settings_str += ' {0} ::: '.format(value)
        self.stepper_settings_label.setText(sm_settings_str)

    def fts_start_stop_scan(self):
        '''
        '''
        if self.sender().text() == 'Start':
            self.fts_update_scan_params()
            self.sender().setText('Stop')
            self.started = True
            self.bands_combobox.setDisabled(True)
            self.optical_element_active_checkbox.setDisabled(True)
            self.optical_elements_combobox.setDisabled(True)
            self.fts_scan()
        else:
            self.sender().setText('Start')
            self.bands_combobox.setDisabled(False)
            self.optical_element_active_checkbox.setDisabled(False)
            self.optical_elements_combobox.setDisabled(False)
            self.started = False

    def fts_scan(self):
        '''
        '''
        start = self.scan_settings_dict['start']
        end = self.scan_settings_dict['end']
        mirror_interval = self.scan_settings_dict['mirror_interval']
        pause_time = self.scan_settings_dict['pause_time']
        n_data_points = self.scan_settings_dict['n_data_points']
        device = self.scan_settings_dict['device']
        int_time = float(self.int_time_lineedit.text())
        sample_rate = float(self.sample_rate_lineedit.text())
        signal_channel = self.scan_settings_dict['daq']
        scan_positions = range(start, end + mirror_interval, mirror_interval)
        signal_channels = [signal_channel]
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=int_time,
                      sample_rate=sample_rate,
                      device=device)
        self.status_bar.showMessage('Moving mirror to starting position!...')
        QtWidgets.QApplication.processEvents()
        self.csm_widget.csm_set_position(position=scan_positions[0], verbose=False)
        position = ''
        while len(position) == 0:
            position = self.csm_widget.csm_get_position()
            if '\r' in position:
                position = position.split('\r')[0]
        velocity = self.csm_widget.csm_get_velocity()
        velocity = float(self.csm_widget.stepper_settings_dict['velocity'])
        position_diff = np.abs(int(position) - int(scan_positions[0])) * 1e-5
        wait = position_diff / velocity
        time.sleep(wait)
        self.status_bar.showMessage('Mirror is in position! Starting Scan...')
        QtWidgets.QApplication.processEvents()
        while self.started:
            t_start = datetime.now()
            self.x_data, self.x_stds = [], []
            self.y_data, self.y_stds = [], []
            for i, scan_position in enumerate(scan_positions):
                self.csm_widget.csm_set_position(position=scan_position, verbose=False)
                if i == 0:
                    self.csm_widget.csm_get_position()
                    time.sleep(self.start_pause) # wait for motor to reach starting point
                time.sleep(pause_time * 1e-3)
                if self.zero_lock_in_checkbox.isChecked():
                    self.srs_widget.srs_zero_lock_in_phase()
                    time.sleep(0.5)
                # Gather Data and Append to Vector then plot
                self.x_data.append(scan_position)
                self.x_stds.append(1) # guesstimated < 1 step error in position
                data_dict = daq.run()
                out_ts = data_dict[signal_channel]['ts']
                out_mean = data_dict[signal_channel]['mean']
                out_min = data_dict[signal_channel]['min']
                out_max = data_dict[signal_channel]['max']
                out_std = data_dict[signal_channel]['std']
                self.y_data.append(out_mean)
                self.y_stds.append(out_std)
                self.fts_plot()
                self.fts_plot_time_stream(out_ts, out_min, out_max)
                self.data_mean_label.setText('Data Mean (V): {0:.6f}'.format(out_mean))
                self.data_std_label.setText('Data STD (V): {0:.6f}'.format(out_std))
                # Compute and report time diagnostics
                t_now = datetime.now()
                t_elapsed = t_now - t_start
                t_elapsed = t_elapsed.seconds + t_elapsed.microseconds * 1e-6
                t_average = t_elapsed / float(i + 1)
                steps_remain = n_data_points - i
                t_remain = t_average * steps_remain / 60.0
                status_message = 'Elapsed Time(s): {0:.1f} Remaining Time (m): {1:.1f} Avg Time / point (s) {2:.2f}'.format(t_elapsed, t_remain, t_average)
                status_message += ':::Scan Postion {0} (Step {1} of {2})'.format(scan_position, i, n_data_points)
                self.status_bar.showMessage(status_message)
                QtWidgets.QApplication.processEvents()
                if not self.started:
                    break
                elif i + 1 == self.n_data_points:
                    self.started = False
                    self.start_pushbutton.setText('Start')
        self.bands_combobox.setDisabled(False)
        self.optical_element_active_checkbox.setDisabled(False)
        self.optical_elements_combobox.setDisabled(False)
        self.fts_save()
        self.csm_widget.csm_set_position(position=start, verbose=False)

    #################################################
    # File handling and plotting
    #################################################

    def fts_index_file_name(self, suffix='if'):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}.{2}'.format(self.sample_name_lineedit.text(), str(i).zfill(3), suffix)
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def fts_save(self):
        '''
        '''
        if_save_path = self.fts_index_file_name()
        if_save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', if_save_path)[0]
        fft_save_path = if_save_path.replace('if', 'fft')
        ss_save_path = if_save_path.replace('.if', '_meta.png')
        screen = QtWidgets.QApplication.primaryScreen()
        screenshot = screen.grabWindow(self.winId())
        screenshot.save(ss_save_path, 'png')
        if len(if_save_path) > 0:
            mirror_interval = self.scan_settings_dict['mirror_interval']
            with open(if_save_path, 'w') as if_save_handle:
                for i, x_data in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_data[i], self.x_stds[i], self.y_data[i], self.y_stds[i])
                    if_save_handle.write(line)
            fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector = self.ftsy_convert_IF_to_FFT_data(self.x_data, self.y_data, mirror_interval, data_selector='All')
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real)
            with open(fft_save_path, 'w') as fft_save_handle:
                for i, fft_freq in enumerate(fft_freq_vector):
                    if fft_freq >= 0:
                        line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(fft_freq_vector[i], normalized_phase_corrected_fft_vector[i], fft_vector[i], phase_corrected_fft_vector[i])
                        fft_save_handle.write(line)
            self.fts_plot()
            self.fts_plot_int()
            self.fts_plot_spectra()
            shutil.copy(os.path.join('temp_files', 'temp_int.png'), fft_save_path.replace('.fft', '_int.png'))
            shutil.copy(os.path.join('temp_files', 'temp_spectra.png'), fft_save_path.replace('.fft', '_spectra.png'))
            shutil.copy(os.path.join('temp_files', 'temp_combo.png'), fft_save_path.replace('.fft', '_combo.png'))
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')

    def fts_load(self):
        '''
        '''
        if_save_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select IF data', '.if')[0]
        self.x_data, self.x_stds, self.y_data, self.y_stds = [], [], [], []
        with open(if_save_path, 'r') as fh:
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
        self.fts_plot()

    def fts_plot_time_stream(self, ts, min_, max_):
        '''
        '''
        fig, ax = self.fts_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.2, top=0.9, bottom=0.23, n_axes=1, left=0.15)
        ax.plot(ts)
        ax.set_xlabel('Samples', fontsize=12)
        ax.set_ylabel('($V$)', fontsize=12)
        fig.savefig('temp_files/temp_ts.png', transparent=True)
        image = QtGui.QPixmap('temp_files/temp_ts.png')
        self.time_stream_plot_label.setPixmap(image)
        pl.close('all')

    def fts_plot(self):
        '''
        '''
        pl.close('all')
        data_clip_lo = float(self.data_clip_lo_lineedit.text()) * 1e9
        data_clip_hi = float(self.data_clip_hi_lineedit.text()) * 1e9
        smoothing_factor = float(self.smoothing_factor_lineedit.text())
        band = self.bands_combobox.currentText()
        if len(band) > 0:
            fft_frequency_vector_simulated, fft_vector_simulated = self.ftsy_load_simulated_band(data_clip_lo, data_clip_hi, band)
        mirror_interval = self.scan_settings_dict['mirror_interval']
        fig, ax1, ax2 = self.fts_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.4, hspace=0.35, bottom=0.18, left=0.15)
        ax1.set_xlabel('Mirror Position (Steps)', fontsize=12)
        ax1.set_ylabel('Response (V)', fontsize=12)
        ax2.set_xlabel('Frequency (GHz)', fontsize=12)
        ax2.set_ylabel('Norm Spectral Amp', fontsize=12)
        title = 'Inteferogram and Spectra'
        if len(self.sample_name_lineedit.text()) > 0:
            title += ': {0}'.format(self.sample_name_lineedit.text())
        ax1.set_title(title, fontsize=12)
        if len(self.x_data) > 10:
            fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector = self.ftsy_convert_IF_to_FFT_data(self.x_data, self.y_data, mirror_interval, data_selector='All')
            ax1.errorbar(self.x_data, self.y_data, yerr=self.y_stds, marker='.', linestyle='-')
            selector = np.logical_and(0 < fft_freq_vector, fft_freq_vector < data_clip_hi)
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real)
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real / np.max(phase_corrected_fft_vector.real))
            normalized_phase_corrected_fft_vector = self.ftsy_running_mean(normalized_phase_corrected_fft_vector, smoothing_factor=smoothing_factor)
            if len(band) > 0:
                selector = fft_frequency_vector_simulated < data_clip_hi * 1e-9
                integrated_bandwidth = np.trapz(fft_vector_simulated[selector], fft_vector_simulated[selector] * 1e9)
                label = 'HFSS BW {0:.2f} GHz '.format(integrated_bandwidth)
                ax2.plot(fft_frequency_vector_simulated, fft_vector_simulated, label=label)
            ax2, fft_freq_vector, normalized_phase_corrected_fft_vector = self.fts_plot_optical_elements(ax2, fft_freq_vector, normalized_phase_corrected_fft_vector)
            selector = np.logical_and(0 < fft_freq_vector, fft_freq_vector < data_clip_hi)
            ax2.errorbar(fft_freq_vector[selector] * 1e-9, normalized_phase_corrected_fft_vector[selector], marker='.', linestyle='-', label='FFT')
            max_idx = np.argmax(normalized_phase_corrected_fft_vector[selector]) + 1
            max_freq = fft_freq_vector[max_idx]
            integrated_bandwidth = np.trapz(normalized_phase_corrected_fft_vector[selector], fft_freq_vector[selector])
            label = 'Peak/BW {0:.2f}/{1:.2f} GHz'.format(max_freq * 1e-9, integrated_bandwidth * 1e-9)

            ax2.errorbar(max_freq * 1e-9, normalized_phase_corrected_fft_vector[max_idx], marker='*', markersize=3, label=label)
        ax1.errorbar(self.x_data, self.y_data, yerr=self.y_stds, marker='.', linestyle='-')
        pl.legend()
        temp_png_path = os.path.join('temp_files', 'temp_combo.png')
        fig.savefig(temp_png_path, transparent=True)
        image_to_display = QtGui.QPixmap(temp_png_path)
        self.int_spec_plot_label.setPixmap(image_to_display)

    def fts_plot_optical_elements(self, ax, frequency_vector, normalized_transmission_vector):
        '''
        '''
        data_clip_lo = float(self.data_clip_lo_lineedit.text()) * 1e9
        data_clip_hi = float(self.data_clip_hi_lineedit.text()) * 1e9
        for optical_element in self.optical_elements:
            active = self.optical_elements[optical_element]['Active']
            path = self.optical_elements[optical_element]['Path']
            if active and not self.started:
                element_frequency_vector, element_transmission_vector = self.ftsy_load_optical_element_response(path)
                frequency_vector, normalized_transmission_vector = self.ftsy_divide_out_optical_element_response(frequency_vector, normalized_transmission_vector, optical_element, path)
                selector = np.logical_and(data_clip_lo < np.asarray(element_frequency_vector), np.asarray(element_frequency_vector) < data_clip_hi)
                ax.plot(np.asarray(element_frequency_vector)[selector] * 1e-9, np.asarray(element_transmission_vector)[selector], label=optical_element)
        return ax, frequency_vector, normalized_transmission_vector

    def fts_plot_spectra(self):
        '''
        '''
        pl.close('all')
        mirror_interval = self.scan_settings_dict['mirror_interval']
        data_clip_lo = float(self.data_clip_lo_lineedit.text()) * 1e9
        data_clip_hi = float(self.data_clip_hi_lineedit.text()) * 1e9
        band = self.bands_combobox.currentText()
        fig, ax = self.fts_create_blank_fig(n_axes=1)
        ax.set_xlabel('Frequency (GHz)', fontsize=14)
        ax.set_ylabel('Bolometer Response (Au)', fontsize=14)
        title = 'Spectra for {0}'.format(self.sample_name_lineedit.text())
        ax.set_title(title, fontsize=14)
        data_selector = 'All'
        if len(self.x_data) > 10:
            fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector = self.ftsy_convert_IF_to_FFT_data(self.x_data, self.y_data, mirror_interval, data_selector=data_selector)
            selector = np.logical_and(0 < fft_freq_vector, fft_freq_vector < data_clip_hi)
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real)
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real / np.max(phase_corrected_fft_vector.real))
            ax.errorbar(fft_freq_vector[selector] * 1e-9, normalized_phase_corrected_fft_vector[selector], marker='.', linestyle='-')
        if len(band) > 0:
            fft_frequency_vector_simulated, fft_vector_simulated = self.ftsy_load_simulated_band(data_clip_lo, data_clip_hi, band)
            ax.plot(fft_frequency_vector_simulated, fft_vector_simulated, label='HFSS')
        fig.savefig(os.path.join('temp_files', 'temp_spectra.png'))

    def fts_plot_int(self):
        '''
        '''
        pl.close('all')
        fig, ax = self.fts_create_blank_fig(n_axes=1)
        ax.set_xlabel('Mirror Position (steps)', fontsize=14)
        ax.set_ylabel('Bolometer Response (V)', fontsize=14)
        title = 'Interferogram for {0}'.format(self.sample_name_lineedit.text())
        ax.set_title(title, fontsize=14)
        ax.errorbar(self.x_data, self.y_data, self.y_stds, marker='.', linestyle='-')
        fig.savefig(os.path.join('temp_files', 'temp_int.png'))

    def fts_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.8,
                             left=0.08, right=0.98, top=0.95, bottom=0.08,
                             hspace=0.1, wspace=0.02, n_axes=2, aspect=None):
        if frac_screen_width is None and frac_screen_height is None:
            fig = pl.figure()
        else:
            width = (frac_screen_width * self.screen_resolution.width()) / self.monitor_dpi
            height = (frac_screen_height * self.screen_resolution.height()) / self.monitor_dpi
            fig = pl.figure(figsize=(width, height))
        fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom, hspace=hspace, wspace=wspace)
        if n_axes == 2:
            ax1 = fig.add_subplot(211, label='int')
            ax2 = fig.add_subplot(212, label='spec')
            return fig, ax1, ax2
        else:
            ax = fig.add_subplot(111)
            return fig, ax
