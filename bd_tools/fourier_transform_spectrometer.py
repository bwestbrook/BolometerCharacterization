import time
import os
import pylab as pl
import numpy as np
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.fourier import Fourier
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass
from bd_tools.configure_stepper_motor import ConfigureStepperMotor

class FourierTransformSpectrometer(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, csm_widget, srs_widget):
        '''
        '''
        super(FourierTransformSpectrometer, self).__init__()
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
        self.fts_plot_panel = QtWidgets.QWidget(self)
        self.layout().addWidget(self.fts_plot_panel, 0, 2, 20, 1)
        self.fts_plot_panel.setLayout(grid_2)
        self.fts_plot_panel.setFixedWidth(0.6 * screen_resolution.width())
        self.fts_configure_input_panel()
        self.fts_configure_plot_panel()
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = os.path.join('Data', '{0}'.format(self.today_str))
        self.fourier = Fourier()
        self.start_pause = 5.0
        self.status_bar.showMessage('Ready')
        self.x_data = []
        self.x_stds = []
        self.y_data = []
        self.y_stds = []
        self.fts_plot(running=True)
        self.fts_plot_time_stream([0], -1.0, 1.0)

    #################################################
    # Gui Config
    #################################################

    def fts_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.fts_update_scan_params()


    def fts_configure_input_panel(self):
        '''
        '''
        welcome_header_label = QtWidgets.QLabel('Welcome to FTS', self)
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
        self.daq_settings_label = QtWidgets.QLabel('DAQ Settings', self)
        self.layout().addWidget(self.daq_settings_label, 3, 1, 1, 1)
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
        self.pause_time_lineedit = QtWidgets.QLineEdit('100', self)
        self.pause_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.pause_time_lineedit))
        self.layout().addWidget(self.pause_time_lineedit, 6, 1, 1, 1)
        #Start Scan
        start_position_header_label = QtWidgets.QLabel('Start Position:', self)
        self.layout().addWidget(start_position_header_label, 7, 0, 1, 1)
        self.start_position_lineedit = QtWidgets.QLineEdit('-30000', self)
        self.start_position_lineedit.setValidator(QtGui.QIntValidator(-500000, 0, self.start_position_lineedit))
        self.start_position_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.layout().addWidget(self.start_position_lineedit, 7, 1, 1, 1)
        #End Scan
        end_position_header_label = QtWidgets.QLabel('End Position:', self)
        self.layout().addWidget(end_position_header_label, 8, 0, 1, 1)
        self.end_position_lineedit = QtWidgets.QLineEdit('30000', self)
        self.end_position_lineedit.setValidator(QtGui.QIntValidator(0, 300000, self.end_position_lineedit))
        self.end_position_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.layout().addWidget(self.end_position_lineedit, 8, 1, 1, 1)
        #Mirror Interval 
        mirror_interval_header_label = QtWidgets.QLabel('Mirror Interval (steps):', self)
        self.layout().addWidget(mirror_interval_header_label, 9, 0, 1, 1)
        self.mirror_interval_lineedit = QtWidgets.QLineEdit('3000', self)
        self.mirror_interval_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.mirror_interval_lineedit.setValidator(QtGui.QIntValidator(1, 200000, self.mirror_interval_lineedit))
        self.layout().addWidget(self.mirror_interval_lineedit, 9, 1, 1, 1)
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
        sample_name_header_label = QtWidgets.QLabel('Sample Name:', self)
        self.layout().addWidget(sample_name_header_label, 12, 0, 1, 1)
        self.sample_name_lineedit = QtWidgets.QLineEdit('', self)
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
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.layout().addWidget(save_pushbutton, 15, 0, 1, 2)
        save_pushbutton.clicked.connect(self.fts_save)
        spacer_label = QtWidgets.QLabel(' ', self)
        self.layout().addWidget(spacer_label, 16, 0, 8, 2)

    def fts_configure_plot_panel(self):
        '''
        '''
        self.int_spec_plot_label = QtWidgets.QLabel('', self.fts_plot_panel)
        self.int_spec_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.fts_plot_panel.layout().addWidget(self.int_spec_plot_label, 0, 0, 1, 4)
        # Time stream 
        self.time_stream_plot_label = QtWidgets.QLabel('', self.fts_plot_panel)
        self.time_stream_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.fts_plot_panel.layout().addWidget(self.time_stream_plot_label, 1, 0, 1, 4)
        # Mean 
        data_mean_header_label = QtWidgets.QLabel('Data Mean (V):', self.fts_plot_panel)
        data_mean_header_label.setAlignment(QtCore.Qt.AlignRight)
        self.fts_plot_panel.layout().addWidget(data_mean_header_label, 2, 0, 1, 1)
        self.data_mean_label = QtWidgets.QLabel('', self.fts_plot_panel)
        self.fts_plot_panel.layout().addWidget(self.data_mean_label, 2, 1, 1, 1)
        # STD
        data_std_header_label = QtWidgets.QLabel('Data STD (V):', self.fts_plot_panel)
        data_std_header_label.setAlignment(QtCore.Qt.AlignRight)
        self.fts_plot_panel.layout().addWidget(data_std_header_label, 2, 2, 1, 1)
        self.data_std_label = QtWidgets.QLabel('', self.fts_plot_panel)
        self.fts_plot_panel.layout().addWidget(self.data_std_label, 2, 3, 1, 1)

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
        self.scan_settings_dict = {
             'end': end,
             'start': start,
             'mirror_interval': mirror_interval,
             'distance_per_step': distance_per_step,
             'pause_time': pause_time,
             'n_data_points': self.n_data_points
            }
        info_string = 'N Data Points: {0} ::: '.format(self.n_data_points)
        info_string += 'Resolution: {0} ::: Max Frequency (GHz): {1}'.format(resolution, max_frequency)
        self.scan_info_label.setText(info_string)
        device = self.device_combobox.currentText()
        daq = self.daq_combobox.currentText()
        self.scan_settings_dict.update({'device': device, 'daq': daq})
        daq_settings = str(self.daq_settings[device][daq])
        daq_settings_str = ''
        self.scan_settings_dict.update(self.daq_settings[device][daq])
        for setting, value in self.daq_settings[device][daq].items():
            daq_settings_str += ' '.join([x.title() for x in setting.split('_')])
            if setting == 'int_time':
                daq_settings_str += ' (ms): '
            if setting == 'sample_rate':
                daq_settings_str += ' (Hz): '
            daq_settings_str += '{0} ::: '.format(value)
        self.daq_settings_label.setText(daq_settings_str)
        self.fts_setup_stepper()

    def fts_setup_stepper(self):
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

    def fts_start_stop_scan(self):
        '''
        '''
        if self.sender().text() == 'Start':
            self.fts_update_scan_params()
            self.sender().setText('Stop')
            self.started = True
            self.fts_scan()
        else:
            self.sender().setText('Start')
            self.started = False

    def fts_scan(self):
        '''
        '''
        pprint(self.scan_settings_dict)
        start = self.scan_settings_dict['start']
        end = self.scan_settings_dict['end']
        mirror_interval = self.scan_settings_dict['mirror_interval']
        pause_time = self.scan_settings_dict['pause_time']
        n_data_points = self.scan_settings_dict['n_data_points']
        device = self.scan_settings_dict['device']
        int_time = self.scan_settings_dict['int_time']
        sample_rate = self.scan_settings_dict['sample_rate']
        signal_channel = self.scan_settings_dict['daq']
        scan_positions = range(start, end + mirror_interval, mirror_interval)
        while self.started:
            t_start = datetime.now()
            self.x_data, self.x_stds = [], []
            self.y_data, self.y_stds = [], []
            for i, scan_position in enumerate(scan_positions):
                self.csm_widget.csm_set_position(position=scan_position, verbose=False)
                if i == 0:
                    self.status_bar.showMessage('Waiting {0}s for mirror to move to start position'.format(self.start_pause))
                    QtWidgets.QApplication.processEvents()
                    time.sleep(self.start_pause) # wait for motor to reach starting point
                if self.zero_lock_in_checkbox.isChecked():
                    self.srs_widget.srs_zero_lock_in_phase()
                time.sleep(pause_time * 1e-3)
                # Gather Data and Append to Vector then plot
                self.x_data.append(scan_position)
                self.x_stds.append(3) # guesstimated < 3 step error in position
                out_ts, out_mean, out_min, out_max, out_std = self.daq.get_data(signal_channel=signal_channel,
                                                                                int_time=int_time,
                                                                                sample_rate=sample_rate,
                                                                                device=device)
                self.y_data.append(out_mean)
                self.y_stds.append(out_std)
                self.fts_plot(running=True)
                self.fts_plot_time_stream(out_ts, out_min, out_max)
                self.data_mean_label.setText('{0:.6f}'.format(out_mean))
                self.data_std_label.setText('{0:.6f}'.format(out_std))
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
                    self.start_pushbutton.setText('Start')

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
        if_save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', if_save_path, filter=',*.txt,*.dat')[0]
        fft_save_path = if_save_path.replace('if', 'fft')
        if len(if_save_path) > 0:
            mirror_interval = self.scan_settings_dict['mirror_interval']
            with open(if_save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_data[i], self.x_stds[i], self.y_data[i], self.y_stds[i])
                    save_handle.write(line)
            fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector = self.fourier.convert_IF_to_FFT_data(self.x_data, self.y_data, mirror_interval, data_selector='All')
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real)
            #normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real / np.max(phase_corrected_fft_vector.real))
            with open(fft_save_path, 'w') as save_handle:
                for i, fft_freq in enumerate(fft_freq_vector):
                    if fft_freq >= 0:
                        line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(fft_freq_vector[i], normalized_phase_corrected_fft_vector[i], fft_vector[i], phase_corrected_fft_vector[i])
                        save_handle.write(line)
        else:
            self.gb_quick_message('Warning {0} Data Not Written to File!'.format(suffix), msg_type='Warning')
        self.fts_plot()
        self.fts_plot_int()
        self.fts_plot_spectra()

    def fts_plot_time_stream(self, ts, min_, max_):
        '''
        '''
        fig, ax = self.fts_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.25, top=0.9, bottom=0.23, n_axes=1, left=0.15)
        ax.plot(ts)
        ax.set_xlabel('Samples', fontsize=14)
        ax.set_ylabel('($V$)', fontsize=14)
        fig.savefig('temp_files/temp_ts.png', transparent=True)
        image = QtGui.QPixmap('temp_files/temp_ts.png')
        self.time_stream_plot_label.setPixmap(image)
        pl.close('all')

    def fts_plot(self, running=False):
        '''
        '''
        pl.close('all')
        mirror_interval = self.scan_settings_dict['mirror_interval']
        fig, ax1, ax2 = self.fts_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.5, hspace=0.35, bottom=0.15, left=0.15)
        ax1.set_xlabel('Mirror Position (Steps)', fontsize=14)
        ax1.set_ylabel('Response (V)', fontsize=14)
        ax2.set_xlabel('Frequency (GHz)', fontsize=14)
        ax2.set_ylabel('Norm Spectral Amp', fontsize=14)
        title = 'Inteferogram and Spectra'
        if len(self.sample_name_lineedit.text()) > 0:
            title += ': {0}'.format(self.sample_name_lineedit.text())
        ax1.set_title(title, fontsize=14)
        if len(self.x_data) > 10:
            fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector = self.fourier.convert_IF_to_FFT_data(self.x_data, self.y_data, mirror_interval, data_selector='All')
            ax1.errorbar(self.x_data, self.y_data, yerr=self.y_stds, marker='.', linestyle='-')
            selector = np.where(fft_freq_vector > 0)
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real)
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real / np.max(phase_corrected_fft_vector.real))
            ax2.errorbar(fft_freq_vector[selector] * 1e-9, normalized_phase_corrected_fft_vector[selector], marker='.', linestyle='-')
        else:
            ax1.errorbar(self.x_data, self.y_data, yerr=self.y_stds, marker='.', linestyle='-')
        if running:
            temp_png_path = os.path.join('temp_files', 'temp_int.png')
            fig.savefig(temp_png_path, transparent=True)
            image_to_display = QtGui.QPixmap(temp_png_path)
            self.int_spec_plot_label.setPixmap(image_to_display)
            os.remove(temp_png_path)
        else:
            pl.show()

    def fts_plot_spectra(self):
        '''
        '''
        pl.close('all')
        mirror_interval = self.scan_settings_dict['mirror_interval']
        fig, ax = self.fts_create_blank_fig(n_axes=1)
        ax.set_xlabel('Frequency (GHz)', fontsize=14)
        ax.set_ylabel('Bolometer Response (Au)', fontsize=14)
        title = 'Spectra for {0}'.format(self.sample_name_lineedit.text())
        ax.set_title(title, fontsize=14)
        fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector = self.fourier.convert_IF_to_FFT_data(self.x_data, self.y_data, mirror_interval)
        selector = np.where(fft_freq_vector > 0)
        normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real)
        normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real / np.max(phase_corrected_fft_vector.real))
        ax.errorbar(fft_freq_vector[selector] * 1e-9, normalized_phase_corrected_fft_vector[selector], marker='.', linestyle='-')
        pl.show()

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
        pl.show()

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
