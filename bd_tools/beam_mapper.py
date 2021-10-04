import time
import shutil
import os
import simplejson
import subprocess
import pylab as pl
import numpy as np
import scipy.optimize as opt
from scipy.signal import medfilt2d
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class BeamMapper(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, csm_widget_dict, srs_widget, data_folder):
        '''
        '''
        super(BeamMapper, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.srs_widget = srs_widget
        self.fit_params_1d_human = ['Amp', 'x_0', 'sigma']
        self.fit_params_2d_human = ['Amp', 'x_0', 'y_0', 'sigma_x', 'sigma_y', 'theta']
        self.com_port_x = csm_widget_dict['X']['com_port']
        self.com_port_y = csm_widget_dict['Y']['com_port']
        self.csm_widget_x = csm_widget_dict['X']['widget']
        self.csm_widget_y = csm_widget_dict['Y']['widget']
        self.start_scan_wait_time = 5.0
        if not os.path.exists('temp_beam_files'):
            os.makedirs('temp_beam_files')
        self.bm_update_samples()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = data_folder
        self.bm_configure_input_panel()
        self.bm_configure_plot_panel()
        self.bm_plot_time_stream([0], -1.0, 1.0)
        self.bm_plot_beam_map([], [], [], running=True)
        self.bm_plot_residual_beam_map([], [], [], [], '')
        self.bm_plot_x_cut(np.asarray([]), np.asarray([]))
        self.bm_plot_y_cut(np.asarray([]), np.asarray([]))
        self.resize(self.minimumSizeHint())

    def bm_update_samples(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)

    def bm_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.bm_update_scan_params()

    def bm_configure_input_panel(self):
        '''
        '''
        #self.welcome_header_label = QtWidgets.QLabel('Welcome to Beam Mapper', self)
        #self.layout().addWidget(self.welcome_header_label, 0, 0, 1, 4)
        # DAQ (Device + Channel) Selection
        device_header_label = QtWidgets.QLabel('Device:', self)
        self.layout().addWidget(device_header_label, 0, 0, 1, 1)
        self.device_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.device_combobox, 0, 1, 1, 1)
        for device in self.daq_settings:
            self.device_combobox.addItem(device)
        self.device_combobox.setCurrentIndex(1)
        daq_header_label = QtWidgets.QLabel('DAQ:', self)
        self.layout().addWidget(daq_header_label, 1, 0, 1, 1)
        self.daq_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.daq_combobox, 1, 1, 1, 1)
        for channel in sorted([int(x) for x in self.daq_settings[device]]):
            self.daq_combobox.addItem(str(channel))
        #Pause Time 
        self.pause_time_lineedit = self.gb_make_labeled_lineedit(label_text='Pause Time (ms):', lineedit_text='1250')
        self.pause_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.pause_time_lineedit))
        self.layout().addWidget(self.pause_time_lineedit, 2, 0, 1, 1)
        #Int Time 
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int Time (ms): ', lineedit_text='500')
        self.int_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.int_time_lineedit))
        self.layout().addWidget(self.int_time_lineedit, 2, 1, 1, 1)
        #Sample rate 
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz): ', lineedit_text='5000')
        self.sample_rate_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.sample_rate_lineedit))
        self.layout().addWidget(self.sample_rate_lineedit, 2, 2, 1, 1)
        # Basic stepper control X
        self.set_position_x_lineedit = self.gb_make_labeled_lineedit(label_text='Set to Position X')
        self.set_position_x_lineedit.setValidator(QtGui.QIntValidator(-300000, 300000, self.set_position_x_lineedit))
        self.layout().addWidget(self.set_position_x_lineedit, 3, 0, 1, 1)
        self.set_position_x_pushbutton = QtWidgets.QPushButton('Set Position X')
        self.layout().addWidget(self.set_position_x_pushbutton, 3, 1, 1, 1)
        self.reset_zero_x_pushbutton = QtWidgets.QPushButton('Reset Zero X')
        self.layout().addWidget(self.reset_zero_x_pushbutton, 3, 2, 1, 2)
        # Basic stepper control Y
        self.set_position_y_lineedit = self.gb_make_labeled_lineedit(label_text='Set to Position Y')
        self.layout().addWidget(self.set_position_y_lineedit, 4, 0, 1, 1)
        self.set_position_y_lineedit.setValidator(QtGui.QIntValidator(-300000, 300000, self.set_position_y_lineedit))
        self.set_position_y_pushbutton = QtWidgets.QPushButton('Set Position Y')
        self.layout().addWidget(self.set_position_y_pushbutton, 4, 1, 1, 1)
        self.reset_zero_y_pushbutton = QtWidgets.QPushButton('Reset Zero Y')
        self.layout().addWidget(self.reset_zero_y_pushbutton, 4, 2, 1, 2)
        self.reset_zero_x_pushbutton.clicked.connect(self.bm_reset_zero)
        self.reset_zero_y_pushbutton.clicked.connect(self.bm_reset_zero)
        self.set_position_x_pushbutton.clicked.connect(self.bm_set_position)
        self.set_position_y_pushbutton.clicked.connect(self.bm_set_position)
        # Common Positions 
        self.set_origin_pushbutton = QtWidgets.QPushButton('Go to Origin')
        self.set_origin_pushbutton.clicked.connect(self.bm_set_origin)
        self.layout().addWidget(self.set_origin_pushbutton, 5, 0, 1, 2)
        self.set_ln2_load_pushbutton = QtWidgets.QPushButton('Go to LN2 Load')
        self.set_ln2_load_pushbutton.clicked.connect(self.bm_set_ln2_load)
        self.layout().addWidget(self.set_ln2_load_pushbutton, 5, 2, 1, 2)
        # Stepper Motor Selection
        ######
        # Scan Params
        ######
        #X Scan
        self.start_position_x_lineedit = self.gb_make_labeled_lineedit(label_text='Start Position X:', lineedit_text='-50000')
        self.start_position_x_lineedit.setValidator(QtGui.QIntValidator(-300000, 300000, self.start_position_x_lineedit))
        self.start_position_x_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.start_position_x_lineedit, 7, 0, 1, 2)
        self.end_position_x_lineedit = self.gb_make_labeled_lineedit(label_text='End Position X:', lineedit_text='50000')
        self.end_position_x_lineedit.setValidator(QtGui.QIntValidator(-300000, 300000, self.end_position_x_lineedit))
        self.end_position_x_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.end_position_x_lineedit, 7, 2, 1, 2)
        #Y Scan
        self.start_position_y_lineedit = self.gb_make_labeled_lineedit(label_text='Start Position Y:', lineedit_text='-50000')
        self.start_position_y_lineedit.setValidator(QtGui.QIntValidator(-300000, 300000, self.start_position_y_lineedit))
        self.start_position_y_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.start_position_y_lineedit, 8, 0, 1, 2)
        self.end_position_y_lineedit = self.gb_make_labeled_lineedit(label_text='End Position Y:', lineedit_text='50000')
        self.end_position_y_lineedit.setValidator(QtGui.QIntValidator(-300000, 300000, self.end_position_y_lineedit))
        self.end_position_y_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.end_position_y_lineedit, 8, 2, 1, 2)
        #Step Size 
        self.step_size_x_lineedit = self.gb_make_labeled_lineedit(label_text='Step Size X (steps):', lineedit_text='25000')
        self.step_size_x_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.step_size_x_lineedit.setValidator(QtGui.QIntValidator(1, 200000, self.step_size_x_lineedit))
        self.layout().addWidget(self.step_size_x_lineedit, 9, 0, 1, 2)
        step_size_y_header_label = QtWidgets.QLabel
        self.step_size_y_lineedit = self.gb_make_labeled_lineedit(label_text='Step Size Y (steps):', lineedit_text='25000')
        self.step_size_y_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.step_size_y_lineedit.setValidator(QtGui.QIntValidator(1, 200000, self.step_size_y_lineedit))
        self.layout().addWidget(self.step_size_y_lineedit, 9, 2, 1, 2)
        #Scan Info size
        self.aperture_description_lineedit = self.gb_make_labeled_lineedit(label_text='Aperture Description')
        self.layout().addWidget(self.aperture_description_lineedit, 10, 0, 1, 2)
        self.voltage_bias_lineedit = self.gb_make_labeled_lineedit(label_text='Voltage Bias (uV):')
        self.voltage_bias_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 3, self.voltage_bias_lineedit))
        self.layout().addWidget(self.voltage_bias_lineedit, 10, 2, 1, 2)
        #Source Information 
        self.source_type_combobox = self.gb_make_labeled_combobox(label_text='Source Type')
        for source_type in ['Analyzer', 'LN2', 'Heater']:
            self.source_type_combobox.addItem(source_type)
        self.source_type_combobox.currentIndexChanged.connect(self.bm_update_source_type)
        self.layout().addWidget(self.source_type_combobox, 11, 0, 1, 1)

        self.modulation_frequency_lineedit = self.gb_make_labeled_lineedit(label_text='Modulation Frequency (Hz)', lineedit_text='12')
        self.modulation_frequency_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 3, self.modulation_frequency_lineedit))
        self.layout().addWidget(self.modulation_frequency_lineedit, 11, 1, 1, 1)
        # Source Temp
        self.source_temp_lineedit = self.gb_make_labeled_lineedit(label_text='Source Temp (K):')
        self.source_temp_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 3, self.source_temp_lineedit))
        self.layout().addWidget(self.source_temp_lineedit, 11, 2, 1, 2)
        # Source Frequency
        self.source_frequency_lineedit = self.gb_make_labeled_lineedit(label_text='Source Frequency (GHz):')
        self.source_frequency_lineedit.setValidator(QtGui.QDoubleValidator(0, 1000, 3, self.source_frequency_lineedit))
        self.layout().addWidget(self.source_frequency_lineedit, 12, 0, 1, 1)
        # Source Power
        self.source_power_lineedit = self.gb_make_labeled_lineedit(label_text='Source Power (dBm):')
        self.source_power_lineedit.setValidator(QtGui.QDoubleValidator(-1e3, 1e3, 5, self.source_power_lineedit))
        self.layout().addWidget(self.source_power_lineedit, 12, 1, 1, 1)
        # Source Angle
        self.source_angle_lineedit = self.gb_make_labeled_lineedit(label_text='Source Angle (degrees):')
        self.source_angle_lineedit.setValidator(QtGui.QDoubleValidator(0, 360, 2, self.source_angle_lineedit))
        self.layout().addWidget(self.source_angle_lineedit, 12, 2, 1, 1)
        # Source Distance
        self.source_distance_lineedit = self.gb_make_labeled_lineedit(label_text='Source Distance (in):', lineedit_text='10')
        self.source_distance_lineedit.setValidator(QtGui.QDoubleValidator(0, 360, 2, self.source_distance_lineedit))
        self.layout().addWidget(self.source_distance_lineedit, 12, 3, 1, 1)
        # Time Stream and data label
        self.time_stream_plot_label = QtWidgets.QLabel('', self)
        self.time_stream_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.layout().addWidget(self.time_stream_plot_label, 13, 0, 1, 3)
        self.data_string_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.data_string_label, 13, 3, 1, 1)
        self.bm_update_scan_params()
        #Sample Name and Notes
        self.sample_name_combobox = self.gb_make_labeled_combobox(label_text='Sample Name Select:')
        for sample in self.samples_settings:
            self.sample_name_combobox.addItem(sample)
        self.sample_name_combobox.activated.connect(self.bm_update_sample_name)
        self.sample_name_combobox.setCurrentIndex(0)
        self.layout().addWidget(self.sample_name_combobox, 14, 0, 1, 1)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name:')
        self.layout().addWidget(self.sample_name_lineedit, 14, 1, 1, 3)
        self.bm_update_sample_name()
        self.notes_lineedit = self.gb_make_labeled_lineedit(label_text='Notes/Comments:')
        self.layout().addWidget(self.notes_lineedit, 15, 0, 1, 4)
        # Zero Lock in
        self.zero_lock_in_checkbox = QtWidgets.QCheckBox('Zero Lock In?', self)
        self.zero_lock_in_checkbox.setChecked(True)
        self.layout().addWidget(self.zero_lock_in_checkbox, 16, 0, 1, 1)
        # Reverse Scan
        self.reverse_scan_checkbox = QtWidgets.QCheckBox('Reverse Scan', self)
        self.reverse_scan_checkbox.setChecked(False)
        self.reverse_scan_checkbox.clicked.connect(self.bm_show_scan)
        self.layout().addWidget(self.reverse_scan_checkbox, 16, 1, 1, 1)
        # Vertical/Horizontal Scan
        self.scan_raster_combobox = self.gb_make_labeled_combobox(label_text='Scan Orientation')
        for scan in ['Vertical', 'Horizontal']:
            self.scan_raster_combobox.addItem(scan)
        self.scan_raster_combobox.currentIndexChanged.connect(self.bm_show_scan)
        self.layout().addWidget(self.scan_raster_combobox, 16, 2, 1, 1)
        self.scan_display_label = QtWidgets.QLabel(self)
        self.layout().addWidget(self.scan_display_label, 16, 3, 1, 1)

        ######
        # Control Buttons 
        ######
        self.start_pushbutton = QtWidgets.QPushButton('Start', self)
        self.layout().addWidget(self.start_pushbutton, 17, 0, 1, 2)
        self.start_pushbutton.clicked.connect(self.bm_start_stop_scan)
        self.pause_pushbutton = QtWidgets.QPushButton('Pause', self)
        self.layout().addWidget(self.pause_pushbutton, 17, 2, 1, 2)
        self.pause_pushbutton.clicked.connect(self.bm_pause)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.layout().addWidget(save_pushbutton, 18, 0, 1, 2)
        save_pushbutton.clicked.connect(self.bm_save)
        load_pushbutton = QtWidgets.QPushButton('Load', self)
        self.layout().addWidget(load_pushbutton, 18, 2, 1, 2)
        load_pushbutton.clicked.connect(self.bm_load)
        #Call the the source type
        self.source_type_combobox.setCurrentIndex(1)
        self.source_type_combobox.setCurrentIndex(0)
        self.bm_show_scan()

    def bm_show_scan(self):
        '''
        '''
        orientation = self.scan_raster_combobox.currentText()
        direction = 'Forward'
        if self.reverse_scan_checkbox.isChecked():
            direction = 'Reverse'
        path = os.path.join('bd_resources', '{0}_{1}.png'.format(orientation, direction))
        pixmap = QtGui.QPixmap(path)
        new_pixmap = pixmap.scaled(30, 30)
        self.scan_display_label.setPixmap(new_pixmap)

    def bm_update_source_type(self):
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

    def bm_configure_plot_panel(self):
        '''
        '''
        # BEAM MAP
        self.beam_map_plot_label = QtWidgets.QLabel('', self)
        self.beam_map_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.layout().addWidget(self.beam_map_plot_label, 0, 4, 10, 2)
        # BEAM MAP
        self.residual_beam_map_plot_label = QtWidgets.QLabel('', self)
        self.residual_beam_map_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.layout().addWidget(self.residual_beam_map_plot_label, 0, 6, 10, 2)
        # X
        self.x_cut_plot_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.x_cut_plot_label, 10, 4, 4, 2)
        self.x_cut_select_combobox = self.gb_make_labeled_combobox(label_text='X Slice')
        self.x_cut_select_combobox.activated.connect(self.bm_plot_beam_map)
        self.layout().addWidget(self.x_cut_select_combobox, 14, 4, 1, 1)
        for x_tick in self.x_ticks:
            self.x_cut_select_combobox.addItem(x_tick)
        self.x_slice_fit_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.x_slice_fit_label, 15, 4, 1, 1)
        # Y
        self.y_cut_plot_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.y_cut_plot_label, 10, 6, 4, 2)
        self.device_combobox.setCurrentIndex(0)
        self.y_cut_select_combobox = self.gb_make_labeled_combobox(label_text='Y Slice')
        self.y_cut_select_combobox.activated.connect(self.bm_plot_beam_map)
        self.layout().addWidget(self.y_cut_select_combobox, 14, 6, 1, 1)
        for y_tick in self.y_ticks:
            self.y_cut_select_combobox.addItem(y_tick)
        self.y_slice_fit_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.y_slice_fit_label, 15, 6, 1, 1)

    ##############################################################################
    # Scanning 
    ##############################################################################

    def bm_set_ln2_load(self):
        '''
        '''
        if not hasattr(self.csm_widget_x, 'com_port') or not hasattr(self.csm_widget_y, 'com_port'):
            return None
        self.csm_widget_x.csm_set_position(position=0)
        self.csm_widget_y.csm_set_position(position=-250000)
        self.set_position_x_lineedit.setText('0')
        self.set_position_y_lineedit.setText('-250000')

    def bm_set_origin(self):
        '''
        '''
        if not hasattr(self.csm_widget_x, 'com_port') or not hasattr(self.csm_widget_y, 'com_port'):
            return None
        self.csm_widget_x.csm_set_position(position=0)
        self.csm_widget_y.csm_set_position(position=0)
        self.set_position_x_lineedit.setText('0')
        self.set_position_y_lineedit.setText('0')

    def bm_reset_zero(self):
        '''
        '''
        axis = self.sender().text().split(' ')[-1]
        csm_widget = getattr(self, 'csm_widget_{0}'.format(axis).lower())
        lineedit = getattr(self, 'set_position_{0}_lineedit'.format(axis).lower())
        if not hasattr(csm_widget, 'com_port'):
            return None
        csm_widget.csm_reset_zero()
        lineedit.setText('0')

    def bm_set_position(self):
        '''
        '''
        axis = self.sender().text().split(' ')[-1]
        print()
        print(axis)
        csm_widget = getattr(self, 'csm_widget_{0}'.format(axis).lower())
        lineedit = getattr(self, 'set_position_{0}_lineedit'.format(axis).lower())
        if not hasattr(csm_widget, 'com_port'):
            return None
        position = int(lineedit.text())
        csm_widget.csm_set_position(position=position, verbose=True)

    def bm_update_sample_name(self):
        '''
        '''
        sample_key = self.sample_name_combobox.currentText()
        sample_name = self.samples_settings[sample_key]
        self.sample_name_lineedit.setText(sample_name)

    def bm_update_scan_params(self):
        '''
        '''
        if len(self.start_position_x_lineedit.text()) == 0 or len(self.end_position_x_lineedit.text()) == 0:
            return None
        if len(self.start_position_y_lineedit.text()) == 0 or len(self.end_position_y_lineedit.text()) == 0:
            return None
        if len(self.step_size_x_lineedit.text()) == 0 or len(self.step_size_y_lineedit.text()) == 0:
            return None
        if int(self.step_size_x_lineedit.text()) == 0 or int(self.step_size_y_lineedit.text()) == 0:
            return None
        if self.start_position_x_lineedit.text() == '-' or self.start_position_y_lineedit.text() == '-':
            return None
        if self.end_position_x_lineedit.text() == '-' or self.end_position_y_lineedit.text() == '-':
            return None
        end_x = int(self.end_position_x_lineedit.text())
        start_x = int(self.start_position_x_lineedit.text())
        step_size_x = int(self.step_size_x_lineedit.text())
        end_y = int(self.end_position_y_lineedit.text())
        start_y = int(self.start_position_y_lineedit.text())
        step_size_y = int(self.step_size_y_lineedit.text())
        pause_time = float(self.pause_time_lineedit.text())
        if step_size_x > 0:
            self.n_x_data_points = int((end_x - start_x) / step_size_x) + 1
        else:
            self.n_x_data_points = np.nan
        if step_size_y > 0:
            self.n_y_data_points = int((end_y - start_y) / step_size_y) + 1
        else:
            self.n_y_data_points = np.nan
        x_grid = np.arange(start_x, end_x + step_size_x, step_size_x)
        y_grid = np.arange(start_y, end_y + step_size_y, step_size_y)
        self.x_ticks = [str(int(x * 1e-3)) for x in x_grid]
        self.y_ticks = [str(int(x * 1e-3)) for x in y_grid]
        if hasattr(self, 'x_cut_select_combobox'):
            self.x_cut_select_combobox.clear()
            for x_tick in self.x_ticks:
                self.x_cut_select_combobox.addItem(x_tick)
        if hasattr(self, 'y_cut_select_combobox'):
            self.y_cut_select_combobox.clear()
            for y_tick in self.y_ticks:
                self.y_cut_select_combobox.addItem(y_tick)
        self.n_data_points = self.n_x_data_points * self.n_y_data_points
        #import ipdb;ipdb.set_trace()
        device = self.device_combobox.currentText()
        signal_channel = self.daq_combobox.currentText()
        data_string = '{0} x {1} scan {2} total points\n'.format(self.n_x_data_points, self.n_y_data_points, self.n_data_points)
        self.data_string_label.setText(data_string)
        sm_settings_str = ''

    def bm_pause(self):
        '''
        '''
        if self.sender().text() == 'Pause':
            self.started = False
            self.sender().setText('Paused')
        else:
            self.started = False
            self.sender().setText('Pause')

    def bm_start_stop_scan(self):
        '''
        '''
        self.saved = False
        if self.sender().text() == 'Start':
            self.bm_update_scan_params()
            self.sender().setText('Stop')
            self.started = True
            self.bm_scan()
        else:
            self.sender().setText('Start')
            self.started = False
            self.saved = True
            #print(self.started)
            #import ipdb;ipdb.set_trace()

    def bm_get_daq(self):
        '''
        '''
        int_time = float(self.int_time_lineedit.text())
        sample_rate = float(self.sample_rate_lineedit.text())
        device = self.device_combobox.currentText()
        signal_channel = self.daq_combobox.currentText()
        signal_channels = [signal_channel]
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=int_time,
                      sample_rate=sample_rate,
                      device=device)
        return daq

    def bm_setup_scan(self):
        '''
        '''
        start_x = int(self.start_position_x_lineedit.text())
        end_x = int(self.end_position_x_lineedit.text())
        step_size_x = int(self.step_size_x_lineedit.text())
        start_y = int(self.start_position_y_lineedit.text())
        end_y = int(self.end_position_y_lineedit.text())
        step_size_y = int(self.step_size_y_lineedit.text())
        x_grid = np.arange(start_x, end_x + step_size_x, step_size_x)
        y_grid = np.arange(start_y, end_y + step_size_y, step_size_y)
        x_ticks = [str(int(x * 1e-3)) for x in x_grid]
        y_ticks = [str(int(x * 1e-3)) for x in y_grid]
        if self.reverse_scan_checkbox.isChecked():
            x_grid = list(reversed(x_grid))
            y_grid = list(reversed(y_grid))
        raster_1, raster_2 = np.meshgrid(x_grid, y_grid)
        if self.scan_raster_combobox.currentText() == 'Vertical':
            raster_1 = raster_1.T
            raster_2 = raster_2.T
        if self.scan_raster_combobox.currentText() != 'Vertical':
            raster_1_temp = copy(raster_2)
            raster_2 = raster_1
            raster_1 = raster_1_temp
        Z_data = np.zeros(shape=raster_1.shape)
        Z_fit_data = np.zeros(shape=Z_data.shape)
        return x_ticks, y_ticks, raster_1, raster_2, Z_data, Z_fit_data

    def bm_initialize_scan(self, grid_1_start_position, grid_2_start_position):
        '''
        '''
        self.status_bar.showMessage('Moving source to start position')
        QtWidgets.QApplication.processEvents()
        if self.csm_widget_x is not None:
            if self.scan_raster_combobox.currentText() == 'Vertical':
                self.csm_widget_x.csm_set_position(position=grid_1_start_position, verbose=False)
                self.csm_widget_y.csm_set_position(position=grid_2_start_position, verbose=False)
            else:
                self.csm_widget_x.csm_set_position(position=grid_2_start_position, verbose=False)
                self.csm_widget_y.csm_set_position(position=grid_1_start_position, verbose=False)
            time.sleep(1)
        self.status_bar.showMessage('Beam Mapper is Ready! Starting Scan.... ')
        QtWidgets.QApplication.processEvents()

    def bm_update_stats(self, start_time, count, x_pos, y_pos, Z_data, mean, std, pct_residual):
        '''
        '''
        now_time = datetime.now()
        now_time_str = datetime.strftime(now_time, '%H:%M')
        duration = now_time - start_time
        time_per_step = duration.seconds / count
        steps_left = self.n_data_points - count
        time_left = time_per_step * steps_left / 60
        progress = 1e2 * float(float(count) / float(Z_data.size))
        data_string = '{0} x {1} scan {2} total points\n'.format(self.n_x_data_points, self.n_y_data_points, self.n_data_points)
        data_string += 'X:{0}\t\tY:{1}\nZ:{2:.4f}+/-{3:.4f}\n'.format(x_pos, y_pos, mean, std)
        data_string += '{0} of {1} Points Taken {2:.0f}%\n'.format(count, Z_data.size, progress)
        data_string += 'Fit Resisdual {0:.2f}%\n'.format(pct_residual)
        self.status_bar.progress_bar.setValue(int(progress))
        status_msg = 'X: {0} Y: {1} ::: '.format(x_pos, y_pos)
        status_msg += '{0} of {1} ::: Total Duration {2:.2f} (m) ::: Time per Point {3:.2f} (s) ::: Time Left {4:.2f} (m)'.format(count, self.n_data_points, duration.seconds / 60, time_per_step, time_left)
        self.status_bar.showMessage(status_msg)
        QtWidgets.QApplication.processEvents()

    def bm_take_1d_cuts(self, x_ticks, y_ticks, Z_data):
        '''
        '''
        fit_params, residuals = self.bm_plot_x_cut(x_ticks, Z_data)
        fit_string = 'No X Fit'
        if fit_params is not None:
            fit_string = ''
            for param, value in zip(self.fit_params_1d_human, fit_params):
                fit_string += '{0}: {1:.2f} '.format(param, value)
        self.x_slice_fit_label.setText(fit_string)
        fit_params, residuals = self.bm_plot_y_cut(y_ticks, Z_data)
        fit_string = 'No Y Fit'
        if fit_params is not None:
            fit_string = ''
            for param, value in zip(self.fit_params_1d_human, fit_params):
                fit_string += '{0}: {1:.2f} '.format(param, value)
        self.y_slice_fit_label.setText(fit_string)

    def bm_fit_and_plot_2d_data(self, x_grid, x_ticks, y_grid, y_ticks, Z_data):
        '''
        '''
        #print(Z_data)
        # Process Slices
        Z_fit_data = np.zeros(shape=Z_data.shape)
        good_fit = False
        pct_residual = 0.0
        try:
            #print(Z_data)
            X = x_grid.reshape(Z_data.shape)
            Y = y_grid.reshape(Z_data.shape)
            fit_Z, fit_params = self.bm_fit_2d_data(X, Y, Z_data.flatten())
            self.bm_plot_beam_map(x_ticks, y_ticks, Z_data, fit_Z.reshape(x_grid.shape), running=True)
            Z_res = Z_data.flatten() - fit_Z.reshape(Z_data.flatten().shape)
            Z_res = Z_res.reshape(Z_data.shape)
            fit_Z = fit_Z.reshape(Z_data.shape)
            self.bm_plot_residual_beam_map(x_ticks, y_ticks, fit_Z, Z_res, fit_params)
            pct_residual = 1e2 * np.max(np.abs(Z_res)) / np.max(Z_data)
            good_fit = True
        except RuntimeError:
            self.bm_plot_beam_map(x_ticks, y_ticks, Z_data, None, running=True)
        data_string = ''
        if good_fit:
            k = 0
            for param, value in zip(self.fit_params_2d_human, fit_params):
                if 'sigma' in param or '0' in param:
                    value *= 1e-5
                if k in (2, 4):
                    data_string += '\n{0}: {1:.2f}\n'.format(param, value)
                else:
                    data_string += '{0}: {1:.2f} '.format(param, value)
                k += 1
        self.data_string_label.setText(data_string)
        return pct_residual

    def bm_scan(self):
        '''
        '''
        if self.csm_widget_x is None:
            return None
        if os.path.exists('temp_beam_files'):
            for file_name in os.listdir('temp_beam_files'):
                os.remove(os.path.join('temp_beam_files', file_name))
        else:
            os.makedirs('temp_beam_files')
        daq = self.bm_get_daq()
        x_ticks, y_ticks, raster_1, raster_2, Z_data, Z_fit_data = self.bm_setup_scan()
        self.bm_initialize_scan(raster_1.ravel()[0], raster_2.ravel()[0])
        pause_time = float(self.pause_time_lineedit.text())
        source_distance = float(self.source_distance_lineedit.text())
        self.x_posns = []
        self.y_posns = []
        self.Z_data = []
        self.Z_stds = []
        start_time = datetime.now()
        count = 1
        direction = 1
        #positions_1 = raster_1.ravel()
        #positions_2 = raster_2.ravel()
        #import ipdb;ipdb.set_trace()
        while self.started:
            for i, positions_1 in enumerate(raster_1):
                positions_2 = raster_2[i]
                if direction == -1:
                    #print(positions_2)
                    positions_2 = list(reversed(positions_2)) # Reverse scan direction every time
                    #import ipdb;ipdb.set_trace()
                #print(positions_2)
                #print(positions_2)
                for j, position_2 in enumerate(positions_2):
                    if self.scan_raster_combobox.currentText() == 'Vertical':
                        x_position = positions_1[j]
                        y_position = positions_2[j]
                        if i == 0:
                            x_grid = raster_1
                            y_grid = raster_2
                    else:
                        x_position = positions_2[j]
                        y_position = positions_1[j]
                        print()
                        print(x_position)
                        print(y_position)
                        #import ipdb;ipdb.set_trace()
                        if i == 0:
                            x_grid = raster_2
                            y_grid = raster_1
                    self.csm_widget_x.csm_set_position(position=int(x_position), verbose=False)
                    self.csm_widget_y.csm_set_position(position=int(y_position), verbose=False)
                    self.x_posns.append(x_position)
                    self.y_posns.append(y_position)
                    time.sleep(pause_time * 1e-3)
                    if self.zero_lock_in_checkbox.isChecked():
                        self.srs_widget.srs_zero_lock_in_phase()
                        time.sleep(0.500) # Post Zero lock-in wait 3 or 1 time constants at 100 or 300 ms
                    # Process Slices
                    if self.scan_raster_combobox.currentText() == 'Vertical':
                        Z_data, Z_fit_data, mean, std = self.bm_collect_data(daq, Z_data, Z_fit_data, count, i, j, direction, raster_2.size)
                    else:
                        Z_data, Z_fit_data, mean, std = self.bm_collect_data(daq, Z_data, Z_fit_data, count, i, j, direction, raster_2.size)
                    self.bm_take_1d_cuts(x_ticks, y_ticks, Z_data)
                    pct_residual = self.bm_fit_and_plot_2d_data(x_grid, x_ticks, y_grid, y_ticks, Z_data)
                    self.bm_update_stats(start_time, count, x_position, y_position, Z_data, mean, std, pct_residual)
                    time.sleep(0.300) # Wait 3 or 1 time constants at 100 or 300 ms, before moving motor
                    self.resize(self.minimumSizeHint())
                    self.y_ticks_temp = y_ticks
                    self.Z_data_temp = Z_data
                    count += 1
                    #print(x_position, y_position)
                    print(self.started)
                    #print(x_grid)
                    #import ipdb;ipdb.set_trace()
                    if not self.started:
                        break
                direction *= -1 # 
                if i + 1 == len(x_grid):
                    self.started = False
                    self.start_pushbutton.setText('Start')
                self.x_cut_select_combobox.setCurrentIndex(i - 1)
                if not self.started:
                    break
        try:
            X = x_grid.reshape(Z_data.shape)
            Y = y_grid.reshape(Z_data.shape)
            Z_fit, fit_params = self.bm_fit_2d_data(X, Y, Z_data.flatten())
            self.bm_plot_beam_map(x_ticks, y_ticks, Z_data, Z_fit.reshape(X.shape), running=True)
            Z_res = Z_data - Z_fit.reshape(X.shape)
            self.bm_plot_residual_beam_map(x_ticks, y_ticks, Z_fit.reshape(X.shape), Z_res, fit_params)
        except RuntimeError:
            self.gb_quick_message('Error With Final Fit', msg_type='Warning')
            fit_params = None
        if not self.saved:
            self.bm_take_all_y_cuts(y_ticks, Z_data.reshape(X.shape))
            self.bm_take_all_x_cuts(x_ticks, Z_data.reshape(X.shape))
            self.bm_save(fit_params)
        #self.bm_set_origin()

    def bm_collect_data(self, daq, Z_data, Z_fit_data, count, x_i, y_i, direction, size_y):
        '''
        '''
        signal_channel = self.daq_combobox.currentText()
        data_dict = daq.run()
        data_time_stream = data_dict[signal_channel]['ts']
        mean = data_dict[signal_channel]['mean']
        min_ = data_dict[signal_channel]['min']
        max_ = data_dict[signal_channel]['max']
        std = data_dict[signal_channel]['std']
        self.bm_plot_time_stream(data_time_stream, min_, max_)
        if direction == -1:
            try:
                if self.scan_raster_combobox.currentText() == 'Vertical':
                    Z_data[Z_data.shape[1] - 1 - y_i][x_i] = mean
                    Z_fit_data[Z_data.shape[1] - 1 - y_i][x_i] = mean
                else:
                    Z_data[x_i][Z_data.shape[1] - 1 - y_i] = mean
                    Z_fit_data[x_i][Z_data.shape[1] - 1 - y_i] = mean
            except IndexError:
                print('reverse')
                import ipdb;ipdb.set_trace()
        else:
            try:
                if self.scan_raster_combobox.currentText() == 'Vertical':
                    Z_data[y_i][x_i] = mean
                    Z_fit_data[y_i][x_i] = mean
                else:
                    Z_data[x_i][y_i] = mean
                    Z_fit_data[x_i][y_i] = mean
            except IndexError:
                print('forward')
                import ipdb;ipdb.set_trace()
        self.Z_data.append(mean)
        self.Z_stds.append(std)
        return Z_data, Z_fit_data, mean, std

    ##############################################################################
    # Saving and plotting
    ##############################################################################

    def bm_take_all_x_cuts(self, x_ticks, Z_data):
        '''
        '''
        for i in range(self.x_cut_select_combobox.count()):
            self.x_cut_select_combobox.setCurrentIndex(i)
            fit_params, residuals = self.bm_plot_x_cut(x_ticks, Z_data)
            self.status_bar.showMessage('Taking x cut {0}'.format(i + 1))
            QtWidgets.QApplication.processEvents()

    def bm_take_all_y_cuts(self, y_ticks, Z_data):
        '''
        '''
        for i in range(self.y_cut_select_combobox.count()):
            self.y_cut_select_combobox.setCurrentIndex(i)
            fit_params, residuals = self.bm_plot_y_cut(y_ticks, Z_data)
            self.status_bar.showMessage('Taking y cut {0}'.format(i + 1))
            QtWidgets.QApplication.processEvents()

    def bm_index_file_name(self):
        '''
        '''
        start_x = np.abs(float(self.start_position_x_lineedit.text())) / 1e5
        step_size_x = np.abs(float(self.step_size_x_lineedit.text())) / 1e5
        save_folder, folder_name = '', ''
        for i in range(1, 1000):
            folder_name = 'Scan_{0:.1f}x{0:.1f}in_Step_{1:.3f}in_{2}_{3}'.format(start_x, step_size_x, self.sample_name_lineedit.text(), str(i).zfill(3)).replace('.', 'p')
            save_folder = os.path.join(self.data_folder, folder_name)
            if not os.path.exists(save_folder):
                msg =  'Save data to {0}'.format(save_folder)
                response = self.gb_quick_message(msg=msg, add_cancel=True, add_yes=True)
                if response == QtWidgets.QMessageBox.Yes:
                    os.makedirs(save_folder)
                    break
                else:
                    return False, False
        return save_folder, folder_name

    def bm_load(self):
        '''
        '''
        if save_folder:
            save_path = os.path.join(save_folder, '{0}.dat'.format(folder_name))
            self.gb_save_meta_data(save_path, 'dat')
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_posns):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_posns[i], self.y_posns[i], self.Z_data[i], self.Z_stds[i])
                    save_handle.write(line)
            self.bm_save_plots(save_folder, folder_name)


    def bm_save_fit_data(self, save_path, fit_params):
        '''
        '''
        fit_params_2d_human = ['Amp', 'x_0', 'y_0', 'sigma_x', 'sigma_y', 'theta']
        with open(save_path, 'w') as fh:
            for param, value in zip(fit_params_2d_human, fit_params):
                if '0' in param or 'sigma' in param:
                    value *= 1e-5
                    units = ' in'
                elif 'theta' in param:
                    units = ' degs'
                else:
                    units = ''
                line = '{0}: {1}{2}\n'.format(param, value, units)
                fh.write(line)

    def bm_save(self, fit_params=None):
        '''
        '''
        save_folder, folder_name = self.bm_index_file_name()
        if save_folder:
            save_path = os.path.join(save_folder, '{0}.dat'.format(folder_name))
            self.gb_save_meta_data(save_path, 'dat')
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_posns):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_posns[i], self.y_posns[i], self.Z_data[i], self.Z_stds[i])
                    save_handle.write(line)
            self.bm_save_plots(save_folder, folder_name)
            if fit_params is not None:
                fit_save_path = save_path.replace('.dat', '_fits.txt')
                self.bm_save_fit_data(fit_save_path, fit_params)
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')

    def bm_save_plots(self, save_folder, folder_name):
        '''
        '''
        # Beams
        save_path = os.path.join(save_folder, 'raw_beam_{0}.png'.format(folder_name))
        temp_path = os.path.join('temp_beam_files', 'temp_beam.png')
        shutil.copy(temp_path, save_path)
        # Residuals
        save_path = os.path.join(save_folder, 'beam_fit_and_res_{0}.png'.format(folder_name))
        temp_path = os.path.join('temp_beam_files', 'temp_beammap_res.png')
        shutil.copy(temp_path, save_path)
        for plot_name in os.listdir('temp_beam_files'):
            if '_cut' in plot_name:
                new_name = plot_name.replace('temp_', '')
                shutil.copy(os.path.join('temp_beam_files', plot_name), os.path.join(save_folder, new_name))

    def bm_plot_x_cut(self, x_ticks, Z_data, x_pos=0):
        '''
        '''
        fit_params, residual = None, None
        x_cut_pos = int(self.x_cut_select_combobox.currentIndex())
        x_pos = self.x_cut_select_combobox.currentText()
        x_cut_beam_path = os.path.join('temp_beam_files', 'temp_x_beam_cut_{0}.png'.format(x_pos))
        if len(x_ticks) > 0 and Z_data.size > 8:
            amps = Z_data.T[x_cut_pos]
            fig, ax = self.bm_create_blank_fig(left=0.12, bottom=0.26, right=0.98, top=0.83,
                                               frac_screen_width=0.25, frac_screen_height=0.3)
            ax.plot(x_ticks, amps, label='data')
            try:
                fit_amps, fit_params = self.bm_fit_1d_data(x_ticks, amps)
                residual = amps - fit_amps
                ax.plot(x_ticks, fit_amps, label='fit')
                ax.plot(x_ticks, residual, label='residual')
            except RuntimeError:
                print('')
            ax.set_xlabel('Position (steps)', fontsize=12)
            ax.set_xlabel('X cut at {0} (steps)'.format(x_pos), fontsize=12)
            ax.set_ylabel('Amplitude', fontsize=12)
            pl.legend()
            fig.savefig(x_cut_beam_path, transparent=True)
            pl.close('all')
        if os.path.exists(x_cut_beam_path):
            image = QtGui.QPixmap(x_cut_beam_path)
            self.x_cut_plot_label.setPixmap(image)
        return fit_params, residual

    def bm_plot_y_cut(self, y_ticks, Z_data, y_pos=0):
        '''
        '''
        fit_params, residual = None, None
        y_cut_pos = int(self.y_cut_select_combobox.currentIndex())
        y_pos = self.y_cut_select_combobox.currentText()
        y_cut_beam_path = os.path.join('temp_beam_files', 'temp_y_beam_cut_{0}.png'.format(y_pos))
        if len(y_ticks) > 0:
            y_cut_pos = int(self.y_cut_select_combobox.currentIndex())
            try:
                amps = Z_data[y_cut_pos - 1][:]
            except IndexError:
                #print(Z_data)
                #print(y_cut_pos)
                import ipdb;ipdb.set_trace()
            fig, ax = self.bm_create_blank_fig(left=0.12, bottom=0.26, right=0.98, top=0.83,
                                               frac_screen_width=0.25, frac_screen_height=0.3)
            ax.plot(y_ticks, amps, label='data')
            try:
                fit_amps, fit_params = self.bm_fit_1d_data(y_ticks, amps)
                residual = amps - fit_amps
                ax.plot(y_ticks, fit_amps, label='fit')
                ax.plot(y_ticks, residual, label='residual')
            except RuntimeError:
                print('')
            ax.set_xlabel('Position (steps)', fontsize=12)
            ax.set_xlabel('Y cut at {0} (steps)'.format(y_pos), fontsize=12)
            ax.set_ylabel('Amplitude', fontsize=12)
            pl.legend()
            y_cut_beam_path = os.path.join('temp_beam_files', 'temp_y_beam_cut_{0}.png'.format(y_pos))
            fig.savefig(y_cut_beam_path, transparent=True)
            pl.close('all')
        if os.path.exists(y_cut_beam_path):
            image = QtGui.QPixmap(y_cut_beam_path)
            self.y_cut_plot_label.setPixmap(image)
        return fit_params, residual

    def bm_plot_time_stream(self, ts, min_, max_):
        '''
        '''
        fig, ax = self.bm_create_blank_fig(left=0.15, bottom=0.26, right=0.98, top=0.85,
                                           frac_screen_width=0.4, frac_screen_height=0.2,
                                           font_label_size=10)
        ax.plot(ts)
        ax.set_xlabel('Samples', fontsize=8)
        ax.set_ylabel('($V$)', fontsize=8)
        fig.savefig(os.path.join('temp_beam_files', 'temp_ts.png'), transparent=True)
        pl.close('all')
        image = QtGui.QPixmap(os.path.join('temp_beam_files', 'temp_ts.png'))
        self.time_stream_plot_label.setPixmap(image)

    def bm_plot_residual_beam_map(self, x_ticks=[], y_ticks=[], Z_fit=[], Z_res=[], fit_params=''):
        '''
        '''
        fig, ax = self.bm_create_blank_fig(left=0.05, bottom=0.11, right=0.98, top=0.9,
                                           frac_screen_width=0.3, frac_screen_height=0.4,
                                           aspect='equal')
        if len(x_ticks) > 0:
            if self.reverse_scan_checkbox.isChecked():
                ax_image = ax.contour(np.flip(Z_fit))
            else:
                ax_image = ax.contour(Z_fit)
            ax_image = ax.pcolormesh(Z_res, label=str(fit_params))
            ax.set_title('Beam Fit and Residual', fontsize=12)
            ax.set_xlabel('X Position (k-steps)', fontsize=12)
            ax.set_ylabel('Y Position (k-steps)', fontsize=12)
            x_tick_locs = [0.5 + x for x in range(len(x_ticks))]
            y_tick_locs = [0.5 + x for x in range(len(x_ticks))]
            y_cut_idx = int(self.y_cut_select_combobox.currentIndex())
            x_cut_idx = int(self.x_cut_select_combobox.currentIndex())
            ax.axvline(x_tick_locs[x_cut_idx], color='r', lw=3, alpha=0.75)
            ax.axhline(y_tick_locs[y_cut_idx], color='m', lw=3, alpha=0.75)
            ax.set_xticks(x_tick_locs)
            ax.set_yticks(y_tick_locs)
            ax.set_xticklabels(x_ticks, rotation=35, fontsize=10)
            ax.set_yticklabels(y_ticks, fontsize=10)
            color_bar = fig.colorbar(ax_image, ax=ax)
        fig.savefig(os.path.join('temp_beam_files', 'temp_beammap_res.png'), transparent=True)
        pl.close('all')
        image = QtGui.QPixmap(os.path.join('temp_beam_files', 'temp_beammap_res.png'))
        self.residual_beam_map_plot_label.setPixmap(image)

    def bm_plot_beam_map(self, x_ticks=[], y_ticks=[], Z=[], fit_Z=None, x_cut_pos=0, y_cut_pos=0, running=False):
        '''
        '''
        fig, ax = self.bm_create_blank_fig(left=0.05, bottom=0.11, right=0.98, top=0.9,
                                           frac_screen_width=0.3, frac_screen_height=0.4,
                                           aspect='equal')
        if type(x_ticks) == int:
            x_tick_index = x_ticks
            ax.axvline(self.x_ticks[x_tick_index], color='r', lw=3)
        elif len(x_ticks) > 0:
            if self.reverse_scan_checkbox.isChecked():
                ax_image = ax.pcolormesh(np.flip(Z))
            else:
                ax_image = ax.pcolormesh(Z)
            ax.set_title('BEAM DATA', fontsize=12)
            ax.set_xlabel('X Position (k-steps)', fontsize=12)
            ax.set_ylabel('Y Position (k-steps)', fontsize=12)
            x_tick_locs = [0.5 + x for x in range(len(self.x_ticks))]
            y_tick_locs = [0.5 + x for x in range(len(self.y_ticks))]
            ax.set_xticks(x_tick_locs)
            ax.set_yticks(y_tick_locs)
            ax.set_xticklabels(x_ticks, rotation=35, fontsize=10)
            ax.set_yticklabels(y_ticks, fontsize=10)
            color_bar = fig.colorbar(ax_image, ax=ax)
        fig.savefig(os.path.join('temp_beam_files', 'temp_beam.png'), transparent=True)
        pl.close('all')
        image = QtGui.QPixmap(os.path.join('temp_beam_files', 'temp_beam.png'))
        self.beam_map_plot_label.setPixmap(image)

    def bm_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.8,
                            left=0.18, right=0.98, top=0.95, bottom=0.08, n_axes=1,
                            font_label_size=12, aspect=None):
        '''
        '''
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
            ax1.tick_params(axis='x', labelsize=font_label_size)
            ax1.tick_params(axis='y', labelsize=font_label_size)
            ax2.tick_params(axis='x', labelsize=font_label_size)
            ax2.tick_params(axis='y', labelsize=font_label_size)
            return fig, ax1, ax2
        else:
            if aspect is None:
                ax = fig.add_subplot(111)
            else:
                ax = fig.add_subplot(111, aspect=aspect)
            ax.tick_params(axis='x', labelsize=font_label_size)
            ax.tick_params(axis='y', labelsize=font_label_size)
            return fig, ax

    ################################# 
    # Math and Fitting Functions    #
    ################################# 

    def bm_fit_1d_data(self, pos, amp):
        '''
        '''
        pos = [float(x) for x in pos]
        initial_guess = self.bm_guess_fit_params_1D(pos, amp)
        fit_params = self.bm_fit_1D_gaussian(self.bm_oneD_Gaussian, pos, amp, initial_guess)
        fit_amplitude = self.bm_oneD_Gaussian(np.asarray(pos), *fit_params)
        return fit_amplitude, fit_params

    def bm_fit_2d_data(self, X, Y, Z):
        '''
        '''
        XY = (X, Y)
        initial_guess = self.bm_guess_fit_params_2D(Z)
        fit_params = self.bm_fit_2D_gaussian(self.bm_twoD_Gaussian, XY, Z, initial_guess)
        fit_amplitude = self.bm_twoD_Gaussian(XY, *fit_params)
        return fit_amplitude, fit_params

    def bm_fit_1D_gaussian(self, function, position, amplitude, initial_guess):
        '''
        '''
        popt, pcov = opt.curve_fit(self.bm_oneD_Gaussian, position, amplitude, p0=initial_guess)
        return popt

    def bm_fit_2D_gaussian(self, function, XY, Z, initial_guess):
        '''
        '''
        X, Y = XY[0], XY[1]
        Z = Z.ravel()
        #print(Z)
        #print(XY)
        #import ipdb;ipdb.set_trace()
        popt, pcov = opt.curve_fit(self.bm_twoD_Gaussian, XY, Z, p0=initial_guess)
        return popt

    #Initial Guesses for Fitting
    def bm_guess_fit_params_1D(self, positions, amplitudes):
        '''
        '''
        amplitude = amplitudes.max()
        x_0 = 0
        sigma_x = 0.5 * np.max(positions)
        return amplitude, x_0, sigma_x

    def bm_guess_fit_params_2D(self, data):
        '''
        '''
        height = data.max()
        x = 0
        y = 0
        width_x = 25000
        width_y = 25000
        rotation = 0
        return height, x, y, width_x, width_y, rotation

    #Math Definitions
    def bm_twoD_Gaussian(self, XY, amplitude, x_0, y_0, sigma_x, sigma_y, theta):
        '''
        '''
        x = XY[0]
        y = XY[1]
        x_0 = float(x_0)
        y_0 = float(y_0)
        theta = np.deg2rad(theta)
        a = (np.cos(theta) ** 2) / (2 * sigma_x ** 2) + (np.sin(theta) ** 2) / (2 * sigma_y ** 2)
        b = -(np.sin(2 * theta)) / (4 * sigma_x ** 2) + (np.sin(2 * theta)) / (4 * sigma_y ** 2)
        c = (np.sin(theta) ** 2) / (2 * sigma_x ** 2) + (np.cos(theta) ** 2) / (2 * sigma_y ** 2)
        Z = amplitude * np.exp(- (a * ((x - x_0) **2) + 2 * b * (x - x_0) * (y - y_0) + c * ((y - y_0) ** 2)))
        return Z.ravel()

    def bm_oneD_Gaussian(self, position, amplitude, x_0, sigma_x):
        '''
        '''
        x_0 = float(x_0)
        gaussian = (amplitude / (sigma_x * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((position - x_0)/(sigma_x)) **2)
        return gaussian
