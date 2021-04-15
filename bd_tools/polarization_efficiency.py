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

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, csm_widget, srs_widget, data_folder):
        '''
        '''
        super(PolarizationEfficiency, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.srs_widget = srs_widget
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.csm_widget = csm_widget
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

    def pe_update_sample_name(self):
        '''
        '''
        sample_key = self.sample_name_combobox.currentText()
        sample_name = self.samples_settings[sample_key]
        self.sample_name_lineedit.setText(sample_name)

    def pe_configure_input_panel(self):
        '''
        '''
        welcome_header_label = QtWidgets.QLabel('Welcome to Polarization Efficiency', self)
        welcome_header_label.setFixedWidth(0.3 * self.screen_resolution.width())
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
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int Time (ms):')
        self.layout().addWidget(self.int_time_lineedit, 3, 0, 1, 1)
        self.int_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.int_time_lineedit))
        self.int_time_lineedit.setText('500')
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz):')
        self.layout().addWidget(self.sample_rate_lineedit, 3, 1, 1, 1)
        self.sample_rate_lineedit.setText('5000')
        self.sample_rate_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.sample_rate_lineedit))
        # Stepper Motor Selection
        stepper_motor_header_label = QtWidgets.QLabel('Stepper Motor:', self)
        self.layout().addWidget(stepper_motor_header_label, 4, 0, 1, 1)
        self.stepper_motor_label = QtWidgets.QLabel(self.csm_widget.com_port, self)
        self.layout().addWidget(self.stepper_motor_label, 4, 1, 1, 1)
        self.stepper_settings_label = QtWidgets.QLabel('Stepper Settings', self)
        self.layout().addWidget(self.stepper_settings_label, 5, 1, 1, 1)
        ######
        # Scan Params
        ######
        #Pause Time 
        pause_time_header_label = QtWidgets.QLabel('Pause Time (ms):', self)
        self.layout().addWidget(pause_time_header_label, 6, 0, 1, 1)
        self.pause_time_lineedit = QtWidgets.QLineEdit('1000', self)
        self.pause_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.pause_time_lineedit))
        self.layout().addWidget(self.pause_time_lineedit, 6, 1, 1, 1)
        #Start Scan
        start_position_header_label = QtWidgets.QLabel('Start Position:', self)
        self.layout().addWidget(start_position_header_label, 7, 0, 1, 1)
        self.start_position_lineedit = QtWidgets.QLineEdit('-45000', self)
        self.start_position_lineedit.setValidator(QtGui.QIntValidator(-500000, 0, self.start_position_lineedit))
        self.start_position_lineedit.textChanged.connect(self.pe_update_scan_params)
        self.layout().addWidget(self.start_position_lineedit, 7, 1, 1, 1)
        #End Scan
        end_position_header_label = QtWidgets.QLabel('End Position:', self)
        self.layout().addWidget(end_position_header_label, 8, 0, 1, 1)
        self.end_position_lineedit = QtWidgets.QLineEdit('45000', self)
        self.end_position_lineedit.setValidator(QtGui.QIntValidator(0, 300000, self.end_position_lineedit))
        self.end_position_lineedit.textChanged.connect(self.pe_update_scan_params)
        self.layout().addWidget(self.end_position_lineedit, 8, 1, 1, 1)
        #Grid Angle Interval
        grid_angle_interval_header_label = QtWidgets.QLabel('Grid Angle Interval (steps):', self)
        self.layout().addWidget(grid_angle_interval_header_label, 9, 0, 1, 1)
        self.grid_angle_interval_lineedit = QtWidgets.QLineEdit('1000', self)
        self.grid_angle_interval_lineedit.textChanged.connect(self.pe_update_scan_params)
        self.grid_angle_interval_lineedit.setValidator(QtGui.QIntValidator(1, 200000, self.grid_angle_interval_lineedit))
        self.layout().addWidget(self.grid_angle_interval_lineedit, 9, 1, 1, 1)
        #Angle Step size (Fixed for Bill's pe right now)
        angle_per_step_header_label = QtWidgets.QLabel('Angle Per Step (mDeg):', self)
        self.layout().addWidget(angle_per_step_header_label, 10, 0, 1, 1)
        self.angle_per_step_combobox = QtWidgets.QComboBox(self)
        for angle_per_step in ['72']:
            self.angle_per_step_combobox.addItem(angle_per_step)
        self.angle_per_step_combobox.activated.connect(self.pe_update_scan_params)
        self.layout().addWidget(self.angle_per_step_combobox, 10, 1, 1, 1)
        #Scan Info size
        self.scan_info_label = QtWidgets.QLabel('Scan Info', self)
        self.layout().addWidget(self.scan_info_label, 11, 1, 1, 1)
        self.pe_update_scan_params()
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name:')
        self.layout().addWidget(self.sample_name_lineedit, 12, 1, 1, 1)
        self.sample_name_combobox = self.gb_make_labeled_combobox(label_text='Sample Name:')
        for i in range(6):
            self.sample_name_combobox.addItem(str(i + 1))
        self.sample_name_combobox.activated.connect(self.pe_update_sample_name)
        self.sample_name_combobox.currentIndexChanged.connect(self.pe_update_sample_name)
        self.sample_name_combobox.setCurrentIndex(5)
        self.layout().addWidget(self.sample_name_combobox, 12, 0, 1, 1)
        # Zero Lock in
        self.zero_lock_in_checkbox = QtWidgets.QCheckBox('Zero Lock In?', self)
        self.zero_lock_in_checkbox.setChecked(True)
        self.layout().addWidget(self.zero_lock_in_checkbox, 13, 0, 1, 1)
        self.reverse_scan_checkbox = QtWidgets.QCheckBox('Reverse Scan?', self)
        self.reverse_scan_checkbox.setChecked(False)
        self.layout().addWidget(self.reverse_scan_checkbox, 13, 1, 1, 1)
        #####
        # Control Buttons 
        ######
        self.start_pushbutton = QtWidgets.QPushButton('Start', self)
        self.layout().addWidget(self.start_pushbutton, 14, 0, 1, 2)
        self.start_pushbutton.clicked.connect(self.pe_start_stop_scan)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.layout().addWidget(save_pushbutton, 15, 0, 1, 2)
        save_pushbutton.clicked.connect(self.pe_save)
        spacer_label = QtWidgets.QLabel(' ', self)
        self.layout().addWidget(spacer_label, 15, 0, 8, 2)

    def pe_configure_plot_panel(self):
        '''
        '''
        self.pe_plot_label = QtWidgets.QLabel('', self.pe_plot_panel)
        self.pe_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.pe_plot_panel.layout().addWidget(self.pe_plot_label, 0, 0, 1, 4)
        self.time_stream_plot_label = QtWidgets.QLabel('', self.pe_plot_panel)
        self.time_stream_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.pe_plot_panel.layout().addWidget(self.time_stream_plot_label, 1, 0, 1, 4)
        data_mean_header_label = QtWidgets.QLabel('Data Mean (V):', self.pe_plot_panel)
        data_mean_header_label.setAlignment(QtCore.Qt.AlignRight)
        self.pe_plot_panel.layout().addWidget(data_mean_header_label, 2, 0, 1, 1)
        self.data_mean_label = QtWidgets.QLabel('', self.pe_plot_panel)
        self.pe_plot_panel.layout().addWidget(self.data_mean_label, 2, 1, 1, 1)
        data_std_header_label = QtWidgets.QLabel('Data STD (V):', self.pe_plot_panel)
        data_std_header_label.setAlignment(QtCore.Qt.AlignRight)
        self.pe_plot_panel.layout().addWidget(data_std_header_label, 2, 2, 1, 1)
        self.data_std_label = QtWidgets.QLabel('', self.pe_plot_panel)
        self.pe_plot_panel.layout().addWidget(self.data_std_label, 2, 3, 1, 1)

    def bd_get_simulated_data(self, datatype, current_position, noise=10):
        '''
        noise is in percent and is of the max-min of data
        '''
        in_degree = current_position*np.pi/180
        dev = (np.random.randn()-0.5)*2/100*noise
        simulated_data = np.sin(in_degree) + dev
        return simulated_data

    #################################################
    # Scanning
    #################################################

    def pe_update_scan_params(self):
        '''
        '''
        end = int(self.end_position_lineedit.text())
        start = int(self.start_position_lineedit.text())
        grid_angle_interval = int(self.grid_angle_interval_lineedit.text())
        angle_per_step = float(self.angle_per_step_combobox.currentText())
        pause_time = float(self.pause_time_lineedit.text())
        if grid_angle_interval > 0:
            self.n_data_points = int((end - start) / grid_angle_interval)
        else:
            self.n_data_points = np.nan
        self.scan_settings_dict = {
             'end': end,
             'start': start,
             'grid_angle_interval': grid_angle_interval,
             'angle_per_step': angle_per_step,
             'pause_time': pause_time,
             'n_data_points': self.n_data_points
            }
        info_string = 'N Data Points: {0} ::: '.format(self.n_data_points)
        self.scan_info_label.setText(info_string)
        device = self.device_combobox.currentText()
        daq = self.daq_combobox.currentText()
        self.scan_settings_dict.update({'device': device, 'daq': daq})
        daq_settings = str(self.daq_settings[device][daq])
        self.scan_settings_dict.update(self.daq_settings[device][daq])
        self.pe_setup_stepper()

    def pe_setup_stepper(self):
        '''
        '''
        sm_com_port = self.stepper_motor_label.text()
        self.scan_settings_dict.update({'sm_com_port': sm_com_port})
        self.status_bar.showMessage('Setting up serial connection to stepper motor on {0}'.format(sm_com_port))
        QtWidgets.QApplication.processEvents()
        sm_settings_str = ''
        self.scan_settings_dict.update(self.csm_widget.stepper_settings_dict)
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

    def pe_scan(self):
        '''
        '''
        pprint(self.scan_settings_dict)
        start = self.scan_settings_dict['start']
        end = self.scan_settings_dict['end']
        grid_angle_interval = self.scan_settings_dict['grid_angle_interval']
        pause_time = self.scan_settings_dict['pause_time']
        n_data_points = self.scan_settings_dict['n_data_points']
        device = self.scan_settings_dict['device']
        int_time = float(self.int_time_lineedit.text())
        sample_rate = float(self.sample_rate_lineedit.text())
        signal_channel = self.scan_settings_dict['daq']
        scan_positions = range(start, end + grid_angle_interval, grid_angle_interval)
        start_position = scan_positions[0]
        signal_channels = [signal_channel]
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=int_time,
                      sample_rate=sample_rate,
                      device=device)
        while self.started:
            t_start = datetime.now()
            self.x_data, self.x_stds = [], []
            self.y_data, self.y_stds = [], []
            if self.reverse_scan_checkbox.isChecked():
                scan_positions = list(reversed(scan_positions))
            for i, scan_position in enumerate(scan_positions):
                self.csm_widget.csm_set_position(position=scan_position, verbose=False)
                if i == 0:
                    self.status_bar.showMessage('Waiting {0}s for grid to move to start position'.format(self.start_pause))
                    QtWidgets.QApplication.processEvents()
                    time.sleep(self.start_pause) # wait for motor to reach starting point
                if self.zero_lock_in_checkbox.isChecked():
                    self.srs_widget.srs_zero_lock_in_phase()
                time.sleep(pause_time * 1e-3)
                # Gather Data and Append to Vector then plot
                self.x_data.append(scan_position)
                self.x_stds.append(2) # guesstimated < 2 step error in position
                data_dict = daq.run()
                data_time_stream = data_dict[signal_channel]['ts']
                mean = data_dict[signal_channel]['mean']
                min_ = data_dict[signal_channel]['min']
                max_ = data_dict[signal_channel]['max']
                std = data_dict[signal_channel]['std']
                self.y_data.append(mean)
                self.y_stds.append(std)
                pol_eff_str = None
                if np.abs(scan_position - start_position) > 30000:
                    normalized_amplitude = self.y_data / np.max(self.y_data)
                    degsperpoint = 5.0
                    initial_fit_params = self.pe_moments(self.x_data, np.asarray(self.y_data), degsperpoint)
                    fit_params = self.pe_fit_sine(self.x_data, np.asarray(self.y_data), initial_fit_params)
                    self.y_fit = []
                    self.x_fit = []
                    for x_val in np.arange(start_position, scan_position, 50):
                        fit_val = self.pe_test_sine(x_val, fit_params[0], fit_params[1], fit_params[2], fit_params[3])
                        angle_ = (x_val /fit_params[1]) * 2 * np.pi
                        self.y_fit.append(fit_val)
                        self.x_fit.append(x_val)
                    pol_eff_fit = np.min(self.y_fit) / np.max(self.y_fit) * 1e2 # is a pct
                    pol_eff_data = np.min(self.y_data) / np.max(self.y_data) * 1e2 # is a pct
                    pol_eff_str = 'Pol Eff: {0:.2f}% (Fit) Pol Eff: {1:.2f}% (Data)'.format(pol_eff_fit, pol_eff_data)
                self.pe_plot_time_stream(data_time_stream, min_, max_)
                self.pe_plot(running=True, pol_eff_str=pol_eff_str)
                self.data_mean_label.setText('{0:.6f}'.format(mean))
                self.data_std_label.setText('{0:.6f}'.format(std))
                # Compute and report time diagnostics
                t_now = datetime.now()
                t_elapsed = t_now - t_start
                t_elapsed = t_elapsed.seconds + t_elapsed.microseconds * 1e-6
                t_average = t_elapsed / float(i + 1)
                steps_remain = n_data_points - i
                t_remain = t_average * steps_remain
                status_message = 'Elapsed Time(s): {0:.1f} Remaining Time (s): {1:.1f} ::: Current Position (step) {2} ::: (Step {3} of {4})'.format(t_elapsed, t_remain, scan_position, i, n_data_points)
                self.status_bar.showMessage(status_message)
                QtWidgets.QApplication.processEvents()
                if not self.started:
                    break
                elif i + 1 == self.n_data_points:
                    self.started = False
        self.pe_save()
        self.sender().setText('Start')
        self.started = False
        self.csm_widget.csm_set_position(position=scan_positions[0], verbose=False)

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

    def pe_save(self):
        '''
        '''
        save_path = self.pe_index_file_name()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter='*.txt,*.dat')[0]
        if len(save_path) > 0:
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
        self.pe_plot()

    def pe_plot_time_stream(self, ts, min_, max_):
        '''
        '''
        fig, ax = self.pe_create_blank_fig(frac_screen_width=0.7, frac_screen_height=0.3, top=0.9, bottom=0.21, n_axes=1)
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
        fig, ax = self.pe_create_blank_fig(frac_screen_width=0.7, frac_screen_height=0.6, n_axes=1)
        ax.set_xlabel('Steps', fontsize=10)
        ax.set_ylabel('Amplitude', fontsize=10)
        title = 'Polarization Efficiency'
        if len(self.sample_name_lineedit.text()) > 0:
            title += ' {0}'.format(self.sample_name_lineedit.text())
        ax.set_title(title, fontsize=14)
        ax.errorbar(self.x_data, self.y_data, yerr=self.y_stds, xerr=self.x_stds, marker='.', linestyle='-', label='data')
        if len(self.y_fit) > 0:
            if pol_eff_str is not None:
                ax.plot(self.x_fit, self.y_fit, color='r', linestyle='-', label=pol_eff_str)
            else:
                ax.plot(self.x_fit, self.y_fit, color='r', linestyle='-', label='fit')
        pl.legend()
        if running:
            fig.savefig(os.path.join('temp_files', 'temp_pol.png'), transparent=True)
            image = QtGui.QPixmap(os.path.join('temp_files', 'temp_pol.png'))
            self.pe_plot_label.setPixmap(image)
        else:
            pl.show()

    def pe_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.8,
                             left=0.08, right=0.98, top=0.95, bottom=0.08, n_axes=2,
                             aspect=None):
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
            return fig, ax

    ##################################################
    ## Fitting Utilities
    ##################################################
    def pe_arbitrary_sine(self, amplitude, period, y_offset):
        def arb_sine(x):
            value = amplitude*np.sin(x * period) ** 2 + y_offset
            return value
        return arb_sine

    def pe_test_sine(self, x_val, amplitude, period, phase, y_offset):
        print(x_val)
        period = float(period)
        y_offset = float(y_offset)
        #value = amplitude * np.sin((2.5 * x_val / period) * 2 * np.pi + phase) + y_offset
        value = amplitude * np.sin((x_val / period) * 2 * np.pi + phase) + y_offset
        return value

    def pe_moments(self, raw_angle, data, degsperstep):
        amplitude = (np.max(data) - np.min(data)) / 2.0
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
