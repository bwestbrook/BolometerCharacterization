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
        self.welcome_header_label = QtWidgets.QLabel('Welcome to Beam Mapper', self)
        self.layout().addWidget(self.welcome_header_label, 0, 0, 1, 4)
        # DAQ (Device + Channel) Selection
        device_header_label = QtWidgets.QLabel('Device:', self)
        self.layout().addWidget(device_header_label, 1, 0, 1, 1)
        self.device_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.device_combobox, 1, 1, 1, 1)
        for device in self.daq_settings:
            self.device_combobox.addItem(device)
        self.device_combobox.setCurrentIndex(1)
        daq_header_label = QtWidgets.QLabel('DAQ:', self)
        self.layout().addWidget(daq_header_label, 2, 0, 1, 1)
        self.daq_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.daq_combobox, 2, 1, 1, 1)
        for channel in sorted([int(x) for x in self.daq_settings[device]]):
            self.daq_combobox.addItem(str(channel))
        #Pause Time 
        self.pause_time_lineedit = self.gb_make_labeled_lineedit(label_text='Pause Time (ms):')
        self.pause_time_lineedit.setText('750')
        self.pause_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.pause_time_lineedit))
        self.layout().addWidget(self.pause_time_lineedit, 4, 0, 1, 1)
        #Int Time 
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int Time (ms): ')
        self.int_time_lineedit.setText('250')
        self.int_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.int_time_lineedit))
        self.layout().addWidget(self.int_time_lineedit, 4, 1, 1, 1)
        #Sample rate 
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz): ')
        self.sample_rate_lineedit.setText('5000')
        self.sample_rate_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.sample_rate_lineedit))
        self.layout().addWidget(self.sample_rate_lineedit, 4, 3, 1, 1)
        # Stepper Motor Selection
        ######
        # Scan Params
        ######
        #Start Scan
        self.start_position_x_lineedit = self.gb_make_labeled_lineedit(label_text='Start Position X:')
        self.start_position_x_lineedit.setText('-250000')
        self.start_position_x_lineedit.setValidator(QtGui.QIntValidator(-300000, 300000, self.start_position_x_lineedit))
        self.start_position_x_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.start_position_x_lineedit, 7, 0, 1, 2)
        self.start_position_y_lineedit = self.gb_make_labeled_lineedit(label_text='Start Position Y:')
        self.start_position_y_lineedit.setText('-250000')
        self.start_position_y_lineedit.setValidator(QtGui.QIntValidator(-300000, 300000, self.start_position_y_lineedit))
        self.start_position_y_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.start_position_y_lineedit, 7, 2, 1, 2)
        #End Scan
        self.end_position_x_lineedit = self.gb_make_labeled_lineedit(label_text='End Position X:')
        self.end_position_x_lineedit.setText('250000')
        self.end_position_x_lineedit.setValidator(QtGui.QIntValidator(-300000, 300000, self.end_position_x_lineedit))
        self.end_position_x_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.end_position_x_lineedit, 8, 0, 1, 2)
        end_position_y_header_label = QtWidgets.QLabel
        self.end_position_y_lineedit = self.gb_make_labeled_lineedit(label_text='End Position Y:')
        self.end_position_y_lineedit.setText('250000')
        self.end_position_y_lineedit.setValidator(QtGui.QIntValidator(-300000, 300000, self.end_position_y_lineedit))
        self.end_position_y_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.end_position_y_lineedit, 8, 2, 1, 2)
        #Step Size 
        self.step_size_x_lineedit = self.gb_make_labeled_lineedit(label_text='Step Size X (steps):')
        self.step_size_x_lineedit.setText('25000')
        self.step_size_x_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.step_size_x_lineedit.setValidator(QtGui.QIntValidator(1, 200000, self.step_size_x_lineedit))
        self.layout().addWidget(self.step_size_x_lineedit, 9, 0, 1, 2)
        step_size_y_header_label = QtWidgets.QLabel
        self.step_size_y_lineedit = self.gb_make_labeled_lineedit(label_text='Step Size Y (steps):')
        self.step_size_y_lineedit.setText('25000')
        self.step_size_y_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.step_size_y_lineedit.setValidator(QtGui.QIntValidator(1, 200000, self.step_size_y_lineedit))
        self.layout().addWidget(self.step_size_y_lineedit, 9, 2, 1, 2)
        #Scan Info size
        self.aperture_size_lineedit = self.gb_make_labeled_lineedit(label_text='Aperture Size (in)')
        self.layout().addWidget(self.aperture_size_lineedit, 10, 0, 1, 2)
        self.aperture_size_lineedit.setValidator(QtGui.QDoubleValidator(0, 3, 3, self.aperture_size_lineedit))
        self.aperture_size_lineedit.textChanged.connect(self.bm_update_aperture_size)
        self.aperture_size_label = self.gb_make_labeled_label(label_text='Aperture Size (steps)')
        self.layout().addWidget(self.aperture_size_label, 10, 2, 1, 2)
        #Source Information 
        self.source_type_combobox = self.gb_make_labeled_combobox(label_text='Source Type')
        self.source_type_combobox.activated.connect(self.bm_update_source_type)
        for source_type in ['Analyzer', 'LN2', 'Heater']:
            self.source_type_combobox.addItem(source_type)
        self.layout().addWidget(self.source_type_combobox, 11, 0, 1, 2)
        self.source_temp_lineedit = self.gb_make_labeled_lineedit(label_text='Source Temp (K):')
        self.source_temp_lineedit.setValidator(QtGui.QDoubleValidator(0, 300, 3, self.source_temp_lineedit))
        self.layout().addWidget(self.source_temp_lineedit, 11, 2, 1, 2)
        self.source_frequency_lineedit = self.gb_make_labeled_lineedit(label_text='Source Frequency (GHz):')
        self.source_frequency_lineedit.setValidator(QtGui.QDoubleValidator(0, 1000, 3, self.source_frequency_lineedit))
        self.layout().addWidget(self.source_frequency_lineedit, 12, 0, 1, 1)
        self.source_power_lineedit = self.gb_make_labeled_lineedit(label_text='Source Power (dBm):')
        self.source_power_lineedit.setValidator(QtGui.QDoubleValidator(-1e3, 1e3, 5, self.source_power_lineedit))
        self.layout().addWidget(self.source_power_lineedit, 12, 1, 1, 1)

        self.source_angle_lineedit = self.gb_make_labeled_lineedit(label_text='Source Angle (degrees):')
        self.source_angle_lineedit.setValidator(QtGui.QDoubleValidator(0, 360, 2, self.source_angle_lineedit))
        self.layout().addWidget(self.source_angle_lineedit, 12, 2, 1, 1)

        # Time Stream and data label
        self.time_stream_plot_label = QtWidgets.QLabel('', self)
        self.time_stream_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.layout().addWidget(self.time_stream_plot_label, 13, 0, 1, 4)
        self.data_string_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.data_string_label, 14, 0, 1, 4)
        self.bm_update_scan_params()
        #Sample Name
        self.sample_name_combobox = self.gb_make_labeled_combobox(label_text='Sample Name Select:')
        for sample in self.samples_settings:
            self.sample_name_combobox.addItem(sample)
        self.sample_name_combobox.activated.connect(self.bm_update_sample_name)
        self.sample_name_combobox.setCurrentIndex(0)
        self.layout().addWidget(self.sample_name_combobox, 15, 0, 1, 2)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name:')
        self.layout().addWidget(self.sample_name_lineedit, 16, 0, 1, 2)
        self.bm_update_sample_name()
        # Zero Lock in
        self.zero_lock_in_checkbox = QtWidgets.QCheckBox('Zero Lock In?', self)
        self.zero_lock_in_checkbox.setChecked(True)
        self.layout().addWidget(self.zero_lock_in_checkbox, 14, 3, 1, 1)
        # Reverse Scan Lock in
        self.reverse_scan_checkbox = QtWidgets.QCheckBox('Reverse Scan', self)
        self.reverse_scan_checkbox.setChecked(False)
        self.layout().addWidget(self.reverse_scan_checkbox, 15, 3, 1, 1)
        ######
        # Control Buttons 
        ######
        self.start_pushbutton = QtWidgets.QPushButton('Start', self)
        self.layout().addWidget(self.start_pushbutton, 16, 0, 1, 4)
        self.start_pushbutton.clicked.connect(self.bm_start_stop_scan)
        self.pause_pushbutton = QtWidgets.QPushButton('Pause', self)
        self.layout().addWidget(self.pause_pushbutton, 17, 0, 1, 4)
        self.pause_pushbutton.clicked.connect(self.bm_pause)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.layout().addWidget(save_pushbutton, 18, 0, 1, 4)
        save_pushbutton.clicked.connect(self.bm_save)
        load_pushbutton = QtWidgets.QPushButton('Load', self)
        self.layout().addWidget(load_pushbutton, 19, 0, 1, 4)
        load_pushbutton.clicked.connect(self.bm_load)

    def bm_update_aperture_size(self):
        '''
        '''
        aperture_size = float(self.aperture_size_lineedit.text())
        aperture_size_in_steps = int(1e5 * aperture_size)
        self.aperture_size_label = '{0} steps'.format(aperture_size_in_steps)

    def bm_update_source_type(self):
        '''
        '''
        source_type = self.source_type_combobox.currentText()
        if source_type in ['LN2', 'Heater']:
            self.source_frequency_lineedit.setDisabled(True)
            self.source_power_lineedit.setDisabled(True)
            self.source_angle_lineedit.setDisabled(True)
            self.source_temp_lineedit.setDisabled(False)
            if source_type == 'LN2':
                self.source_temp_lineedit.setText('77')
        else:
            self.source_frequency_lineedit.setDisabled(False)
            self.source_power_lineedit.setDisabled(False)
            self.source_angle_lineedit.setDisabled(False)
            self.source_temp_lineedit.setDisabled(True)
            self.source_temp_lineedit.setText('')

    def bm_configure_plot_panel(self):
        '''
        '''
        # BEAM MAP
        self.beam_map_plot_label = QtWidgets.QLabel('', self)
        self.beam_map_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.layout().addWidget(self.beam_map_plot_label, 0, 4, 12, 4)
        # BEAM MAP
        self.residual_beam_map_plot_label = QtWidgets.QLabel('', self)
        self.residual_beam_map_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.layout().addWidget(self.residual_beam_map_plot_label, 0, 8, 12, 4)
        # X
        self.x_cut_plot_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.x_cut_plot_label, 12, 4, 6, 4)
        self.x_cut_select_combobox = self.gb_make_labeled_combobox(label_text='X Slice')
        self.x_cut_select_combobox.activated.connect(self.bm_plot_beam_map)
        self.layout().addWidget(self.x_cut_select_combobox, 17, 4, 1, 4)
        for x_tick in self.x_ticks:
            self.x_cut_select_combobox.addItem(x_tick)
        # Y
        self.y_cut_plot_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.y_cut_plot_label, 12, 8, 6, 4)
        self.device_combobox.setCurrentIndex(0)
        self.y_cut_select_combobox = self.gb_make_labeled_combobox(label_text='Y Slice')
        self.y_cut_select_combobox.activated.connect(self.bm_plot_beam_map)
        self.layout().addWidget(self.y_cut_select_combobox, 17, 8, 1, 4)
        for y_tick in self.y_ticks:
            self.y_cut_select_combobox.addItem(y_tick)

    ##############################################################################
    # Scanning 
    ##############################################################################

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
            n_x_data_points = int((end_x - start_x) / step_size_x) + 1
        else:
            n_x_data_points = np.nan
        if step_size_y > 0:
            n_y_data_points = int((end_y - start_y) / step_size_y) + 1
        else:
            n_y_data_points = np.nan
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
        n_data_points = n_x_data_points * n_y_data_points
        #import ipdb;ipdb.set_trace()
        device = self.device_combobox.currentText()
        signal_channel = self.daq_combobox.currentText()
        self.scan_settings_dict = {
             'device': device,
             'signal_channel': signal_channel,
             'end_x': end_x,
             'start_x': start_x,
             'step_size_x': step_size_x,
             'end_y': end_y,
             'start_y': start_y,
             'step_size_y': step_size_y,
             'pause_time': pause_time,
             'n_x_data_points': n_x_data_points,
             'n_y_data_points': n_y_data_points,
             'n_data_points': n_data_points
            }
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
        device = self.scan_settings_dict['device']
        test_data_path = os.path.join('bd_lib', 'Scan_2p5x2p5in_Step_0p250in_BT8-14-30T_001.dat')
        test_data_path = os.path.join('bd_lib', 'Scan_2p5x2p5in_Step_0p250in_BT8-14-30T_002.dat')
        signal_channel = self.scan_settings_dict['signal_channel']
        pause_time = self.scan_settings_dict['pause_time']
        total_points = self.scan_settings_dict['n_data_points']
        start_x = self.scan_settings_dict['start_x']
        start_y = self.scan_settings_dict['start_y']
        end_x = self.scan_settings_dict['end_x']
        end_y = self.scan_settings_dict['end_y']
        step_size_x = self.scan_settings_dict['step_size_x']
        step_size_y = self.scan_settings_dict['step_size_y']
        pause_time = float(self.pause_time_lineedit.text())
        int_time = float(self.int_time_lineedit.text())
        sample_rate = float(self.sample_rate_lineedit.text())
        x_grid = np.arange(start_x, end_x + step_size_x, step_size_x)
        y_grid = np.arange(start_y, end_y + step_size_y, step_size_y)
        x_ticks = [str(int(x * 1e-3)) for x in x_grid]
        y_ticks = [str(int(x * 1e-3)) for x in y_grid]
        if self.reverse_scan_checkbox.isChecked():
            y_grid_reversed = y_grid
            y_grid = np.flip(y_grid_reversed)
            x_grid = np.flip(x_grid)
        else:
            y_grid_reversed = np.flip(y_grid)
        X, Y = np.meshgrid(x_grid, y_grid)
        Z_data = np.zeros(shape=X.shape)
        Z_fit_data = np.zeros(shape=X.shape)
        #Z_data_loaded = []
        #with open(test_data_path, 'r') as file_handle:
            #lines = file_handle.readlines()
            #for line in lines:
                #Z_data_loaded.append(float(line.split(',')[2]))
        #Z_data_loaded = np.asarray(Z_data_loaded).reshape(X.shape)
        self.z_stds = np.zeros(shape=X.shape)
        direction = -1
        start_time = datetime.now()
        count = 1
        i = 0
        signal_channels = [signal_channel]
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=int_time,
                      sample_rate=sample_rate,
                      device=device)
        self.x_posns = []
        self.y_posns = []
        self.Z_data = []
        self.Z_stds = []
        start_position_x = x_grid[0]
        start_position_y = y_grid[0]
        self.status_bar.showMessage('Moving source to start position')
        QtWidgets.QApplication.processEvents()
        if self.csm_widget_x is not None:
            self.csm_widget_x.csm_set_position(position=start_position_x, verbose=False)
            self.csm_widget_y.csm_set_position(position=start_position_y, verbose=False)
            position_x = ''
            while len(position_x) == 0:
                position_x = self.csm_widget_x.csm_get_position()
            velocity_x = self.csm_widget_y.csm_get_velocity()
            velocity_x = float(self.csm_widget_x.stepper_settings_dict['velocity'])
            x_diff = np.abs(int(position_x) - int(start_position_x)) * 1e-5
            wait_x = x_diff / velocity_x
            position_y = ''
            while len(position_y) == 0:
                position_y = self.csm_widget_y.csm_get_position()
            position_y = self.csm_widget_y.csm_get_position()
            velocity_y = float(self.csm_widget_x.stepper_settings_dict['velocity'])
            y_diff = np.abs(int(position_x) - int(start_position_x)) * 1e-5
            wait_y = y_diff / velocity_y
            wait = np.max((wait_x, wait_y))
            y_diff = np.abs(int(position_y) - int(start_position_y))
            time.sleep(2 * wait) # Safety factor of three
        self.status_bar.showMessage('Beam Mapper is Ready! Starting Scan.... ')
        QtWidgets.QApplication.processEvents()
        while i < len(x_grid) and self.started:
            x_pos = x_grid[i]
            if self.csm_widget_x is not None:
                self.csm_widget_x.csm_set_position(position=int(x_pos), verbose=False)
            act_x_pos = x_pos
            direction *= -1
            if direction == -1:
                y_scan = y_grid_reversed
            else:
                y_scan = y_grid
            j = 0
            while j < len(y_scan) and self.started:
                y_pos = y_scan[j]
                if self.csm_widget_x is not None:
                    self.csm_widget_y.csm_set_position(position=int(y_pos), verbose=False)
                self.x_posns.append(x_pos)
                self.y_posns.append(y_pos)
                act_y_pos = y_pos
                time.sleep(pause_time * 1e-3)
                if self.zero_lock_in_checkbox.isChecked():
                    print('adfadfdas')
                    self.srs_widget.srs_zero_lock_in_phase()
                time.sleep(0.300) # Post Zero lock-in wait 3 or 1 time constants at 100 or 300 ms
                data_dict = daq.run()
                #data_dict = {
                    #'0':
                        #{'ts': [0, 1, 1, 2, 3, 1],
                        ##'mean': 0.13,
                        #'max': 3,
                        ##'min': 0,
                        #'std': 0.5
                         #}
                        #}
                mean = data_dict[signal_channel]['mean']
                min_ = data_dict[signal_channel]['min']
                max_ = data_dict[signal_channel]['max']
                std = data_dict[signal_channel]['std']
                data_time_stream = data_dict[signal_channel]['ts']
                mean = data_dict[signal_channel]['mean']
                min_ = data_dict[signal_channel]['min']
                max_ = data_dict[signal_channel]['max']
                std = data_dict[signal_channel]['std']
                self.bm_plot_time_stream(data_time_stream, min_, max_)
                Z_datum = mean
                #Z_datum = Z_data_loaded[i][j]
                fit_params, residuals = self.bm_plot_x_cut(y_ticks, Z_data)
                fit_params, residuals = self.bm_plot_y_cut(x_ticks, Z_data)
                if direction == -1:
                    self.z_stds[len(y_scan) -1 - j][i] = std
                    Z_data[len(y_scan) - 1- j][i] = Z_datum
                    Z_fit_data[len(y_scan) - 1- j][i] = Z_datum
                else:
                    self.z_stds[j][i] = std
                    Z_data[j][i] = Z_datum
                    Z_fit_data[j][i] = Z_datum
                Z_fit_data = np.zeros(shape=X.shape)
                self.Z_data.append(Z_datum)
                self.Z_stds.append(std)
                try:
                    X, Y = np.meshgrid(x_grid, y_grid)
                    fit_Z, fit_params = self.bm_fit_2d_data(X, Y, Z_data.flatten())
                    self.bm_plot_beam_map(x_ticks, y_ticks, Z_data, fit_Z.reshape(X.shape), running=True)
                    Z_res = Z_data - fit_Z.reshape(X.shape)
                    self.bm_plot_residual_beam_map(x_ticks, y_ticks, fit_Z.reshape(X.shape), Z_res, fit_params)
                except RuntimeError:
                    self.bm_plot_beam_map(x_ticks, y_ticks, Z_data, None, running=True)
                data_string = '{0} x {1} scan {2} total points'.format(self.scan_settings_dict['n_x_data_points'], self.scan_settings_dict['n_y_data_points'], self.scan_settings_dict['n_data_points'])
                data_string += '\nX:{0}\t\tY:{1}\nZ:{2:.4f}+/-{3:.4f}'.format(x_pos, y_pos, Z_datum, std)
                self.data_string_label.setText(data_string)
                now_time = datetime.now()
                now_time_str = datetime.strftime(now_time, '%H:%M')
                duration = now_time - start_time
                time_per_step = duration.seconds / count
                steps_left = total_points - count
                time_left = time_per_step * steps_left / 60
                status_msg = 'X: {0} Y: {1} ::: '.format(act_x_pos, act_y_pos)
                status_msg += '{0} of {1} ::: Total Duration {2:.2f} (m) ::: Time per Point {3:.2f} (s) ::: Time Left {4:.2f} (m)'.format(count, total_points, duration.seconds / 60, time_per_step, time_left)
                self.status_bar.showMessage(status_msg)
                QtWidgets.QApplication.processEvents()
                time.sleep(0.300) # Wait 3 or 1 time constants at 100 or 300 ms, before moving motor
                self.resize(self.minimumSizeHint())
                count += 1
                j += 1
                self.y_ticks_temp = y_ticks
                self.Z_data_temp = Z_data
            if i + 1 == len(x_grid):
                self.started = False
                self.start_pushbutton.setText('Start')
            i += 1
            self.x_cut_select_combobox.setCurrentIndex(i - 1)
        X, Y = np.meshgrid(x_grid, y_grid)
        try:
            Z_fit, fit_params = self.bm_fit_2d_data(X, Y, Z_data.flatten())
            self.bm_plot_beam_map(x_ticks, y_ticks, Z_data, Z_fit.reshape(X.shape), running=True)
            Z_res = Z_data - fit_Z.reshape(X.shape)
            self.bm_plot_residual_beam_map(x_ticks, y_ticks, Z_fit.reshape(X.shape), Z_res, fit_params)
        except RuntimeError:
            self.gb_quick_message('Error With Final Fit', msg_type='Warning')
        if not self.saved:
            self.bm_take_all_y_cuts(y_ticks, Z_data.reshape(X.shape))
            self.bm_take_all_x_cuts(x_ticks, Z_data.reshape(X.shape))
            self.bm_save()

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

    def bm_save(self):
        '''
        '''
        save_folder, folder_name = self.bm_index_file_name()
        print(save_folder, folder_name)
        if save_folder:
            save_path = os.path.join(save_folder, '{0}.dat'.format(folder_name))
            print(save_path)
            ss_save_path = save_path.replace('.dat', '_meta.png')
            screen = QtWidgets.QApplication.primaryScreen()
            screenshot = screen.grabWindow(self.winId())
            screenshot.save(ss_save_path, 'png')
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_posns):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_posns[i], self.y_posns[i], self.Z_data[i], self.Z_stds[i])
                    save_handle.write(line)
            self.bm_save_plots(save_folder, folder_name)
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
            amps = Z_data.transpose()[x_cut_pos]
            fig, ax = self.bm_create_blank_fig(left=0.12, bottom=0.26, right=0.98, top=0.83,
                                               frac_screen_width=0.35, frac_screen_height=0.3)
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
                print(Z_data)
                print(y_cut_pos)
                import ipdb;ipdb.set_trace()
            fig, ax = self.bm_create_blank_fig(left=0.12, bottom=0.26, right=0.98, top=0.83,
                                               frac_screen_width=0.35, frac_screen_height=0.3)
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
        fig, ax = self.bm_create_blank_fig(left=0.1, bottom=0.26, right=0.98, top=0.85,
                                           frac_screen_width=0.3, frac_screen_height=0.2,
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
                                           frac_screen_width=0.4, frac_screen_height=0.4,
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
                                           frac_screen_width=0.4, frac_screen_height=0.4,
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
        X, Y = XY[0], XY[0]
        popt, pcov = opt.curve_fit(self.bm_twoD_Gaussian, XY, Z.T, p0=initial_guess)
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
