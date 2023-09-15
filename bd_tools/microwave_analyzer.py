import time
import shutil
import os
import simplejson
import pylab as pl
import numpy as np
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from bd_lib.bolo_pyvisa import BoloPyVisa
from bd_lib.mpl_canvas import MplCanvas
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class MicrowaveAnalyzer(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, srs_widget, data_folder):
        super(MicrowaveAnalyzer, self).__init__()
        self.srs_widget = srs_widget
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.data_folder = os.path.join(data_folder, 'MicrowaveAnalyzer')
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        self.bpv = BoloPyVisa()
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
        self.mplc = MplCanvas(self, screen_resolution, monitor_dpi)
        self.main_fig = self.mplc.mplc_create_basic_fig(left=0.2, frac_screen_width=0.3, frac_screen_height=0.5)[0]
        self.ts_fig = self.mplc.mplc_create_basic_fig(left=0.15, bottom=0.1, frac_screen_width=0.3, frac_screen_height=0.2)[0]
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.ma_update_samples()
        self.ma_input_panel()
        self.ma_update_frequencies()
        self.y_data = np.ones(len(self.frequency_array))
        self.y_err = np.zeros(len(self.frequency_array))
        self.bands = {
            '': {
                'Active': False,
                'Band Center': '',
                'Project': '',
                'Freq Column': 'NA',
                'Transmission Column': 'NA',
                'Header Lines': 'NA',
                'Path': 'NA',
                },
            '90': {
                'Active': False,
                'Band Center': 90,
                'Project': 'Simons Array',
                'Freq Column': 0,
                'Transmission Column': 1,
                'Header Lines': 1,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'PB2abcBands.csv')
                },
            '150': {
                'Active': False,
                'Band Center': 150,
                'Project': 'Simons Array',
                'Freq Column': 0,
                'Transmission Column': 2,
                'Header Lines': 1,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'PB2abcBands.csv')
                },
            'SO30': {
                'Active': False,
                'Band Center': 30,
                'Project': 'Simons Observatory',
                'Freq Column': 0,
                'Transmission Column': 3,
                'Header Lines': 2,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'Nitride_Lumped_Diplexer_030_05_040_08_MoreWider20190226_300GHz.csv')
                },
            'SO40': {
                'Active': False,
                'Band Center': 40,
                'Project': 'Simons Observatory',
                'Freq Column': 0,
                'Transmission Column': 4,
                'Header Lines': 2,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'Nitride_Lumped_Diplexer_030_05_040_08_MoreWider20190226_300GHz.csv')
                },
            'LBLF4-40': {
                'Active': False,
                'Band Center':40,
                'Project': 'LiteBird',
                'Freq Column': 0,
                'Transmission Column': 4,
                'Header Lines': 2,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'Nitride_Lumped_Diplexer_030_05_040_08_MoreWider20190226_300GHz.csv')
                },
            'LBLF4-58': {
                'Active': False,
                'Band Center': 58,
                'Project': 'LiteBird',
                'Freq Column': 0,
                'Transmission Column': 4,
                'Header Lines': 2,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'Nitride_Lumped_Diplexer_030_05_040_08_MoreWider20190226_300GHz.csv')
                },
            'LBLF4-82': {
                'Active': False,
                'Band Center': 82,
                'Project': 'LiteBird',
                'Freq Column': 0,
                'Transmission Column': 4,
                'Header Lines': 2,
                },
            'LBLF4-78': {
                'Active': False,
                'Band Center': 70,
                'Project': 'LiteBird',
                'Freq Column': 0,
                'Transmission Column': 4,
                'Header Lines': 2,
                'Path': os.path.join('bd_lib', 'simulated_bands', '20190428_LB_78100140_WithoutNotch.csv')
                },
            'LBLF4-100': {
                'Active': False,
                'Band Center': 100,
                'Project': 'LiteBird',
                'Freq Column': 0,
                'Transmission Column': 5,
                'Header Lines': 2,
                'Path': os.path.join('bd_lib', 'simulated_bands', '20190428_LB_78100140_WithoutNotch.csv')
                },
            'LBLF4-140': {
                'Active': False,
                'Band Center': 140,
                'Project': 'LiteBird',
                'Freq Column': 0,
                'Transmission Column': 6,
                'Header Lines': 2,
                'Path': os.path.join('bd_lib', 'simulated_bands', '20190428_LB_78100140_WithoutNotch.csv')
                }
            }
        self.ma_plot()
        self.ma_set_all_sa_settings()
        self.ma_update_sample_name()
        QtWidgets.QApplication.processEvents()

    def ma_update_samples(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)

    def ma_update_sample_name(self):
        '''
        '''
        sample_key = self.sample_name_combobox.currentText()
        sample_name = self.samples_settings[sample_key]
        self.sample_name_lineedit.setText(sample_name)

    def ma_input_panel(self):
        '''
        '''
        self.welcome_header_label = QtWidgets.QLabel('Welcome to Time Constant', self)
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
        self.layout().addWidget(daq_header_label, 1, 2, 1, 1)
        self.daq_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.daq_combobox, 1, 3, 1, 1)
        for channel in sorted([int(x) for x in self.daq_settings[device]]):
            self.daq_combobox.addItem(str(channel))
        self.sample_name_combobox = self.gb_make_labeled_combobox(label_text='Select Sample')
        for sample in self.samples_settings:
            self.sample_name_combobox.addItem(str(sample))
        self.layout().addWidget(self.sample_name_combobox, 2, 0, 1, 1)
        self.sample_name_combobox.currentIndexChanged.connect(self.ma_update_sample_name)

        self.sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Name')
        self.layout().addWidget(self.sample_name_lineedit, 2, 1, 1, 3)
        #Pause Time 
        self.pause_time_lineedit = self.gb_make_labeled_lineedit(label_text='Pause Time (ms):')
        self.pause_time_lineedit.setText('1500')
        self.pause_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.pause_time_lineedit))
        self.layout().addWidget(self.pause_time_lineedit, 3, 0, 1, 1)
        #Int Time 
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int Time (ms): ')
        self.int_time_lineedit.setText('1500')
        self.int_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.int_time_lineedit))
        self.layout().addWidget(self.int_time_lineedit, 3, 1, 1, 1)
        #Sample rate 
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz): ')
        self.sample_rate_lineedit.setText('5000')
        self.sample_rate_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.sample_rate_lineedit))
        self.layout().addWidget(self.sample_rate_lineedit, 3, 2, 1, 1)
        # SA Settings 
        self.power_lineedit = self.gb_make_labeled_lineedit(label_text='Power (dbM)', lineedit_text='-25.0')
        self.layout().addWidget(self.power_lineedit, 4, 0, 1, 1)
        self.n_points_lineedit = self.gb_make_labeled_lineedit(label_text='N Points', lineedit_text='5001')
        self.layout().addWidget(self.n_points_lineedit, 4, 1, 1, 1)
        self.n_averages_lineedit = self.gb_make_labeled_lineedit(label_text='N Averages', lineedit_text='5')
        self.layout().addWidget(self.n_averages_lineedit, 4, 2, 1, 1)
        #Frequency Range
        self.start_frequency_lineedit = self.gb_make_labeled_lineedit(label_text='Start Frequency (GHz):')
        self.start_frequency_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e4, 3, self.start_frequency_lineedit))
        self.start_frequency_lineedit.setText('25')
        self.layout().addWidget(self.start_frequency_lineedit, 5, 0, 1, 1)
        self.end_frequency_lineedit = self.gb_make_labeled_lineedit(label_text='End Frequency (GHz):')
        self.end_frequency_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e4, 3, self.end_frequency_lineedit))
        self.end_frequency_lineedit.setText('42.5')
        self.layout().addWidget(self.end_frequency_lineedit, 5, 1, 1, 1)
        self.frequency_spacing_lineedit = self.gb_make_labeled_lineedit(label_text='Frequency Spacing (GHz):')
        self.frequency_spacing_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e4, 3, self.frequency_spacing_lineedit))
        self.frequency_spacing_lineedit.setText('0.1')
        self.layout().addWidget(self.frequency_spacing_lineedit, 5, 2, 1, 1)
        self.frequency_span_lineedit = self.gb_make_labeled_lineedit(label_text='Frequency Sweep (GHz):')
        self.frequency_span_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e4, 3, self.frequency_span_lineedit))
        self.frequency_span_lineedit.setText('0.0')
        self.layout().addWidget(self.frequency_span_lineedit, 5, 3, 1, 1)
        self.start_frequency_lineedit.textChanged.connect(self.ma_update_frequencies)
        self.frequency_spacing_lineedit.textChanged.connect(self.ma_update_frequencies)
        self.plot_so30_checkbox = QtWidgets.QCheckBox('Plot SO30')
        self.layout().addWidget(self.plot_so30_checkbox, 6, 0, 1, 1)
        self.plot_so40_checkbox = QtWidgets.QCheckBox('Plot SO40')
        self.layout().addWidget(self.plot_so40_checkbox, 6, 1, 1, 1)
        self.normalize_checkbox = QtWidgets.QCheckBox('Normalize?')
        self.layout().addWidget(self.normalize_checkbox, 6, 2, 1, 1)
        self.time_stream_plot_label = QtWidgets.QLabel()
        self.layout().addWidget(self.time_stream_plot_label, 7, 0, 1, 4)
        # Control Buttons
        self.start_pushbutton = QtWidgets.QPushButton('Start', self)
        self.start_pushbutton.clicked.connect(self.ma_start_stop)
        self.layout().addWidget(self.start_pushbutton, 9, 0, 1, 4)
        self.save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.save_pushbutton.clicked.connect(self.ma_save)
        self.layout().addWidget(self.save_pushbutton, 10, 0, 1, 4)
        self.load_pushbutton = QtWidgets.QPushButton('Load', self)
        self.load_pushbutton.clicked.connect(self.ma_load)
        self.layout().addWidget(self.load_pushbutton, 11, 0, 1, 4)
        # Plotting 
        self.plot_data_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.plot_data_label, 0, 4, 10, 1)
        self.device_combobox.setCurrentIndex(0)

    #######################
    # Network Analyzer Setup 
    ######################

    def ma_set_all_sa_settings(self):
        '''
        '''
        self.ma_set_frequency()
        time.sleep(0.3)
        self.ma_set_frequency_span()
        time.sleep(0.3)
        self.ma_set_n_points()
        time.sleep(0.3)
        self.ma_set_n_averages()
        time.sleep(0.3)
        self.ma_set_power()
        time.sleep(0.3)

    def ma_set_frequency(self, frequency=None):
        '''
        '''
        if frequency is None:
            frequency = float(self.start_frequency_lineedit.text()) * 1e9 #GHz
        self.bpv.inst.write("FREQuency:CENTer {0:.5f}".format(frequency))

    def ma_set_frequency_span(self, frequency_span=None):
        '''
        '''
        if frequency_span is None:
            frequency_span = float(self.frequency_span_lineedit.text()) * 1e9 #GHz
        self.bpv.inst.write("FREQuency:SPAN {0:.3f}".format(frequency_span))

    def ma_set_n_points(self, n_points=None):
        '''
        '''
        if n_points is None:
            n_points = int(self.n_points_lineedit.text())
        self.bpv.inst.write("SWEep:POINts {0}".format(n_points))

    def ma_set_n_averages(self, n_averages=None):
        '''
        '''
        if n_averages is None:
            n_averages = int(self.n_averages_lineedit.text())
        self.bpv.inst.write("AVERage:COUNt {0}".format(n_averages))

    def ma_set_power(self, power=-25.0):
        '''
        '''
        if power is None:
            power = float(self.power_lineedit.text())
        self.bpv.inst.write("SOURce:POWer {0:.1f}".format(power))

    def ma_set_sweep_mode(self):
        '''
        '''
        self.bpv.inst.write("FORM ASCII,0") # set format to ASCII; p. 451
        self.bpv.inst.write("CALC:PAR1:SEL") # select trace 1
        self.bpv.inst.query("INIT:CONT 1; *OPC?") # set up single sweep mode, p. 453
        # ---- set data format to log magnitude, autoscale the trace ----#
        self.bpv.inst.query("CALC:FORM MLOG; *OPC?") # set data format to log magnitude, p. 301
        time.sleep(1.)

    #######################
    # Data Taking 
    ######################

    def ma_start_stop(self):
        '''
        '''
        self.saved = False
        if self.sender().text() == 'Start':
            self.sender().setText('Stop')
            self.started = True
            self.ma_scan()
        else:
            self.sender().setText('Start')
            self.started = False
            self.saved = True

    def ma_update_frequencies(self):
        '''
        '''
        start_frequency = self.start_frequency_lineedit.text()
        if len(start_frequency) == 0 or float(start_frequency) == 0.0:
            return None
        else:
            start_frequency = float(start_frequency)
        end_frequency = self.end_frequency_lineedit.text()
        if len(end_frequency) == 0 or float(end_frequency) == 0.0:
            return None
        else:
            end_frequency = float(self.end_frequency_lineedit.text())
        frequency_spacing = self.frequency_spacing_lineedit.text()
        if len(frequency_spacing) == 0 or float(frequency_spacing) == 0.0:
            return None
        else:
            frequency_spacing = float(self.frequency_spacing_lineedit.text())
        frequency_array = np.arange(start_frequency, end_frequency + frequency_spacing, frequency_spacing)
        self.start_frequency_lineedit.setDisabled(False)
        self.frequency_spacing_lineedit.setDisabled(False)
        self.frequency_array = frequency_array
        return frequency_array

    def ma_scan(self):
        '''
        '''
        int_time = float(self.int_time_lineedit.text())
        pause_time = float(self.pause_time_lineedit.text())
        int_time = float(self.int_time_lineedit.text())
        self.ma_set_all_sa_settings()
        sample_rate = float(self.sample_rate_lineedit.text())
        device = self.device_combobox.currentText()
        signal_channel = self.daq_combobox.currentText()
        signal_channels = [signal_channel]
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=int_time,
                      sample_rate=sample_rate,
                      device=device)
        self.ma_update_frequencies()
        self.y_data = np.zeros(len(self.frequency_array))
        self.y_err = np.zeros(len(self.frequency_array))
        for i, frequency in enumerate(self.frequency_array):
            self.ma_set_frequency(frequency * 1e9)
            time.sleep(pause_time * 1e-3) # in s
            data_dict = daq.run()
            self.ma_plot_ts(data_dict[signal_channel]['ts'])
            self.y_data[i] = data_dict[signal_channel]['mean']
            self.y_err[i] = data_dict[signal_channel]['std']
            self.ma_plot()
            time.sleep(pause_time * 1e-3) # in s
            pct_finished = float(i + 1) / float(self.frequency_array.size) * 1e2
            status = '{0} of {1} {2:.1f}GHz {3:.3f}V'.format(i, self.frequency_array.size, frequency, data_dict[signal_channel]['mean'])
            self.status_bar.showMessage(status)
            print(i, self.frequency_array.size)
            self.status_bar.progress_bar.setValue(int(np.ceil(pct_finished)))
            QtWidgets.QApplication.processEvents()
            if not self.started:
                break
        self.ma_save()
        self.sender().setText('Start')

    #######################
    # Loading and Saving
    ######################

    def ma_load(self, path):
        '''
        '''
        with open(path, 'r') as fh:
            freq_vector, amp_vector, error_vector = [],[],[]
            for line in fh.readlines():
                split_line = line.split('\t')
                freq = float(split_line[0])
                amp = float(split_line[1])
                error = float(split_line[2].replace('\n', ''))
                print(freq, amp, error)
                freq_vector.append(freq)
                amp_vector.append(amp)
                error_vector.append(error)
        return freq_vector, amp_vector, error_vector

    def ma_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            sample_name = self.sample_name_lineedit.text().replace('-', '').replace(' ', '_').replace('__', '_')
            file_name = 'ma_{0}_{1}.txt'.format(sample_name, str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def ma_save(self):
        '''
        '''
        save_path = self.ma_index_file_name()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', save_path, '.txt')[0]
        if len(save_path) == 0:
            return None
        print(save_path)
        plot_save_path = save_path.replace('.dat', '.png')
        shutil.copy(os.path.join('temp_files', 'temp_ma.png'), plot_save_path)
        self.gb_save_meta_data(save_path, 'txt')
        print(plot_save_path)
        with open(save_path, 'w') as fh:
            header = 'Frequency (Ghz), Amp (AU), STD (AU)\n'
            fh.write(header)
            for i, freq in enumerate(self.frequency_array):
                line = '{0:.1f}, {1:.3f}, {2:.3f}\n'.format(freq, self.y_data[i], self.y_err[i])
                fh.write(line)

    #######################
    # Plotting
    ######################

    def ma_is_float(self, value):
        '''
        '''
        try:
            float(value)
            return True
        except ValueError:
            return False

    def ma_load_simulated_band(self, data_clip_lo, data_clip_hi, band):
        '''
        '''
        data_path = self.bands[band]['Path']
        freq_idx = self.bands[band]['Freq Column']
        trans_idx = self.bands[band]['Transmission Column']
        header_lines = self.bands[band]['Header Lines']
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            frequency_data = np.zeros([])
            transmission_data = np.zeros([])
            for i, line in enumerate(lines):
                if i > header_lines:
                    try:
                        if ',' in line:
                            frequency = line.split(',')[freq_idx].strip()
                            transmission = line.split(',')[trans_idx].strip()
                        else:
                            frequency = line.split('\t')[freq_idx].strip()
                            transmission = line.split('\t')[trans_idx].strip()
                        #import ipdb;ipdb.set_trace()
                        if float(data_clip_lo) < float(frequency) * 1e9 < float(data_clip_hi) and self.ma_is_float(transmission):
                            frequency_data = np.append(frequency_data, float(frequency))
                            transmission_data = np.append(transmission_data, float(transmission))
                    except ValueError:
                        pass
        return frequency_data, transmission_data

    def ma_plot(self):
        '''
        '''
        ax = self.main_fig.get_axes()[0]
        ax.cla()
        if self.plot_so30_checkbox.isChecked():
            freq_30, trans_30 = self.ma_load_simulated_band(10e9, 40e9, 'SO30')
            ax.plot(freq_30, trans_30, label='Sim 30 1.0')
        if self.plot_so40_checkbox.isChecked():
            freq_40, trans_40 = self.ma_load_simulated_band(20e9, 60e9, 'SO40')
            ax.plot(freq_40, trans_40, label='Sim 40 1.0')
        if self.normalize_checkbox.isChecked():
            y_data = self.y_data / np.max(self.y_data)
        else:
            y_data = self.y_data
        ax.errorbar(self.frequency_array, y_data, yerr=self.y_err, ms=3, label='TES response')
        ax.set_title("{0}".format(self.sample_name_lineedit.text()))
        ax.set_xlabel('Frequency (GHz)',fontsize=14)
        ax.set_ylabel('TES Response',fontsize=14)
        ax.legend()
        temp_png_path = os.path.join('temp_files', 'temp_ma.png')
        self.main_fig.savefig(temp_png_path)
        image_to_display = QtGui.QPixmap(temp_png_path)
        self.plot_data_label.setPixmap(image_to_display)

    def ma_plot_ts(self, data):
        '''
        '''
        ax = self.ts_fig.get_axes()[0]
        ax.cla()
        ax.plot(data)
        temp_png_path = os.path.join('temp_files', 'temp_ts.png')
        self.ts_fig.savefig(temp_png_path)
        image_to_display = QtGui.QPixmap(temp_png_path)
        self.time_stream_plot_label.setPixmap(image_to_display)
