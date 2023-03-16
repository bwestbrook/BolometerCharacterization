import time
import shutil
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

    def __init__(self,
            daq_settings,
            status_bar,
            screen_resolution,
            monitor_dpi,
            csm_mirror_widget,
            csm_input_widget,
            csm_output_widget,
            srs_widget,
            data_folder):
            #csm_input_polarizer_widget,
            #csm_output_polarizer_widget,
        '''
        '''
        super(FourierTransformSpectrometer, self).__init__()
        self.c = 2.99792458 * 10 ** 8 # speed of light in m/s
        self.com_port_dict_path = os.path.join('bd_settings', 'com_settings.json')
        self.fts_load_com_port_settings()
        self.bands = self.ftsy_get_bands()
        self.optical_elements = self.ftsy_get_optical_elements()
        self.fts_update_samples()
        self.status_bar = status_bar
        self.srs_widget = srs_widget
        self.csm_mirror_widget = csm_mirror_widget
        self.csm_input_widget = csm_input_widget
        self.csm_output_widget = csm_output_widget
        #self.csm_input_polarizer_widget = csm_input_polarizer_widget
        #self.csm_output_polarizer_widget = csm_output_polarizer_widget
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid_2 = QtWidgets.QGridLayout()
        self.fts_configure_input_panel()
        self.fts_configure_analysis_panel()
        self.data_folder = data_folder
        self.start_pause = 5.0
        self.status_bar.showMessage('Ready')
        self.x_data = []
        self.x_stds = []
        self.y_data = []
        self.y_stds = []
        self.loaded_data_dict = {}
        self.fts_plot_all()
        self.started = False
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

    def fts_load_com_port_settings(self):
        '''
        '''
        with open(self.com_port_dict_path, 'r') as fh:
            self.com_ports_dict = simplejson.load(fh )

    def fts_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.fts_update_scan_params()

    def fts_update_sample_name(self, index):
        '''
        '''
        self.fts_load_com_port_settings()
        sample_key = self.sample_select_combobox.currentText()
        sample_name = self.samples_settings[sample_key]
        self.sample_name_lineedit.setText(sample_name)

    def fts_configure_input_panel(self):
        '''
        '''
        # Basic stepper control
        col = 0
        for i, comport in enumerate(['COM12', 'COM13', 'COM14']):
            stepper_settings_label = QtWidgets.QLabel('{0} Steppper Settings:'.format(comport))
            self.layout().addWidget(stepper_settings_label, 0, i, 1, 1)
            set_position_lineedit = self.gb_make_labeled_lineedit(label_text='{0} Set to Position'.format(comport))
            set_position_lineedit.setValidator(QtGui.QIntValidator(-600000, 300000, set_position_lineedit))
            self.layout().addWidget(set_position_lineedit, 1, i, 1, 1)
            set_position_pushbutton = QtWidgets.QPushButton('{0} Set Mirror Position'.format(comport))
            self.layout().addWidget(set_position_pushbutton, 2, i, 1, 1)
            reset_zero_pushbutton = QtWidgets.QPushButton('{0} Reset Mirror Zero'.format(comport))
            self.layout().addWidget(reset_zero_pushbutton, 3, i, 1, 1)
            setattr(self, '{0}_stepper_settings_label'.format(comport), stepper_settings_label)
            reset_zero_pushbutton.clicked.connect(self.fts_reset_zero)
            set_position_pushbutton.clicked.connect(self.fts_set_position)
            col += 1
        # Reverse Scan Interval 
        self.reverse_scan_checkbox = QtWidgets.QCheckBox('Reverse Scan', self)
        self.layout().addWidget(self.reverse_scan_checkbox, 4, 0, 1, 1)
        self.reverse_scan_checkbox.setChecked(False)
        # Zero Lockin
        self.zero_lock_in_checkbox = QtWidgets.QCheckBox('Zero Lock-in', self)
        self.layout().addWidget(self.zero_lock_in_checkbox, 4, 1, 1, 1)
        self.zero_lock_in_checkbox.setChecked(True)
        # Start Button
        self.start_pushbutton = QtWidgets.QPushButton('Start', self)
        self.layout().addWidget(self.start_pushbutton, 4, 2, 1, 1)
        self.start_pushbutton.clicked.connect(self.fts_start_stop_scan)

        ######
        # DAQ Params (Device + Channel) Selection
        ######
        self.device_combobox = self.gb_make_labeled_combobox(label_text='Device:')
        self.layout().addWidget(self.device_combobox, 0, 3, 1, 1)
        for device in self.daq_settings:
            self.device_combobox.addItem(device)
        self.daq_combobox = self.gb_make_labeled_combobox(label_text='DAQ:')
        self.layout().addWidget(self.daq_combobox, 1, 3, 1, 1)
        for channel in sorted([int(x) for x in self.daq_settings[device]]):
            self.daq_combobox.addItem(str(channel))
        #Pause Time 
        self.pause_time_lineedit = self.gb_make_labeled_lineedit(label_text='Pause Time (ms):')
        self.pause_time_lineedit.setText('500')
        self.pause_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.pause_time_lineedit))
        self.layout().addWidget(self.pause_time_lineedit, 2, 3, 1, 1)
        #Int Time 
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int Time (ms): ')
        self.int_time_lineedit.setText('250')
        self.int_time_lineedit.setValidator(QtGui.QIntValidator(10, 1000000, self.int_time_lineedit))
        self.layout().addWidget(self.int_time_lineedit, 3, 3, 1, 1)
        #Sample Rate 
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz): ')
        self.sample_rate_lineedit.setText('5000')
        self.sample_rate_lineedit.setValidator(QtGui.QIntValidator(100, 5000, self.sample_rate_lineedit))
        self.layout().addWidget(self.sample_rate_lineedit, 4, 3, 1, 1)
        ######
        # Scan Params
        ######
        # Start Scan
        self.start_position_lineedit = self.gb_make_labeled_lineedit(label_text='Start Position:')
        self.start_position_lineedit.setText('30000')
        self.start_position_lineedit.setValidator(QtGui.QIntValidator(-600000, 300000, self.start_position_lineedit))
        self.start_position_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.layout().addWidget(self.start_position_lineedit, 0, 4, 1, 1)
        # End Scan
        self.end_position_lineedit = self.gb_make_labeled_lineedit(label_text='End Position:')
        self.end_position_lineedit.setValidator(QtGui.QIntValidator(-600000, 300000, self.end_position_lineedit))
        self.end_position_lineedit.setText('-60000')
        self.end_position_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.layout().addWidget(self.end_position_lineedit, 1, 4, 1, 1)
        # Mirror Interval 
        self.mirror_interval_lineedit = self.gb_make_labeled_lineedit(label_text='Mirror Interval (steps):')
        self.mirror_interval_lineedit.setText('2000')
        self.mirror_interval_lineedit.textChanged.connect(self.fts_update_scan_params)
        self.mirror_interval_lineedit.setValidator(QtGui.QIntValidator(1, 200000, self.mirror_interval_lineedit))
        self.layout().addWidget(self.mirror_interval_lineedit, 2, 4, 1, 1)
        # Step size (Fixed for Bill's FTS right now)
        self.distance_per_step_combobox = self.gb_make_labeled_combobox(label_text='Distance Per Step (nm):')
        for distance_per_step in ['250.39']:
            self.distance_per_step_combobox.addItem(distance_per_step)
        self.distance_per_step_combobox.activated.connect(self.fts_update_scan_params)
        self.layout().addWidget(self.distance_per_step_combobox, 3, 4, 1, 1)
        #Scan Info 
        self.scan_info_label = QtWidgets.QLabel('Scan Info', self)
        self.layout().addWidget(self.scan_info_label, 4, 4, 1, 1)
        self.fts_update_scan_params()
        # Source Type
        self.source_type_combobox = self.gb_make_labeled_combobox(label_text='Soure Type')
        for source in ['Network Analyzer', 'Heater']:
            self.source_type_combobox.addItem(source)
        self.layout().addWidget(self.source_type_combobox, 0, 5, 1, 1)
        # Source Power 
        self.source_power_lineedit = self.gb_make_labeled_lineedit(label_text='Source Power (dBm):')
        self.layout().addWidget(self.source_power_lineedit, 1, 5, 1, 1)
        # Source Frequency 
        self.source_frequency_lineedit = self.gb_make_labeled_lineedit(label_text='Source Frequency (GHz):')
        self.layout().addWidget(self.source_frequency_lineedit, 2, 5, 1, 1)
        self.source_type_combobox.setCurrentIndex(-1)
        self.source_type_combobox.currentIndexChanged.connect(self.fts_update_source_power)
        self.source_type_combobox.setCurrentIndex(1)
        # Source Modulation Frequency 
        self.modulation_frequency_lineedit = self.gb_make_labeled_lineedit(label_text='Mod Frequency (Hz):')
        self.modulation_frequency_lineedit.setValidator(QtGui.QDoubleValidator(0, 2e5, 2, self.modulation_frequency_lineedit))
        self.layout().addWidget(self.modulation_frequency_lineedit, 3, 5, 1, 1)
        self.modulation_frequency_lineedit.setText('12')
        # Voltage Bias 
        self.voltage_bias_lineedit = self.gb_make_labeled_lineedit(label_text='TES Bias Voltage (uV):')
        self.voltage_bias_lineedit.setValidator(QtGui.QDoubleValidator(0, 25000, 3, self.voltage_bias_lineedit))
        self.layout().addWidget(self.voltage_bias_lineedit, 4, 5, 1, 1)
        #Sample Name and Info 
        self.sample_select_combobox = self.gb_make_labeled_combobox(label_text='Sample Select:')
        self.layout().addWidget(self.sample_select_combobox, 0, 6, 1, 2)
        for sample in self.samples_settings:
            self.sample_select_combobox.addItem(sample)
        self.sample_select_combobox.activated.connect(self.fts_update_sample_name)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name:')
        self.layout().addWidget(self.sample_name_lineedit, 1, 6, 1, 2)
        # Transmission Sample
        self.transmission_sample_lineedit = self.gb_make_labeled_lineedit(label_text='Transmission Sample:', lineedit_text='None')
        self.layout().addWidget(self.transmission_sample_lineedit, 2, 6, 1, 2)
        # Notes
        self.notes_lineedit = self.gb_make_labeled_lineedit(label_text='Notes:')
        self.layout().addWidget(self.notes_lineedit, 3, 6, 2, 2)

    def fts_configure_analysis_panel(self):
        '''
        '''

        # Smoothing Factor
        self.smoothing_factor_lineedit = self.gb_make_labeled_lineedit(label_text='Smoothing Factor:')
        self.smoothing_factor_lineedit.setText('0.002')
        self.smoothing_factor_lineedit.setValidator(QtGui.QDoubleValidator(0, 1, 5, self.smoothing_factor_lineedit))
        self.smoothing_factor_lineedit.returnPressed.connect(self.fts_plot_all)
        self.layout().addWidget(self.smoothing_factor_lineedit, 7, 0, 1, 1)
        # Optical Elements 
        self.optical_elements_combobox = self.gb_make_labeled_combobox(label_text='Optical Elements')
        for optical_element in self.optical_elements:
            self.optical_elements_combobox.addItem(optical_element)
        self.layout().addWidget(self.optical_elements_combobox, 7, 1, 1, 1)
        self.optical_elements_combobox.activated.connect(self.fts_show_active_optical_elements)
        self.optical_element_active_checkbox = QtWidgets.QCheckBox('Active', self)
        self.optical_element_active_checkbox.clicked.connect(self.fts_update_active_optical_elements)
        self.layout().addWidget(self.optical_element_active_checkbox, 7, 2, 1, 1)
        # Co-plot or divide spectra
        self.co_plot_checkbox = QtWidgets.QCheckBox('Co Plot?')
        self.layout().addWidget(self.co_plot_checkbox, 8, 2, 1, 1)
        self.co_plot_checkbox.clicked.connect(self.fts_plot_all)
        self.divide_checkbox = QtWidgets.QCheckBox('Divide Spectra')
        self.layout().addWidget(self.divide_checkbox, 9, 2, 1, 1)
        self.divide_checkbox.clicked.connect(self.fts_plot_all)
        self.symmeterize_data_checkbox = QtWidgets.QCheckBox('Symmeterize IF')
        self.layout().addWidget(self.symmeterize_data_checkbox, 10, 2, 1, 1)
        self.symmeterize_data_checkbox.setChecked(True)
        # Optial Elements
        self.divide_elements_checkbox = QtWidgets.QCheckBox('Divide Optical Elements?')
        self.layout().addWidget(self.divide_elements_checkbox, 8, 1, 1, 1)
        self.divide_elements_checkbox.clicked.connect(self.fts_plot_all)
        # Element Division Threshold 
        self.element_division_threshhold_lineedit = self.gb_make_labeled_lineedit(label_text='Threshhold:')
        self.element_division_threshhold_lineedit.setText('0.1')
        self.element_division_threshhold_lineedit.setValidator(QtGui.QDoubleValidator(0, 1, 3, self.element_division_threshhold_lineedit))
        self.element_division_threshhold_lineedit.returnPressed.connect(self.fts_plot_all)
        self.layout().addWidget(self.element_division_threshhold_lineedit, 8, 0, 1, 1)
        # Bands
        self.bands_combobox = self.gb_make_labeled_combobox(label_text='Detector Band')
        for band in self.bands:
            self.bands_combobox.addItem(band)
        self.layout().addWidget(self.bands_combobox, 9, 0, 1, 1)
        self.bands_combobox.activated.connect(self.fts_show_active_bands)
        self.detector_band_active_checkbox = QtWidgets.QCheckBox('Active', self)
        self.detector_band_active_checkbox.clicked.connect(self.fts_update_active_bands)
        self.layout().addWidget(self.detector_band_active_checkbox, 9, 1, 1, 1)
        # Data Clip
        self.data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo (GHz):')
        self.data_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(0, 25000, 3, self.data_clip_lo_lineedit))
        self.data_clip_lo_lineedit.setText('0.0')
        self.data_clip_lo_lineedit.returnPressed.connect(self.fts_plot_all)
        self.layout().addWidget(self.data_clip_lo_lineedit, 10, 0, 1, 1)
        self.data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi (GHz):')
        self.data_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(0, 25000, 3, self.data_clip_hi_lineedit))
        self.data_clip_hi_lineedit.returnPressed.connect(self.fts_plot_all)
        self.data_clip_hi_lineedit.setText('600.0')
        self.layout().addWidget(self.data_clip_hi_lineedit, 10, 1, 1, 1)

        ######
        # Plotting Buttons 
        ######
        # Interferogram and Spectrum
        self.int_spec_plot_label = QtWidgets.QLabel('', self)
        self.int_spec_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.layout().addWidget(self.int_spec_plot_label, 7, 3, 9, 4)
        # Time stream 
        self.time_stream_plot_label = QtWidgets.QLabel('', self)
        self.time_stream_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.layout().addWidget(self.time_stream_plot_label, 11, 0, 2, 3)
        # Mean 
        self.data_mean_label = self.gb_make_labeled_label(label_text='Data Mean (V):')
        self.layout().addWidget(self.data_mean_label, 13, 0, 1, 1)
        # STD
        self.data_std_label = self.gb_make_labeled_label(label_text='Data STD (V):')
        self.layout().addWidget(self.data_std_label, 13, 1, 1, 1)
        # Interferogram
        self.interferogram_quality_label = self.gb_make_labeled_label(label_text='Int Data Quality:')
        self.layout().addWidget(self.interferogram_quality_label, 13, 2, 1, 1)
        ######
        # Loading Control 
        ######

        # Load Button 
        self.load_pushbutton = QtWidgets.QPushButton('Load', self)
        self.load_pushbutton.clicked.connect(self.fts_load)
        self.layout().addWidget(self.load_pushbutton, 14, 0, 1, 1)
        # Loaded Files Combobox 
        self.loaded_files_combobox = self.gb_make_labeled_combobox(label_text='Loaded Files')
        self.layout().addWidget(self.loaded_files_combobox, 14, 1, 1, 1)
        self.loaded_files_combobox.activated.connect(self.fts_plot_all)
        # Remove File Button
        self.remove_file_pushbutton = QtWidgets.QPushButton('Remove File')
        self.remove_file_pushbutton.clicked.connect(self.fts_remove_file)
        self.layout().addWidget(self.remove_file_pushbutton, 14, 2, 1, 1)
        # Replot
        self.replot_pushbutton = QtWidgets.QPushButton('Replot', self)
        self.layout().addWidget(self.replot_pushbutton, 15, 0, 1, 3)
        self.replot_pushbutton.clicked.connect(self.fts_plot_all)
        # Save
        self.save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.layout().addWidget(self.save_pushbutton, 16, 0, 1, 3)
        self.save_pushbutton.clicked.connect(self.fts_save)


    def fts_update_source_power(self):
        '''
        '''
        source_type = self.source_type_combobox.currentText()
        if source_type == 'Heater':
            self.source_power_lineedit.setLabelText('AC Volts')
            self.source_frequency_lineedit.setText('Thermal')
            self.source_power_lineedit.setValidator(QtGui.QDoubleValidator(0, 150, 2, self.source_power_lineedit))
        else:
            self.source_power_lineedit.setValidator(QtGui.QDoubleValidator(-1e6, 1e3, 2, self.source_power_lineedit))

    def fts_update_active_bands(self):
        '''
        '''
        band = self.bands_combobox.currentText()
        self.bands[band]['Active'] = self.detector_band_active_checkbox.isChecked()
        if self.bands[band]['Active']:
            self.status_bar.showMessage('{0} is Active'.format(band))
        self.fts_plot_all()

    def fts_show_active_bands(self):
        '''
        '''
        band = self.bands_combobox.currentText()
        active = self.bands[band]['Active']
        self.detector_band_active_checkbox.setChecked(active)
        self.fts_plot_all()

    def fts_update_active_optical_elements(self):
        '''
        '''
        optical_element = self.optical_elements_combobox.currentText()
        self.optical_elements[optical_element]['Active'] = self.optical_element_active_checkbox.isChecked()
        if self.optical_elements[optical_element]['Active']:
            self.status_bar.showMessage('{0} is Active'.format(optical_element))
        self.fts_plot_all()

    def fts_show_active_optical_elements(self):
        '''
        '''
        optical_element = self.optical_elements_combobox.currentText()
        active = self.optical_elements[optical_element]['Active']
        self.optical_element_active_checkbox.setChecked(active)
        self.fts_plot_all()

    #################################################
    # Scanning
    #################################################

    def fts_reset_zero(self):
        '''
        '''
        if not hasattr(self.csm_mirror_widget, 'com_port'):
            return None
        self.csm_mirror_widget.csm_reset_zero()
        self.set_position_lineedit.setText('0')

    def fts_set_position(self):
        '''
        '''
        if not hasattr(self.csm_mirror_widget, 'com_port'):
            return None
        position = int(self.set_position_lineedit.text())
        print('adfa', position)
        self.csm_mirror_widget.csm_set_position(position=position, verbose=True)

    def fts_update_scan_params(self):
        '''
        '''
        if len(self.end_position_lineedit.text()) == 0:
            return None
        if len(self.start_position_lineedit.text()) == 0:
            return None
        if len(self.mirror_interval_lineedit.text()) == 0:
            return None
        if len(self.pause_time_lineedit.text()) == 0:
            return None
        end = int(self.end_position_lineedit.text())
        start = int(self.start_position_lineedit.text())
        mirror_interval = int(self.mirror_interval_lineedit.text())
        distance_per_step = float(self.distance_per_step_combobox.currentText())
        pause_time = float(self.pause_time_lineedit.text())
        if mirror_interval > 0:
            self.n_data_points = abs(int((end - start) / mirror_interval))
        else:
            self.n_data_points = np.nan
        total_distance = (np.abs(end) + np.abs(start)) * distance_per_step * 1e-9
        long_arm_distance = np.abs(end) * distance_per_step * 2 * 1e-9
        min_distance = distance_per_step * mirror_interval * 1e-9
        if min_distance > 0 and total_distance > 0:
            nyquist_distance = 4 * min_distance
            self.max_frequency = (self.c / nyquist_distance) / (10 ** 9) # GHz
            self.resolution = (self.c / total_distance) / (10 ** 9) # GHz
            resolution = '{0:.2f} GHz'.format(self.resolution)
            self.long_resolution = (self.c / long_arm_distance) / (10 ** 9) # GHz
            long_resolution = '{0:.2f} GHz'.format(self.long_resolution)
            max_frequency = '{0:.2f} GHz'.format(self.max_frequency)
            info_string = 'Data Points: {0}\n'.format(self.n_data_points)
            info_string += 'Res: {0} GHz (raw)\n'.format(long_resolution)
            info_string += 'Res: {0} GHz (sym)\n'.format(resolution)
            info_string += 'Max Freq {0} (GHz)'.format(max_frequency)
        else:
            info_string = ''
            self.resolution = np.nan
            self.max_frequency = np.nan
        self.scan_info_label.setText(info_string)
        self.fts_setup_stepper()

    def fts_setup_stepper(self):
        '''
        '''
        QtWidgets.QApplication.processEvents()
        for i, comport in enumerate(['COM12', 'COM13', 'COM14']):
            if i == 0:
                settings_dict = self.csm_mirror_widget.stepper_settings_dict
            elif i == 1 and self.csm_input_widget is not None:
                settings_dict = self.csm_input_widget.stepper_settings_dict
            elif i == 2 and self.csm_output_widget is not None:
                settings_dict = self.csm_output_widget.stepper_settings_dict
            sm_settings_str = '{0} Settings:'.format(comport)
            for setting, value in settings_dict.items():
                self.status_bar.showMessage('Setting up serial connection to stepper motor on {0}'.format(comport))

                print(setting[0].title())
                sm_settings_str += setting[0].title()
                sm_settings_str += ': {0:.1f} -'.format(float(value))
                getattr(self, '{0}_stepper_settings_label'.format(comport)).setText(sm_settings_str)

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
        if self.csm_mirror_widget is None:
            return None
        start = int(self.start_position_lineedit.text())
        end = int(self.end_position_lineedit.text())
        mirror_interval = int(self.mirror_interval_lineedit.text())
        pause_time = float(self.pause_time_lineedit.text())
        device = self.device_combobox.currentText()
        int_time = float(self.int_time_lineedit.text())
        sample_rate = float(self.sample_rate_lineedit.text())
        signal_channel = self.daq_combobox.currentText()
        scan_positions = np.linspace(start, end, self.n_data_points + 1)
        signal_channels = [signal_channel]
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=int_time,
                      sample_rate=sample_rate,
                      device=device)
        self.status_bar.showMessage('Moving mirror to starting position!...')
        QtWidgets.QApplication.processEvents()
        self.csm_mirror_widget.csm_set_position(position=scan_positions[0], verbose=False)
        position = ''
        while len(position) == 0:
            position = self.csm_mirror_widget.csm_get_position()
            if '\r' in position:
                position = position.split('\r')[0]
        velocity = self.csm_mirror_widget.csm_get_velocity()
        velocity = float(self.csm_mirror_widget.stepper_settings_dict['velocity'])
        position_diff = np.abs(int(position) - int(scan_positions[0])) * 1e-5
        wait = position_diff / velocity
        time.sleep(wait)
        self.status_bar.showMessage('Mirror is in position! Starting Scan...')
        QtWidgets.QApplication.processEvents()
        while self.started:
            t_start = datetime.now()
            self.x_data, self.x_stds = [], []
            self.y_data, self.y_stds = [], []
            if self.reverse_scan_checkbox.isChecked():
                scan_positions = list(reversed(scan_positions))
            for i, scan_position in enumerate(scan_positions):
                self.csm_mirror_widget.csm_set_position(position=scan_position, verbose=False)
                if i == 0:
                    self.csm_mirror_widget.csm_get_position()
                    time.sleep(self.start_pause) # wait for motor to reach starting point
                time.sleep(pause_time * 1e-3)
                if self.zero_lock_in_checkbox.isChecked():
                    self.srs_widget.srs_zero_lock_in_phase()
                    time.sleep(pause_time * 1e-3)
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
                self.fts_plot_all()
                self.fts_plot_time_stream(out_ts, out_min, out_max)
                int_average = np.mean(self.y_data)
                peak_to_peak_average = 0.5 * (np.max(self.y_data) + np.min(self.y_data))
                self.data_mean_label.setText('Data Mean (V): {0:.6f}'.format(out_mean))
                self.data_std_label.setText('Data STD (V): {0:.6f}'.format(out_std))
                self.interferogram_quality_label.setText('Int Data Quality: Avg {0:.3f} (V) Pk-Pk-Avg {1:.3f} (V)'.format(int_average, peak_to_peak_average))
                # Compute and report time diagnostics
                t_now = datetime.now()
                t_elapsed = t_now - t_start
                t_elapsed = t_elapsed.seconds + t_elapsed.microseconds * 1e-6
                t_average = t_elapsed / float(i + 1)
                steps_remain = self.n_data_points - i
                t_remain_s = t_average * steps_remain
                t_remain_m = t_average * steps_remain / 60.0
                status_message = 'Elapsed Time: {0:.1f} (s) Remaining Time: {1:.1f}/{2:.1f} (s/m) Avg Time / point (s) {3:.2f}'.format(t_elapsed, t_remain_s, t_remain_m, t_average)
                status_message += ':::Scan Postion {0} (Step {1} of {2})'.format(scan_position, i, self.n_data_points)
                self.status_bar.showMessage(status_message)
                pct_finished = 1e2 * float(i + 1) / float(self.n_data_points)
                self.status_bar.progress_bar.setValue(np.ceil(pct_finished))
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
        self.csm_mirror_widget.csm_set_position(position=scan_positions[0], verbose=False)

    #################################################
    # File handling and plotting
    #################################################

    def fts_remove_file(self):
        '''
        '''
        idx = self.loaded_files_combobox.currentIndex()
        self.loaded_files_combobox.removeItem(idx)

    def fts_index_file_name(self, suffix='if'):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}GHz_Res_{2}GHz_MaxFreq_{3}.{4}'.format(
                    self.sample_name_lineedit.text(),
                    self.resolution,
                    self.max_frequency,
                    str(i).zfill(3),
                    suffix)
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def fts_save(self):
        '''
        '''
        if_save_path = self.fts_index_file_name()
        if_save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', if_save_path)[0]
        if len(if_save_path) > 0:
            self.gb_save_meta_data(if_save_path, 'if')
            fft_save_path = if_save_path.replace('if', 'fft')
            ss_save_path = if_save_path.replace('.if', '_meta.png')
            mirror_interval = float(self.mirror_interval_lineedit.text())
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
            self.fts_plot_all()
            self.fts_plot_int()
            self.fts_plot_spectra()
            shutil.copy(os.path.join('temp_files', 'temp_int.png'), fft_save_path.replace('.fft', '_int.png'))
            shutil.copy(os.path.join('temp_files', 'temp_spectra.png'), fft_save_path.replace('.fft', '_spectra.png'))
            shutil.copy(os.path.join('temp_files', 'temp_combo.png'), fft_save_path.replace('.fft', '_combo.png'))
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')

    def fts_get_path(self):
        '''
        '''
        if_save_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select IF data', '.if')[0]
        if len(if_save_path) == 0:
            return None
        if self.loaded_files_combobox.count() < 2:
            self.loaded_files_combobox.addItem(if_save_path)
            self.loaded_files_combobox.setCurrentIndex(0)
        else:
            self.loaded_files_combobox.removeItem(-1)
            self.loaded_files_combobox.addItem(if_save_path)
            self.loaded_files_combobox.setCurrentIndex(1)
        return if_save_path

    def fts_load_from_combobox(self, clicked, plot_type='Single', fig=None, load_meta_data=True):
        '''
        '''
        if_save_path = self.loaded_files_combobox.currentText()
        self.fts_load(False, if_save_path=if_save_path, plot_type=plot_type, fig=fig, load_meta_data=load_meta_data)

    def fts_load(self, clicked, if_save_path=None, plot_type='Single', fig=None, load_meta_data=True):
        '''
        '''
        self.load_meta_data = False
        if hasattr(self.sender(), 'text') and self.sender().text() == 'Load':
            if if_save_path is None or type(if_save_path) is bool:
                if_save_path = self.fts_get_path()
                self.load_meta_data = True
        if if_save_path is not None:
            if self.load_meta_data:
                self.meta_dict = self.gb_load_meta_data(if_save_path, 'if')
                self.loaded_data_dict[if_save_path] = self.meta_dict
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
            fig = self.fts_plot(False, plot_type=plot_type, fig=fig, if_save_path=if_save_path)

    def fts_plot_time_stream(self, ts, min_, max_):
        '''
        '''
        fig, ax = self.fts_create_blank_fig(
            frac_screen_width=0.35,
            frac_screen_height=0.2,
            top=0.90,
            bottom=0.23,
            n_axes=1,
            left=0.15)
        ax.plot(ts, label='TOD')
        ax.set_xlabel('Samples', fontsize=10)
        ax.set_ylabel('($V$)', fontsize=10)
        ax.set_title('Data', fontsize=10)
        pl.legend()
        fig.savefig('temp_files/temp_ts.png', transparent=True)
        image = QtGui.QPixmap('temp_files/temp_ts.png')
        self.time_stream_plot_label.setPixmap(image)
        pl.close('all')

    def fts_plot_all(self, fig=None):
        '''
        '''
        if self.loaded_files_combobox.count() <=1 or not self.co_plot_checkbox.isChecked():
            self.fts_plot(False)
        if self.co_plot_checkbox.isChecked():
            fig, ax1, ax2, ax3, ax4 = self.fts_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.4, wspace=0.2, hspace=0.4, bottom=0.18, left=0.15)
            for idx in range(self.loaded_files_combobox.count()):
                self.loaded_files_combobox.setCurrentIndex(idx)
                self.fts_load_from_combobox(False, plot_type='Multi', fig=fig, load_meta_data=True)
        if self.divide_checkbox.isChecked():
            self.fts_plot_divided(fig)

    def fts_plot_divided(self, fig=None):
        '''
        '''
        data_clip_lo = float(self.data_clip_lo_lineedit.text()) * 1e9
        data_clip_hi = float(self.data_clip_hi_lineedit.text()) * 1e9
        data_dict = {}
        if fig is None:
            fig, ax1, ax2, ax3, ax4 = self.fts_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.4, hspace=0.4, bottom=0.18, left=0.15)
        label = ''
        transmission_samples = []
        for idx in range(self.loaded_files_combobox.count()):
            self.loaded_files_combobox.setCurrentIndex(idx)
            if_save_path = self.loaded_files_combobox.currentText()
            transmission_sample = self.loaded_data_dict[if_save_path]['transmission_sample_lineedit']
            transmission_samples.append(transmission_sample)
            self.fts_load_from_combobox(False, plot_type='Multi', fig=fig, load_meta_data=False)
            mirror_interval = self.mirror_interval_lineedit.text()
            smoothing_factor = float(self.smoothing_factor_lineedit.text())
            fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector = self.ftsy_convert_IF_to_FFT_data(self.x_data, self.y_data, mirror_interval, data_selector='All')
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real)
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real / np.max(phase_corrected_fft_vector.real))
            normalized_phase_corrected_fft_vector = self.ftsy_running_mean(normalized_phase_corrected_fft_vector, smoothing_factor=smoothing_factor)
            normalized_phase_corrected_fft_vector = normalized_phase_corrected_fft_vector / np.max(normalized_phase_corrected_fft_vector)
            data_dict[idx] = {
                    'fft_frequency_vector': fft_freq_vector,
                    'normalized_phase_corrected_fft_vector': normalized_phase_corrected_fft_vector,
                    }
        label = '{0} / {1}'.format(transmission_samples[0], transmission_samples[1])
        data_dict['plot_label'] = label
        if len(data_dict[0]['fft_frequency_vector']) != len(data_dict[1]['normalized_phase_corrected_fft_vector']):
            self.gb_quick_message('FFTs have different resolution cannot divide!', msg_type='Warning')
        else:
            fft_frequency_vector = data_dict[0]['fft_frequency_vector']
            divided_spectra = data_dict[0]['normalized_phase_corrected_fft_vector'] / data_dict[1]['normalized_phase_corrected_fft_vector']
            selector = np.logical_and(data_clip_lo < fft_frequency_vector, fft_frequency_vector < data_clip_hi)
            normalized_spectra = divided_spectra[selector] / np.nanmax(divided_spectra[selector])
            fft_frequency_vector = fft_frequency_vector[selector] * 1e-9
            if fig is None or type(fig) is bool:
                fig, ax1, ax2, ax3, ax4 = self.fts_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.4, hspace=0.4, bottom=0.18, left=0.15)
            else:
                ax1, ax2, ax3, ax4 = fig.get_axes()
            ax1.plot(fft_frequency_vector, normalized_spectra, label=label)
            ax1.set_xlabel('Frequency (GHz)', fontsize=12)
            ax1.set_ylabel('Spectral Amp', fontsize=12)

            temp_png_path = os.path.join('temp_files', 'temp_combo.png')
            handles, labels = ax1.get_legend_handles_labels()
            handles += ax3.get_legend_handles_labels()[0]
            labels += ax3.get_legend_handles_labels()[1]
            ax2.legend(handles, labels, numpoints=1, mode="expand", bbox_to_anchor=(0, 0.1, 1, 1), fontsize=9)
            fig.savefig(temp_png_path, transparent=True)
            image_to_display = QtGui.QPixmap(temp_png_path)
            self.int_spec_plot_label.setPixmap(image_to_display)

    def fts_plot(self, clicked, plot_type='Single', fig=None, if_save_path=None):
        '''
        '''
        if plot_type == 'Single':
            pl.close('all')
        data_clip_lo = float(self.data_clip_lo_lineedit.text()) * 1e9
        data_clip_hi = float(self.data_clip_hi_lineedit.text()) * 1e9
        smoothing_factor = float(self.smoothing_factor_lineedit.text())
        mirror_interval = float(self.mirror_interval_lineedit.text())
        band = self.bands_combobox.currentText()
        if fig is None or type(fig) == bool:
            fig, ax1, ax2, ax3, ax4 = self.fts_create_blank_fig(frac_screen_width=0.4, frac_screen_height=0.4, wspace=0.2, hspace=0.4, bottom=0.18, left=0.15, top=0.9)
        else:
            ax1, ax2, ax3, ax4 = fig.get_axes()
        ax1.set_xlabel('Frequency (GHz)', fontsize=10)
        ax1.set_ylabel('Spectral Amp', fontsize=10)
        ax3.set_xlabel('Mirror Position (Steps)', fontsize=10)
        ax3.set_ylabel('Response (V)', fontsize=10)
        ax4.set_xlabel('Mirror Position (Inches)', fontsize=10)
        title = 'Inteferogram and Spectra'
        if len(self.sample_name_lineedit.text()) > 0:
            title += ': {0}'.format(self.sample_name_lineedit.text())
        ax1.set_title(title, fontsize=12)
        label = None
        self.meta_dict=None
        if if_save_path is not None:
            self.meta_dict = self.loaded_data_dict[if_save_path]
        if_label = 'Raw IF'
        ax3.errorbar(self.x_data, self.y_data, yerr=self.y_stds, marker='.', linestyle='-', label=if_label)
        if len(self.x_data) > 10:
            if self.symmeterize_data_checkbox.isChecked() and np.abs(min(self.x_data)) >= max(self.x_data):
                sym_x_data, sym_y_data = self.ftsy_symmeterize_interferogram(self.x_data, self.y_data)
                ax4.errorbar(sym_x_data, sym_y_data, linestyle='-', label='Sym IF')
            else:
                sym_x_data, sym_y_data = self.x_data, self.y_data
            fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector = self.ftsy_convert_IF_to_FFT_data(sym_x_data, sym_y_data, mirror_interval, data_selector='All')
            # Plot IF 
            color = 'm'
            label = 'Raw FFT'
            if self.co_plot_checkbox.isChecked():
                color = None
                label = None
                if_label = None
            # Plot Raw FFT 
            data_selector = np.logical_and(data_clip_lo < fft_freq_vector, fft_freq_vector < data_clip_hi)
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real / np.max(phase_corrected_fft_vector.real))
            max_idx, max_freq, integrated_bandwidth = self.fts_find_max_frequency(fft_freq_vector[data_selector], normalized_phase_corrected_fft_vector[data_selector])
            pk_label = 'Peak/BW {0:.2f}/{1:.2f} GHz Raw'.format(max_freq * 1e-9, integrated_bandwidth * 1e-9)
            ax1.errorbar(max_freq * 1e-9, normalized_phase_corrected_fft_vector[data_selector][max_idx], color=color, marker='*', markersize=10, label=pk_label)
            ax1.errorbar(fft_freq_vector[data_selector] * 1e-9, normalized_phase_corrected_fft_vector[data_selector], color=color, linestyle='-', label=label)
            # Normalized and Smooth
            print(smoothing_factor)
            normalized_phase_corrected_fft_vector = self.ftsy_running_mean(normalized_phase_corrected_fft_vector, smoothing_factor=smoothing_factor)
            print(smoothing_factor)
            for band in self.bands:
                if self.bands[band]['Active']:
                    fft_frequency_vector_simulated, fft_vector_simulated = self.ftsy_load_simulated_band(data_clip_lo, data_clip_hi, band)
                    sim_selector = np.where(fft_frequency_vector_simulated < data_clip_hi * 1e-9)
                    integrated_bandwidth = np.trapz(fft_vector_simulated[sim_selector], fft_frequency_vector_simulated[sim_selector] * 1e9)
                    label = '{0} Band BW {1:.2f} GHz '.format(band, integrated_bandwidth * 1e-9)
                    ax1.plot(fft_frequency_vector_simulated[sim_selector], fft_vector_simulated[sim_selector], label=label)
                    ax1.plot(fft_frequency_vector_simulated[sim_selector], fft_vector_simulated[sim_selector])
            if self.meta_dict is not None:
                label = '{0} FFT'.format(self.meta_dict['transmission_sample_lineedit'])
            if label in ax3.get_legend_handles_labels()[1]:
                label = None
            # Plot processed FFT
            ax1, fft_freq_vector, normalized_phase_corrected_fft_vector = self.fts_plot_and_divide_optical_elements(ax1, fft_freq_vector[data_selector], normalized_phase_corrected_fft_vector[data_selector])
            normalized_phase_corrected_fft_vector = normalized_phase_corrected_fft_vector/ np.max(normalized_phase_corrected_fft_vector)
            color = 'g'
            label = 'Proc FFT'
            if self.co_plot_checkbox.isChecked():
                color = None
                label = None
            #ax1.errorbar(fft_freq_vector * 1e-9, normalized_phase_corrected_fft_vector, color=color, marker='.', linestyle='-', label=label)
            #max_idx, max_freq, integrated_bandwidth = self.fts_find_max_frequency(fft_freq_vector, normalized_phase_corrected_fft_vector)
            #pk_label = 'Peak/BW {0:.2f}/{1:.2f} GHz Proc'.format(max_freq * 1e-9, integrated_bandwidth * 1e-9)
            #ax1.errorbar(max_freq * 1e-9, normalized_phase_corrected_fft_vector[max_idx], color=color, marker='*', markersize=10, label=pk_label)
            # Raw Data
            fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector = self.ftsy_convert_IF_to_FFT_data(self.x_data, self.y_data, mirror_interval, data_selector='All')
            data_selector = np.logical_and(data_clip_lo < fft_freq_vector, fft_freq_vector < data_clip_hi)
            normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real / np.max(phase_corrected_fft_vector.real))
            ax1.errorbar(fft_freq_vector[data_selector] * 1e-9, normalized_phase_corrected_fft_vector[data_selector], color='k', alpha=0.25, linewidth=3, linestyle='-', label='All data')
        if self.meta_dict is not None:
            label = '{0} IF'.format(self.meta_dict['transmission_sample_lineedit'])
        if label in ax1.get_legend_handles_labels()[1]:
            label = None
        temp_png_path = os.path.join('temp_files', 'temp_combo.png')
        handles, labels = ax1.get_legend_handles_labels()
        handles += ax3.get_legend_handles_labels()[0]
        labels += ax3.get_legend_handles_labels()[1]
        handles += ax4.get_legend_handles_labels()[0]
        labels += ax4.get_legend_handles_labels()[1]
        ax2.legend(handles, labels, numpoints=1, mode="expand", bbox_to_anchor=(0, 0.1, 1, 1), fontsize=8)
        fig.savefig(temp_png_path, transparent=True)
        image_to_display = QtGui.QPixmap(temp_png_path)
        self.int_spec_plot_label.setPixmap(image_to_display)
        return fig

    def fts_find_max_frequency(self, frequency_vector, normalized_transmission_vector):
        '''
        '''
        max_idx = np.argmax(normalized_transmission_vector)
        max_freq = frequency_vector[max_idx]
        integrated_bandwidth = np.trapz(normalized_transmission_vector, frequency_vector)
        return max_idx, max_freq, integrated_bandwidth



    def fts_plot_and_divide_optical_elements(self, ax, frequency_vector, normalized_transmission_vector):
        '''
        '''
        data_clip_lo = float(self.data_clip_lo_lineedit.text()) * 1e9
        data_clip_hi = float(self.data_clip_hi_lineedit.text()) * 1e9
        threshhold = float(self.element_division_threshhold_lineedit.text())
        divide_elements = self.divide_elements_checkbox.isChecked()
        for optical_element in self.optical_elements:
            active = self.optical_elements[optical_element]['Active']
            path = self.optical_elements[optical_element]['Path']
            if active and not self.started:
                element_frequency_vector, element_transmission_vector = self.ftsy_load_optical_element_response(path)
                if divide_elements:
                    frequency_vector, normalized_transmission_vector = self.ftsy_divide_out_optical_element_response(frequency_vector, normalized_transmission_vector,
                                                                                                                     optical_element, path, threshhold=threshhold)
                selector = np.logical_and(data_clip_lo < np.asarray(element_frequency_vector), np.asarray(element_frequency_vector) < data_clip_hi)
                ax.plot(np.asarray(element_frequency_vector)[selector] * 1e-9, np.asarray(element_transmission_vector)[selector], label=optical_element)
        return ax, frequency_vector, normalized_transmission_vector

    def fts_plot_spectra(self):
        '''
        '''
        pl.close('all')
        mirror_interval = self.mirror_interval_lineedit.text()
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
        for band in self.bands:
            if self.bands[band]['Active']:
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
            ax1 = fig.add_subplot(221, label='int')
            ax2 = fig.add_subplot(222, label='legend')
            ax3 = fig.add_subplot(223, label='spec')
            ax4 = fig.add_subplot(224)
            ax2.set_axis_off()
            return fig, ax1, ax2, ax3, ax4
        else:
            ax = fig.add_subplot(111)
            return fig, ax
