import time
import shutil
import os

import simplejson
import numpy as np
import pickle as pkl
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.mpl_canvas import MplCanvas
from bd_lib.iv_curve_lib import IVCurveLib
from bd_lib.bolo_pyvisa import BoloPyVisa
from bd_lib.fourier_transform_spectroscopy import FourierTransformSpectroscopy
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

class ResonanceMeasurement(QtWidgets.QWidget, GuiBuilder, IVCurveLib, FourierTransformSpectroscopy):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, data_folder, dewar, ls_372_widget):
        '''
        '''
        super(ResonanceMeasurement, self).__init__()
        self.thermometer_dict = {
                'MXC': 6,
                'X110595': 9
                }
        self.mplc = MplCanvas(self, screen_resolution, monitor_dpi)
        self.bands = self.ftsy_get_bands()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.ls_372_widget = ls_372_widget
        self.dewar = dewar
        self.bpv = BoloPyVisa()
        self.fig = self.mplc.mplc_create_horizontal_array_fig()
        self.temp_scan = False
        self.drift_scan = False
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = os.path.join(data_folder, 'Resonator_Data')
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        self.rm_populate()
        self.qthreadpool = QtCore.QThreadPool()
        self.rm_get_t_bath()
        response = self.gb_quick_message('Would you like to reset the Network Analyzer?', add_yes=True, add_no=True)
        if response == QtWidgets.QMessageBox.Yes:
            self.rm_reset_network_analyzer()
        self.rm_read_set_points()

    #########################################################
    # GUI and Input Handling
    #########################################################

    def rm_populate(self):
        '''
        '''
        self.gb_initialize_panel('self')
        self.rm_configure_panel()

    def rm_configure_panel(self):
        '''
        '''

        #Housekeeping Scan Setup
        self.set_t_bath_lineedit = self.gb_make_labeled_lineedit('Bath Temp', lineedit_text='20.0')
        self.layout().addWidget(self.set_t_bath_lineedit, 1, 0, 1, 1)
        self.t_bath_set_pushbutton = QtWidgets.QPushButton('Set T_Bath')
        self.t_bath_set_pushbutton.clicked.connect(self.rm_set_t_bath)
        self.layout().addWidget(self.t_bath_set_pushbutton, 1, 1, 1, 1)
        self.t_bath_get_pushbutton = QtWidgets.QPushButton('Get T_Bath')
        self.t_bath_get_pushbutton.clicked.connect(self.rm_get_t_bath)
        self.layout().addWidget(self.t_bath_get_pushbutton, 2, 1, 1, 1)
        self.t_bath_label = self.gb_make_labeled_label(label_text='T_bath (Act)')
        self.layout().addWidget(self.t_bath_label, 1, 2, 1, 1)
        self.thermometer_combobox = self.gb_make_labeled_combobox('Thermometer')
        for thermometer in self.thermometer_dict:
            self.thermometer_combobox.addItem(thermometer)
        self.layout().addWidget(self.thermometer_combobox, 2, 2, 1, 1)
        self.thermometer_combobox.currentIndexChanged.connect(self.rm_scan_new_lakeshore_channel)

        self.start_temp_lineedit = self.gb_make_labeled_lineedit('Start Temp', lineedit_text='0.200')
        self.start_temp_lineedit.textChanged.connect(self.rm_update_scan_info)
        self.layout().addWidget(self.start_temp_lineedit, 3, 0, 1, 1)
        self.end_temp_lineedit = self.gb_make_labeled_lineedit('End Temp', lineedit_text='.250')
        self.end_temp_lineedit.textChanged.connect(self.rm_update_scan_info)
        self.layout().addWidget(self.end_temp_lineedit, 3, 1, 1, 1)
        self.n_temp_points_lineedit = self.gb_make_labeled_lineedit('N Temp Points', lineedit_text='2')
        self.n_temp_points_lineedit.textChanged.connect(self.rm_update_scan_info)
        self.layout().addWidget(self.n_temp_points_lineedit, 3, 2, 1, 1)
        self.log_spacing_checkbox = QtWidgets.QCheckBox('Log Spacing?')
        self.log_spacing_checkbox.clicked.connect(self.rm_update_scan_info)
        self.layout().addWidget(self.log_spacing_checkbox, 3, 3, 1, 1)
        self.n_drift_points_lineedit = self.gb_make_labeled_lineedit('N Drift Points', lineedit_text='500')
        self.layout().addWidget(self.n_drift_points_lineedit, 4, 0, 1, 1)
        self.drift_scan_delay_lineedit = self.gb_make_labeled_lineedit('Drift Delay (m)', lineedit_text='0.01')
        self.layout().addWidget(self.drift_scan_delay_lineedit, 4, 1, 1, 1)

        #Spectrum Analyzer Scan Setup
        self.start_power_lineedit = self.gb_make_labeled_lineedit('Start Power (dBm)', lineedit_text='-35')
        self.start_power_lineedit.textChanged.connect(self.rm_update_scan_info)
        self.layout().addWidget(self.start_power_lineedit, 6, 0, 1, 1)
        self.end_power_lineedit = self.gb_make_labeled_lineedit('End Power (dBm)', lineedit_text='0')
        self.end_power_lineedit.textChanged.connect(self.rm_update_scan_info)
        self.layout().addWidget(self.end_power_lineedit, 6, 1, 1, 1)
        self.n_power_points_lineedit = self.gb_make_labeled_lineedit('N Power Points', lineedit_text='2')
        self.layout().addWidget(self.n_power_points_lineedit, 6, 2, 1, 1)
        self.n_power_points_lineedit.textChanged.connect(self.rm_update_scan_info)
        self.scan_info_label = self.gb_make_labeled_label()
        self.layout().addWidget(self.scan_info_label, 8, 0, 1, 3)

        self.start_multitemp_scan_pushbutton = QtWidgets.QPushButton('Start Multitemp Scan')
        self.layout().addWidget(self.start_multitemp_scan_pushbutton, 9, 0, 1, 1)
        self.start_multitemp_scan_pushbutton.clicked.connect(self.rm_start_multitemp_scan)
        self.start_drift_scan_pushbutton = QtWidgets.QPushButton('Start Drift Scan')
        self.layout().addWidget(self.start_drift_scan_pushbutton, 9, 1, 1, 1)
        self.start_drift_scan_pushbutton.clicked.connect(self.rm_start_drift_scan)
        self.stop_scan_pushbutton = QtWidgets.QPushButton('Stop Scan')
        self.stop_scan_pushbutton.clicked.connect(self.rm_stop)
        self.layout().addWidget(self.stop_scan_pushbutton, 9, 2, 1, 1)

        #Spectrum Analzyer General Setup 
        self.reset_network_analyzer = QtWidgets.QPushButton('Reset SA')
        self.layout().addWidget(self.reset_network_analyzer, 10, 0, 1, 1)
        self.reset_network_analyzer.clicked.connect(self.rm_reset_network_analyzer)
        self.get_network_analyzer_data_pushbutton = QtWidgets.QPushButton('Get SA data')
        self.get_network_analyzer_data_pushbutton.clicked.connect(self.rm_get_network_analyzer_data)
        self.layout().addWidget(self.get_network_analyzer_data_pushbutton, 10, 1, 1, 1)

        # Frequency Range 
        self.center_frequency_combobox = self.gb_make_labeled_combobox(label_text='Center Frequency (GHz)')
        self.center_frequency_combobox.setEditable(True)
        self.layout().addWidget(self.center_frequency_combobox, 11, 0, 1, 1)
        self.set_center_frequency_pushbutton = QtWidgets.QPushButton('Set Center Frequency (GHz)')
        self.set_center_frequency_pushbutton.clicked.connect(self.rm_set_center_frequency)
        self.layout().addWidget(self.set_center_frequency_pushbutton, 11, 1, 1, 1)
        self.frequency_span_lineedit = self.gb_make_labeled_lineedit(label_text='Frequency Span (MHz)', lineedit_text='1000.0')
        self.layout().addWidget(self.frequency_span_lineedit, 12, 0, 1, 1)
        self.set_frequency_span_pushbutton = QtWidgets.QPushButton('Set Frequency Span')
        self.set_frequency_span_pushbutton.clicked.connect(self.rm_set_frequency_span)
        self.layout().addWidget(self.set_frequency_span_pushbutton, 12, 1, 1, 1)

        # N Points
        self.n_points_lineedit = self.gb_make_labeled_lineedit(label_text="N Points", lineedit_text='801')
        self.layout().addWidget(self.n_points_lineedit, 13, 0, 1, 1)
        self.set_n_points_pushbutton = QtWidgets.QPushButton("Set N Points")
        self.set_n_points_pushbutton.clicked.connect(self.rm_set_n_points)
        self.layout().addWidget(self.set_n_points_pushbutton, 13, 1, 1, 1)

        # N Averages
        self.n_averages_lineedit = self.gb_make_labeled_lineedit(label_text="N Averages", lineedit_text='5')
        self.layout().addWidget(self.n_averages_lineedit, 14, 0, 1, 1)
        self.set_n_averages_pushbutton = QtWidgets.QPushButton("Set N Averages")
        self.set_n_averages_pushbutton.clicked.connect(self.rm_set_n_averages)
        self.layout().addWidget(self.set_n_averages_pushbutton, 14, 1, 1, 1)
        self.time_per_average_lineedit = self.gb_make_labeled_lineedit(label_text='Time Per Avg (ms)', lineedit_text='50')
        self.layout().addWidget(self.time_per_average_lineedit, 14, 2, 1, 1)

        # Power
        self.power_lineedit = self.gb_make_labeled_lineedit(label_text="Power (dBm)", lineedit_text='-30')
        self.layout().addWidget(self.power_lineedit, 15, 0, 1, 1)
        self.set_power_pushbutton = QtWidgets.QPushButton("Set Power")
        self.set_power_pushbutton.clicked.connect(self.rm_set_power)
        self.layout().addWidget(self.set_power_pushbutton, 15, 1, 1, 1)
        self.attenuation_lineedit = self.gb_make_labeled_lineedit(label_text="Attenuation (dB)", lineedit_text='-10')
        self.layout().addWidget(self.attenuation_lineedit, 15, 2, 1, 1)

        self.set_all_sa_settings_pushbutton = QtWidgets.QPushButton('Set All')
        self.set_all_sa_settings_pushbutton.clicked.connect(self.rm_set_all_sa_settings)
        self.layout().addWidget(self.set_all_sa_settings_pushbutton, 16, 0, 1, 2)

        # Filename
        self.filename_lineedit = self.gb_make_labeled_lineedit(label_text="Filename")
        self.layout().addWidget(self.filename_lineedit, 17, 0, 1, 1)
        self.filename_lineedit.textChanged.connect(self.rm_set_filename)
        self.filename_label = self.gb_make_labeled_label(label_text="Filename")
        self.layout().addWidget(self.filename_label, 17, 1, 1, 1)

        #Data Display
        self.data_plot_label = QtWidgets.QLabel()
        self.layout().addWidget(self.data_plot_label, 0, 4, 15, 1)
        self.running_temp_label = QtWidgets.QLabel()
        self.layout().addWidget(self.running_temp_label, 18, 0, 1, 4)

        self.rm_set_filename()
        self.rm_update_scan_info()

    ############################################
    # Lakeshore Temperature Control
    ############################################

    def rm_scan_new_lakeshore_channel(self):
        '''
        '''
        if self.ls_372_widget is None:
            return None
        thermometer_index = int(self.thermometer_dict[self.thermometer_combobox.currentText()])
        self.ls_372_widget.ls372_scan_channel(index=thermometer_index)
        self.ls_372_widget.analog_outputs.ls372_monitor_channel_aux_analog(thermometer_index, self.ls_372_widget.analog_outputs.analog_output_aux)
        self.rm_get_t_bath()

    def rm_get_t_bath(self):
        '''
        '''
        if not hasattr(self.ls_372_widget, 'channels'):
            self.temperature = np.nan
            return None
        thermometer_index = int(self.thermometer_dict[self.thermometer_combobox.currentText()])
        channel_readout_info = self.ls_372_widget.channels.ls372_get_channel_value(thermometer_index, reading='kelvin') # 6 is MXC
        if self.gb_is_float(channel_readout_info):
            temperature = '{0:.3f}'.format(float(channel_readout_info) * 1e3) # mK
        else:
            temperature = '300'
        self.t_bath_label.setText(temperature)
        self.temperature = float(temperature)

    def rm_set_t_bath(self):
        '''
        '''
        if not self.gb_is_float(self.set_t_bath_lineedit.text()):
            return None
        target_temp = float(self.set_t_bath_lineedit.text()) * 1e-3 # into K
        self.ls_372_widget.temp_control.ls372_set_temp_set_point(target_temp)

    def rm_update_scan_info(self):
        '''
        '''
        if len(self.start_temp_lineedit.text()) == 0:
            return None
        if len(self.end_temp_lineedit.text()) == 0:
            return None
        if len(self.n_temp_points_lineedit.text()) == 0:
            return None
        if len(self.start_power_lineedit.text()) == 0:
            return None
        if len(self.end_power_lineedit.text()) == 0:
            return None
        if len(self.n_power_points_lineedit.text()) == 0:
            return None
        start_temp = int(float(self.start_temp_lineedit.text()) * 1e3)
        end_temp = int(float(self.end_temp_lineedit.text()) * 1e3)
        n_temp_points = int(self.n_temp_points_lineedit.text())
        start_power = int(self.start_power_lineedit.text())
        end_power = int(self.end_power_lineedit.text())
        n_power_points = int(self.n_power_points_lineedit.text())
        scan_info = '{0}mK_to_{1}mK_{2}step_{3}dBm_to_{4}dBm_{5}Steps'.format(start_temp, end_temp, n_temp_points, start_power, end_power, n_power_points)
        self.scan_info_label.setText(scan_info)
        self.temp_range = np.linspace(start_temp * 1e-3, end_temp * 1e-3, n_temp_points)
        self.power_range = np.linspace(start_power, end_power, n_power_points)

    def rm_stop(self):
        '''
        '''
        self.stop = True

    def rm_start_drift_scan(self):
        '''
        '''
        self.temp_scan = False
        self.drift_scan = True
        self.rm_set_all_sa_settings()
        try:
            self.rm_set_sweep_mode()
        except pyvisa.errors.VisaIOError:
            print('encountered pyvisa error')
            import ipdb;ipdb.set_trace()
        self.stop = False
        n_drift_points = int(self.n_drift_points_lineedit.text())
        for i in enumerate(range(n_drift_points)):
            print(i)
            self.rm_get_t_bath()
            for i in range(self.center_frequency_combobox.count()):
                self.center_frequency_combobox.setCurrentIndex(i)
                center_frequency = self.center_frequency_combobox.itemText(i)
                self.rm_set_center_frequency()
                for j, power in enumerate(self.power_range):
                    print(power)
                    status = '{0} {1}'.format(self.temperature, power)
                    self.status_bar.showMessage(status)
                    self.power_lineedit.setText('{0:.1f}'.format(power))
                    self.rm_set_power()
                    time.sleep(0.5)
                    self.rm_get_network_analyzer_data()
                    time.sleep(3.0)
                    self.status_bar.showMessage('Temps:{0}/{1} Powers: {2}/{3}'.format(i, n_drift_points, j, len(self.power_range)))
                    QtWidgets.QApplication.processEvents()
                    if self.stop:
                        break
            #wait_time = int(float(self.drift_scan_delay_lineedit.text()) / 60.0)
            time.sleep(5.0)
            if self.stop:
                break
        self.stop = False

    def rm_start_multitemp_scan(self):
        '''
        '''
        self.temp_scan = True
        self.drift_scan = False
        self.rm_set_all_sa_settings()
        self.rm_set_sweep_mode()
        self.stop = False
        self.delta_threshold = 1.2
        self.temperatures = []
        self.times = []
        for i, set_temperature in enumerate(self.temp_range):
            self.current_set_temperature = int(set_temperature * 1e3)
            self.delta_threshold = 0.012 * self.current_set_temperature
            self.ls_372_widget.temp_control.ls372_set_temp_set_point(set_temperature)
            temp_out_of_range = True
            wait_count = 0
            in_range_count = 0
            while temp_out_of_range:
                self.rm_get_t_bath()
                current_temp = self.temperature
                self.temperatures.append(current_temp)
                self.times.append(datetime.now())
                delta = set_temperature * 1e3 - self.temperature
                self.status_bar.showMessage('T_delta:{0:.4f}mK Current:{1:.3f}mK Set:{2:.0f}mK {3}'.format(delta, current_temp, set_temperature * 1e3, in_range_count))
                QtWidgets.QApplication.processEvents()
                if np.abs(delta) <= self.delta_threshold:
                    in_range_count += 1
                    msg = 'Under threshold waiting 1 second to check if still in range:'
                    msg += '{0}/100 checks complete. Current:{1:.1f}mK Set:{2:.1f}mK Delta:{3:.1f}mK Threshold:{4:.1f}mK'.format(in_range_count, current_temp, set_temperature * 1e3, delta, self.delta_threshold)
                    self.status_bar.showMessage(msg)
                    QtWidgets.QApplication.processEvents()
                    time.sleep(1)
                    if in_range_count > 100:
                        temp_out_of_range = False
                else:
                    time.sleep(3)
                    in_range_count = 0
                wait_count += 1
                self.rm_plot_running_temp(set_temperature)
            for i in range(self.center_frequency_combobox.count()):
                self.center_frequency_combobox.setCurrentIndex(i)
                center_frequency = self.center_frequency_combobox.itemText(i)
                self.rm_set_center_frequency()
                self.rm_get_t_bath()

                for j, power in enumerate(self.power_range):
                    current_temp = self.temperature
                    self.temperatures.append(current_temp)
                    self.times.append(datetime.now())
                    self.rm_plot_running_temp(set_temperature)
                    status = '{0} {1}'.format(set_temperature, power)
                    self.status_bar.showMessage(status)
                    self.power_lineedit.setText('{0:.1f}'.format(power))
                    self.rm_set_power()
                    time.sleep(0.5)
                    self.rm_get_network_analyzer_data()
                    time.sleep(5.0)
                    self.status_bar.showMessage('Temps:{0}/{1} Powers: {2}/{3}'.format(i, len(self.temp_range), j, len(self.power_range)))
                    QtWidgets.QApplication.processEvents()
                    if self.stop:
                        break
            if self.stop:
                break
        self.stop = False

    ############################################
    # Spectrum Analyzer

    ############################################

    def rm_err_check(self):
        '''
        '''
        err = self.bpv.inst.query("SYST:ERR?")
        if err:
          self.status_bar.showMessage(err)

    def rm_reset_network_analyzer(self):
        '''
        '''
        # ---- reset, then put instrument into network analyzer mode ----
        self.status_bar.showMessage("...reset and put instrument into network analyzer mode")
        self.bpv.inst.query("*RST; INSTrument 'NA'; *OPC?")			# set operating mode, p. 460
        time.sleep(1.0)
        self.rm_err_check()
        # ---- turn off time gating (not sure why reset does not do this) ----
        self.status_bar.showMessage("...turn off time gating")
        self.bpv.inst.query("CALCulate:FILTer:TIME:STATe 0; *OPC?")		# turn off time gating, p. 299
        time.sleep(1.0)
        self.rm_err_check()
        # ---- set up standard measurement of S21 from fstart to fstop GHz ----
        self.bpv.inst.write("CALC:PAR:DEF S21")				# measure S21
        self.bpv.inst.query("CALC:FORM MLOG; *OPC?")				# set data format to log magnitude, p. 301
        time.sleep(1.0)
        self.rm_err_check()

    def rm_set_all_sa_settings(self):
        '''
        '''
        self.rm_set_center_frequency()
        time.sleep(0.3)
        self.rm_set_frequency_span()
        time.sleep(0.3)
        self.rm_set_n_points()
        time.sleep(0.3)
        self.rm_set_n_averages()
        time.sleep(0.3)
        self.rm_set_power()
        time.sleep(0.3)

    def rm_set_center_frequency(self):
        '''
        '''
        frequency = float(self.center_frequency_combobox.currentText()) * 1e9 # GHz
        self.bpv.inst.write("FREQuency:CENTer {0:.5f}".format(frequency))

    def rm_set_frequency_span(self):
        '''
        '''
        frequency = float(self.frequency_span_lineedit.text()) * 1e6 #MHz
        self.bpv.inst.write("FREQuency:SPAN {0:.3f}".format(frequency))

    def rm_set_n_points(self):
        '''
        '''
        n_points = int(self.n_points_lineedit.text())
        self.bpv.inst.write("SWEep:POINts {0}".format(n_points))

    def rm_set_n_averages(self):
        '''
        '''
        n_averages = int(self.n_averages_lineedit.text())
        self.bpv.inst.write("AVERage:COUNt {0}".format(n_averages))

    def rm_set_power(self):
        '''
        '''
        power = float(self.power_lineedit.text())
        self.bpv.inst.write("SOURce:POWer {0:.1f}".format(power))

    def rm_set_sweep_mode(self):
        '''
        '''
        self.bpv.inst.write("FORM ASCII,0") # set format to ASCII; p. 451
        self.bpv.inst.write("CALC:PAR1:SEL") # select trace 1
        self.bpv.inst.query("INIT:CONT 1; *OPC?") # set up single sweep mode, p. 453
        # ---- set data format to log magnitude, autoscale the trace ----#
        self.bpv.inst.query("CALC:FORM MLOG; *OPC?") # set data format to log magnitude, p. 301
        time.sleep(1.)

    def rm_set_filename(self):
        '''
        '''
        if self.center_frequency_combobox.currentText() == '':
            return None
        self.rm_get_t_bath()
        sample_name = self.filename_lineedit.text()
        cent_freq = float(self.center_frequency_combobox.currentText())# GHz
        freq_span = float(self.frequency_span_lineedit.text())#MHz
        power = float(self.power_lineedit.text())
        attenuation = float(self.attenuation_lineedit.text())
        now = datetime.now()
        now_str = datetime.strftime(now, '%Y_%m_%d_%H_%M_%S')
        if np.isnan(self.temperature):
            temperature = 'nan'
            self.filename = '{0}_CF{1:.2f}GHz_Span{2:.1f}MHz_Power{3:.0f}dBm_Atten{4:.0f}_Temp{5}mK_{6}'.format(sample_name, cent_freq, freq_span, power, attenuation, temperature, now_str)
        else:
            temperature = int(np.round(self.temperature))
            self.filename = '{0}_CF{1:.2f}GHz_Span{2:.1f}MHz_Power{3:.0f}dBm_Atten{4:.0f}_Temp{5:d}mK_{6}'.format(sample_name, cent_freq, freq_span, power, attenuation, temperature, now_str)
        self.filename = self.filename.replace('.', 'p')
        self.filename += '.csv'
        if self.filename.startswith('_'):
            self.filename = self.filename[1:]
        self.filename_label.setText(self.filename)
        self.status_bar.showMessage(self.filename)

    def rm_read_set_points(self):
        '''
        '''
        rt_set_points_path = os.path.join('bd_resources', 'rm_set_points.txt')
        with open(rt_set_points_path, 'r') as fh:
            line = fh.readlines()[0]
        cf_1, cf_2, frequency_span, n_points, n_averages, power, attenuation, start_temp, end_temp = line.split(', ')
        self.center_frequency_combobox.addItem(cf_1)
        self.center_frequency_combobox.addItem(cf_2)
        self.frequency_span_lineedit.setText(frequency_span)
        self.n_points_lineedit.setText(n_points)
        self.n_averages_lineedit.setText(n_averages)
        self.power_lineedit.setText(power)
        self.attenuation_lineedit.setText(attenuation)
        self.start_temp_lineedit.setText(start_temp)
        self.end_temp_lineedit.setText(end_temp)

    def rm_write_set_points(self):
        '''
        '''
        frequency_span = self.frequency_span_lineedit.text()
        n_points = self.n_points_lineedit.text()
        n_averages = self.n_averages_lineedit.text()
        power = self.power_lineedit.text()
        attenuation = self.attenuation_lineedit.text()
        start_temp = self.start_temp_lineedit.text()
        end_temp = self.end_temp_lineedit.text()
        cf_1 = self.center_frequency_combobox.itemText(0)
        cf_2 = self.center_frequency_combobox.itemText(1)
        rt_set_points_path = os.path.join('bd_resources', 'rm_set_points.txt')
        with open(rt_set_points_path, 'w') as fh:
            line = '{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}'.format(cf_1, cf_2, frequency_span, n_points, n_averages, power, attenuation, start_temp, end_temp)
            fh.write(line)

    def rm_get_network_analyzer_data(self):
        '''
        '''
        self.rm_set_sweep_mode()
        self.rm_write_set_points()
        self.rm_set_filename()
        #---- wait for navg sweeps to complete ---- #
        n_averages = int(self.n_averages_lineedit.text())
        self.status_bar.showMessage("...clear averaging, wait for {0} sweeps to complete".format(n_averages))
        self.bpv.inst.query("AVERage:CLEar; *OPC?")
        n_acum = 0
        while n_acum < n_averages:
            #n_acum = int(self.bpv.inst.query("SENSe:AVERage:COUNt?"))
            sleep_time = float(self.time_per_average_lineedit.text()) * 1e-3
            time.sleep(sleep_time)
            self.status_bar.showMessage("{0} sweeps complete".format(n_acum))
            QtWidgets.QApplication.processEvents()
            n_acum += 1
        self.rm_err_check()
        # ---- read frequencies ----
        self.status_bar.showMessage("...reading frequencies")
        line = self.bpv.inst.query("SENS:FREQ:DATA?") # returns comma separated array of freq values; p. 638
        self.frqGHz = [ float(x)/1.e9 for x in line.split(',') ]	# convert to list of floats, in GHz
        self.rm_err_check()
        time.sleep(3)
        # ---- read S21 amplitude (log magnitude) ----
        self.status_bar.showMessage("...reading out S21 magnitudes")
        line = self.bpv.inst.query("CALCulate:DATA:FDATa?")# read selected trace data in current display format, p. 296
        self.S21amp = [ float(x) for x in line.split(',') ] # convert to list of floats
        self.rm_err_check()
        # ---- read S21 phase ----
        self.status_bar.showMessage("...switch to phase plot")
        self.bpv.inst.query("CALCulate:FORMat PHASe; *OPC?") # set data format to phase in degrees (-180 to 180), p. 301
        self.status_bar.showMessage("...reading out S21 phases")
        time.sleep(5)
        line = self.bpv.inst.query("CALCulate:DATA:FDATa?")# read selected trace data in current display format, p. 296
        self.S21phs = [ float(x) for x in line.split(',') ]# convert to list of floats
        self.rm_err_check()
        time.sleep(3)
        self.bpv.inst.query("CALC:FORM MLOG; *OPC?")# set data format to log magnitude, p. 301
        self.rm_err_check()
        self.rm_set_sweep_mode()
        self.rm_plot_data()
        time.sleep(1)
        self.rm_save_data()
        time.sleep(1)

    def rm_save_data(self):
        '''
        '''
        power = float(self.power_lineedit.text())
        if np.isnan(self.temperature):
            temperature = 'nan'
        else:
            temperature = int(np.round(self.temperature))
        if self.temp_scan:
            temperature = self.current_set_temperature
        temperature_str = 'T{0}mK'.format(temperature)
        if not os.path.exists(os.path.join(self.data_folder, temperature_str)):
            os.makedirs(os.path.join(self.data_folder, temperature_str))
        save_path = os.path.join(self.data_folder, temperature_str, self.filename)
        self.status_bar.showMessage("...writing data to file {0}".format(save_path))
        frequency_span = float(self.frequency_span_lineedit.text())
        n_points = self.n_points_lineedit.text()
        n_averages = self.n_averages_lineedit.text()
        power = float(self.power_lineedit.text())
        attenuation = float(self.attenuation_lineedit.text())
        cf = float(self.center_frequency_combobox.currentText())
        with open(save_path, "w") as fout:
            fout.write("# %s\n" % self.filename)
            fout.write("# %s\n" % time.ctime())			# write current date and time as comment
            fout.write("# VNA Power={0:.1f}dBm CF={1:.3f}GHz Span={2:.1f}Mhz Attn={3:.1f}dB Temp={4}mK\n\n".format(power, cf, frequency_span, attenuation, temperature))
            fout.write("#   fGHz        S21_dB      S21_phs\n")
            for i in range(0, len(self.frqGHz)) :
                fout.write("{0:.7f}   {1:.6f}   {2:.5f}\n".format(float(self.frqGHz[i]), float(self.S21amp[i]), float(self.S21phs[i])))
        shutil.copy(self.fig_save_path, save_path.replace('csv', 'png'))

    def rm_plot_data(self):
        '''
        '''
        frequency_span = self.frequency_span_lineedit.text()
        n_points = self.n_points_lineedit.text()
        n_averages = self.n_averages_lineedit.text()
        power = self.power_lineedit.text()
        attenuation = self.attenuation_lineedit.text()
        cf = self.center_frequency_combobox.currentText()
        line = 'CF:{0}GHz, SPAN{1}MHz, Np{2}, Na{3}, Pwr:{4}-dBm, Attn:{5}dB, T{6:.2f}mK'.format(cf, frequency_span, n_points, n_averages, power, attenuation, self.temperature)
        ax = self.fig.get_axes()[0]
        ax.cla()
        ax.set_axis_off()
        #ax.set_xlabel('Frequency (GHz)')
        ax1 = self.fig.get_axes()[0]
        ax1.set_xlabel('Frequency (GHz)')
        ax1.set_title(line)
        ax1.cla()
        ax1.set_ylabel('Amp (dBm)')
        ax1.plot(self.frqGHz, self.S21amp)
        ax2 = self.fig.get_axes()[1]
        self.fig.suptitle(line)
        ax2.set_ylabel('Phase ($^\circ$)')
        ax2.cla()
        ax2.plot(self.frqGHz, self.S21phs)
        #ax1.legend()

        self.fig_save_path = os.path.join('temp_files', 'temp_resonantor.png')
        self.fig.savefig(self.fig_save_path)
        image_to_display = QtGui.QPixmap(self.fig_save_path)
        self.data_plot_label.setPixmap(image_to_display)

    def rm_plot_running_temp(self, set_temperature):
        '''
        '''
        if not hasattr(self, 'temp_fig'):
            self.temp_fig, ax = self.mplc.mplc_create_basic_fig(
                name='x_fig',
                left=0.18,
                right=0.95,
                bottom=0.25,
                top=0.88,
                frac_screen_height=0.15,
                frac_screen_width=0.25)
        else:
            ax = self.temp_fig.get_axes()[0]
        ax.plot(self.times, self.temperatures, color='b', label='Temp')
        ax.axhline(set_temperature * 1e3, color='k', lw=3, alpha=0.5, label='Target')
        ax.axhline(set_temperature * 1e3 + self.delta_threshold, color='r', lw=3, alpha=0.75, label='Target')
        ax.axhline(set_temperature * 1e3 - self.delta_threshold, color='r', lw=3, alpha=0.75, label='Target')
        ax.set_xlabel('Time')
        ax.set_ylabel('Temp (mK)')
        self.temp_fig.savefig('temp_temps.png', transparent=True)
        image_to_display = QtGui.QPixmap('temp_temps.png')
        self.running_temp_label.setPixmap(image_to_display)
