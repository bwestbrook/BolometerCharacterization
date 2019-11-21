import sys
import imageio
import smtplib
import serial
import json
import os
import subprocess
import shutil
import time
import datetime
import numpy as np
import pylab as pl
import matplotlib.pyplot as plt
import time
import threading
from tkinter import *
from PyPDF2 import PdfFileMerger
from pprint import pprint, pformat
from datetime import datetime
from copy import copy
from PyQt5 import QtCore, QtGui, QtWidgets
from libraries.gen_class import Class
from ba_settings.all_settings import settings
from RT_Curves.plot_rt_curves import RTCurve
from IV_Curves.plot_iv_curves import IVCurve
from FTS_Curves.plot_fts_curves import FTSCurve
from FTS_Curves.numerical_processing import Fourier
from Beam_Maps.beam_mapper_tools import BeamMapperTools
from POL_Curves.plot_pol_curves import PolCurve
from TAU_Curves.plot_tau_curves import TAUCurve
from FTS_DAQ.fts_daq import FTSDAQ
from Motor_Driver.stepper_motor import stepper_motor
from FTS_DAQ.analyzeFTS import FTSanalyzer
from realDAQ.daq import DAQ
from FridgeCycle.fridge_cycle import FridgeCycle
from LockIn.lock_in import LockIn
from PowerSupply.power_supply import PowerSupply
from GuiBuilder.gui_builder import GuiBuilder


#Global variables
continue_run = False
pause_run = False
do_cycle_fridge = False
root = Tk()

class DAQGuiTemplate(QtWidgets.QWidget, GuiBuilder):


    def __init__(self, screen_resolution):
        super(DAQGuiTemplate, self).__init__()
        self.grid = QtWidgets.QGridLayout()
        self.grid.setVerticalSpacing(0)
        self.setLayout(self.grid)
        self.__apply_settings__(settings)
        self._create_main_window('daq_main_panel_widget')
        self.data_folder = './data'
        self.simulated_bands_folder = './FTS_Curves/Simulations'
        self.sample_dict_folder = './Sample_Dicts'
        self.selected_files = []
        self.current_stepper_position = 100
        self.user_desktop_path = os.path.expanduser('~')
        self.fts_analyzer = FTSanalyzer()
        self.real_daq = DAQ()
        self.active_devices = self.real_daq.get_active_devices()
        self.screen_resolution = screen_resolution
        self.monitor_dpi = 120.0
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = './Data/{0}'.format(self.today_str)
        self.squid_channels = settings.xy_collector_combobox_entry_dict['_xy_collector_popup_squid_select_combobox']
        self.voltage_conversion_list = settings.xy_collector_combobox_entry_dict['_xy_collector_popup_voltage_factor_combobox']
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        self.daq_main_panel_widget.showMaximized()
        self.active_ports = self.get_active_serial_ports()
        self.raw_data_path = None
        self.fts = FTSCurve()
        self.fourier = Fourier()
        self.loaded_spectra_data_path = None
        self._create_log()

    def __apply_settings__(self, settings):
        for setting in dir(settings):
            if '__' not in setting:
                setattr(self, setting, getattr(settings, setting))


    def _dummy(self):
        print(self.sender().whatsThis())
        print('Dummy Function')

    def _final_plot(self):
        print('Dummy Function')

    def _create_log(self):
        date_str = datetime.strftime(datetime.now(), '%Y_%m_%d')
        log_file_name = 'Data_Log_{0}.txt'.format(date_str)
        self.data_log_path = os.path.join(self.data_folder, log_file_name)
        if not os.path.exists(self.data_log_path):
            header = 'Data log for {0}\n'.format(date_str)
            with open(self.data_log_path, 'w') as data_log_handle:
                data_log_handle.write(header)

    def _update_log(self):
        if hasattr(self, 'raw_data_path') and self.raw_data_path is not None:
            temp_log_file_name = 'temp_log.txt'
            notes = self._quick_info_gather()
            with open(temp_log_file_name, 'w') as temp_log_handle:
                with open(self.data_log_path, 'r') as log_handle:
                    for line in log_handle.readlines():
                        temp_log_handle.write(line)
                    new_line = '{0}\t{1}\n'.format(self.raw_data_path[0], notes)
                    temp_log_handle.write(new_line)
            shutil.copy(temp_log_file_name, self.data_log_path)

    #################################################
    # Stepper Motor and Com ports
    #################################################

    def get_active_serial_ports(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        active_ports = ['']
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                active_ports.append(port)
            except (OSError, serial.SerialException):
                pass
        return active_ports

    def _get_com_port(self, combobox):
        com_port = str(getattr(self, combobox).currentText())
        return com_port

    def _connect_to_com_port(self, com_port=None):
        sender_whats_this_str = str(self.sender().whatsThis())
        current_string, position_string, velocity_string, acceleration_string = 'NA', 'NA', 'NA', 'NA'
        if type(self.sender()) == QtWidgets.QComboBox:
            com_port = self._get_com_port(combobox=sender_whats_this_str)
            if len(com_port) == 0:
                return None
        elif com_port is not None and type(com_port) is str:
            com_port = com_port
        else:
            message = 'Not a combobox sender and no comport explicitly specificied, no connection made'
            print(message, com_port)
            self._quick_message(message)
        if not hasattr(self, 'sm_{0}'.format(com_port)):
            setattr(self, 'sm_{0}'.format(com_port), stepper_motor(com_port))
            setattr(self, 'sm_{0}_connected'.format(com_port), True)
            current_string = getattr(self, 'sm_{0}'.format(com_port)).get_motor_current().strip('CC=')
            position_string = getattr(self, 'sm_{0}'.format(com_port)).get_position().strip('SP=')
            velocity_string = getattr(self, 'sm_{0}'.format(com_port)).get_velocity().strip('VE=')
            acceleration_string = getattr(self, 'sm_{0}'.format(com_port)).get_acceleration().strip('AC=')
        else:
            current_string, position_string, velocity_string, acceleration_string = self.last_current_string, self.last_position_string, self.last_velocity_string, self.last_acceleration_string
        if len(current_string) == 'NA' or len(current_string) == 0:
            message = 'Problem with connection to stepper motor on {0}\n'.format(com_port)
            message += 'Please check the hardware and software!\n'
            message += 'Current: {0} (A)\n'.format(current_string)
            message += 'Velocity: {0} (mm/s)\n'.format(velocity_string)
            message += 'Acceleration: {0} (mm/s/s)\n'.format(acceleration_string)
            message += 'Position: {0} (steps)\n'.format(position_string)
            self._quick_message(message)
            error = True
        else:
            message = 'Successful connection to stepper motor on {0}\n'.format(com_port)
            message += 'Current: {0} (A)\n'.format(current_string)
            message += 'Velocity: {0} (mm/s)\n'.format(velocity_string)
            message += 'Acceleration: {0} (mm/s/s)\n'.format(acceleration_string)
            message += 'Position: {0} (steps)\n'.format(position_string)
            message += 'You can change these motor stettings using the "User Move Stepper" App'
#            self._quick_message(message)
            error = False
        if 'user_move_stepper' in sender_whats_this_str and not error:
            if self._is_float(position_string):
                getattr(self, '_user_move_stepper_popup_current_position_label').setText('{0} (steps)'.format(position_string))
                getattr(self, '_user_move_stepper_popup_move_to_position_lineedit').setText('{0}'.format(position_string))
                getattr(self, '_user_move_stepper_popup_stepper_slider').setSliderPosition(int(position_string))
            if self._is_float(current_string, enforce_positive=True):
                getattr(self, '_user_move_stepper_popup_actual_current_label').setText('{0} (A)'.format(current_string))
                getattr(self, '_user_move_stepper_popup_set_current_to_lineedit').setText('{0}'.format(current_string))
            if self._is_float(velocity_string, enforce_positive=True):
                getattr(self, '_user_move_stepper_popup_actual_velocity_label').setText('{0} (mm/s)'.format(velocity_string))
                getattr(self, '_user_move_stepper_popup_set_velocity_to_lineedit').setText('{0}'.format(velocity_string))
            if self._is_float(acceleration_string, enforce_positive=True):
                getattr(self, '_user_move_stepper_popup_actual_acceleration_label').setText('{0} (mm/s/s)'.format(acceleration_string))
                getattr(self, '_user_move_stepper_popup_set_acceleration_to_lineedit').setText('{0}'.format(acceleration_string))
        elif 'single_channel_fts' in sender_whats_this_str and not error:
            if str(getattr(self, '_single_channel_fts_popup_fts_sm_com_port_combobox').currentText()) == com_port:
                getattr(self, '_single_channel_fts_popup_fts_sm_connection_status_label').setStyleSheet('QLabel {color: green}')
                getattr(self, '_single_channel_fts_popup_fts_sm_connection_status_label').setText('Ready!')
            if str(getattr(self, '_single_channel_fts_popup_grid_sm_com_port_combobox').currentText()) == com_port:
                getattr(self, '_single_channel_fts_popup_grid_sm_connection_status_label').setStyleSheet('QLabel {color: green}')
                getattr(self, '_single_channel_fts_popup_grid_sm_connection_status_label').setText('Ready!')
            if position_string != 'NA':
                getattr(self, '_single_channel_fts_popup_position_monitor_slider').setSliderPosition(int(position_string))
        self.last_current_string, self.last_position_string, self.last_velocity_string, self.last_acceleration_string = current_string, position_string, velocity_string, acceleration_string
        return current_string, position_string, velocity_string, acceleration_string

    def _verify_params(self):
        sender = str(self.sender().whatsThis())
        if '_single_channel_fts' in sender:
            meta_data = self._get_all_meta_data(popup='_single_channel_fts')
            scan_params = self._get_all_params(meta_data, settings.fts_scan_params, 'single_channel_fts')
            params_str = pformat(scan_params, indent=2)
        if '_pol_efficiency' in sender:
            meta_data = self._get_all_meta_data(popup='_pol_efficiency')
            scan_params = self._get_all_params(meta_data, settings.pol_efficiency_scan_params, 'pol_efficiency')
            params_str = pformat(scan_params, indent=2)
        response = self._quick_message(params_str, add_cancel=True, add_apply=True)
        if response == QtWidgets.QMessageBox.Cancel:
            return True
        elif response == QtWidgets.QMessageBox.Apply:
            return False

    #################################################
    # Generica Control Function (Common to all DAQ Types)
    #################################################

    def _create_sample_dict_path(self):
        self.sample_dict = {}
        total_len_of_names = 0
        for i in range(1, 7):
            widget = '_daq_main_panel_set_sample_{0}_lineedit'.format(i)
            sample_name = str(getattr(self, widget).text())
            self.sample_dict[str(i)] = sample_name
            total_len_of_names += len(sample_name)
        pump_used = str(getattr(self, '_daq_main_panel_pump_lineedit').text())
        pump_oil_level = str(getattr(self, '_daq_main_panel_pump_oil_level_lineedit').text())
        self.sample_dict['Pump Used'] = pump_used
        self.sample_dict['Pump Oil Level'] = pump_oil_level
        if len(pump_used) == 0 or len(pump_oil_level) == 0:
            self._quick_message('Please Record Pump and Oil Level\nNew info not saved!')
            return None
        sample_dict_path = './Sample_Dicts/{0}.json'.format(self.today_str)
        response = None
        if total_len_of_names == 0 and os.path.exists(sample_dict_path):
            warning_msg = 'Warning! {0} exists and you are '.format(sample_dict_path)
            warning_msg += 'going to overwrite with blank names for all channels'
            response = self._quick_info_gather(warning_msg)
            #response = self._quick_message(warning_msg, add_save=True, add_cancel=True)

            if response == QtWidgets.QMessageBox.Save:
                with open(sample_dict_path, 'w') as sample_dict_file_handle:
                    json.dump(self.sample_dict, sample_dict_file_handle)
                getattr(self, '_daq_main_panel_set_sample_dict_path_label').setText('Set Path @ {0}'.format(sample_dict_path))
        else:
            with open(sample_dict_path, 'w') as sample_dict_file_handle:
                json.dump(self.sample_dict, sample_dict_file_handle)
            getattr(self, '_daq_main_panel_set_sample_dict_path_label').setText('Set Path @ {0}'.format(sample_dict_path))

    def _set_sample_dict_path(self):
        sample_dict_path = QtWidgets.QFileDialog.getOpenFileName(self, directory=self.sample_dict_folder, filter='*.json')[0]
        if len(sample_dict_path) == 0:
            return None
        with open(sample_dict_path, 'r') as sample_dict_file_handle:
            self.sample_dict = json.load(sample_dict_file_handle)
        getattr(self, '_daq_main_panel_set_sample_dict_path_label').setText(sample_dict_path)
        getattr(self, '_daq_main_panel_set_sample_dict_path_label').setText('Set Path @ {0}'.format(sample_dict_path))
        for i in range(1, 7):
            widget = '_daq_main_panel_set_sample_{0}_lineedit'.format(i)
            sample_name = getattr(self, widget).setText(self.sample_dict[str(i)])
        if 'Pump Used' in self.sample_dict and 'Pump Oil Level' in self.sample_dict:
            getattr(self, '_daq_main_panel_pump_lineedit').setText(self.sample_dict['Pump Used'])
            getattr(self, '_daq_main_panel_pump_oil_level_lineedit').setText(self.sample_dict['Pump Oil Level'])
        else:
            getattr(self, '_daq_main_panel_pump_lineedit').setText('')
            getattr(self, '_daq_main_panel_pump_oil_level_lineedit').setText('')

    def _add_index_to_suggested_file_name(self, suggested_file_name):
        last_index = '00'
        for file_name in os.listdir(self.data_folder):
            if suggested_file_name in file_name and '.dat' in file_name:
                appendix = file_name.split(suggested_file_name)[1]
                if len(appendix) == 6:
                    last_index = appendix.replace('.dat', '')
            if suggested_file_name in file_name and '.if' in file_name:
                appendix = file_name.split(suggested_file_name)[1]
                #import ipdb;ipdb.set_trace()
                if len(appendix) == 5:
                    last_index = appendix.replace('.if', '')
        new_index = '{0}'.format(int(last_index) + 1).zfill(2)
        if 'FTS_Scan' in suggested_file_name:
            suggested_file_name = '{0}{1}.if'.format(suggested_file_name, new_index)
        else:
            suggested_file_name = '{0}{1}.dat'.format(suggested_file_name, new_index)
        return suggested_file_name

    def _get_raw_data_save_path(self):
        sender = str(self.sender().whatsThis())
        if 'xy_collector' in sender:
            run_mode = str(getattr(self, '_xy_collector_popup_mode_combobox').currentText())
            meta_data = self._get_all_meta_data(popup='xy_collector')
            plot_params = self._get_all_params(meta_data, settings.xy_collector_plot_params, 'xy_collector')
            squid = plot_params['squid_select']
            label = plot_params['sample_name']
            temp = plot_params['sample_temp'].replace('.', 'p')
            drift = plot_params['sample_drift_direction']
            optical_load = plot_params['optical_load']
            if run_mode == 'IV':
                suggested_file_name = 'SQ{0}_{1}_IVCurve_at_Tbath_{2}_w_{3}_Load_Raw_'.format(squid, label, temp, optical_load)
            elif run_mode == 'RT':
                suggested_file_name = 'SQ{0}_{1}_RTCurve_{2}_Raw_'.format(squid, label, drift)
            print(suggested_file_name)
            suggested_file_name = self._add_index_to_suggested_file_name(suggested_file_name)
            print(suggested_file_name)
            paths = [os.path.join(self.data_folder, suggested_file_name)]
        elif 'time_constant' in sender:
            plot_params = self._get_params_from_time_constant()
            squid = plot_params['squid_select']
            label = plot_params['sample_name']
            signal_voltage = plot_params['signal_voltage'].replace('.', 'p')
            voltage_bias = plot_params['voltage_bias'].replace('.', 'p')
            suggested_file_name = 'SQ{0}_{1}_TauCurve_Vbias_of_{2}uV_w_Vsignal_of_{3}V_Raw_'.format(squid, label, voltage_bias, signal_voltage)
            suggested_file_name = self._add_index_to_suggested_file_name(suggested_file_name)
            paths = [os.path.join(self.data_folder, suggested_file_name)]
        elif 'cosmic_rays' in sender:
            meta_data = self._get_all_meta_data(popup='cosmic_rays')
            plot_params = self._get_all_params(meta_data, settings.cosmic_rays_run_params, 'cosmic_rays')
            paths = []
            for i in range(1, 3):
                squid = plot_params['squid_{0}_select'.format(i)]
                label = plot_params['sample_{0}_name'.format(i)]
                now_str = datetime.strftime(datetime.now(), '%m_%d_%H_%M')
                suggested_file_name = '{0}_SQ{1}_{2}_Cosmic_Ray_Data'.format(now_str, squid, label)
                path = os.path.join(self.data_folder, suggested_file_name)
                paths.append(path)
        elif 'single_channel_fts' in sender:
            meta_data = self._get_all_meta_data(popup='single_channel_fts')
            scan_params = self._get_all_params(meta_data, settings.fts_scan_params, 'single_channel_fts')
            squid = scan_params['squid_select']
            label = scan_params['sample_name']
            resolution = scan_params['resolution']
            max_frequency = scan_params['max_frequency']
            grid_angle = scan_params['grid_angle']
            if len(grid_angle) > 0:
                suggested_file_name = 'SQ{0}_{1}_FTS_Scan Max_Freq_{2}GHz_Resolution_{3}GHz_Grid_Angle_{4}Deg_Raw_'.format(squid, label, max_frequency, resolution, grid_angle)
            else:
                suggested_file_name = 'SQ{0}_{1}_FTS_Scan Max_Freq_{2}_Resolution_{3}_Raw_'.format(squid, label, max_frequency, resolution)
            suggested_file_name = suggested_file_name.replace(' ', '_')
            suggested_file_name = self._add_index_to_suggested_file_name(suggested_file_name)
            paths = [os.path.join(self.data_folder, suggested_file_name)]
        elif 'beam_mapper' in sender:
            meta_data = self._get_all_meta_data(popup='beam_mapper')
            scan_params = self._get_all_params(meta_data, settings.beam_mapper_params, 'beam_mapper')
            squid = scan_params['squid_select']
            label = scan_params['sample_name']
            suggested_file_name = 'SQ{0}_{1}_Beam_Map_'.format(squid, label)
            suggested_file_name = suggested_file_name.replace(' ', '_')
            suggested_file_name = self._add_index_to_suggested_file_name(suggested_file_name)
            paths = [os.path.join(self.data_folder, suggested_file_name)]
        elif 'pol_efficiency' in sender:
            meta_data = self._get_all_meta_data(popup='pol_efficiency')
            scan_params = self._get_all_params(meta_data, settings.pol_efficiency_scan_params, 'pol_efficiency')
            squid = scan_params['squid_select']
            label = scan_params['sample_name']
            suggested_file_name = 'SQ{0}_{1}_Pol_Eff_'.format(squid, label)
            suggested_file_name = suggested_file_name.replace(' ', '_')
            suggested_file_name = self._add_index_to_suggested_file_name(suggested_file_name)
            paths = [os.path.join(self.data_folder, suggested_file_name)]
        self.raw_data_path = []
        self.parsed_data_path = []
        self.plotted_data_path = []
        for path in paths:
            if 'FTS_Scan' in suggested_file_name:
                data_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Raw Data Save Location', path, '.if')[0]
            else:
                data_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Raw Data Save Location', path, '.dat')[0]
            if len(data_name) > 0:
                full_path = os.path.join(self.data_folder, data_name)
                self.raw_data_path.append(full_path)
                self.plotted_data_path.append(full_path.replace('.dat', '_plotted.png'))
                self.parsed_data_path.append(full_path.replace('.dat', '_calibrated.dat'))
            else:
                self.raw_data_path = None
                self.plotted_data_path = None
                self.parsed_data_path = None

    def _get_plotted_data_save_path(self):
        data_name = str(QtWidgets.QFileDialog.getSaveFileName(self, 'Plotted Data Save Location', self.data_folder))
        self.plotted_data_path = os.path.join(self.data_folder, data_name)
        getattr(self, '_final_plot_popup_plot_path_label').setText(self.plotted_data_path)

    def _get_parsed_data_save_path(self):
        data_name = str(QtWidgets.QFileDialog.getSaveFileName(self, 'Parsed Data Save Location', self.data_folder))
        self.parsed_data_path = os.path.join(self.data_folder, data_name)
        getattr(self, '_final_plot_popup_data_path_label').setText(self.parsed_data_path)

    def _launch_daq(self):
        function_name = '_'.join(str(' ' + self.sender().text()).split(' ')).lower()
        getattr(self, function_name)()

    def populate_combobox(self, unique_combobox_name, entries):
        for entry_str in entries:
            getattr(self, unique_combobox_name).addItem(entry_str)

    def _get_all_meta_data(self, popup=None):
        if popup is None:
            popup = str(self.sender().whatsThis()).split('_popup')[0]
        widgets = []
        for widget in dir(self):
            if popup in widget:
                widgets.append(widget)
        param_data_dict = {}
        for widget in widgets:
            if hasattr(getattr(self, widget), 'text'):
                value = str(getattr(self, widget).text())
                param_data_dict[widget] = value
            elif hasattr(getattr(self, widget), 'currentText'):
                value = str(getattr(self, widget).currentText())
                param_data_dict[widget] = value
        return param_data_dict

    def _get_all_params(self, meta_data, scan_param_list, popup):
        '''
        Collect Settings from panel
        '''
        scan_params = {}
        #pprint(meta_data)
        for scan_param_widget_end in scan_param_list:
            widget = '_{0}_popup_{1}'.format(popup, scan_param_widget_end)
            scan_param = '_'.join(scan_param_widget_end.split('_')[:-1])
            #print(widget, scan_param)
            if widget in meta_data:
                value = meta_data[widget]
                scan_params[scan_param] = value
        #pprint(scan_params)
        #import ipdb;ipdb.set_trace()
        return scan_params

    def _draw_time_stream(self, data_time_stream=[], min_=0.0, max_=1.0, set_to_widget=''):
        if 'fts_' in set_to_widget:
            fig, ax = self._create_blank_fig(frac_screen_width=0.45, frac_screen_height=0.25)
            ylabel = 'Lock-in Voltage (V)'
        else:
            fig, ax = self._create_blank_fig()
            ylabel = 'SQUID Voltage (V)'
        ax.plot(data_time_stream)
        ax.set_title('Timestream')
        ax.set_xlabel('Number of Samples')
        ax.set_ylabel(ylabel)
        fig.savefig('temp_files/temp_ts.png')
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_ts.png')
        getattr(self, set_to_widget).setPixmap(image)

    def _pause(self):
        global pause_run
        if 'beam_mapper' in str(self.sender().whatsThis()):
            if str(self.sender().text()) == 'Restart':
                pause_run = False
                self.sender().setText('Pause')
            else:
                pause_run = True
                self.sender().setText('Restart')

    def _stop(self):
        global continue_run
        print(self.sender().whatsThis())
        if 'xy_collector' in str(self.sender().whatsThis()):
            getattr(self, '_xy_collector_popup_start_pushbutton').setFlat(False)
            getattr(self, '_xy_collector_popup_start_pushbutton').setText('Start')
            getattr(self, '_xy_collector_popup_save_pushbutton').setFlat(False)
        elif 'multimeter' in str(self.sender().whatsThis()):
            getattr(self, '_multimeter_popup_get_data_pushbutton').setFlat(False)
            getattr(self, '_multimeter_popup_get_data_pushbutton').setText('Get Data')
        elif 'beam_mapper' in str(self.sender().whatsThis()):
            getattr(self, '_beam_mapper_popup_start_pushbutton').setDisabled(False)
            getattr(self, '_beam_mapper_popup_status_label').setText('Scan Aborted')
        self.repaint()
        continue_run = False

    def _stop_fts(self):
        global continue_run
        continue_run = False

    def _force_min_time(self, min_value=40.0):
        value = float(str(self.sender().text()))
        if value < min_value:
            self.sender().setText(str(40))

    def _create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.3,
                          left=0.12, right=0.98, top=0.8, bottom=0.23, multiple_axes=False,
                          aspect=None):
        if frac_screen_width is None and frac_screen_height is None:
            fig = pl.figure()
        else:
            width = (frac_screen_width * float(self.screen_resolution.width())) / self.monitor_dpi
            height = (frac_screen_height * float(self.screen_resolution.height())) / self.monitor_dpi
            fig = pl.figure(figsize=(width, height))
        if not multiple_axes:
            if aspect is None:
                ax = fig.add_subplot(111)
            else:
                ax = fig.add_subplot(111, aspect=aspect)
        else:
            ax = None
        fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
        return fig, ax

    def _update_squid_calibration(self):
        combobox = self.sender()
        #import ipdb;ipdb.set_trace()
        if type(combobox) == QtWidgets.QComboBox:
            selected_squid = str(combobox.currentText())
            if selected_squid == '':
                squid_calibration = 'NaN'
            else:
                squid_calibration = settings.squid_calibration_dict[selected_squid]
            squid_str = '{0}'.format(squid_calibration)
            if 'xy_collector' in str(combobox.whatsThis()):
                getattr(self, '_xy_collector_popup_squid_conversion_label').setText(squid_str)
                if hasattr(self, 'sample_dict') > 0 and selected_squid in self.sample_dict:
                    getattr(self, '_xy_collector_popup_sample_name_lineedit').setText(self.sample_dict[selected_squid])
            elif 'time_constant' in str(combobox.whatsThis()):
                if hasattr(self, 'sample_dict') > 0 and selected_squid in self.sample_dict:
                    getattr(self, '_time_constant_popup_sample_name_lineedit').setText(self.sample_dict[selected_squid])
            elif 'cosmic_rays' in str(combobox.whatsThis()):
                if hasattr(self, 'sample_dict') > 0 and selected_squid in self.sample_dict:
                    whats_this_str = str(combobox.whatsThis())
                    if '1' in whats_this_str:
                        channel = '1'
                    elif '2' in whats_this_str:
                        channel = '2'
                    widget_name = whats_this_str.replace('squid_{0}_select_combobox'.format(channel),
                                                         'sample_{0}_name_lineedit'.format(channel))
                    getattr(self, widget_name).setText(self.sample_dict[selected_squid])
            elif 'single_channel_fts' in str(combobox.whatsThis()):
                if hasattr(self, 'sample_dict') > 0 and selected_squid in self.sample_dict:
                    whats_this_str = str(combobox.whatsThis())
                    widget_name = whats_this_str.replace('squid_select_combobox', 'sample_name_lineedit')
                    getattr(self, widget_name).setText(self.sample_dict[selected_squid])
            elif 'beam_mapper' in str(combobox.whatsThis()):
                #import ipdb;ipdb.set_trace()
                if hasattr(self, 'sample_dict') > 0 and selected_squid in self.sample_dict:
                    whats_this_str = str(combobox.whatsThis())
                    widget_name = whats_this_str.replace('squid_select_combobox', 'sample_name_lineedit')
                    getattr(self, widget_name).setText(self.sample_dict[selected_squid])
            elif 'pol_efficiency' in str(combobox.whatsThis()):
                #import ipdb;ipdb.set_trace()
                if hasattr(self, 'sample_dict') > 0 and selected_squid in self.sample_dict:
                    whats_this_str = str(combobox.whatsThis())
                    widget_name = whats_this_str.replace('squid_select_combobox', 'sample_name_lineedit')
                    getattr(self, widget_name).setText(self.sample_dict[selected_squid])

    #################################################
    # Data Analysis Integration (Common to all Data Analysis Types)
    #################################################

    def _select_analysis_type(self):
        sender_name = str(self.sender().whatsThis())
        pushbuttons = ['_data_analysis_popup_polcurve_pushbutton', '_data_analysis_popup_ivcurve_pushbutton',
                       '_data_analysis_popup_rtcurve_pushbutton', '_data_analysis_popup_ftscurve_pushbutton',
                       '_data_analysis_popup_ifcurve_pushbutton', '_data_analysis_popup_taucurve_pushbutton',
                       '_data_analysis_popup_beammap_pushbutton']
        for pushbutton in pushbuttons:
            if sender_name == pushbutton:
                self.analysis_type = pushbutton.split('_')[4]
                preset_parameters = self._get_preset_parameters()
                getattr(self, '_build_{0}_settings_popup'.format(self.analysis_type))(preset_parameters=preset_parameters)

    def _get_preset_parameters(self):
        preset_parameters = {}
        for file_path in self.selected_files:
            appendix = file_path.split('.')[-1]
            json_file_path = file_path.replace(appendix, 'json')
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r') as preset_file_handle:
                    preset_dict = json.load(preset_file_handle)
                    preset_parameters[file_path] = preset_dict
        return preset_parameters

    def _select_files(self):
        data_paths = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open file', self.data_folder)[0]
        for data_path in data_paths:
            if str(data_path) not in self.selected_files:
                self.selected_files.append(str(data_path))
        selected_files_string = ',\n'.join(self.selected_files)
        getattr(self, '_data_analysis_popup_selected_file_label').setText(selected_files_string)

    def _clear_files(self):
        self.selected_files = []
        getattr(self, '_data_analysis_popup_selected_file_label').setText('')

    def _run_analysis(self):
        if not hasattr(self, 'analysis_type'):
            getattr(self, '_data_analysis_popup_selected_file_label').setText('Please Select a Analysis Type')
        else:
            getattr(self, '_plot_{0}'.format(self.analysis_type))()

    def _add_checkboxes(self, popup_name, name, list_, row, col, squid=None, voltage_conversion=None):
        if type(list_) is dict:
            list_ = sorted(list_.keys())
        for i, item_ in enumerate(list_):
            reduced_name = name.replace(' ', '_').lower()
            if len(item_) > 0:
                unique_widget_name = '_{0}_{1}_{2}_{3}_checkbox'.format(popup_name, col, reduced_name, item_)
                function = '_select_{0}_checkbox'.format(name.replace(' ', '_')).lower()
                text = '{0} {1}'.format(name, item_)
                if 'SQUID' in name:
                    text = 'SQ{0}'.format(item_)
                widget_settings = {'text': text,
                                   'function': getattr(self, function),
                                   'position': (row, col + i, 1, 1)}
                self._create_and_place_widget(unique_widget_name, **widget_settings)
                if 'grt_res_factor_1000.' in unique_widget_name:
                    getattr(self, unique_widget_name).setCheckState(True)
                if 'sample_res_factor_1.0' in unique_widget_name:
                    getattr(self, unique_widget_name).setCheckState(True)
                if '29268' in unique_widget_name:
                    getattr(self, unique_widget_name).setCheckState(True)
                if squid is not None and squid in item_:
                    getattr(self, unique_widget_name).setCheckState(True)
                if voltage_conversion is not None and voltage_conversion in item_:
                    getattr(self, unique_widget_name).setCheckState(True)
            else:
                col -= 1
        return 1

    #################################################
    # Final Plotting and Saving (Common to all DAQ Types)
    #################################################

    def _load_plot_data(self):
        #data_folder = './Data/{0}'.format(self.today_str)
        #if not os.path.exists(data_folder):
            #data_folder = './Data'
        #data_folder = './Data/{0}'.format(self.today_str)
        #if not os.path.exists(data_folder):
        data_folder = './Data'
        self.raw_data_path = [QtWidgets.QFileDialog.getOpenFileName(self, directory=data_folder)[0]]
        self.parsed_data_path = [self.raw_data_path[0].replace('.dat', '_calibrated.dat')]
        self.plotted_data_path = [self.raw_data_path[0].replace('.dat', '_plotted.png')]
        meta_data = self._get_all_meta_data(popup='xy_collector')
        plot_params = self._get_all_params(meta_data, settings.xy_collector_plot_params, 'xy_collector')
        self.xdata, self.ydata, self.ystd = [], [], []
        with open(self.raw_data_path[0], 'r') as data_file_handle:
            for line in data_file_handle.readlines():
                line = line.replace('\n', '')
                self.xdata.append(float(line.split('\t')[0]))
                self.ydata.append(float(line.split('\t')[1]))
                self.ystd.append(float(line.split('\t')[2]))
        if plot_params['mode'] == 'IV':
            self._final_iv_plot()
        elif plot_params['mode'] == 'RT':
            self._final_rt_plot()
        else:
            print('bad mode found {0}'.format(mode))

    def _adjust_final_plot_popup(self, plot_type, title=None, xlabel=None, ylabel=None):
        if not hasattr(self, 'final_plot_popup'):
            self._create_popup_window('final_plot_popup')
        else:
            self._initialize_panel('final_plot_popup')
        self._build_panel(settings.final_plot_build_dict)
        # Fill GUI in based on sender elif above
        # Add the actual plot and save paths to the new popup
        if hasattr(self, 'temp_plot_path'):
            image = QtGui.QPixmap(self.temp_plot_path)
            getattr(self,  '_final_plot_popup_result_label').setPixmap(image)
            self.plotted_data_path = self.raw_data_path[0].replace('.dat', '_plotted.png')
            self.parsed_data_path = self.raw_data_path[0].replace('.dat', '_calibrated.dat')
            relative_plotted_data_path = '/'.join(self.plotted_data_path.split('/')[5:])
            relative_parsed_data_path = '/'.join(self.parsed_data_path.split('/')[5:])
            getattr(self, '_final_plot_popup_plot_path_label').setText(relative_plotted_data_path)
            getattr(self, '_final_plot_popup_data_path_label').setText(relative_parsed_data_path)
            if title is not None:
                getattr(self, '_final_plot_popup_plot_title_lineedit').setText(title)
            if xlabel is not None:
                getattr(self, '_final_plot_popup_x_label_lineedit').setText(xlabel)
            if ylabel is not None:
                getattr(self, '_final_plot_popup_y_label_lineedit').setText(ylabel)
            if plot_type == 'IV':
                squid_conversion = getattr(self, '_xy_collector_popup_squid_conversion_label').text()
                voltage_factor = getattr(self, '_xy_collector_popup_voltage_factor_combobox').currentText()
            elif plot_type == 'tau':
                #squid_conversion = getattr(self, '_time_constant_popup_take_data_point_pushbutton').text()
                squid_conversion = '1.0'
                voltage_factor = '1.0'
            else:
                squid_conversion = '1.0'
                voltage_factor = '1.0'
            getattr(self, '_final_plot_popup_x_conversion_label').setText(voltage_factor)
            getattr(self, '_final_plot_popup_y_conversion_label').setText(squid_conversion)
        self.final_plot_popup.setWindowTitle('Adjust Final Plot')
        self.final_plot_popup.showMaximized()

    def _close_final_plot(self):
        self.final_plot_popup.close()

    def _save_plots_and_data(self, sender=None):
        if sender is not None:
            sender = str(self.sender().whatsThis())
        if sender == '_xy_collector_popup_save_pushbutton':
            meta_data = self._get_all_meta_data(popup='xy_collector')
            plot_params = self._get_all_params(meta_data, settings.xy_collector_plot_params, 'xy_collector')
            with open(self.raw_data_path[0].replace('.dat', '.json'), 'w') as meta_data_handle:
                json.dump(meta_data, meta_data_handle)
            if plot_params['mode'] == 'IV':
                self._final_iv_plot()
            elif plot_params['mode'] == 'RT':
                self._final_rt_plot()
        elif sender == '_time_constant_popup_save_pushbutton':
            self.temp_plot_path = './temp_files/temp_tau_png.png'
            self.active_fig.savefig(self.temp_plot_path)
            title = str(self.active_fig.axes[0].title).split(',')[-1].replace(')', '')
            xlabel = self.active_fig.axes[0].get_xlabel()
            ylabel = self.active_fig.axes[0].get_ylabel()
            self._adjust_final_plot_popup('tau', title=title, xlabel=xlabel, ylabel=ylabel)
        elif sender == '_cosmic_rays_popup_save_pushbutton':
            fig, ax = self._create_blank_fig()
            data_1 = self.cr_data_1
            ax.plot(data_1)
            ax.set_xlabel('Time (ms)')
            ax.set_ylabel('SQUID Output Amplitude (V)')
            fig.savefig(self.cr_data_path_1.replace('.dat', '.png'))
            with open(self.cr_data_path_1, 'w') as fh:
                for data_point in data_1:
                    line = '{0}\n'.format(data_point)
                    fh.write(line)
            fig, ax = self._create_blank_fig()
            ax.set_xlabel('Time (ms)')
            ax.set_ylabel('SQUID Output Amplitude (V)')
            data_2 = self.cr_data_2
            ax.plot(data_2)
            fig.savefig(self.cr_data_path_2.replace('.dat', '.png'))
            with open(self.cr_data_path_2, 'w') as fh:
                for data_point in data_2:
                    line = '{0}\n'.format(data_point)
                    fh.write(line)
        elif sender == '_single_channel_fts_popup_save_pushbutton':
            if_fig, if_ax = self._create_blank_fig()
            if_xs = self.fts_positions_steps
            if_ys = self.fts_amplitudes
            if_stds = self.fts_amplitudes
            if_ax.plot(if_xs, if_ys)
            if_ax.errorbar(if_xs, if_ys, if_stds, marker=',', linestyle='None')
            #pl.show()
            print(self.raw_data_path)
            print(self.raw_data_path[0].replace('.if', '_if.png'))
            print(self.raw_data_path[0].replace('.if', '_fft.png'))
            if_fig.savefig(self.raw_data_path[0].replace('.if', '_if.png'))
            fft_fig, fft_ax = self._create_blank_fig()
            fft_fig.savefig(self.raw_data_path[0].replace('.if', '_fft.png'))
            with open(self.raw_data_path[0], 'w') as fh:
                for i, position in enumerate(if_xs):
                    amplitude = if_ys[i]
                    std = if_stds[i]
                    line = '{0}\t{1}\t{2}\n'.format(position, amplitude, std)
                    fh.write(line)
            #self._adjust_final_plot_popup('fts')
        else:
            print(sender)
            print('need to be configured')
            self._adjust_final_plot_popup('new')

    def _final_rt_plot(self):
        meta_data = self._get_all_meta_data(popup='xy_collector')
        plot_params = self._get_all_params(meta_data, settings.xy_collector_plot_params, 'xy_collector')
        rtc = RTCurve([])
        invert = getattr(self, '_xy_collector_popup_invert_output_checkbox').isChecked()
        normal_res = str(getattr(self, '_xy_collector_popup_sample_res_lineedit').text())
        if self._is_float(normal_res, enforce_positive=True):
            normal_res = float(normal_res)
        else:
            normal_res = np.nan
        title = '{0} R vs. T'.format(plot_params['label'])
        label = '{0}-{1}'.format(plot_params['label'], plot_params['drift'])
        data_clip = plot_params['data_clip']
        if len(self.xdata) > 2:
            xlim_range = max(data_clip) - min(data_clip)
            xlim = (data_clip[0] - 0.01 * xlim_range, data_clip[1] + 0.01 * xlim_range)
            input_dict = {'invert': invert, 'normal_res': normal_res, 'label': label,
                          'title': title, 'xlim': xlim}
            sample_res_vector = rtc.normalize_squid_output(self.ydata, input_dict)
            selector = np.logical_and(np.asarray(self.xdata) > data_clip[0], np.asarray(self.xdata) < data_clip[1])
            self.active_fig = rtc.plot_rt_curves(np.asarray(self.xdata)[selector], np.asarray(sample_res_vector)[selector],
                                                 in_millikelvin=True, fig=None, input_dict=input_dict)
            self.temp_plot_path = './temp_files/temp_rt_png.png'
            self.active_fig.savefig(self.temp_plot_path)
        self._adjust_final_plot_popup('RT', xlabel='Sample Temp (mK)', ylabel='Sample Res ($\Omega$)', title=title)


    def _final_iv_plot(self):
        meta_data = self._get_all_meta_data(popup='xy_collector')
        plot_params = self._get_all_params(meta_data, settings.xy_collector_plot_params, 'xy_collector')
        pprint(plot_params)
        label = plot_params['sample_name']
        fit_clip = [float(plot_params['fit_clip_lo']), float(plot_params['fit_clip_hi'])]
        data_clip = [float(plot_params['data_clip_lo']), float(plot_params['data_clip_hi'])]
        voltage_factor = float(plot_params['voltage_factor'])
        squid_conversion = float(plot_params['squid_conversion'])
        ivc = IVCurve([])
        title = '{0} @ {1} w {2} Load'.format(label, plot_params['sample_temp'], plot_params['optical_load'])
        v_bias_real, i_bolo_real, i_bolo_std = ivc.convert_IV_to_real_units(np.asarray(self.xdata), np.asarray(self.ydata),
                                                                            stds=np.asarray(self.ystd),
                                                                            squid_conv=squid_conversion,
                                                                            v_bias_multiplier=voltage_factor,
                                                                            determine_calibration=False,
                                                                            clip=fit_clip, label=label)
        if hasattr(self, 'parsed_data_path'):
            with open(self.parsed_data_path[0], 'w') as parsed_data_handle:
                for i, v_bias in enumerate(v_bias_real):
                    i_bolo = i_bolo_real[i]
                    parsed_data_line = '{0}\t{1}\t{2}\n'.format(v_bias, i_bolo, i_bolo_std)
                    parsed_data_handle.write(parsed_data_line)
            self.active_fig = ivc.plot_all_curves(v_bias_real, i_bolo_real, stds=i_bolo_std, label=label,
                                                  fit_clip=fit_clip, plot_clip=data_clip, title=title,
                                                  pturn=True)
            self.temp_plot_path = './temp_files/temp_iv_png.png'
            self.active_fig.savefig(self.temp_plot_path)
        self._adjust_final_plot_popup('IV', xlabel='Voltage ($\mu$V)', title=title)

    def _draw_final_plot(self, x, y, stds=None, save_path=None, mode=None,
                         title='Result', xlabel='', ylabel='',
                         left_m=0.1, right_m=0.95, top_m=0.80, bottom_m=0.20,
                         x_conversion_factor=1.0, y_conversion_factor=1.0):
        # Create Blank Plot Based on Monitor Size
        width = (0.8 * float(self.screen_resolution.width())) / self.monitor_dpi
        height = (0.5 * float(self.screen_resolution.height())) / self.monitor_dpi
        # Configure Plot based on plotting parameters
        #fig = pl.figure(figsize=(width, height))
        #ax = fig.add_subplot(111)
        #if stds is not None:
            #ax.errorbar(1e6 * np.asarray(x) * x_conversion_factor, np.asarray(y) * y_conversion_factor, yerr=stds)
        #else:
            #ax.plot(1e6 * np.asarray(x) * x_conversion_factor, np.asarray(y) * y_conversion_factor)
        if False:
            fig.subplots_adjust(left=left_m, right=right_m, top=top_m, bottom=bottom_m)
            ax.set_xlabel(xlabel, fontsize=14)
            ax.set_ylabel(ylabel, fontsize=14)
            ax.set_title(title, fontsize=16)
            # Plot and display it in the GUI
            temp_save_path = 'temp_files/temp_final_plot.png'
            fig.savefig(temp_save_path)
            image_to_display = QtGui.QPixmap(temp_save_path)
            getattr(self, '_final_plot_popup_result_label').setPixmap(image_to_display)
            self.repaint()
            pl.close('all')

    def _draw_beammaper_final(self,save_path=None):
        fig = pl.figure()
        ax = fig.add_subplot(111)
        ax.pcolor(self.X, self.Y, self.Z_data)
        ax.set_title('BEAM DATA', fontsize=12)
        ax.set_xlabel('Position (cm)', fontsize=12)
        ax.set_ylabel('Position (cm)', fontsize=12)
        fig.savefig('temp_files/temp_beam.png')
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_beam.png')
        image = image.scaled(600, 300)
        if save_path is not None:
            fig.savefig(save_path)
        else:
            fig.savefig('temp_files/temp_beam.png')
            image = QtGui.QPixmap('temp_files/temp_beam.png')
            image = image.scaled(800, 400)
            getattr(self,  '_final_plot_popup_result_label').setPixmap(image)
        pl.close('all')

    def _replot(self):
        if not getattr(self, '_final_plot_popup_error_bars_checkbox').isChecked():
            stds = None
        else:
            stds = self.ystd
        left_m = float(str(getattr(self, '_final_plot_popup_subplots_left_margin_lineedit').text()))
        right_m = float(str(getattr(self, '_final_plot_popup_subplots_right_margin_lineedit').text()))
        top_m = float(str(getattr(self, '_final_plot_popup_subplots_top_margin_lineedit').text()))
        bottom_m = float(str(getattr(self, '_final_plot_popup_subplots_bottom_margin_lineedit').text()))
        xlabel = str(getattr(self, '_final_plot_popup_x_label_lineedit').text())
        ylabel = str(getattr(self, '_final_plot_popup_y_label_lineedit').text())
        title = str(getattr(self, '_final_plot_popup_plot_title_lineedit').text())
        self.active_fig.subplots_adjust(left=left_m, right=right_m, top=top_m, bottom=bottom_m)
        for i, axis in enumerate(self.active_fig.axes):
            if i == 0:
                self.active_fig.axes[0].set_title(title)
        if len(self.active_fig.axes) == 1:
            axis.set_xlabel(xlabel)
            axis.set_ylabel(ylabel)
        self.active_fig.savefig(self.plotted_data_path)
        image = QtGui.QPixmap(self.plotted_data_path)
        getattr(self,  '_final_plot_popup_result_label').setPixmap(image)

    def _save_final_plot(self):
        self.active_fig.savefig(self.plotted_data_path)
        self._quick_message('Saved png to {0}'.format(self.plotted_data_path))
        if False:
            if self.is_beam:
                self._draw_beammaper_final(str(plot_path))
                self.write_file(self.X,self.Y,save_path,self.Z_data,stds=self.stds)
            elif self.is_iv:
                self._draw_final_plot(self.xdata,self.ydata,str(plot_path))
                self.write_file(self.xdata,self.ydata,save_path)
            else:
                self._draw_final_plot(self.xdata,self.ydata,str(plot_path),stds=self.stds)
                self.write_file(self.xdata,self.ydata,save_path,stds=self.stds)
            if self.is_fft:
                fft_path = str(copy(save_path)).strip('.csv')
                fft_path += '_fft.csv'
                self.write_file(self.posFreqArray,self.FTArrayPosFreq,[0]*len(self.posFreqArray),data_path = fft_path)
                filenameRoot = copy(fft_path).replace('csv','png')
                self.fts_analyzer.plotCompleteFT(self.posFreqArray,self.FTArrayPosFreq,filenameRoot)

    def write_file(self,xdata,ydata,data_path,stds=None,zdata=None):
        with open(data_path,'w') as f:
            if zdata is None:
                if stds is None:
                    for x, y in zip(xdata, ydata):
                        f.write('{:f}\t{:f}\n'.format(x, y))
                else:
                    for x, y,std in zip(xdata, ydata,stds):
                        f.write('{:f}\t{:f}\t{:f}\n'.format(x, y, std))
            else:
                for i, x in enumerate(self.x_grid):
                    for j, y in enumerate(self.y_grid):
                        f.write('{0},{1},{2},{3}\n'.format(x, y, zdata[j,i], stds[j,i]))

    def _is_float(self, value, enforce_positive=False):
        try:
            float(value)
            is_float = True
            if float(value) <= 0 and enforce_positive:
                is_float = False
        except ValueError:
            is_float = False
        return is_float

    #################################################
    #################################################
    # DAQ TYPE SPECFIC CODES
    #################################################
    #################################################

    #################################################
    # Main Window 
    #################################################

    def _create_main_window(self, name):
        self._create_popup_window(name)
        self._build_panel(settings.daq_main_panel_build_dict)

    def _close_main(self):
        self.daq_main_panel_widget.close()
        sys.exit()

    #################################################
    # Data Analyzer in 
    #################################################

    def _data_analyzer(self):
        if not hasattr(self, 'data_analysis_popup'):
            self._create_popup_window('data_analysis_popup')
        else:
            self._initialize_panel('data_analysis_popup')
        self._build_panel(settings.data_analysis_popup_build_dict)
        self.data_analysis_popup.showMaximized()

    #################################################
    # Lock in SRS SR830 DSP
    #################################################

    def _close_lock_in(self):
        self.lock_in_popup.close()

    def _sr830_dsp(self):
        if not hasattr(self, 'lock_in'):
            self.lock_in = LockIn()
        if not hasattr(self, 'lock_in_popup'):
            self._create_popup_window('lock_in_popup')
        else:
            self._initialize_panel('lock_in_popup')
        self._build_panel(settings.lock_in_popup_build_dict)
        for combobox_widget, entry_list in self.lock_in_combobox_entry_dict.items():
            self.populate_combobox(combobox_widget, entry_list)
        # Set current values to gui
        #time_constant_index = self.lock_in._get_current_time_constant()
        #getattr(self, '_lock_in_popup_lock_in_time_constant_combobox').setCurrentIndex(time_constant_index)
        getattr(self, '_lock_in_popup_lock_in_sensitivity_range_combobox').setCurrentIndex(22)
        self.lock_in_popup.showMaximized()
        self.lock_in_popup.setWindowTitle('SR830 DSP')
        self.repaint()

    def _change_lock_in_sensitivity_range(self):
        if 'combobox' in str(self.sender().whatsThis()):
            new_value = int(getattr(self, '_lock_in_popup_lock_in_sensitivity_range_combobox').currentText())
            self.lock_in._change_lock_in_sensitivity_range(setting=new_value)
        elif 'down' in str(self.sender().whatsThis()):
            self.lock_in._change_lock_in_sensitivity_range(direction='down')
        else:
            self.lock_in._change_lock_in_sensitivity_range(direction='up')

    def _change_lock_in_time_constant(self):
        if 'combobox' in str(self.sender().whatsThis()):
            new_value = int(getattr(self, '_lock_in_popup_lock_in_time_constant_combobox').currentText())
            self.lock_in._change_lock_in_time_constant(setting=new_value)
        elif 'down' in str(self.sender().whatsThis()):
            self.lock_in._change_lock_in_time_constant(direction='down')
        else:
            self.lock_in._change_lock_in_time_constant(direction='up')

    def _zero_lock_in_phase(self):
        self.lock_in._zero_lock_in_phase()

    #################################################
    # Power Supply Agilent E3634A
    #################################################

    def _close_power_supply(self):
        self.power_supply_popup.close()

    def _e3634a(self):
        if not hasattr(self, 'ps'):
            self.ps = PowerSupply()
        if not hasattr(self, 'power_supply_popup'):
            self._create_popup_window('power_supply_popup')
        else:
            self._initialize_panel('power_supply_popup')
        self._build_panel(settings.power_supply_popup_build_dict)
        #for combobox_widget, entry_list in self.power_supply_combobox_entry_dict.items():
            #self.populate_combobox(combobox_widget, entry_list)
        #voltage_to_set, voltage_to_set_str = self.ps.get_voltage()
        #if voltage_to_set < 0:
            #voltage_to_set, voltage_to_set_str = 0.0, '0.0'
        #self._set_ps_voltage(voltage_to_set=voltage_to_set)
        #getattr(self, '_power_supply_popup_set_voltage_lineedit').setText(voltage_to_set_str)
        self.power_supply_popup.showMaximized()
        self.power_supply_popup.setWindowTitle('Agilent E3634 A')
        self.repaint()

    def _set_ps_voltage(self, voltage_to_set=None):
        if voltage_to_set is None or type(voltage_to_set) is bool:
            voltage_to_set = getattr(self, '_power_supply_popup_set_voltage_lineedit').text()
        if self._is_float(voltage_to_set, enforce_positive=True):
            self.ps.apply_voltage(float(voltage_to_set))
            set_voltage, set_voltage_str = self.ps.get_voltage()
            if float(voltage_to_set) < 10:
                getattr(self, '_power_supply_popup_which_squid_label').setText('SQUID 1')
            else:
                getattr(self, '_power_supply_popup_which_squid_label').setText('SQUID 2')
            getattr(self, '_power_supply_popup_set_voltage_label').setText(set_voltage_str)
            getattr(self, '_power_supply_popup_voltage_control_dial').setSliderPosition(int(voltage_to_set))

    def _set_ps_voltage_dial(self):
        dial_value = float(getattr(self, '_power_supply_popup_voltage_control_dial').value())
        getattr(self, '_power_supply_popup_test2_label').setText(str(dial_value))
        self._set_ps_voltage(dial_value)

    #################################################
    # Fridge Cycle
    #################################################

    def _close_fridge_cycle(self):
        self.fridge_cycle_popup.close()

    def _fridge_cycle(self):
        if not hasattr(self, 'fc'):
            self.fc = FridgeCycle()
        if not hasattr(self, 'fridge_cycle_popup'):
            self._create_popup_window('fridge_cycle_popup')
        else:
            self._initialize_panel('fridge_cycle_popup')
        self._build_panel(settings.fridge_cycle_popup_build_dict)
        for combobox_widget, entry_list in self.fridge_cycle_combobox_entry_dict.items():
            self.populate_combobox(combobox_widget, entry_list)
        getattr(self, '_fridge_cycle_popup_grt_daq_channel_combobox').setCurrentIndex(0)
        getattr(self, '_fridge_cycle_popup_grt_serial_combobox').setCurrentIndex(2)
        getattr(self, '_fridge_cycle_popup_grt_range_combobox').setCurrentIndex(3)
        getattr(self, '_fridge_cycle_popup_cycle_voltage_combobox').setCurrentIndex(1)
        getattr(self, '_fridge_cycle_popup_cycle_end_temperature_combobox').setCurrentIndex(2)
        self.fc_time_stamp_vector, self.ps_voltage_vector, self.abr_resistance_vector, self.abr_temperature_vector, self.grt_temperature_vector = [], [], [], [], []
        self.fridge_cycle_popup.showMaximized()
        fc_params = self._get_params_from_fride_cycle()
        # Update with measured values
        grt_temperature, grt_temperature_str = self._get_grt_temp(fc_params)
        getattr(self, '_fridge_cycle_popup_grt_temperature_value_label').setText(grt_temperature_str)
        abr_resistance, abr_resistance_str = self.fc.get_resistance()
        getattr(self, '_fridge_cycle_popup_abr_resistance_value_label').setText(abr_resistance_str)
        abr_temperature, abr_temperature_str = self.fc.abr_resistance_to_kelvin(abr_resistance)
        getattr(self, '_fridge_cycle_popup_abr_temperature_value_label').setText(abr_temperature_str)
        applied_voltage, applied_voltage_str = self.fc.get_voltage()
        getattr(self, '_fridge_cycle_popup_ps_voltage_value_label').setText(applied_voltage_str)
        self._update_fridge_cycle()
        self.repaint()

    def _get_fridge_cycle_save_path(self):
        date = datetime.now()
        date_str = datetime.strftime(date, '%Y_%m_%d_%H_%M')
        for i in range(1, 10):
            data_path = './FridgeCycles/fc_{0}_{1}.dat'.format(date_str, str(i).zfill(2))
            if not os.path.exists(data_path):
                break
        return data_path

    def _get_grt_temp(self, fc_params):
        grt_data, grt_data_mean, grt_data_min, grt_data_max, grt_data_std = self.real_daq.get_data(signal_channel=fc_params['grt_daq_channel'],
                                                                                                   integration_time=100,
                                                                                                   sample_rate=1000,
                                                                                                   active_devices=[self.active_devices[0]])
        rtc = RTCurve([])
        voltage_factor = float(self.multimeter_voltage_factor_range_dict[fc_params['grt_range']])
        grt_serial = fc_params['grt_serial']
        temperature_array, is_valid = rtc.resistance_to_temp_grt(grt_data * voltage_factor, serial_number=grt_serial)
        if is_valid:
            temperature = np.mean(1e3 * temperature_array)
        else:
            self._quick_message('GRT config is not correct assuming 1000 Ohms')
        if self._is_float(temperature, enforce_positive=True):
            temperature_str = '{0:.3f} mK'.format(temperature)
        else:
            temperature_str = 'NaN'
        pprint(fc_params)
        print(np.mean(grt_data), voltage_factor, grt_serial, temperature, temperature_str)
        #import ipdb;ipdb.set_trace()
        return temperature, temperature_str

    def _set_ps_voltage_fc(self):
        voltage = float(str(getattr(self, '_fridge_cycle_popup_man_set_voltage_lineedit').text()))
        applied_voltage = self.fc.apply_voltage(voltage)
        return applied_voltage

    def _start_fridge_cycle(self, sleep_time=1.0):
        # Config globals
        global do_cycle_fridge
        self.aborted_cycle = False
        do_cycle_fridge = True
        # Get essential FC params
        fc_params = self._get_params_from_fride_cycle()
        charcoal_start_resistance = float(fc_params['charcoal_start_resistance'])
        charcoal_end_resistance = float(fc_params['charcoal_end_resistance'])
        cycle_end_temperature = float(fc_params['cycle_end_temperature'])
        # Set Data Path
        data_path = self._get_fridge_cycle_save_path()
        self._quick_message('Saving data to {0}'.format(data_path))
        fig = None
        with open(data_path, 'w') as fc_file_handle:
            # Get new data 
            data_line = self._check_cycle_stage_and_update_data(fc_params, data_path, sleep_time)
            print(data_line)
            fc_file_handle.write(data_line)
            self._update_fridge_cycle(data_path=data_path)
            # Update status
            status = 'Cooling ABR before heating'
            getattr(self, '_fridge_cycle_popup_status_label').setText(status)
            # Check ABR Res to Start While Loop
            abr_resistance, abr_resistance_str = self.fc.get_resistance()
            while abr_resistance < charcoal_start_resistance and do_cycle_fridge:
                # Get new data 
                data_line = self._check_cycle_stage_and_update_data(fc_params, data_path, sleep_time)
                fc_file_handle.write(data_line)
                # Check ABR Res
                abr_resistance, abr_resistance_str = self.fc.get_resistance()
            if do_cycle_fridge:
                # Update Status
                status = 'Charcoal has reached {0} turning on voltage'.format(charcoal_start_resistance)
                getattr(self, '_fridge_cycle_popup_status_label').setText(status)
                # Turn on voltage in steps of 1 volt over with a sleep between
                for i in range(0, int(fc_params['cycle_voltage']) + 1, 5):
                    # Apply voltage and update gui
                    applied_voltage = self.fc.apply_voltage(i)
                    getattr(self, '_fridge_cycle_popup_ps_voltage_value_label').setText(str(applied_voltage))
                    # Get new data 
                    data_line = self._check_cycle_stage_and_update_data(fc_params, data_path, sleep_time)
                    fc_file_handle.write(data_line)
                # Update Status
                status = 'Charcoal being heated: Voltage to heater set to {0} V'.format(i)
                getattr(self, '_fridge_cycle_popup_status_label').setText(status)
            # Check ABR Res to Start While Loop
            abr_resistance, abr_resistance_str = self.fc.get_resistance()
            while abr_resistance > charcoal_end_resistance and do_cycle_fridge:
                # Get new data 
                data_line = self._check_cycle_stage_and_update_data(fc_params, data_path, sleep_time)
                fc_file_handle.write(data_line)
                # Check ABR Res
                abr_resistance, abr_resistance_str = self.fc.get_resistance()
            status = 'Charcoal reached {0} turning off voltage and cooling stage'.format(abr_resistance)
            getattr(self, '_fridge_cycle_popup_status_label').setText(status)
            self.fc.apply_voltage(0)
            getattr(self, '_fridge_cycle_popup_ps_voltage_value_label').setText('0')
            # Record the data until grt reaches base temp 
            grt_temperature, grt_temperature_str = self._get_grt_temp(fc_params)
            while grt_temperature > cycle_end_temperature and do_cycle_fridge:
                # Get new data 
                data_line = self._check_cycle_stage_and_update_data(fc_params, data_path, sleep_time)
                fc_file_handle.write(data_line)
                # Check GRT Temp 
                grt_temperature, grt_temperature_str = self._get_grt_temp(fc_params)
            if self.aborted_cycle:
                status = 'Previous Cycle Aborted, Idle'
                getattr(self, '_fridge_cycle_popup_status_label').setText(status)
            else:
                status = 'Stage has reached {0}, cycle finished'.format(grt_temperature_str)
                getattr(self, '_fridge_cycle_popup_status_label').setText(status)
            do_cycle_fridge = False
            root.update()

    def _check_cycle_stage_and_update_data(self, fc_params, data_path, sleep_time):
        # Update ABR resistance
        abr_resistance, abr_resistance_str = self.fc.get_resistance()
        getattr(self, '_fridge_cycle_popup_abr_resistance_value_label').setText(abr_resistance_str)
        abr_temperature, abr_temperature_str = self.fc.abr_resistance_to_kelvin(abr_resistance)
        getattr(self, '_fridge_cycle_popup_abr_temperature_value_label').setText(abr_temperature_str)
        # Update ABR temperature
        abr_resistance, abr_resistance_str = self.fc.get_resistance()
        getattr(self, '_fridge_cycle_popup_abr_resistance_value_label').setText(abr_resistance_str)
        # Update temp
        grt_temperature, grt_temperature_str = self._get_grt_temp(fc_params)
        getattr(self, '_fridge_cycle_popup_grt_temperature_value_label').setText(grt_temperature_str)
        # Update voltage
        applied_voltage, applied_voltage_str = self.fc.get_voltage()
        getattr(self, '_fridge_cycle_popup_ps_voltage_value_label').setText(applied_voltage_str)
        # Update time stamp
        time_stamp = datetime.now()
        time_stamp = datetime.strftime(time_stamp, '%Y_%m_%d_%H_%M_%S')
        # Add and plot data
        self.fc_time_stamp_vector.append(time_stamp)
        self.ps_voltage_vector.append(applied_voltage)
        self.abr_resistance_vector.append(abr_resistance)
        self.abr_temperature_vector.append(abr_temperature)
        self.grt_temperature_vector.append(grt_temperature)
        self._update_fridge_cycle(data_path=data_path)
        # Write Data 
        data_line = '{0}\t{1}\t{2}\t{3}\t{4}\n'.format(time_stamp, abr_resistance, abr_temperature, applied_voltage, grt_temperature)
        # Update Gui and Sleep
        root.update()
        self.repaint()
        time.sleep(sleep_time)
        return data_line

    def _stop_fridge_cycle(self):
        if hasattr(self, 'fc'):
            self.fc.apply_voltage(0)
        global do_cycle_fridge
        do_cycle_fridge = False
        self.aborted_cycle = True
        self.fc_time_stamp_vector, self.ps_voltage_vector, self.abr_resistance_vector, self.grt_temperature_vector = [], [], [], []
        root.update()

    def _get_params_from_fride_cycle(self):
        params = {}
        grt_daq_channel = str(getattr(self, '_fridge_cycle_popup_grt_daq_channel_combobox').currentText())
        grt_serial = str(getattr(self, '_fridge_cycle_popup_grt_serial_combobox').currentText())
        grt_range = str(getattr(self, '_fridge_cycle_popup_grt_range_combobox').currentText())
        ps_voltage = str(getattr(self, '_fridge_cycle_popup_ps_voltage_value_label').text())
        abr_resistance = str(getattr(self, '_fridge_cycle_popup_abr_resistance_value_label').text())
        grt_temperature = str(getattr(self, '_fridge_cycle_popup_grt_temperature_value_label').text())
        charcoal_start_resistance = str(getattr(self, '_fridge_cycle_popup_start_resistance_lineedit').text())
        charcoal_end_resistance = str(getattr(self, '_fridge_cycle_popup_end_resistance_lineedit').text())
        cycle_voltage = str(getattr(self, '_fridge_cycle_popup_cycle_voltage_combobox').currentText())
        cycle_end_temperature = str(getattr(self, '_fridge_cycle_popup_cycle_end_temperature_combobox').currentText())
        params.update({'grt_daq_channel': grt_daq_channel})
        params.update({'grt_serial': grt_serial})
        params.update({'grt_range': grt_range})
        params.update({'ps_voltage': ps_voltage})
        params.update({'abr_resistance': abr_resistance})
        params.update({'grt_temperature': grt_temperature})
        params.update({'charcoal_start_resistance': charcoal_start_resistance})
        params.update({'charcoal_end_resistance': charcoal_end_resistance})
        params.update({'cycle_voltage': cycle_voltage})
        params.update({'cycle_end_temperature': cycle_end_temperature})
        return params

    def _update_fridge_cycle(self, data_path=None):
        fc_params = self._get_params_from_fride_cycle()
        fig, ax = self._create_blank_fig(frac_screen_width=0.75, frac_screen_height=0.7,
                                         left=0.08, right=0.98, top=0.9, bottom=0.1,
                                         multiple_axes=True)
        ax1 = fig.add_subplot(411)
        ax2 = fig.add_subplot(412)
        ax3 = fig.add_subplot(413)
        ax4 = fig.add_subplot(414)
        time_stamp_vector = [datetime.strptime(x, '%Y_%m_%d_%H_%M_%S') for x in self.fc_time_stamp_vector]
        ax1.plot(time_stamp_vector, self.ps_voltage_vector, color='r', label='PS Voltage (V)')
        date = datetime.strftime(datetime.now(), '%Y_%m_%d')
        ax1.set_title('576 Fridge Cycle {0}'.format(date))
        ax1.set_ylabel('PS Voltage (V)')
        ax1.set_ylim([0, 26])
        ax2.plot(time_stamp_vector, self.abr_temperature_vector, color='g', label='ABR Temp (K)')
        ax2.set_ylabel('ABR Temp (K)')
        ax2.axhline(float(self.fc.abr_resistance_to_kelvin(float(fc_params['charcoal_end_resistance']))[0]), color='b', label='ABR End')
        ax2.axhline(float(self.fc.abr_resistance_to_kelvin(float(fc_params['charcoal_start_resistance']))[0]), color='m', label='ABR Start')
        ax3.plot(time_stamp_vector, np.asarray(self.abr_resistance_vector) * 1e-3, color='k', label='GRT Temp (mK)')
        ax3.axhline(float(fc_params['charcoal_end_resistance']) * 1e-3, color='b', label='ABR End')
        ax3.axhline(float(fc_params['charcoal_start_resistance']) * 1e-3, color='m', label='ABR Start')
        ax3.set_ylabel('ABR Res (kOhms)')
        ax4.plot(time_stamp_vector, self.grt_temperature_vector, color='c', label='GRT Temp (mK)')
        ax4.axhline(float(fc_params['cycle_end_temperature']), color='b', label='Approx GRT Base')
        ax4.set_ylabel('GRT Temp (mK)')
        ax4.set_xlabel('Time Stamps')
        # Add legends
        handles, labels = ax1.get_legend_handles_labels()
        ax1.legend(handles, labels, numpoints=1)
        handles, labels = ax2.get_legend_handles_labels()
        ax2.legend(handles, labels, numpoints=1)
        handles, labels = ax3.get_legend_handles_labels()
        ax3.legend(handles, labels, numpoints=1)
        if data_path is not None:
            save_path = data_path.replace('.dat', '.png')
        else:
            save_path = 'temp_files/temp_fc.png'
        pl.legend()
        fig.savefig(save_path)
        pl.cla()
        pl.close('all')
        image_to_display = QtGui.QPixmap(save_path)
        getattr(self, '_fridge_cycle_popup_fridge_cycle_plot_label').setPixmap(image_to_display)
        self.repaint()


    #################################################
    # MULTIMETER
    #################################################

    def _multimeter(self):
        '''
        Opens the panel
        '''
        if not hasattr(self, 'multimeter_popup'):
            self._create_popup_window('multimeter_popup')
        else:
            self._initialize_panel('multimeter_popup')
        self._build_panel(settings.multimeter_popup_build_dict)
        for combobox_widget, entry_list in self.multimeter_combobox_entry_dict.items():
            self.populate_combobox(combobox_widget, entry_list)
        getattr(self, '_multimeter_popup_daq_channel_1_combobox').setCurrentIndex(2)
        getattr(self, '_multimeter_popup_daq_channel_2_combobox').setCurrentIndex(3)
        getattr(self, '_multimeter_popup_daq_sample_rate_1_combobox').setCurrentIndex(2)
        getattr(self, '_multimeter_popup_daq_sample_rate_2_combobox').setCurrentIndex(2)
        getattr(self, '_multimeter_popup_daq_integration_time_1_combobox').setCurrentIndex(0)
        getattr(self, '_multimeter_popup_daq_integration_time_2_combobox').setCurrentIndex(0)
        getattr(self, '_multimeter_popup_grt_range_1_combobox').setCurrentIndex(3)
        getattr(self, '_multimeter_popup_grt_range_2_combobox').setCurrentIndex(3)
        self.multimeter_popup.showMaximized()
        self.multimeter_popup.setWindowTitle('Mulitmeter')

    def _close_multimeter(self):
        '''
        Closes the panel with a warning if data is being collected
        '''
        global continue_run
        if continue_run:
            self._quick_message('Taking data!!!\nPlease stop taking data before closing XY Collector!')
        else:
            self.multimeter_popup.close()
            continue_run = False

    def _update_multimeter(self, channel='1', title='', xlabel='', ylabel=''):
        '''
        Updates the panel with DAQ output
        '''
        fig, ax = self._create_blank_fig()
        grt_serial = str(getattr(self, '_multimeter_popup_grt_serial_{0}_combobox'.format(channel)).currentText())
        grt_range = str(getattr(self, '_multimeter_popup_grt_range_{0}_combobox'.format(channel)).currentText())
        if len(grt_serial) > 1:
            rtc = RTCurve([])
            voltage_factor = float(self.multimeter_voltage_factor_range_dict[grt_range])
            temp_data, is_valid = 1e3 * rtc.resistance_to_temp_grt(self.mm_data * voltage_factor, serial_number=grt_serial)
            ax.plot(temp_data)
            temp_data_std = np.std(temp_data)
            temp_data_mean = np.mean(temp_data)
            getattr(self, '_multimeter_popup_data_point_mean_{0}_label'.format(channel)).setText('{0:.4f} mK'.format(temp_data_mean))
            getattr(self, '_multimeter_popup_data_point_std_{0}_label'.format(channel)).setText('{0:.4f} mK'.format(temp_data_std))
            unit = 'mK'
        else:
            ax.plot(self.mm_data)
            getattr(self, '_multimeter_popup_data_point_mean_{0}_label'.format(channel)).setText('{0:.4f}'.format(self.mm_mean))
            getattr(self, '_multimeter_popup_data_point_std_{0}_label'.format(channel)).setText('{0:.4f}'.format(self.mm_data_std))
            unit = 'V'
        ax.set_title(title, fontsize=10)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel('CH{0} Output ({1})'.format(channel, unit), fontsize=10)
        save_path = 'temp_files/temp_mm.png'
        fig.savefig(save_path)
        pl.close('all')
        image_to_display = QtGui.QPixmap(save_path)
        getattr(self, '_multimeter_popup_data_point_monitor_{0}_label'.format(channel)).setPixmap(image_to_display)
        self.repaint()

    def _take_multimeter_data_point(self):
        global continue_run
        continue_run = True
        daq_channel_1 = getattr(self,'_multimeter_popup_daq_channel_1_combobox').currentText()
        integration_time_1 = int(float(str(getattr(self, '_multimeter_popup_daq_integration_time_1_combobox').currentText())))
        sample_rate_1 = int(float(str(getattr(self, '_multimeter_popup_daq_sample_rate_1_combobox').currentText())))
        daq_channel_2 = getattr(self,'_multimeter_popup_daq_channel_2_combobox').currentText()
        integration_time_2 = int(float(str(getattr(self, '_multimeter_popup_daq_integration_time_2_combobox').currentText())))
        sample_rate_2 = int(float(str(getattr(self, '_multimeter_popup_daq_sample_rate_2_combobox').currentText())))
        getattr(self, '_multimeter_popup_get_data_pushbutton').setFlat(True)
        getattr(self, '_multimeter_popup_get_data_pushbutton').setText('Acquiring Data')
        while continue_run:
            self.mm_data, self.mm_mean, self.mm_data_min, self.mm_data_max, self.mm_data_std = self.real_daq.get_data(signal_channel=daq_channel_1,
                                                                                                                      integration_time=integration_time_1,
                                                                                                                      sample_rate=sample_rate_1,
                                                                                                                      active_devices=self.active_devices)

            self._update_multimeter(channel='1')
            self.mm_data, self.mm_mean, self.mm_data_min, self.mm_data_max, self.mm_data_std = self.real_daq.get_data(signal_channel=daq_channel_2,
                                                                                                                      integration_time=integration_time_2,
                                                                                                                      sample_rate=sample_rate_2,
                                                                                                                      active_devices=self.active_devices)
            self._update_multimeter(channel='2')
            root.update()

    #################################################
    # COSMIC RAYS
    #################################################

    def _close_cosmic_rays(self):
        self.cosmic_rays_popup.close()

    def _cosmic_rays(self):
        if not hasattr(self, 'cosmic_rays_popup'):
            self._create_popup_window('cosmic_rays_popup')
        else:
            self._initialize_panel('cosmic_rays_popup')
        self._build_panel(settings.cosmic_rays_build_dict)
        for combobox_widget, entry_list in self.cosmic_rays_combobox_entry_dict.items():
            self.populate_combobox(combobox_widget, entry_list)
        self.cosmic_rays_popup.showMaximized()
        for i in range(1, 3):
            getattr(self, '_cosmic_rays_popup_daq_{0}_sample_rate_combobox'.format(i)).setCurrentIndex(2)
            getattr(self, '_cosmic_rays_popup_daq_{0}_integration_time_combobox'.format(i)).setCurrentIndex(0)
        getattr(self, '_cosmic_rays_popup_daq_channel_1_combobox').setCurrentIndex(2)
        getattr(self, '_cosmic_rays_popup_daq_channel_2_combobox').setCurrentIndex(3)

    def _draw_cr_timestream(self, data, channel, sub_file_path, title='', xlabel='', ylabel='', save_data=True):
        fig, ax = self._create_blank_fig()
        ax.plot(data)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        save_path = 'temp_files/temp_cr.png'
        fig.savefig(save_path)
        pl.close('all')
        image_to_display = QtGui.QPixmap(save_path)
        if save_data:
            with open(sub_file_path, 'w') as save_handle:
                for data_point in data:
                    line = '{0:.6f}\n'.format(data_point)
                    save_handle.write(line)
            shutil.copy(save_path, sub_file_path.replace('.dat', '.png'))
        getattr(self, '_cosmic_rays_popup_data_{0}_label'.format(channel)).setPixmap(image_to_display)

    def _run_cosmic_rays(self):
        global continue_run
        continue_run = True
        self._get_raw_data_save_path()
        if self.raw_data_path is not None:
            while continue_run:
                meta_data = self._get_all_meta_data(popup='cosmic_rays')
                params = self._get_all_params(meta_data, settings.cosmic_rays_run_params, 'cosmic_rays')
                for i in range(len(self.raw_data_path)):
                    if not os.path.exists(self.raw_data_path[i]):
                        os.makedirs(self.raw_data_path[i])
                number_of_data_files = int(params['number_of_data_files'])
                for j in range(number_of_data_files):
                    sub_file_path_1 = os.path.join(self.raw_data_path[0], '{0}.dat'.format(str(j).zfill(4)))
                    sub_file_path_2 = os.path.join(self.raw_data_path[1], '{0}.dat'.format(str(j).zfill(4)))
                    daq_channel_1 = params['daq_channel_1']
                    integration_time_1 = params['daq_1_integration_time']
                    sample_rate_1 = params['daq_1_sample_rate']
                    daq_channel_2 = params['daq_channel_2']
                    integration_time_2 = params['daq_2_integration_time']
                    sample_rate_2 = params['daq_2_sample_rate']
                    data_1, mean_1, min_1, max_1, std_1 = self.real_daq.get_data(signal_channel=daq_channel_1,
                                                                                 integration_time=integration_time_1,
                                                                                 sample_rate=sample_rate_1,
                                                                                 active_devices=self.active_devices)
                    data_2, mean_2, min_2, max_2, std_2 = self.real_daq.get_data(signal_channel=daq_channel_2,
                                                                                 integration_time=integration_time_2,
                                                                                 sample_rate=sample_rate_2,
                                                                                 active_devices=self.active_devices)
                    getattr(self, '_cosmic_rays_popup_data_1_std_label').setText('{0:.3f}'.format(std_1))
                    getattr(self, '_cosmic_rays_popup_data_2_std_label').setText('{0:.3f}'.format(std_2))
                    getattr(self, '_cosmic_rays_popup_data_1_mean_label').setText('{0:.3f}'.format(mean_1))
                    getattr(self, '_cosmic_rays_popup_data_2_mean_label').setText('{0:.3f}'.format(mean_2))
                    self._draw_cr_timestream(data_1, '1', sub_file_path_1,
                                             title='CR Timestream {0}'.format(params['sample_1_name']),
                                             ylabel='SQUID Output Voltage', xlabel='Time (ms)', save_data=True)
                    self._draw_cr_timestream(data_2, '2', sub_file_path_2,
                                             title='CR Timestream {0}'.format(params['sample_2_name']),
                                             ylabel='SQUID Output Voltage', xlabel='Time (ms)', save_data=True)
                    status_msg = 'Finished {0} of {1}'.format(j + 1, number_of_data_files)
                    getattr(self, '_cosmic_rays_popup_status_label').setText(status_msg)
                    self.repaint()
                    root.update()
                    if j + 1 == number_of_data_files:
                        continue_run = False
        delattr(self, 'raw_data_path')
        self._update_log()

    #################################################
    # XY COLLECTOR
    #################################################

    def _close_xy_collector(self):
        '''
        Closes the panel with a warning if data is being collected
        '''
        global continue_run
        if continue_run:
            self._quick_message('Taking data!!!\nPlease stop taking data before closing XY Collector!')
        else:
            self.xy_collector_popup.close()
            continue_run = False

    def _xy_collector(self):
        '''
        Opens the panel and sets som defaults
        '''
        if not hasattr(self, 'xy_collector_popup'):
            self._create_popup_window('xy_collector_popup')
        else:
            self._initialize_panel('xy_collector_popup')
        self._build_panel(settings.xy_collector_build_dict)
        for combobox_widget, entry_list in self.xy_collector_combobox_entry_dict.items():
            self.populate_combobox(combobox_widget, entry_list)
        self.xy_collector_popup.showMaximized()
        self.xy_collector_popup.setWindowTitle('XY COLLECTOR')
        getattr(self, '_xy_collector_popup_daq_channel_x_combobox').setCurrentIndex(2)
        getattr(self, '_xy_collector_popup_daq_channel_y_combobox').setCurrentIndex(3)
        self.xdata = np.asarray([])
        self.ydata = np.asarray([])
        self.xstd = np.asarray([])
        self.ystd = np.asarray([])
        self._update_in_xy_mode()
        self._update_squid_calibration()
        getattr(self, '_xy_collector_popup_fit_clip_lo_lineedit').setText(str(self.ivcurve_plot_settings_dict['fit_clip_lo']))
        getattr(self, '_xy_collector_popup_fit_clip_hi_lineedit').setText(str(self.ivcurve_plot_settings_dict['fit_clip_hi']))
        getattr(self, '_xy_collector_popup_data_clip_lo_lineedit').setText(str(self.ivcurve_plot_settings_dict['data_clip_lo']))
        getattr(self, '_xy_collector_popup_data_clip_hi_lineedit').setText(str(self.ivcurve_plot_settings_dict['data_clip_hi']))
        getattr(self, '_xy_collector_popup_daq_sample_rate_combobox').setCurrentIndex(4)
        getattr(self, '_xy_collector_popup_sample_temp_combobox').setCurrentIndex(3)
        getattr(self, '_xy_collector_popup_grt_range_combobox').setCurrentIndex(3)
        getattr(self, '_xy_collector_popup_include_errorbars_checkbox').setChecked(True)


    def _draw_x(self, title='', xlabel='', ylabel=''):
        '''
        Draws the x timestream and paints it to the panel
        '''
        fig, ax = self._create_blank_fig()
        ax.plot(self.xdata)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        save_path = 'temp_files/temp_xv.png'
        fig.savefig(save_path)
        pl.close('all')
        image_to_display = QtGui.QPixmap(save_path)
        getattr(self, '_xy_collector_popup_xdata_label').setPixmap(image_to_display)

    def _draw_y(self, title='', xlabel='', ylabel=''):
        '''
        Draws the Y timestream and paints it to the panel
        '''
        e_bars = getattr(self, '_xy_collector_popup_include_errorbars_checkbox').isChecked()
        fig, ax = self._create_blank_fig()
        ax.plot(self.ydata)
        if e_bars:
            ax.errorbar(range(len(self.ydata)), self.ydata, self.ystd, marker='.', linestyle='None')
        ax.set_title(title, fontsize=10)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        save_path = 'temp_files/temp_yv.png'
        fig.savefig(save_path)
        pl.close('all')
        image_to_display = QtGui.QPixmap(save_path)
        getattr(self, '_xy_collector_popup_ydata_label').setPixmap(image_to_display)

    def _draw_xy_collector(self, title='', xlabel='', ylabel='', x_voltage_uV_plotting_factor=10):
        '''
        Draws the X-Y scatter plott and paints it to the panel
        '''
        e_bars = getattr(self, '_xy_collector_popup_include_errorbars_checkbox').isChecked()
        fig, ax = self._create_blank_fig()
        ax.plot(self.xdata * x_voltage_uV_plotting_factor, self.ydata)
        if e_bars:
            ax.errorbar(self.xdata * x_voltage_uV_plotting_factor, self.ydata, self.ystd, marker='.', linestyle='None')
        ax.set_title(title, fontsize=10)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        save_path = 'temp_files/temp_iv.png'
        fig.savefig(save_path)
        pl.close('all')
        image_to_display = QtGui.QPixmap(save_path)
        getattr(self, '_xy_collector_popup_xydata_label').setPixmap(image_to_display)
        self.repaint()

    def _get_params_from_xy_collector(self, meta_data):
        '''
        Collects the parameters from the panel
        '''
        mode = str(getattr(self, '_xy_collector_popup_mode_combobox').currentText())
        voltage_factor = float(str(getattr(self, '_xy_collector_popup_voltage_factor_combobox').currentText()))
        squid = str(getattr(self, '_xy_collector_popup_squid_select_combobox').currentText())
        squid_conversion = str(getattr(self, '_xy_collector_popup_squid_conversion_label').text())
        if len(squid_conversion) > 0:
            squid_conversion = float(squid_conversion.split(' ')[0])
        else:
            squid_conversion = 1.0
        label = str(getattr(self, '_xy_collector_popup_sample_name_lineedit').text())
        fit_clip_lo = float(str(getattr(self, '_xy_collector_popup_fit_clip_lo_lineedit').text()))
        fit_clip_hi = float(str(getattr(self, '_xy_collector_popup_fit_clip_hi_lineedit').text()))
        data_clip_lo = float(str(getattr(self, '_xy_collector_popup_data_clip_lo_lineedit').text()))
        data_clip_hi = float(str(getattr(self, '_xy_collector_popup_data_clip_hi_lineedit').text()))
        e_bars = getattr(self, '_xy_collector_popup_include_errorbars_checkbox').isChecked()
        temp = str(getattr(self, '_xy_collector_popup_sample_temp_combobox').currentText())
        drift = str(getattr(self, '_xy_collector_popup_sample_drift_direction_combobox').currentText())
        optical_load = str(getattr(self, '_xy_collector_popup_optical_load_combobox').currentText())
        grt_serial = str(getattr(self, '_xy_collector_popup_grt_serial_combobox').currentText())
        fit_clip = (fit_clip_lo, fit_clip_hi)
        data_clip = (data_clip_lo, data_clip_hi)
        return {'mode': mode, 'squid': squid, 'squid_conversion': squid_conversion, 'grt_serial': grt_serial,
                'voltage_factor': voltage_factor, 'label': label, 'temp': temp, 'drift': drift,
                'fit_clip': fit_clip, 'data_clip': data_clip, 'e_bars': e_bars,
                'optical_load': optical_load}

    def _update_in_xy_mode(self, dummy=None, voltage_factor='1e-5'):
        '''
        Updats the panel with new defaults
        '''
        run_mode = str(getattr(self, '_xy_collector_popup_mode_combobox').currentText())
        if run_mode == 'IV':
            if voltage_factor == '1e-5':
                x_voltage_uV_plotting_factor = 10
            elif voltage_factor == '1e-4':
                x_voltage_uV_plotting_factor = 100
            else:
                import ipdb;ipdb.set_trace()
            if hasattr(self, 'xdata'):
                self._draw_x(title='X data', xlabel='Sample', ylabel='Bias Voltage @ Box (V)')
                self._draw_y(title='Y data', xlabel='Sample', ylabel='SQUID Output Voltage (V)')
                self._draw_xy_collector(title='IV Curve', xlabel='Bias Voltage @ TES ($\mu$V)', ylabel='SQUID Output Voltage (V)',
                                        x_voltage_uV_plotting_factor=x_voltage_uV_plotting_factor)
                if len(self.xdata) == 0:
                    getattr(self, '_xy_collector_popup_voltage_factor_combobox').setCurrentIndex(0)
        elif run_mode == 'RT':
            if len(self.xdata) == 0:
                getattr(self, '_xy_collector_popup_voltage_factor_combobox').setCurrentIndex(3)
                getattr(self, '_xy_collector_popup_invert_output_checkbox').setChecked(True)
                getattr(self, '_xy_collector_popup_sample_res_lineedit').setText('1.0')
                getattr(self, '_xy_collector_popup_daq_channel_x_combobox').setCurrentIndex(5)
                getattr(self, '_xy_collector_popup_daq_channel_y_combobox').setCurrentIndex(3)
                getattr(self, '_xy_collector_popup_voltage_factor_combobox').setCurrentIndex(1)
                getattr(self, '_xy_collector_popup_data_clip_lo_lineedit').setText(str(250))
                getattr(self, '_xy_collector_popup_data_clip_hi_lineedit').setText(str(600))
            self._draw_x(title='X data', xlabel='Sample', ylabel='GRT Temp (mK)')
            self._draw_y(title='Y data', xlabel='Sample', ylabel='SQUID Output Voltage (V)')
            self._draw_xy_collector(title='RT Curve', xlabel='GRT Temp (mK)', ylabel='SQUID Output Voltage (V)')
        else:
            self._draw_xy_collector()

    def _run_xy_collector(self):
        '''
        Starts the data collection
        '''
        global continue_run
        continue_run = True
        self._get_raw_data_save_path()
        meta_data = self._get_all_meta_data(popup='xy_collector')
        if self.raw_data_path is not None:
            start_time = datetime.now()
            sender_text = str(self.sender().text())
            self.sender().setFlat(True)
            getattr(self, '_xy_collector_popup_save_pushbutton').setFlat(True)
            self.sender().setText('Taking Data')
            daq_channel_x = getattr(self,'_xy_collector_popup_daq_channel_x_combobox').currentText()
            daq_channel_y = getattr(self, '_xy_collector_popup_daq_channel_y_combobox').currentText()
            integration_time = int(float(str(getattr(self, '_xy_collector_popup_daq_integration_time_combobox').currentText())))
            sample_rate = int(float(str(getattr(self, '_xy_collector_popup_daq_sample_rate_combobox').currentText())))
            voltage_factor = str(getattr(self, '_xy_collector_popup_voltage_factor_combobox').currentText())
            self.xdata, self.ydata, self.xstd, self.ystd = np.asarray([]), np.asarray([]), np.asarray([]), np.asarray([])
            run_mode = str(getattr(self, '_xy_collector_popup_mode_combobox').currentText())
            first_x_point = 1.0
            last_time = start_time
            if run_mode == 'RT':
                rtc = RTCurve([])
                grt_range = str(getattr(self, '_xy_collector_popup_grt_range_combobox').currentText())
                grt_serial = str(getattr(self, '_xy_collector_popup_grt_serial_combobox').currentText())
                voltage_factor = float(self.multimeter_voltage_factor_range_dict[grt_range])
                first_x_point = 600
            with open(self.raw_data_path[0].replace('.dat', '.json'), 'w') as meta_data_handle:
                json.dump(meta_data, meta_data_handle)
            with open(self.raw_data_path[0], 'w') as data_handle:
                while continue_run:
                    data_time = datetime.now()
                    tot_elapsed_time = data_time - start_time
                    data_point_elapsed_time = last_time - data_time
                    tot_time_str = str(tot_elapsed_time.seconds)
                    data_point_time_str = str(data_point_elapsed_time.microseconds * 1e-6) # s
                    x_data, x_mean, x_min, x_max, x_std = self.real_daq.get_data(signal_channel=daq_channel_x,
                                                                                 integration_time=integration_time,
                                                                                 sample_rate=sample_rate,
                                                                                 active_devices=self.active_devices)
                    y_data, y_mean, y_min, y_max, y_std = self.real_daq.get_data(signal_channel=daq_channel_y,
                                                                                 integration_time=integration_time,
                                                                                 sample_rate=sample_rate,
                                                                                 active_devices=self.active_devices)
                    if run_mode == 'IV' and x_mean < 0.0:
                        x_mean *= -1
                        x_data = x_data -2 * x_data
                    if run_mode == 'RT':
                        if 3.0 < x_mean * voltage_factor < 600:
                            if grt_serial != '':
                                x_data, is_valid = 1e3 * rtc.resistance_to_temp_grt(x_data * voltage_factor, serial_number=grt_serial)
                        #else:
                            #x_data = [np.nan]
                        x_mean = np.mean(x_data)
                        x_min = np.min(x_data)
                        x_max = np.max(x_data)
                        x_std = np.std(x_data)
                    delta_x = x_mean - first_x_point
                    slew_rate = '{0:.2f} mK/s'.format(delta_x / float(data_point_time_str))
                    if run_mode == 'IV':
                        slew_rate = slew_rate.replace('mK', 'uV')
                    getattr(self, '_xy_collector_popup_data_time_label').setText(tot_time_str)
                    getattr(self, '_xy_collector_popup_data_rate_label').setText(slew_rate)
                    self.xdata = np.append(self.xdata, x_mean)
                    self.ydata = np.append(self.ydata, y_mean)
                    self.xstd = np.append(self.xstd, x_std)
                    self.ystd = np.append(self.ystd, y_std)
                    getattr(self, '_xy_collector_popup_xdata_mean_label').setText('{0:.4f}'.format(x_mean))
                    getattr(self, '_xy_collector_popup_xdata_std_label').setText('{0:.4f}'.format(x_std))
                    getattr(self, '_xy_collector_popup_ydata_mean_label').setText('{0:.4f}'.format(y_mean))
                    getattr(self, '_xy_collector_popup_ydata_std_label').setText('{0:.4f}'.format(y_std))
                    data_line = '{0}\t{1}\t{2}\n'.format(x_mean, y_mean, y_std)
                    data_handle.write(data_line)
                    self._update_in_xy_mode(voltage_factor=voltage_factor)
                    first_x_point = x_mean
                    last_time = data_time
                    root.update()
        self._update_log()
        self._update_fit_data(voltage_factor)

    def _update_fit_data(self, voltage_factor):
        '''
        Updates fit limits based on IV data
        '''
        fit_clip_hi = self.xdata[0] * float(voltage_factor) * 1e6 # uV
        data_clip_lo = self.xdata[-1] * float(voltage_factor) * 1e6 + self.data_clip_offset # uV
        data_clip_hi = fit_clip_hi # uV
        fit_clip_lo = data_clip_lo + self.fit_clip_offset # uV
        getattr(self, '_xy_collector_popup_data_clip_hi_lineedit').setText('{0:.3f}'.format(data_clip_hi))
        getattr(self, '_xy_collector_popup_data_clip_lo_lineedit').setText('{0:.3f}'.format(data_clip_lo))
        getattr(self, '_xy_collector_popup_fit_clip_lo_lineedit').setText('{0:.3f}'.format(fit_clip_lo))
        getattr(self, '_xy_collector_popup_fit_clip_hi_lineedit').setText('{0:.3f}'.format(fit_clip_hi))

    #################################################
    # TIME CONSTANT 
    #################################################

    def _plot_tau_data_point(self, ydata):
        integration_time = int(float(str(getattr(self, '_time_constant_popup_daq_integration_time_combobox').currentText())))
        sample_rate = int(float(str(getattr(self, '_time_constant_popup_daq_sample_rate_combobox').currentText())))
        fig, ax = self._create_blank_fig()
        ax.plot(ydata)
        ax.set_ylabel('Channel Voltage Output (V)')
        ax.set_xlabel('Time (ms)')
        temp_tau_save_path = './temp_files/temp_tau_data_point.png'
        fig.savefig(temp_tau_save_path)
        image_to_display = QtGui.QPixmap(temp_tau_save_path)
        getattr(self, '_time_constant_popup_data_point_monitor_label').setPixmap(image_to_display)

    def _plot_time_constant(self, real_data=True):
        # Grab input from the Time Constant Popup
        plot_params = self._get_params_from_time_constant()
        label = plot_params['label']
        voltage_bias = plot_params['voltage_bias']
        signal_voltage = plot_params['signal_voltage']
        # Use The Tc library to plot the restul
        fig, ax = self._create_blank_fig()
        tc = TAUCurve([])
        color = 'r'
        if real_data:
            freq_vector, amp_vector, error_vector = tc.load(self.raw_data_path[0])
            freq_vector, amp_vector, tau_in_hertz, tau_in_ms, idx = tc.get_3db_point(freq_vector, amp_vector)
            fig, ax = tc.plot(freq_vector, amp_vector, error_vector, idx, fig=fig, ax=ax,
                              tau_in_hertz=tau_in_hertz, color=color)
            f_0_guess = tau_in_hertz
            amp_0_guess = 1.0
            if len(freq_vector) >= 2 and ((max(freq_vector) - min(freq_vector)) >=2):
                fit_params = tc.fit_single_pol(freq_vector, amp_vector / amp_vector[0],
                                               fit_params=[amp_0_guess, f_0_guess])
                test_freq_vector = np.arange(1.0, 250, 0.1)
                fit_amp = tc.test_single_pol(test_freq_vector, fit_params[0], fit_params[1])
                fit_3db_data = tc.get_3db_point(test_freq_vector, fit_amp)
                fit_3db_point_hz = fit_3db_data[2]
                fit_3db_point = 1e3 / (2 * np.pi * fit_3db_point_hz)
                fit_idx = fit_3db_data[-1]
                fig.subplots_adjust(left=0.1, right=0.95, top=0.82, bottom=0.2)
                ax.plot(test_freq_vector[fit_idx], fit_amp[fit_idx],
                        marker='*', ms=15.0, color=color, alpha=0.5, lw=2)
                label = '$\\tau$={0:.2f} ms ({1} Hz) @ $V_b$={2}$\mu$V $V_S$={3}$V$'.format(fit_3db_point, fit_3db_point_hz,
                                                                                             voltage_bias, signal_voltage)
                ax.plot(test_freq_vector, fit_amp, color=color, alpha=0.7, label=label)
            title = 'Response Amplitude vs Frequency\n{0}'.format(plot_params['label'])
            ax.set_title(title)
            ax.legend()
            fig.savefig(self.plotted_data_path[0])
            image_to_display = QtGui.QPixmap(self.plotted_data_path[0])
            getattr(self, '_time_constant_popup_all_data_monitor_label').setPixmap(image_to_display)
            self.temp_plot_path = self.plotted_data_path
            self.active_fig = fig
        else:
            ax.plot(0.0, 0.0, color=color, alpha=0.7, label=label)
            fig.savefig('./blank_fig.png')
            image_to_display = QtGui.QPixmap('./blank_fig.png')
            getattr(self, '_time_constant_popup_all_data_monitor_label').setPixmap(image_to_display)

    def _delete_last_point(self):
        if not hasattr(self, 'raw_data_path'):
            self._quick_message(msg='Please set a data Path First')
        else:
            if os.path.exists(self.raw_data_path[0]):
                with open(self.raw_data_path[0], 'r') as data_handle:
                    existing_lines = data_handle.readlines()
            if len(existing_lines) == 0:
                self._quick_message(msg='You must take at least one data point to delete the last one!')
            else:
                with open(self.raw_data_path[0], 'w') as data_handle:
                    for line in existing_lines[:-1]:
                        data_handle.write(line)
                self._plot_time_constant()

    def _close_time_constant(self):
        '''
        Closes the panel with a warning if data is being collected
        '''
        global continue_run
        if continue_run:
            self._quick_message('Taking data!!!\nPlease stop taking data before closing Time Constant!')
        else:
            self.time_constant_popup.close()
            continue_run = False

    def _clear_time_constant_data(self):
        self._plot_tau_data_point([])
        self._plot_time_constant(real_data=False)
        delattr(self, 'raw_data_path')

    def _get_params_from_time_constant(self):
        squid = str(getattr(self, '_time_constant_popup_squid_select_combobox').currentText())
        label = str(getattr(self, '_time_constant_popup_sample_name_lineedit').text())
        signal_voltage = str(getattr(self, '_time_constant_popup_signal_voltage_lineedit').text())
        voltage_bias = str(getattr(self, '_time_constant_popup_voltage_bias_lineedit').text())
        frequency = str(getattr(self, '_time_constant_popup_frequency_select_combobox').currentText())
        return {'squid': squid, 'voltage_bias': voltage_bias,
                'signal_voltage': signal_voltage, 'label': label,
                'frequency': frequency}

    def _take_time_constant_data_point(self):
        if hasattr(self, 'raw_data_path') and self.raw_data_path is not None:
            print('Active Data Path Found')
            print(self.raw_data_path[0])
        else:
            self._get_raw_data_save_path()
        if self.raw_data_path is not None:
            # check if the file exists and append it
            if os.path.exists(self.raw_data_path[0]):
                with open(self.raw_data_path[0], 'r') as data_handle:
                    existing_lines = data_handle.readlines()
            else:
                existing_lines = []
            # Grab new data
            daq_channel = getattr(self,'_time_constant_popup_daq_select_combobox').currentText()
            integration_time = int(float(str(getattr(self, '_time_constant_popup_daq_integration_time_combobox').currentText())))
            sample_rate = int(float(str(getattr(self, '_time_constant_popup_daq_sample_rate_combobox').currentText())))
            y_data, y_mean, y_min, y_max, y_std = self.real_daq.get_data(signal_channel=daq_channel,
                                                                         integration_time=integration_time,
                                                                         sample_rate=sample_rate,
                                                                         active_devices=self.active_devices)
            frequency = float(str(getattr(self, '_time_constant_popup_frequency_select_combobox').currentText()))
            data_line = '{0}\t{1}\t{2}\n'.format(frequency, y_mean, y_std)
            # Append the data and rewrite to file
            existing_lines.append(data_line)
            with open(self.raw_data_path[0], 'w') as data_handle:
                for line in existing_lines:
                    data_handle.write(line)
            getattr(self, '_time_constant_popup_data_point_mean_label').setText('{0:.3f}'.format(y_mean))
            getattr(self, '_time_constant_popup_data_point_std_label').setText('{0:.3f}'.format(y_std))
            self._plot_tau_data_point(y_data)
            self._plot_time_constant()

    def _time_constant(self):
        if not hasattr(self, 'time_constant_popup'):
            self._create_popup_window('time_constant_popup')
        else:
            self._initialize_panel('time_constant_popup')
        self._build_panel(settings.time_constant_popup_build_dict)
        for combobox_widget, entry_list in self.time_constant_combobox_entry_dict.items():
            self.populate_combobox(combobox_widget, entry_list)
        getattr(self, '_time_constant_popup_daq_select_combobox').setCurrentIndex(0)
        getattr(self, '_time_constant_popup_daq_sample_rate_combobox').setCurrentIndex(2)
        getattr(self, '_time_constant_popup_daq_integration_time_combobox').setCurrentIndex(4)
        self._plot_tau_data_point([])
        self._plot_time_constant(real_data=False)
        self.time_constant_popup.showMaximized()

    #################################################
    # USER MOVE STEPPER
    #################################################

    def _close_user_move_stepper(self):
        '''
        Closes the panel
        '''
        self.user_move_stepper_popup.close()

    def _user_move_stepper(self):
        if not hasattr(self, 'user_move_stepper_popup'):
            self._create_popup_window('user_move_stepper_popup')
        else:
            self._initialize_panel('user_move_stepper_popup')
        self._build_panel(settings.user_move_stepper_build_dict)
        for unique_combobox, entries in settings.user_move_stepper_combobox_entry_dict.items():
            self.populate_combobox(unique_combobox, entries)
        getattr(self, '_user_move_stepper_popup_com_ports_combobox').setCurrentIndex(0)
        self.user_move_stepper_popup.setWindowTitle('User Move Stepper')
        self.user_move_stepper_popup.showMaximized()

    def _add_comports_to_user_move_stepper(self):
        for i, com_port in enumerate(settings.com_ports):
            com_port_entry = QtCore.QString(com_port)
            getattr(self, '_user_move_stepper_popup_com_ports_combobox').addItem(com_port_entry)

    def _set_acceleration(self):
        com_port = self._get_com_port('_user_move_stepper_popup_com_ports_combobox')
        acceleration =  str(getattr(self, '_user_move_stepper_popup_set_acceleration_to_lineedit').text())
        getattr(self, 'sm_{0}'.format(com_port)).set_acceleration(float(acceleration))
        actual = getattr(self, 'sm_{0}'.format(com_port)).get_acceleration().strip('AC=')
        getattr(self,'_user_move_stepper_popup_actual_acceleration_label').setText('{0} (mm/s/s)'.format(str(actual)))
        self.last_acceleration_string = actual

    def _set_velocity(self):
        com_port = self._get_com_port('_user_move_stepper_popup_com_ports_combobox')
        velocity =  str(getattr(self, '_user_move_stepper_popup_set_velocity_to_lineedit').text())
        getattr(self, 'sm_{0}'.format(com_port)).set_velocity(float(velocity))
        actual = getattr(self, 'sm_{0}'.format(com_port)).get_velocity().strip('VE=')
        getattr(self,'_user_move_stepper_popup_actual_velocity_label').setText('{0} (mm/s/s)'.format(str(actual)))
        self.last_velocity_string = actual

    def _set_current(self):
        com_port = self._get_com_port('_user_move_stepper_popup_com_ports_combobox')
        current =  getattr(self, '_user_move_stepper_popup_set_current_to_lineedit').text()
        getattr(self, 'sm_{0}'.format(com_port)).set_current(float(current))
        actual =  getattr(self, 'sm_{0}'.format(com_port)).get_motor_current().strip('CC=')
        getattr(self,'_user_move_stepper_popup_actual_current_label').setText('{0} (mm/s/s)'.format(str(actual)))
        self.last_current_string = actual

    def _limit_current(self):
        value = str(self.sender().text())
        if self._is_float(value, enforce_positive=True):
            value = float(str(self.sender().text()))
            if value > 4.0:
                value = 4.0
                self.sender().setText(str(value))

    def _move_stepper(self):
        move_to_pos = int(str(getattr(self, '_user_move_stepper_popup_move_to_position_lineedit').text()))
        current_pos = str(getattr(self, '_user_move_stepper_popup_current_position_label').text())
        current_pos = int(current_pos.replace(' (steps)', ''))
        move_delta = move_to_pos - current_pos
        com_port = self._get_com_port('_user_move_stepper_popup_com_ports_combobox')
        getattr(self, 'sm_{0}'.format(com_port)).move_to_position(move_to_pos)
        self._update_stepper_position(move_to_pos)

    def _reset_stepper_zero(self):
        com_port = self._get_com_port('_user_move_stepper_popup_com_ports_combobox')
        getattr(self, 'sm_{0}'.format(com_port)).reset_zero()
        stepper_position = getattr(self, 'sm_{0}'.format(com_port)).get_position().replace('SP=', '')
        self._update_stepper_position()
        getattr(self, '_user_move_stepper_popup_move_to_position_lineedit').setText('0')

    def _update_stepper_position(self, move_to_pos=None):
        com_port = self._get_com_port('_user_move_stepper_popup_com_ports_combobox')
        stepper_position = getattr(self, 'sm_{0}'.format(com_port)).get_position().strip('SP=')
        if not self._is_float(stepper_position):
            stepper_position = move_to_pos
        header_str = '{0} (steps)'.format(stepper_position)
        getattr(self, '_user_move_stepper_popup_stepper_slider').setSliderPosition(int(stepper_position))
        getattr(self, '_user_move_stepper_popup_current_position_label').setText(header_str)
        self.last_position_string = stepper_position

    #################################################
    # POL EFFICIENCY
    #################################################

    def _close_pol_efficiency(self):
        '''
        Closes the panel with a warning if data is being collected
        '''
        global continue_run
        if continue_run:
            self._quick_message('Taking data!!!\nPlease stop taking data before closing Pol Efficiency!')
        else:
            self.pol_efficiency_popup.close()
            continue_run = False

    def _pol_efficiency(self):
        if not hasattr(self, 'lock_in'):
            self.lock_in = LockIn()
        if not hasattr(self, 'pol_efficiency_popup'):
            self._create_popup_window('pol_efficiency_popup')
        else:
            self._initialize_panel('pol_efficiency_popup')
        self._build_panel(settings.pol_efficiency_build_dict)
        for combobox_widget, entry_list in self.pol_efficiency_combobox_entry_dict.items():
            self.populate_combobox(combobox_widget, entry_list)
        self._update_pol_efficiency()
        self.pol_efficiency_popup.showMaximized()
        getattr(self, '_pol_efficiency_popup_verify_parameters_checkbox').setChecked(True)
        getattr(self, '_pol_efficiency_popup_signal_channel_combobox').setCurrentIndex(2)
        getattr(self, '_pol_efficiency_popup_pause_time_combobox').setCurrentIndex(2)
        self.pol_efficiency_popup.setWindowTitle('Polarization Efficiency')

    def _update_pol_efficiency(self):
        meta_data = self._get_all_meta_data(popup='_pol_efficiency')
        scan_params = self._get_all_params(meta_data, settings.pol_efficiency_scan_params, 'pol_efficiency')
        if type(scan_params) is not dict:
            return None
        if 'starting_position' in scan_params and 'ending_position' in scan_params and 'step_size' in scan_params:
            start_angle = scan_params['starting_position']
            end_angle = scan_params['ending_position']
            step_size = scan_params['step_size']
            print(start_angle, end_angle, step_size)
            print(self._is_float(start_angle), self._is_float(end_angle), self._is_float(step_size, enforce_positive=True))
            if self._is_float(step_size, enforce_positive=True)\
                    and self._is_float(start_angle)\
                    and self._is_float(end_angle):
                num_steps = (int(end_angle) - int(start_angle)) / int(step_size)
                print(num_steps)
                getattr(self,'_pol_efficiency_popup_number_of_steps_label').setText(str(num_steps))
                getattr(self,'_pol_efficiency_popup_position_slider_min_label').setText(str(start_angle))
                getattr(self,'_pol_efficiency_popup_position_slider_max_label').setText(str(end_angle))
                getattr(self, '_pol_efficiency_popup_position_monitor_slider').setMinimum(int(start_angle))
                getattr(self, '_pol_efficiency_popup_position_monitor_slider').setMaximum(int(end_angle))
            else:
                num_steps = 'NaN'
            getattr(self,'_pol_efficiency_popup_number_of_steps_label').setText(str(num_steps))
            getattr(self,'_pol_efficiency_popup_position_slider_min_label').setText(str(start_angle))
            getattr(self,'_pol_efficiency_popup_position_slider_max_label').setText(str(end_angle))
        self.pol_efficiency_popup.repaint()

    def get_simulated_data(self, datatype, current_position, noise=10):
        '''
        noise is in percent and is of the max-min of data
        '''
        in_degree = current_position*np.pi/180
        dev = (np.random.randn()-0.5)*2/100*noise
        simulated_data = np.sin(in_degree) + dev
        return simulated_data

    def _run_pol_efficiency(self, resume_run=False):
        '''
        Execute a data taking run
        '''
        global continue_run
        continue_run = True
        meta_data = self._get_all_meta_data(popup='pol_efficiency')
        scan_params = self._get_all_params(meta_data, settings.pol_efficiency_scan_params, 'pol_efficiency')
        # Verify params via popu first
        if getattr(self, '_pol_efficiency_popup_verify_parameters_checkbox').isChecked():
            cancel_run = self._verify_params()
            if cancel_run:
                continue_run = False
                return None
        pause = float(scan_params['pause_time']) / 1e3
        self._get_raw_data_save_path()
        if (self.raw_data_path is not None and len(scan_params['signal_channel']) > 0):
            x_data, y_data, error_data = [], [], []
            start_time = datetime.now()
            start_time_str = datetime.strftime(start_time, '%H:%M')
            x_positions = np.arange(int(scan_params['starting_position']), int(scan_params['ending_position']) + int(scan_params['step_size']), int(scan_params['step_size']))
            with open(self.raw_data_path[0].replace('.dat', '.json'), 'w') as meta_data_handle:
                json.dump(meta_data, meta_data_handle)
            with open(self.raw_data_path[0], 'w') as pc_save_handle:
                i = 0
                while continue_run and i < len(x_positions):
                    x_pos = x_positions[i]
                    getattr(self, '_pol_efficiency_popup_position_monitor_slider').setSliderPosition(x_pos)
                    self.repaint()
                    getattr(self, 'sm_{0}'.format(scan_params['sm_com_port'])).move_to_position(x_pos)
                    self.lock_in._zero_lock_in_phase()
                    time.sleep(pause)
                    data_time_stream, mean, min_, max_, std = self.real_daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                                                                     sample_rate=scan_params['sample_rate'], active_devices=self.active_devices)
                    # Update data point info
                    std_pct = 100 * (std / mean)
                    std_pct = '({0:.2f}'.format(std_pct)
                    std_pct += '%)'
                    now_time = datetime.now()
                    now_time_str = datetime.strftime(now_time, '%H:%M')
                    duration = now_time - start_time
                    time_per_step = duration.seconds / (i + 1)
                    steps_left = len(x_positions) - i
                    time_left = time_per_step * steps_left / 60
                    getattr(self, '_pol_efficiency_popup_mean_label').setText('{0:.4f}'.format(mean))
                    getattr(self, '_pol_efficiency_popup_std_label').setText('{0:.4f} {1}'.format(std, std_pct))
                    getattr(self, '_pol_efficiency_popup_current_position_label').setText('{0:.3f} [{1}/{2} complete]'.format(x_pos, i, len(x_positions) - 1))
                    status_str = 'Start: {0} ::::: Tot Duration: {1} (s) ::::: Time Per Step {2:.2f} (s) ::::: Estimated Time Left: {3:.2f} (m)'.format(start_time_str, duration.seconds,
                                                                                                                                                        time_per_step, time_left)
                    getattr(self, '_pol_efficiency_popup_duration_label').setText(status_str)
                    self._draw_time_stream(data_time_stream, min_, max_, '_pol_efficiency_popup_time_stream_label')
                    # Update IF plots and vectors
                    x_data.append(x_pos)
                    y_data.append(mean)
                    error_data.append(std)
                    data_dict = {'x_position': x_data, 'amplitude': y_data, 'error': error_data}
                    self._plot_pol_efficiency(data_dict, scan_params['sample_name'])
                    # Update IF linearity info
                    min_, max_ = np.min(y_data), np.mean(y_data)
                    min_over_max = min_ / max_
                    getattr(self, '_pol_efficiency_popup_min_max_label').setText('Min: {0:.2f} Max: {1:.2f}'.format(min_, max_))
                    getattr(self, '_pol_efficiency_popup_min_over_max_label').setText('{0:.3f} %'.format(1e2 * min_over_max))
                    # Save the data
                    data_line ='{0}\t{1}\t{2}\n'.format(x_pos, mean, std)
                    pc_save_handle.write(data_line)
                    # Update the FFT of the data
                    i += 1
                    root.update()
        continue_run = False
        self._update_log()

    def _plot_pol_efficiency(self, data_dict, sample_name):
        if not hasattr(self, 'pc'):
            self.pc = PolCurve()
        fig, ax = self._create_blank_fig(left=0.06, right=0.95, top=0.9, bottom=0.15)
        if len(data_dict['x_position']) > 5 and False:
            processed_data_dict = self.pc.parse_data(data_dict, degsperpoint=5)
            fig = self.pc.plot_polarization_efficiency(processed_data_dict, sample_name, fig=fig)
        ax.plot(data_dict['x_position'], data_dict['amplitude'])
        ax.set_title('POL EFFICICENCY', fontsize=12)
        ax.set_xlabel('Steps', fontsize=10)
        ax.set_ylabel('Amplitude', fontsize=10)
        fig.savefig('temp_files/temp_pol.png')
        image = QtGui.QPixmap('temp_files/temp_pol.png')
        shutil.copy('temp_files/temp_pol.png', self.raw_data_path[0].replace('.dat', '.png'))
        getattr(self, '_pol_efficiency_popup_data_label').setPixmap(image)
        pl.close('all')

    #################################################
    # SINGLE CHANNEL FTS BILLS
    #################################################

    def _close_single_channel_fts(self):
        '''
        Closes the panel with a warning if data is being collected
        '''
        global continue_run
        if continue_run:
            self._quick_message('Taking data!!!\nPlease stop taking data before closing single channel FTS!')
        else:
            self.single_channel_fts_popup.close()
            continue_run = False

    def _single_channel_fts(self):
        '''
        Creates the panel
        '''
        if not hasattr(self, 'fourier'):
            self.fourier = Fourier()
        if not hasattr(self, 'fts_curve'):
            self.fts_curve = FTSCurve()
        if not hasattr(self, 'lock_in'):
            self.lock_in = LockIn()
        if not hasattr(self, 'single_channel_fts_popup'):
            self._create_popup_window('single_channel_fts_popup')
        else:
            self._initialize_panel('single_channel_fts_popup')
        self.if_count = 0
        self._build_panel(settings.single_channel_fts_build_dict)
        for unique_combobox, entries in settings.fts_combobox_entry_dict.items():
            self.populate_combobox(unique_combobox, entries)
        getattr(self, '_single_channel_fts_popup_integration_time_combobox').setCurrentIndex(0)
        getattr(self, '_single_channel_fts_popup_pause_time_combobox').setCurrentIndex(2)
        getattr(self, '_single_channel_fts_popup_sample_rate_combobox').setCurrentIndex(8)
        #getattr(self, '_single_channel_fts_popup_grid_sm_com_port_combobox').setCurrentIndex(0
        getattr(self, '_single_channel_fts_popup_fts_sm_com_port_combobox').setCurrentIndex(0)
        getattr(self, '_single_channel_fts_popup_verify_parameters_checkbox').setCheckState(True)
        getattr(self, '_single_channel_fts_popup_signal_channel_combobox').setCurrentIndex(2)
        self.fts_positions_steps, self.fts_positions_m, self.fts_amplitudes, self.fts_stds = [], [], [], []
        self._update_single_channel_fts()
        self._plot_interferogram()
        self._draw_time_stream(set_to_widget='_single_channel_fts_popup_time_stream_label')
        self.single_channel_fts_popup.showMaximized()
        self.single_channel_fts_popup.setWindowTitle('Single Channel FTS')

    def _compute_resolution_and_max_frequency(self, scan_params):
        '''
        Compute the resultant quantities on the panel
        '''
        proceed = False
        if self._is_float(scan_params['ending_position'])\
                and self._is_float(scan_params['starting_position'])\
                and self._is_float(scan_params['distance_per_step'], enforce_positive=True)\
                and self._is_float(scan_params['step_size'], enforce_positive=True):
            proceed = True
        if proceed:
            total_steps = int(scan_params['ending_position']) - int(scan_params['starting_position'])
            total_distance = total_steps * float(scan_params['distance_per_step']) #nm
            min_distance = int(scan_params['step_size']) * float(scan_params['distance_per_step']) #m
            if min_distance > 0 and total_distance > 0:
                min_distance *= 1e-9 # from nm to m
                total_distance *= 1e-9 # from nm to m
                nyquist_distance = 4 * min_distance
                max_frequency = ((2.99792458 * 10 ** 8) / nyquist_distance) / (10 ** 9) # GHz
                resolution = ((3 * 10 ** 8) / total_distance) / (10 ** 9) # GHz
                resolution = '{0:.2f} GHz'.format(resolution)
                max_frequency = '{0:.2f} GHz'.format(max_frequency)
            else:
                resolution, max_frequency = 'nan', 'nan'
        else:
            resolution, max_frequency = 'nan', 'nan'
        return resolution, max_frequency

    def _update_single_channel_fts(self):
        '''
        Update the resultant quantities on the panel
        '''
        meta_data = self._get_all_meta_data(popup='_single_channel_fts')
        scan_params = self._get_all_params(meta_data, settings.fts_scan_params, 'single_channel_fts')
        if type(scan_params) is not dict:
            return None
        # Update Slider
        resolution_widget = '_single_channel_fts_popup_resolution_label'
        if hasattr(self, resolution_widget):
            if 'starting_position' in scan_params and 'ending_position' in scan_params:
                resolution, max_frequency = self._compute_resolution_and_max_frequency(scan_params)
                resolution_widget = '_single_channel_fts_popup_resolution_label'
                getattr(self, resolution_widget).setText(resolution)
                max_frequency_widget = '_single_channel_fts_popup_max_frequency_label'
                getattr(self, max_frequency_widget).setText(max_frequency)
                if self._is_float(scan_params['step_size'], enforce_positive=True):
                    num_steps = (int(scan_params['ending_position']) - int(scan_params['starting_position'])) / int(scan_params['step_size'])
                else:
                    num_steps = 'inf'
                getattr(self, '_single_channel_fts_popup_number_of_steps_label').setText(str(num_steps))
                self._update_slider_setup(scan_params)
            fts_com_port = str(getattr(self, '_single_channel_fts_popup_fts_sm_com_port_combobox').currentText())
            grid_com_port = str(getattr(self, '_single_channel_fts_popup_grid_sm_com_port_combobox').currentText())
            if hasattr(self, 'sm_{0}'.format(fts_com_port)):
                getattr(self, '_single_channel_fts_popup_fts_sm_connection_status_label').setStyleSheet('QLabel {color: green}')
                getattr(self, '_single_channel_fts_popup_fts_sm_connection_status_label').setText('Ready!')
            if hasattr(self, 'sm_{0}'.format(grid_com_port)):
                getattr(self, '_single_channel_fts_popup_grid_sm_connection_status_label').setStyleSheet('QLabel {color: green}')
                getattr(self, '_single_channel_fts_popup_grid_sm_connection_status_label').setText('Ready!')
            self.single_channel_fts_popup.repaint()

    def _update_slider_setup(self, scan_params):
        '''
        Update the resultant slider position
        '''
        min_slider = '_single_channel_fts_popup_position_slider_min_label'
        max_slider = '_single_channel_fts_popup_position_slider_max_label'
        getattr(self, min_slider).setText(str(scan_params['starting_position']))
        getattr(self, max_slider).setText(str(scan_params['ending_position']))
        slider = '_single_channel_fts_popup_position_monitor_slider'
        getattr(self, slider).setMinimum(int(scan_params['starting_position']))
        getattr(self, slider).setMaximum(int(scan_params['ending_position']))
        com_port = self._get_com_port('_single_channel_fts_popup_fts_sm_com_port_combobox')
        motor_position = 0
        getattr(self, slider).setSliderPosition(motor_position)
        getattr(self, slider).sliderPressed.connect(self._dummy)
        self.starting_position = scan_params['starting_position']

    def _compute_and_plot_fft(self, position_vector, efficiency_vector, scan_params, fig=None):
        '''
        Post data collection analysis
        '''
        fft_freq_vector, fft_vector, phase_corrected_fft_vector, symmetric_position_vector, symmetric_efficiency_vector\
            = self.fourier.convert_IF_to_FFT_data(position_vector, efficiency_vector, scan_params, data_selector='All')
        normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real / np.max(phase_corrected_fft_vector.real))
        if fig is not None and len(fft_freq_vector) > 0:
            try:
                pos_freq_selector = np.where(fft_freq_vector > 0)
                band = str(scan_params['frequency_band'])
                if len(band) == 0:
                    band = None
                max_idx = np.where(normalized_phase_corrected_fft_vector == np.max(normalized_phase_corrected_fft_vector))
                max_frequency = fft_freq_vector[max_idx][0]
                dx = fft_freq_vector[1] - fft_freq_vector[0] 
                integrated_bandwidth = np.trapz(normalized_phase_corrected_fft_vector[pos_freq_selector], dx=dx) * 1e-9
                #print(integrated_bandwidth)
                #import ipdb;ipdb.set_trace()
                label = 'Peak Frequency {0:.1f} GHz\n'.format(max_frequency * 1e-9)
                ax = fig.axes[-1]
                ax, bandwidth = self.fts_curve.add_sim_data(ax, band=band)
                label += 'Integrated BW ({0:.1f}/{1:.1f}) GHz'.format(integrated_bandwidth, bandwidth)
                pl.grid(True)
                ax.plot(fft_freq_vector[pos_freq_selector] * 1e-9, normalized_phase_corrected_fft_vector[pos_freq_selector], label=label)
                ax.set_xlabel('Frequency (GHz)', fontsize=10)
                ax.set_ylabel('Phase Corrected FFT', fontsize=10)
                ax.set_title('Spectral Response {0}'.format(scan_params['sample_name']), fontsize=12)
                ax.legend()
            except IndexError:
                pass
            #fig.savefig('temp_files/temp_fft.png')
            #fig.savefig('temp_files/IF_GIF/FFT_{0}.png'.format(str(self.if_count).zfill(3)))
            #image = QtGui.QPixmap('temp_files/temp_fft.png')
            #getattr(self, '_single_channel_fts_popup_fft_label').setPixmap(image)
            #pl.close('all')
        return fft_freq_vector, normalized_phase_corrected_fft_vector, fig

    def _plot_interferogram(self, positions=[], amplitudes=[], stds=[]):
        '''
        Plots the collected data as an XY scatter (position, amplitude) and paints it to the panel
        '''
        if len(self.fts_positions_steps) > 5:
            meta_data = self._get_all_meta_data(popup='_single_channel_fts')
            scan_params = self._get_all_params(meta_data, settings.fts_scan_params, 'single_channel_fts')
            basename = os.path.basename(self.raw_data_path[0]) .replace('.if', '')
            fig, ax = self._create_blank_fig(frac_screen_width=0.45, frac_screen_height=0.5, multiple_axes=True)
            fig.add_subplot(211)
            fig.add_subplot(212)
            fig.subplots_adjust(left=0.12, bottom=0.12, top=0.92, right=0.98, hspace=0.45, wspace=0.20)
            fft_frequency_vector, normalized_phase_corrected_fft_vector, fig = self._compute_and_plot_fft(self.fts_positions_steps, self.fts_amplitudes, scan_params, fig)
            ax = fig.axes[0]
            pl.grid(True)
            ax.set_xlabel('Mirror Position (cm)',fontsize = 10)
            ax.set_ylabel('Amplitude',fontsize = 10)
            ax.set_title('Interferogram', fontsize=12)
            ax.plot(positions, amplitudes)
            pl.grid(True)
            ax.errorbar(positions, amplitudes, stds, marker=',', linestyle='None')
            fig.savefig('temp_files/temp_int.png')
            save_folder = './temp_files/{0}'.format(basename)
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)
            incremental_save_path = os.path.join(save_folder, '{0}.png'.format(str(self.if_count).zfill(4)))
            fig.savefig(os.path.join(incremental_save_path))
            self.if_count += 1

            pl.close('all')
            image = QtGui.QPixmap('temp_files/temp_int.png')
            getattr(self, '_single_channel_fts_popup_interferogram_label').setPixmap(image)

    def _rotate_grid(self):
        '''
        Rotates the Pol Gride to the desired angle
        '''
        polar_com_port = self._get_com_port('_single_channel_fts_popup_grid_com_ports_combobox')
        angle = getattr(self,'_single_channel_fts_popup_desired_grid_angle_lineedit').text()
        getattr(self, 'sm_{0}'.format(polar_com_port)).finite_rotation(int(angle))

    def _run_fts(self, resume_run=False):
        '''
        Execute a data taking run
        '''
        global continue_run
        continue_run = True
        # Verify params via popu first
        if getattr(self, '_single_channel_fts_popup_verify_parameters_checkbox').isChecked():
            cancel_run = self._verify_params()
            if cancel_run:
                continue_run = False
                return None
        meta_data = self._get_all_meta_data(popup='_single_channel_fts')
        scan_params = self._get_all_params(meta_data, settings.fts_scan_params, 'single_channel_fts')
        pause = float(scan_params['pause_time']) / 1e3
        if not resume_run:
            if str(getattr(self, '_single_channel_fts_popup_fts_sm_connection_status_label').text()) != 'Ready!':
                getattr(self, '_single_channel_fts_popup_start_pushbutton').setText('Connecting to Stepper Motor')
                getattr(self, '_single_channel_fts_popup_start_pushbutton').setFlat(True)
                self.single_channel_fts_popup.repaint()
                self._connect_to_com_port(com_port=scan_params['fts_sm_com_port'])
            if str(getattr(self, '_single_channel_fts_popup_grid_sm_connection_status_label').text()) != 'Ready!' and False:
                getattr(self, '_single_channel_fts_popup_start_pushbutton').setText('Connecting to Stepper Motor')
                getattr(self, '_single_channel_fts_popup_start_pushbutton').setFlat(True)
                self.single_channel_fts_popup.repaint()
                self._connect_to_com_port(com_port=scan_params['grid_sm_com_port'])
            getattr(self, '_single_channel_fts_popup_start_pushbutton').setText('Taking Data')
            getattr(self, '_single_channel_fts_popup_start_pushbutton').setFlat(True)
            i = 0
            x_positions = np.arange(int(scan_params['starting_position']), int(scan_params['ending_position']) + int(scan_params['step_size']), int(scan_params['step_size']))
            getattr(self, 'sm_{0}'.format(scan_params['fts_sm_com_port'])).move_to_position(int(scan_params['starting_position']))
            time.sleep(2)
            self._get_raw_data_save_path()
        if (self.raw_data_path is not None and len(scan_params['signal_channel']) > 0) or resume_run:
            if resume_run:
                i = 0
                time.sleep(2)
                x_positions = np.arange(self.last_fts_position, int(scan_params['ending_position']) + int(scan_params['step_size']), int(scan_params['step_size']))
            else:
                # reset these to zero
                self.fts_positions_steps, self.fts_positions_m, self.fts_amplitudes, self.fts_stds = [], [], [], []
                self._plot_interferogram()
            start_time = datetime.now()
            start_time_str = datetime.strftime(start_time, '%H:%M')
            with open(self.raw_data_path[0].replace('.if', '.json'), 'w') as meta_data_handle:
                json.dump(meta_data, meta_data_handle)
            with open(self.raw_data_path[0], 'w') as if_save_handle:
                while continue_run and i < len(x_positions):
                    position = x_positions[i]
                    getattr(self, '_single_channel_fts_popup_position_monitor_slider').setSliderPosition(position)
                    self.repaint()
                    getattr(self, 'sm_{0}'.format(scan_params['fts_sm_com_port'])).move_to_position(position)
                    self.lock_in._zero_lock_in_phase()
                    time.sleep(pause)
                    data_time_stream, mean, min_, max_, std = self.real_daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                                                                     sample_rate=scan_params['sample_rate'], active_devices=self.active_devices)
                    # Update data point info
                    std_pct = 100 * (std / mean)
                    std_pct = '({0:.2f}'.format(std_pct)
                    std_pct += '%)'
                    now_time = datetime.now()
                    now_time_str = datetime.strftime(now_time, '%H:%M')
                    duration = now_time - start_time
                    time_per_step = duration.seconds / (i + 1)
                    steps_left = len(x_positions) - i
                    time_left = time_per_step * steps_left / 60
                    getattr(self, '_single_channel_fts_popup_mean_label').setText('{0:.4f}'.format(mean))
                    getattr(self, '_single_channel_fts_popup_std_label').setText('{0:.4f} {1}'.format(std, std_pct))
                    getattr(self, '_single_channel_fts_popup_current_position_label').setText('{0:.3f} [{1}/{2} complete]'.format(position, i, len(x_positions) - 1))
                    status_str = 'Start: {0} ::::: Tot Duration: {1} (s) ::::: Time Per Step {2:.2f} (s) ::::: Estimated Time Left: {3:.2f} (m)'.format(start_time_str, duration.seconds,
                                                                                                                                                        time_per_step, time_left)
                    getattr(self, '_single_channel_fts_popup_duration_label').setText(status_str)
                    self._draw_time_stream(data_time_stream, min_, max_, '_single_channel_fts_popup_time_stream_label')
                    # Update IF plots and vectors
                    self.fts_positions_m.append(position * float(scan_params['distance_per_step']) * 1e-7)
                    self.fts_positions_steps.append(position)
                    self.fts_amplitudes.append(mean)
                    self.fts_stds.append(std)
                    self._plot_interferogram(self.fts_positions_steps, self.fts_amplitudes, self.fts_stds)
                    # Update IF linearity info
                    if_mean = np.mean(self.fts_amplitudes)
                    if_max_min_avg = np.mean([np.max(self.fts_amplitudes), np.min(self.fts_amplitudes)])
                    if_min_over_max = np.min(self.fts_amplitudes) / np.max(self.fts_amplitudes)
                    getattr(self, '_single_channel_fts_popup_if_mean_label').setText('{0:.3f}'.format(if_mean))
                    getattr(self, '_single_channel_fts_popup_if_max_min_label').setText('{0:.3f}'.format(if_max_min_avg))
                    #getattr(self, '_single_channel_fts_popup_if_max_min_label').setText('{0:.3f}'.format(if_min_over_max))
                    # Save the data
                    data_line ='{0}\t{1}\t{2}\n'.format(position, mean, std)
                    if_save_handle.write(data_line)
                    # Update the FFT of the data
                    i += 1
                    self.last_fts_position = position + int(scan_params['step_size'])
                    root.update()
        else:
            getattr(self, '_single_channel_fts_popup_start_pushbutton').setText('Start')
            getattr(self, '_single_channel_fts_popup_start_pushbutton').setFlat(False)
            self._quick_message('Bad data path or no signal channel set!')
        getattr(self, '_single_channel_fts_popup_start_pushbutton').setText('Start')
        getattr(self, '_single_channel_fts_popup_start_pushbutton').setFlat(False)
        self._save_if_and_fft(self.fts_positions_steps, self.fts_amplitudes, scan_params)
        response = self._quick_message('Finished Taking Data\nMoving mirror back to 0')
        getattr(self, 'sm_{0}'.format(scan_params['fts_sm_com_port'])).move_to_position(0)
        getattr(self, '_single_channel_fts_popup_position_monitor_slider').setSliderPosition(0)
        getattr(self, '_single_channel_fts_popup_current_position_label').setText('{0:.3f}'.format(0))
        continue_run = False
        #getattr(self, '_single_channel_fts_popup_stop_pushbutton').setText('Pause')
        self._update_log()

    def _save_if_and_fft(self, position_vector, efficiency_vector, scan_params):
        fft_freq_vector, phase_corrected_fft_vector, fig = self._compute_and_plot_fft(self.fts_positions_steps, self.fts_amplitudes, scan_params, fig=None)
        normalized_phase_corrected_fft_vector = np.abs(phase_corrected_fft_vector.real / np.max(phase_corrected_fft_vector.real))
        fft_save_path = self.raw_data_path[0].replace('.if', '.fft')
        png_save_path = self.raw_data_path[0].replace('.if', '.png')
        with open(fft_save_path, 'w') as file_handle:
            for i, freq in enumerate(fft_freq_vector):
                freq *= 1e-9
                fft_val = normalized_phase_corrected_fft_vector[i]
                line = '{0}\t{1}\n'.format(freq, fft_val)
                file_handle.write(line)
        png_save_path = self.raw_data_path[0].replace('.if', '.png')
        shutil.copy('temp_files/temp_int.png', png_save_path)
        response = self._quick_message('Data saved to {0}\n{1}\n{2}\n'.format(self.raw_data_path[0], self.raw_data_path[0].replace('.if', '.fft'), self.raw_data_path[0].replace('.if', '.png')))

    def _make_if_fft_gif(self):
        gif_basename = os.path.basename(self.raw_data_path[0]).replace('.if', '_{0}.gif'.format(str(self.if_count).zfill(4)))
        gif_path = os.path.join('./temp_files/IF_GIF/', gif_basename)
        with imageio.get_writer(gif_path, mode='I') as writer:
            for i in range(1000):
                if_filename = './temp_files/IF_GIF/IF_{0}.png'.format(str(i).zfill(4))
                fft_filename = './temp_files/IF_GIF/FFT_{0}.png'.format(str(i).zfill(4))
                if os.path.exists(if_filename) and os.path.exists(fft_filename):
                    tiled_filename = './temp_files/IF_GIF/tiled_{0}.png'.format(str(i).zfill(4))
                    montage_command = 'montage {0} {1} -geometry 1600x3200+0+0 -tile 1x2 {2}'.format(if_filename, fft_filename, tiled_filename)
                    subprocess.call(montage_command, shell=True)
                    image = imageio.imread(tiled_filename)
                    writer.append_data(image)

    #################################################
    # BEAM MAPPER
    #################################################

    def _close_beam_mapper(self):
        '''
        Closes the panel with a warning if data is being collected
        '''
        global continue_run
        if continue_run:
            self._quick_message('Taking data!!!\nPlease stop taking data before closing single channel FTS!')
        else:
            self.beam_mapper_popup.close()
            continue_run = False

    def _beam_mapper(self):
        '''
        Opens the panel
        '''
        if not hasattr(self, 'lock_in'):
            self.lock_in = LockIn()
        if not hasattr(self, 'beam_mapper_popup'):
            self._create_popup_window('beam_mapper_popup')
        else:
            self._initialize_panel('beam_mapper_popup')
        self._build_panel(settings.beam_mapper_build_dict)
        for combobox_widget, entry_list in self.beam_mapper_combobox_entry_dict.items():
            self.populate_combobox(combobox_widget, entry_list)
        self._draw_time_stream([0] * 5, -1, -1, '_beam_mapper_popup_time_stream_label')
        self.beam_mapper_popup.showMaximized()
        self._initialize_beam_mapper()
        meta_data = self._get_all_meta_data(popup='beam_mapper')
        scan_params = self._get_all_params(meta_data, settings.beam_mapper_params, 'beam_mapper')
        scan_params = self._get_grid(scan_params)
        x_com_port = scan_params['x_current_com_port']
        y_com_port = scan_params['y_current_com_port']
        x_motor_current = str(getattr(self, 'sm_{0}'.format(x_com_port)).get_motor_current()).replace('CC=', '')
        x_motor_velocity = str(getattr(self, 'sm_{0}'.format(x_com_port)).get_velocity()).replace('VE=', '')
        getattr(self, '_beam_mapper_popup_x_motor_current_label').setText(x_motor_current)
        getattr(self, '_beam_mapper_popup_x_motor_velocity_label').setText(x_motor_velocity)
        y_motor_current = str(getattr(self, 'sm_{0}'.format(y_com_port)).get_motor_current()).replace('CC=', '')
        y_motor_velocity = str(getattr(self, 'sm_{0}'.format(y_com_port)).get_velocity()).replace('VE=', '')
        getattr(self, '_beam_mapper_popup_y_motor_current_label').setText(y_motor_current)
        getattr(self, '_beam_mapper_popup_y_motor_velocity_label').setText(y_motor_velocity)
        getattr(self, '_beam_mapper_popup_signal_channel_combobox').setCurrentIndex(1)
        getattr(self, '_beam_mapper_popup_aperature_size_combobox').setCurrentIndex(1)
        getattr(self, '_beam_mapper_popup_sample_rate_combobox').setCurrentIndex(2)
        getattr(self, '_beam_mapper_popup_integration_time_combobox').setCurrentIndex(0)
        getattr(self, '_beam_mapper_popup_pause_time_combobox').setCurrentIndex(0)
        self.beam_mapper_popup.repaint()

    def _initialize_beam_mapper(self):
        '''
        Updates the panel based on inputs of desired grid
        '''
        if len(str(self.sender().whatsThis())) == 0:
            return None
        else:
            meta_data = self._get_all_meta_data(popup='beam_mapper')
            scan_params = self._get_all_params(meta_data, settings.beam_mapper_params, 'beam_mapper')
            scan_params = self._get_grid(scan_params)
            if scan_params is not None and len(scan_params) > 0:
                #self.bmt.simulate_beam(scan_params, 'temp_files/temp_beam.png')
                #image = QtGui.QPixmap('temp_files/temp_beam.png')
                #getattr(self, '_beam_mapper_popup_2D_plot_label').setPixmap(image)
                n_points_x = int(scan_params['n_points_x'])
                n_points_y = int(scan_params['n_points_y'])
                getattr(self,'_beam_mapper_popup_n_points_x_label').setText(str(n_points_x))
                getattr(self,'_beam_mapper_popup_n_points_y_label').setText(str(n_points_y))

    def _get_grid(self, scan_params):
        '''
        Sets up a gride to place data points into base on specfied params
        '''

        if self._is_float(scan_params['end_x_position']) \
                and self._is_float(scan_params['end_y_position']) \
                and self._is_float(scan_params['end_y_position']) \
                and self._is_float(scan_params['start_x_position']) \
                and self._is_float(scan_params['start_y_position']) \
                and self._is_float(scan_params['step_size_x'], enforce_positive=True) \
                and self._is_float(scan_params['step_size_y'], enforce_positive=True):
            x_total = int(scan_params['end_x_position']) - int(scan_params['start_x_position'])
            x_steps = int(scan_params['step_size_x'])
            if int(scan_params['step_size_x']) == 0 or  int(scan_params['step_size_y']) == 0:
                n_points_x = 1e9
                n_points_y = 1e9
            else:
                n_points_x = (int(scan_params['end_x_position']) + int(scan_params['step_size_y']) - int(scan_params['start_x_position'])) / int(scan_params['step_size_x'])
                n_points_y = (int(scan_params['end_y_position']) + int(scan_params['step_size_y']) - int(scan_params['start_y_position'])) / int(scan_params['step_size_y'])
            scan_params['n_points_x'] = n_points_x
            scan_params['n_points_y'] = n_points_y
            scan_params['x_total'] = x_total
            getattr(self, '_beam_mapper_popup_total_x_label').setText('{0} steps'.format(str(int(x_total))))
            y_total = int(scan_params['end_y_position']) - int(scan_params['start_y_position'])
            y_steps = int(scan_params['step_size_y'])
            getattr(self, '_beam_mapper_popup_total_y_label').setText('{0} steps'.format(str(int(y_total))))
            scan_params['y_total'] = y_total
        return scan_params

    def _plot_beam_map(self, x_ticks, y_ticks, Z, scan_params):
        '''
        '''
        fig, ax = self._create_blank_fig(left=0.02, bottom=0.19, right=0.98, top=0.9,
                                         frac_screen_width=None, frac_screen_height=None,
                                         aspect='equal')
        #ax_image = ax.imshow(Z)
        ax_image = ax.pcolormesh(Z)
        ax.set_title('BEAM DATA', fontsize=12)
        ax.set_xlabel('X Position (k-steps)', fontsize=12)
        ax.set_ylabel('Y Position (k-steps)', fontsize=12)
        x_tick_locs = [0.5 + x for x in range(len(x_ticks))]
        y_tick_locs = [0.5 + x for x in range(len(x_ticks))]
        ax.set_xticks(x_tick_locs)
        ax.set_yticks(y_tick_locs)
        ax.set_xticklabels(x_ticks, rotation=35, fontsize=10)
        ax.set_yticklabels(y_ticks, fontsize=10)
        color_bar = fig.colorbar(ax_image, ax=ax)
        fig.savefig('temp_files/temp_beam.png')
        shutil.copy('temp_files/temp_beam.png', self.raw_data_path[0].replace('.dat', '.png'))
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_beam.png')
        getattr(self, '_beam_mapper_popup_2D_plot_label').setPixmap(image)

    def _take_beam_map(self):
        '''
        Executes a data taking run
        '''
        global continue_run
        global pause_run
        continue_run = True
        pause_run = False
        meta_data = self._get_all_meta_data()
        scan_params = self._get_all_params(meta_data, settings.beam_mapper_params, 'beam_mapper')
        x_start = int(scan_params['start_x_position'])
        x_end =  int(scan_params['end_x_position'])
        x_step = int(scan_params['step_size_x'])
        y_start = int(scan_params['start_y_position'])
        y_end =  int(scan_params['end_y_position'])
        y_step = int(scan_params['step_size_y'])
        x_grid = np.arange(x_start, x_end + x_step, x_step)
        y_grid = np.arange(y_start, y_end + y_step, y_step)
        x_ticks = [str(int(x * 1e-3)) for x in x_grid]
        y_ticks = [str(int(x * 1e-3)) for x in y_grid]
        #x_grid = np.linspace(int(scan_params['start_x_position']), int(scan_params['end_x_position']),  int(scan_params['n_points_x']) + 1)
        #y_grid = np.linspace(int(scan_params['start_y_position']), int(scan_params['end_y_position']),  int(scan_params['n_points_y']) + 1)
        y_grid_reversed = np.flip(y_grid)
        X, Y = np.meshgrid(x_grid, y_grid)
        #import ipdb;ipdb.set_trace()
        Z_data = np.zeros(shape=X.shape)
        self.stds = np.zeros(shape=X.shape)
        x_com_port = scan_params['x_current_com_port']
        y_com_port = scan_params['y_current_com_port']
        total_points = int(scan_params['n_points_x']) * int(scan_params['n_points_y'])
        self._get_raw_data_save_path()
        direction = -1
        if self.raw_data_path is not None:
            start_time = datetime.now()
            getattr(self, '_beam_mapper_popup_start_pushbutton').setDisabled(True)
            with open(self.raw_data_path[0], 'w') as data_handle:
                count = 1
                with open(self.raw_data_path[0].replace('.dat', '.json'), 'w') as meta_data_handle:
                    json.dump(meta_data, meta_data_handle)
                i = 0
                while i < len(x_grid) and continue_run:
                    x_pos = x_grid[i]
                    getattr(self, 'sm_{0}'.format(x_com_port)).move_to_position(x_pos)
                    #act_x_pos = str(getattr(self, 'sm_{0}'.format(x_com_port)).get_position()).replace('SP=', '')
                    act_x_pos = x_pos
                    direction *= -1
                    if direction == -1:
                        y_scan = y_grid_reversed
                    else:
                        y_scan = y_grid
                    j = 0
                    while j < len(y_scan) and continue_run:
                        y_pos = y_scan[j]
                        getattr(self, 'sm_{0}'.format(y_com_port)).move_to_position(y_pos)
                        #act_y_pos = str(getattr(self, 'sm_{0}'.format(y_com_port)).get_position()).replace('SP=', '')
                        act_y_pos = y_pos
                        if i == 0 and j == 0: #sleep extra long on the first point
                            time.sleep(4)
                        else:
                            time.sleep((int(scan_params['pause_time']) / 2) * 1e-3)
                        self.lock_in._zero_lock_in_phase()
                        time.sleep((int(scan_params['pause_time']) / 2) * 1e-3)
                        data_time_stream, mean, min_, max_, std = self.real_daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                                                                         sample_rate=scan_params['sample_rate'], active_devices=self.active_devices)
                        self._draw_time_stream(data_time_stream, min_, max_,'_beam_mapper_popup_time_stream_label')
                        Z_datum = mean
                        if direction == -1:
                            self.stds[len(y_scan) -1 - j][i] = std
                            Z_data[len(y_scan) - 1- j][i] = Z_datum
                        else:
                            self.stds[j][i] = std
                            Z_data[j][i] = Z_datum
                        self._plot_beam_map(x_ticks, y_ticks, Z_data, scan_params)
                        getattr(self, '_beam_mapper_popup_data_mean_label').setText('{0:.3f}'.format(mean))
                        getattr(self, '_beam_mapper_popup_x_position_label').setText('{0}'.format(act_x_pos))
                        getattr(self, '_beam_mapper_popup_y_position_label').setText('{0}'.format(act_y_pos))
                        getattr(self, '_beam_mapper_popup_data_std_label').setText('{0:.3f}'.format(std))
                        data_line = '{0}\t{1}\t{2:.4f}\t{3:.4f}\n'.format(act_x_pos, act_y_pos, Z_datum, std)
                        data_handle.write(data_line)
                        now_time = datetime.now()
                        now_time_str = datetime.strftime(now_time, '%H:%M')
                        duration = now_time - start_time
                        time_per_step = duration.seconds / count
                        steps_left = total_points - count
                        time_left = time_per_step * steps_left / 60
                        status_msg = '{0} of {1} ::: Total Duration {2:.2f} (m) ::: Time per Point {3:.2f} (s) ::: Time Left {4:.2f} (m)'.format(count, total_points, duration.seconds / 60,
                                                                                                                                                 time_per_step, time_left)
                        getattr(self, '_beam_mapper_popup_status_label').setText(status_msg)
                        self.repaint()
                        root.update()
                        count += 1
                        j += 1
                        while pause_run:
                            print('pausing beam mapper')
                            time.sleep(1)
                            root.update()
                    if i + 1 == len(x_grid):
                        continue_run = False
                    i += 1
        #import ipdb;ipdb.set_trace()
        #getattr(self, '_beam_mapper_popup_save_pushbutton').setEnableI#
        # Restore to (0, 0) and erase Z data
        getattr(self, 'sm_{0}'.format(x_com_port)).move_to_position(0)
        getattr(self, 'sm_{0}'.format(y_com_port)).move_to_position(0)
        getattr(self, '_beam_mapper_popup_start_pushbutton').setEnabled(True)
        self.lock_in._zero_lock_in_phase()
        Z_data = np.zeros(shape=X.shape)
        self._update_log()

    #################################################
    # FTS/IF Curves 
    #################################################

    def _build_ifcurve_settings_popup(self):
        popup_name = 'ftscurve_settings_popup'
        self.analyze_interferogram = True
        self._build_ftscurve_settings_popup(popup_name=popup_name)

    def _close_fts(self):
        self.ftscurve_settings_popup.close()

    def _build_ftscurve_settings_popup(self, popup_name=None, preset_parameters={}):
        if popup_name is None:
            popup_name = '{0}_settings_popup'.format(self.analysis_type)
        if hasattr(self, popup_name):
            self._initialize_panel(popup_name)
            self._build_panel(settings.ftscurve_popup_build_dict)
        else:
            self._create_popup_window(popup_name)
            self._build_panel(settings.ftscurve_popup_build_dict)
        row = 3
        self.selected_files_col_dict = {}
        if '.fft' in self.selected_files[0]:
            json_path = self.selected_files[0].replace('.fft', '.json')
        elif '.if' in self.selected_files[0]:
            json_path = self.selected_files[0].replace('.if', '.json')
        distance_per_step = '250.39'
        step_size = '500'
        print(json_path)
        if os.path.exists(json_path):
            with open(json_path, 'r') as json_handle:
                meta_data = json.load(json_handle)
            distance_per_step = meta_data['_single_channel_fts_popup_distance_per_step_combobox']
            step_size = meta_data['_single_channel_fts_popup_step_size_lineedit']
        for i, selected_file in enumerate(self.selected_files):
            # update dict with column file mapping
            col = 1 + i * 2
            basename = os.path.basename(selected_file)
            self.selected_files_col_dict[selected_file] = col
            # Add the file name for organization
            unique_widget_name = '_{0}_{1}_lineedit'.format(popup_name, basename)
            widget_settings = {'text': '{0}'.format(basename),
                               'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add a lineedit for plot title
            print(col)
            unique_widget_name = '_{0}_{1}_plot_title_lineedit'.format(popup_name, col)
            widget_settings = {'text': '',
                               'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add a lineedit for plot labeling
            unique_widget_name = '_{0}_{1}_plot_label_lineedit'.format(popup_name, col)
            widget_settings = {'text': '',
                               'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add an "normalize" checkbox
            unique_widget_name = '_{0}_{1}_normalize_checkbox'.format(popup_name, col)
            widget_settings = {'text': 'Check = Do Normalize',
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setChecked(True)
            row += 1
            # Add an 5mil "Divide Beam Splitter" checkbox
            unique_widget_name = '_{0}_{1}_divide_bs_5mil_checkbox'.format(popup_name, col)
            widget_settings = {'text': '5 mil',
                               'function': self._select_bs_thickness,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            # Add a 10mil "Divide Beam Splitter" checkbox
            unique_widget_name = '_{0}_{1}_divide_bs_10mil_checkbox'.format(popup_name, col)
            widget_settings = {'text': '10 mil',
                               'function': self._select_bs_thickness,
                               'position': (row, col + 1, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setChecked(True)
            row += 1
            # Add a "Add ATM Model" checkbox
            unique_widget_name = '_{0}_{1}_divide_mmf_checkbox'.format(popup_name, col)
            widget_settings = {'text': 'NOT SUPPORTED 3/13/2018',
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setChecked(False)
            row += 1
            # Add a "Add  Model" checkbox
            unique_widget_name = '_{0}_{1}_add_atm_model_checkbox'.format(popup_name, col)
            widget_settings = {'text': 'Check = Do Add ATM Model',
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            if col == 1:
                getattr(self, unique_widget_name).setChecked(True)
            row += 1
            # Add a "Add  CO lines" checkbox
            unique_widget_name = '_{0}_{1}_add_co_lines_checkbox'.format(popup_name, col)
            widget_settings = {'text': 'Check = Do Add CO lines',
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            if col == 1:
                getattr(self, unique_widget_name).setChecked(True)
            row += 1
            # Add a "Sim Bands" checkbox
            for j, band in enumerate(settings.simulated_bands):
                unique_widget_name = '_{0}_{1}_add_sim_band_{2}_checkbox'.format(popup_name, col, band)
                if j == 0:
                    position = (row, col, 1, 1)
                elif j == 1:
                    position = (row, col + 1, 1, 1)
                elif j == 2:
                    position = (row + 1, col, 1, 1)
                elif j == 3:
                    position = (row + 1, col + 1, 1, 1)
                widget_settings = {'text': band,
                                   'position': position}
                self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 2
            # Add a "step size" lineedit
            unique_widget_name = '_{0}_{1}_step_size_lineedit'.format(popup_name, col)
            widget_settings = {'text': distance_per_step, 'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add a "steps per point" lineedit
            unique_widget_name = '_{0}_{1}_steps_per_point_lineedit'.format(popup_name, col)
            widget_settings = {'text': step_size, 'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add an "color" lineedit
            unique_widget_name = '_{0}_{1}_color_lineedit'.format(popup_name, col)
            widget_settings = {'text': 'b',
                               'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add an "xlim clip" lineedit
            unique_widget_name = '_{0}_{1}_xlim_clip_lineedit'.format(popup_name, col)
            widget_settings = {'text': '0:600',
                               'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add an "xlim plot" lineedit
            unique_widget_name = '_{0}_{1}_xlim_plot_lineedit'.format(popup_name, col)
            widget_settings = {'text': '0:600',
                               'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add an "Smoothing" lineedit
            unique_widget_name = '_{0}_{1}_smoothing_factor_lineedit'.format(popup_name, col)
            widget_settings = {'text': '0.0',
                               'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add an "interferogram data select" lineedit
            unique_widget_name = '_{0}_{1}_interferogram_data_select_combobox'.format(popup_name, col)
            widget_settings = {'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            for entry in ['All', 'Right', 'Left']:
                getattr(self, unique_widget_name).addItem(entry)
            getattr(self, unique_widget_name).setCurrentIndex(0)
            row += 1
            # Add an "plot interferogram" checkbox
            unique_widget_name = '_{0}_{1}_plot_interferogram_checkbox'.format(popup_name, col)
            widget_settings = {'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setCheckState(False)
            row += 1
            # Add an "local FFT" checkbox
            unique_widget_name = '_{0}_{1}_add_local_fft_checkbox'.format(popup_name, col)
            widget_settings = {'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setCheckState(False)
            row += 1
            row = 3
        getattr(self, popup_name).show()

    def _build_fts_input_dicts(self):
        list_of_input_dicts = []
        fts_settings = ['smoothing_factor', 'xlim_plot', 'xlim_clip', 'divide_mmf', 'add_atm_model',
                        'divide_bs_5', 'divide_bs_10', 'step_size', 'steps_per_point', 'add_sim_band',
                        'add_co_lines', 'color', 'normalize', 'plot_title', 'plot_label', 'interferogram_data_select',
                        'plot_interferogram', 'add_local_fft', 'data_selector']
        for selected_file, col in self.selected_files_col_dict.items():
            input_dict = {'measurements': {'data_path': selected_file}}
            for setting in fts_settings:
                identity_string = '{0}_{1}'.format(col, setting)
                widgets = [x for x in dir(self) if identity_string in x]
                for widget in widgets:
                    if 'checkbox' in widget:
                        bool_value = getattr(self, widget).isChecked()
                        if 'divide_bs' in widget:
                            input_dict['measurements'][setting] = bool_value
                        elif 'add_sim_band' in widget:
                            input_dict['measurements']['{0}_{1}'.format(setting, widget.split('_')[-2])] = bool_value
                        else:
                            input_dict['measurements'][setting] = bool_value
                    elif 'lineedit' in widget:
                        widget_text = str(getattr(self, widget).text())
                        if 'xlim' in widget:
                            widget_text = (int(widget_text.split(':')[0]), int(widget_text.split(':')[1]))
                        input_dict['measurements'][setting] = widget_text
                    elif 'combobox' in widget:
                        widget_text = str(getattr(self, widget).currentText())
                        input_dict['measurements'][setting] = widget_text
            list_of_input_dicts.append(copy(input_dict))
        pprint(list_of_input_dicts)
        return list_of_input_dicts

    def _select_bs_thickness(self):
        file_col = int(str(self.sender().whatsThis()).split('_')[4])
        other_thickness_dict = {'5': '10', '10': '5'}
        bs_thickness = str(self.sender().text()).split(' ')[0]
        other_thickness = other_thickness_dict[bs_thickness]
        sender_widget_name = '_ftscurve_settings_popup_{0}_divide_bs_{1}mil_checkbox'.format(file_col, bs_thickness)
        other_widget_name = '_ftscurve_settings_popup_{0}_divide_bs_{1}mil_checkbox'.format(file_col, other_thickness)
        getattr(self, sender_widget_name).setCheckState(True)
        getattr(self, other_widget_name).setCheckState(False)

    def _check_for_if_file(self):
        list_of_input_dict = self._build_fts_input_dicts()
        for input_dict in list_of_input_dicts:
            input_dict['measurements']['plot_interferogram']

    def _plot_ifcurve(self):
        '''
        First we do the numerical processing, then save the file as an FFT and plot using normal plotter
        '''
        selected_files = list(set(self.selected_files))
        list_of_input_dicts = self._build_fts_input_dicts()
        getattr(self, '_ftscurve_settings_popup_run_pushbutton').setText('Close Pylab Window')
        getattr(self, '_ftscurve_settings_popup_run_pushbutton').setEnabled(False)
        self.ftscurve_settings_popup.repaint()
        for input_dict in list_of_input_dicts:
            position_vector, efficiency_vector = self.fts.load_IF_data(input_dict['measurements']['data_path'])
            fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector\
                    = self.fourier.convert_IF_to_FFT_data(position_vector, efficiency_vector, scan_param_dict=input_dict)
            new_fft_path = input_dict['measurements']['data_path'].replace('.if', '_local.fft')
            with open(new_fft_path, 'w') as file_handle:
                for i, fft_freq in enumerate(fft_freq_vector):
                    phase_corrected_fft_value = phase_corrected_fft_vector[i].real
                    phase_corrected_fft_value = fft_vector[i].real
                    fft_freq *= 1e-9
                    line = '{0}\t{1}\t{2}\n'.format(fft_freq, np.abs(phase_corrected_fft_value), phase_corrected_fft_value)
                    file_handle.write(line)
            input_dict['measurements']['data_path'] = new_fft_path
        pprint(list_of_input_dicts)
        self.fts.run(list_of_input_dicts)

    def _plot_ftscurve(self):
        selected_files = list(set(self.selected_files))
        list_of_input_dicts = self._build_fts_input_dicts()
        getattr(self, '_ftscurve_settings_popup_run_pushbutton').setText('Close Pylab Window')
        getattr(self, '_ftscurve_settings_popup_run_pushbutton').setEnabled(False)
        self.ftscurve_settings_popup.repaint()
        self.fts.run(list_of_input_dicts)
        #getattr(self, '_ftscurve_settings_popup_run_pushbutton').clicked.connect(self._run_analysis)
        getattr(self, '_ftscurve_settings_popup_run_pushbutton').setText('Run')
        getattr(self, '_ftscurve_settings_popup_run_pushbutton').setEnabled(True)
        pl.close('all')

    #################################################
    # BEAM MAPS 
    #################################################

    def _close_beammap(self):
        self.beammap_settings_popup.close()

    def _build_beammap_settings_popup(self):
        popup_name = '{0}_settings_popup'.format(self.analysis_type)
        print(popup_name)
        if not hasattr(self, 'bm'):
            self.bm = BeamMaps()
        if hasattr(self, popup_name):
            self._initialize_panel(popup_name)
            self._build_panel(settings.beammap_settings_popup_build_dict)
        else:
            self._create_popup_window(popup_name)
            self._build_panel(settings.beammap_settings_popup_build_dict)
        self.selected_files_col_dict = {}
        col = 2
        for i, selected_file in enumerate(self.selected_files):
            getattr(self, '_beammap_settings_popup_file_path_label').setText(selected_file)
            self.selected_files_col_dict[col] = selected_file
        getattr(self, popup_name).show()

    def _build_beammap_dicts(self):
        list_of_input_dicts = []
        beammap_settings = ['', 'color']
        for col in sorted(self.selected_files_col_dict.keys()):
            selected_file = self.selected_files_col_dict[col]
            self.selected_files_col_dict = {}
            input_dict = {'data_path': selected_file}
            for setting in beammap_settings:
                print(setting)
            list_of_input_dicts.append(input_dict)
        return list_of_input_dicts

    def _plot_beammap(self):
        list_of_input_dicts = self._build_beammap_dicts()
        self.bm.run2(list_of_input_dicts)


    #################################################
    # Tau Curves 
    #################################################

    def _close_tau_popup(self):
        self.taucurve_settings_popup.close()

    def _build_taucurve_settings_popup(self):
        popup_name = '{0}_settings_popup'.format(self.analysis_type)
        if hasattr(self, popup_name):
            self._initialize_panel(popup_name)
            self._build_panel(settings.taucurve_popup_build_dict)
        else:
            self._create_popup_window(popup_name)
            self._build_panel(settings.taucurve_popup_build_dict)
        getattr(self, popup_name).show()
        row = 2
        self.selected_files_col_dict = {}
        color_dict = {0: 'r', 1: 'g', 2: 'c', 3: 'b', 4: 'y', 5: 'm'}
        for i, selected_file in enumerate(self.selected_files):
            print(selected_file)
            col = 2 + i * 3
            self.selected_files_col_dict[col] = selected_file
            basename = os.path.basename(selected_file)
            unique_widget_name = '_{0}_{1}_label'.format(popup_name, basename)
            widget_settings = {'text': '{0}'.format(basename),
                               'position': (row, col - 1, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            unique_widget_name = '_{0}_{1}_color_label'.format(popup_name, col)
            widget_settings = {'text': 'Color', 'position': (row, col - 1, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            unique_widget_name = '_{0}_{1}_color_lineedit'.format(popup_name, col)
            color_text = color_dict[i]
            widget_settings = {'text': color_text, 'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            unique_widget_name = '_{0}_{1}_vbias_label'.format(popup_name, col)
            widget_settings = {'text': 'V_bias', 'position': (row, col - 1, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            unique_widget_name = '_{0}_{1}_vbias_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row = 2

    def _build_tau_input_dicts(self):
        list_of_input_dicts = []
        tau_settings = ['vbias', 'color']
        for col in sorted(self.selected_files_col_dict.keys()):
            selected_file = self.selected_files_col_dict[col]
            title_lineedit_name = '_taucurve_settings_popup_title_lineedit'
            title = str(getattr(self, title_lineedit_name).text())
            input_dict = {'data_path': selected_file, 'title': title}
            for setting in tau_settings:
                identity_string = '{0}_{1}'.format(col, setting)
                for widget in [x for x in dir(self) if identity_string in x]:
                    if 'checkbox' in widget and not 'invert' in widget:
                        if getattr(self, widget).isChecked():
                            setting_value = str(getattr(self, widget).text()).split(' ')[-1]
                            input_dict[setting] = float(setting_value)
                    elif 'checkbox' in widget and 'invert' in widget:
                        invert_bool = getattr(self, widget).isChecked()
                        input_dict['invert'] = invert_bool
                    elif 'lineedit' in widget:
                        widget_text = str(getattr(self, widget).text())
                        if len(widget_text) == 0:
                            widget_text = 'None'
                            input_dict[setting] = widget_text
                        elif self._isfloat(widget_text):
                            input_dict[setting] = float(widget_text)
                        else:
                            input_dict[setting] = widget_text
            list_of_input_dicts.append(copy(input_dict))
        pprint(list_of_input_dicts)
        #import ipdb;ipdb.set_trace()
        return list_of_input_dicts

    def _plot_taucurve(self):
        selected_files = list(set(self.selected_files))
        list_of_input_dicts = self._build_tau_input_dicts()
        tau = TAUCurve(list_of_input_dicts)
        tau.run()

    #################################################
    # RT Curves 
    #################################################

    def _build_rtcurve_settings_popup(self):
        popup_name = '{0}_settings_popup'.format(self.analysis_type)
        if hasattr(self, popup_name):
            self._initialize_panel(popup_name)
            self._build_panel(settings.rtcurve_popup_build_dict)
        else:
            self._create_popup_window(popup_name)
            self._build_panel(settings.rtcurve_popup_build_dict)
        row = 2
        self.selected_files_col_dict = {}
        for i, selected_file in enumerate(self.selected_files):
            col = 2 + i * 3
            basename = os.path.basename(selected_file)
            unique_widget_name = '_{0}_{1}_lineedit'.format(popup_name, basename)
            widget_settings = {'text': '{0}'.format(basename),
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            self.selected_files_col_dict[selected_file] = col
            row += self._add_checkboxes(popup_name, 'GRT Serial', self.grt_list, row, col)
            row += self._add_checkboxes(popup_name, 'Sample Res Factor', self.sample_res_factors, row, col)
            row += self._add_checkboxes(popup_name, 'GRT Res Factor', self.grt_res_factors, row, col)
            unique_widget_name = '_{0}_{1}_normal_res_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setText('2.0')
            row += 1
            unique_widget_name = '_{0}_{1}_label_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200, 'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            unique_widget_name = '_{0}_{1}_invert_checkbox'.format(popup_name, col)
            widget_settings = {'text': 'Invert?', 'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setChecked(True)
            row = 2
        if not hasattr(self, popup_name):
            self._create_popup_window(popup_name)
            self._build_panel(rtcurve_build_dict)
        getattr(self, popup_name).show()

    def _select_sample_res_factor_checkbox(self):
        sender = str(self.sender().whatsThis())
        identity_string =  'sample_res_factor'
        checkboxes = [x for x in dir(self) if identity_string in x and 'checkbox' in x]
        self._select_unique_checkbox(sender, identity_string)

    def _select_grt_res_factor_checkbox(self):
        sender = str(self.sender().whatsThis())
        identity_string =  'grt_res_factor'
        self._select_unique_checkbox(sender, identity_string)

    def _select_grt_serial_checkbox(self):
        sender = str(self.sender().whatsThis())
        identity_string = 'grt_serial'
        self._select_unique_checkbox(sender, identity_string)

    def _select_unique_checkbox(self, sender, identity_string):
        checkboxes = [x for x in dir(self) if identity_string in x and 'checkbox' in x]
        identity_string =  sender.split(identity_string)[0]
        checkboxes = [x for x in checkboxes if identity_string in x and 'checkbox' in x]
        for checkbox in checkboxes:
            if 'select' not in checkbox:
                if sender.replace(' ', '_').lower() in checkbox:
                    getattr(self, checkbox).setCheckState(True)
                else:
                    getattr(self, checkbox).setCheckState(False)

    def _close_rt(self):
        self.rtcurve_settings_popup.close()

    def _build_rt_input_dicts(self):
        list_of_input_dicts = []
        rt_settings = ['grt_serial', 'label', 'sample_res_factor',
                       'normal_res', 'invert', 'grt_res_factor']
        for selected_file, row in self.selected_files_col_dict.items():
            input_dict = {'data_path': selected_file}
            for setting in rt_settings:
                identity_string = '{0}_{1}'.format(row, setting)
                for widget in [x for x in dir(self) if identity_string in x]:
                    if 'checkbox' in widget and not 'invert' in widget:
                        if getattr(self, widget).isChecked():
                            setting_value = str(getattr(self, widget).text()).split(' ')[-1]
                            input_dict[setting] = float(setting_value)
                    elif 'checkbox' in widget and 'invert' in widget:
                        invert_bool = getattr(self, widget).isChecked()
                        input_dict['invert'] = invert_bool
                    elif 'lineedit' in widget:
                        widget_text = str(getattr(self, widget).text())
                        if len(widget_text) == 0:
                            widget_text = 'None'
                            input_dict[setting] = widget_text
                        elif self._isfloat(widget_text):
                            input_dict[setting] = float(widget_text)
                        else:
                            input_dict[setting] = widget_text
            list_of_input_dicts.append(copy(input_dict))
        return list_of_input_dicts

    def _isfloat(self, test_val):
        try:
            float(test_val)
            return True
        except ValueError:
            return False

    def _plot_rtcurve(self):
        selected_files = list(set(self.selected_files))
        list_of_input_dicts = self._build_rt_input_dicts()
        rt = RTCurve(list_of_input_dicts)
        rt.run()

    #################################################
    # IV Curves 
    #################################################

    def _close_iv(self):
        self.ivcurve_settings_popup.close()

    def _select_voltage_conversion_checkbox(self):
        sender = str(self.sender().whatsThis())
        identity_string =  'voltage_conversion'
        self._select_unique_checkbox(sender, identity_string)
        popup_name = 'ivcurve_settings_popup'
        col = sender.split('_')[4]
        if '1e-4' in sender:
            fit_lo_limit = 5.0
            fit_hi_limit = 10.0
            plot_lo_limit = 0.0
            plot_hi_limit = 40.0
        elif '1e-5' in sender:
            fit_lo_limit = 3.0
            fit_hi_limit = 8.0
            plot_lo_limit = 0.0
            plot_hi_limit = 12.0
        # Fit Limits
        unique_widget_name = '_{0}_{1}_v_fit_lo_lineedit'.format(popup_name, col)
        #if hasattr(self, unique_widget_name):
        getattr(self, unique_widget_name).setText(str(fit_lo_limit))
        unique_widget_name = '_{0}_{1}_v_fit_hi_lineedit'.format(popup_name, col)
        getattr(self, unique_widget_name).setText(str(fit_hi_limit))
        # Plot Limits
        unique_widget_name = '_{0}_{1}_v_plot_lo_lineedit'.format(popup_name, col)
        getattr(self, unique_widget_name).setText(str(plot_lo_limit))
        unique_widget_name = '_{0}_{1}_v_plot_hi_lineedit'.format(popup_name, col)
        getattr(self, unique_widget_name).setText(str(plot_hi_limit))

    def _select_squid_channel_checkbox(self):
        sender = str(self.sender().whatsThis())
        identity_string =  'squid_channel'
        squid = sender.split('_')[7]
        lineedit_unique_name = '_'.join(sender.split('_')[0:6])
        lineedit_unique_name += '_conversion_lineedit'
        getattr(self, lineedit_unique_name).setText(str(self.squid_channels[squid]))
        self._select_unique_checkbox(sender, identity_string)

    def _build_ivcurve_settings_popup(self, preset_parameters={}):
        popup_name = '{0}_settings_popup'.format(self.analysis_type)
        #pprint(preset_parameters)
        if hasattr(self, popup_name):
            self._initialize_panel(popup_name)
            self._build_panel(settings.ivcurve_popup_build_dict)
        else:
            self._create_popup_window(popup_name)
            self._build_panel(settings.ivcurve_popup_build_dict)
        row = 3
        self.selected_files_col_dict = {}
        optical_load, squid, voltage_conversion = None, None, None
        for i, selected_file in enumerate(self.selected_files):
            col = 2 + i * 6
            basename = os.path.basename(selected_file)
            unique_widget_name = '_{0}_{1}_lineedit'.format(popup_name, basename)
            widget_settings = {'text': '{0}'.format(basename),
                               'position': (row, col, 1, 1)}
            row += 1
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            self.selected_files_col_dict[selected_file] = col
            if selected_file in preset_parameters:
                squid = preset_parameters[selected_file]['_xy_collector_popup_squid_select_combobox']
            row += self._add_checkboxes(popup_name, 'SQUID Channel', self.squid_channels, row, col, squid=squid)
            unique_widget_name = '_{0}_{1}_squid_conversion_lineedit'.format(popup_name, col)
            widget_settings = {'text': '',
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            if squid is not None:
                getattr(self, unique_widget_name).setText(str(self.squid_calibration_dict[squid]))
            row += 1
            if selected_file in preset_parameters:
                voltage_conversion = preset_parameters[selected_file]['_xy_collector_popup_voltage_factor_combobox']
            row += self._add_checkboxes(popup_name, 'Voltage Conversion', self.voltage_conversion_list, row, col, voltage_conversion=voltage_conversion)
            unique_widget_name = '_{0}_{1}_label_lineedit'.format(popup_name, col)
            if selected_file in preset_parameters:
                plot_label = preset_parameters[selected_file]['_xy_collector_popup_sample_name_lineedit']
                optical_load = preset_parameters[selected_file]['_xy_collector_popup_optical_load_combobox']
                plot_label += ' {0}'.format(optical_load)
            widget_settings = {'text': plot_label, 'width': 200,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            unique_widget_name = '_{0}_{1}_v_fit_lo_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            if selected_file in preset_parameters:
                v_fit_lo = preset_parameters[selected_file]['_xy_collector_popup_fit_clip_lo_lineedit']
                getattr(self, unique_widget_name).setText(v_fit_lo)
            row += 1
            unique_widget_name = '_{0}_{1}_v_fit_hi_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            if selected_file in preset_parameters:
                v_fit_hi = preset_parameters[selected_file]['_xy_collector_popup_fit_clip_hi_lineedit']
                getattr(self, unique_widget_name).setText(v_fit_hi)
            row += 1
            unique_widget_name = '_{0}_{1}_v_plot_lo_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            if selected_file in preset_parameters:
                plot_clip_lo = preset_parameters[selected_file]['_xy_collector_popup_data_clip_lo_lineedit']
                getattr(self, unique_widget_name).setText(plot_clip_lo)
            row += 1
            unique_widget_name = '_{0}_{1}_v_plot_hi_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            if selected_file in preset_parameters:
                plot_clip_hi = preset_parameters[selected_file]['_xy_collector_popup_data_clip_hi_lineedit']
                getattr(self, unique_widget_name).setText(plot_clip_hi)
            row += 1
            unique_widget_name = '_{0}_{1}_calibration_resistance_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            unique_widget_name = '_{0}_{1}_fracrn_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            print(unique_widget_name)
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setText('0.75')
            row += 1
            unique_widget_name = '_{0}_{1}_color_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            print(unique_widget_name)
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            if optical_load == '77K':
                getattr(self, unique_widget_name).setText('b')
            elif optical_load == '300K':
                getattr(self, unique_widget_name).setText('r')
            else:
                getattr(self, unique_widget_name).setText('k')
            row += 1
            unique_widget_name = '_{0}_{1}_calibrate_checkbox'.format(popup_name, col)
            widget_settings = {'text': 'Calibrate?',
                               'position': (row, col, 1, 1)}
            print(unique_widget_name)
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setChecked(False)
            row += 1
            unique_widget_name = '_{0}_{1}_difference_checkbox'.format(popup_name, col)
            widget_settings = {'text': 'Difference?',
                               'position': (row, col, 1, 1)}
            print(unique_widget_name)
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setChecked(False)
            row += 1
            unique_widget_name = '_{0}_{1}_load_spectra_pushbutton'.format(popup_name, col)
            widget_settings = {'text': 'Load Spectra', 'function': self._load_spectra,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            print(unique_widget_name)
            unique_widget_name = '_{0}_{1}_loaded_spectra_label'.format(popup_name, col)
            widget_settings = {'text': '',
                               'position': (row, col + 1, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            print(unique_widget_name)
            self._load_spectra(simulated_frequency_band=True, set_to_widget=unique_widget_name)
            row = 3
        if not hasattr(self, popup_name):
            self._create_popup_window(popup_name)
            self._build_panel(rtcurve_build_dict)
        getattr(self, popup_name).showMaximized()

    def _build_iv_input_dicts(self):
        list_of_input_dicts = []
        iv_settings = ['voltage_conversion', 'label', 'squid_conversion', 'color', 'fracrn',
                       'v_fit_lo', 'v_fit_hi', 'v_plot_lo', 'v_plot_hi', 'v_plot_lo', 'v_plot_hi',
                       'calibration_resistance', 'calibrate', 'difference', 'loaded_spectra']
        for selected_file, col in self.selected_files_col_dict.items():
            input_dict = {'data_path': selected_file}
            for setting in iv_settings:
                identity_string = '{0}_{1}'.format(col, setting)
                for widget in [x for x in dir(self) if identity_string in x]:
                    if 'checkbox' in widget and 'difference' in widget:
                        invert_bool = getattr(self, widget).isChecked()
                        input_dict['difference'] = invert_bool
                        pprint(input_dict)
                    elif 'checkbox' in widget and not 'calibrate' in widget:
                        if getattr(self, widget).isChecked():
                            setting_value = str(getattr(self, widget).text()).split(' ')[-1]
                            input_dict[setting] = float(setting_value)
                    elif 'checkbox' in widget and 'calibrate' in widget:
                        invert_bool = getattr(self, widget).isChecked()
                        input_dict['calibrate'] = invert_bool
                    elif 'lineedit' in widget and ('label' in widget or 'color' in widget):
                        widget_text = str(getattr(self, widget).text())
                        input_dict[setting] = widget_text
                    elif 'lineedit' in widget:
                        widget_text = str(getattr(self, widget).text())
                        if len(widget_text) == 0:
                            widget_text = 'None'
                            input_dict[setting] = widget_text
                        else:
                            input_dict[setting] = float(widget_text)
                    elif setting == 'loaded_spectra':
                        print(setting, 'loaded')
                        input_dict[setting] = self.loaded_spectra_data_path
                    elif 'label' in widget:
                        print(setting, 'else')
                        widget_text = str(getattr(self, widget).text())
                        input_dict[setting] = widget_text
            pprint(input_dict)
            list_of_input_dicts.append(copy(input_dict))
        return list_of_input_dicts

    def _load_spectra(self, clicked=True, simulated_frequency_band=False, set_to_widget=None):
        sender_str = str(self.sender().whatsThis())
        if simulated_frequency_band:
            data_path = os.path.join(self.simulated_bands_folder, 'PB2abcBands.csv')
        else:
            data_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', self.simulated_bands_folder)[0]
            base = sender_str.split('_load')[0]
            set_to_widget = '{0}_loaded_spectra_label'.format(base)
        short_data_path = data_path.split('BolometerCharacterization')[-1]
        self.loaded_spectra_data_path = data_path
        getattr(self, set_to_widget).setText(str(short_data_path))

    def _plot_ivcurve(self):
        selected_files = list(set(self.selected_files))
        list_of_input_dicts = self._build_iv_input_dicts()
        pprint(list_of_input_dicts)
        iv = IVCurve(list_of_input_dicts)
        iv.run()

    #################################################
    # POL Curves 
    #################################################

    def _close_pol(self):
        self.polcurve_settings_popup.close()

    def _build_polcurve_settings_popup(self):
        popup_name = '{0}_settings_popup'.format(self.analysis_type)
        if hasattr(self, popup_name):
            self._initialize_panel(popup_name)
            self._build_panel(settings.polcurve_popup_build_dict)
        else:
            self._create_popup_window(popup_name)
            self._build_panel(settings.polcurve_popup_build_dict)
        row = 3
        self.selected_files_col_dict = {}
        for i, selected_file in enumerate(self.selected_files):
            # update dict with column file mapping
            col = 1 + i * 2
            basename = os.path.basename(selected_file)
            self.selected_files_col_dict[selected_file] = col
            # Add the file name for organization
            unique_widget_name = '_{0}_{1}_label'.format(popup_name, basename)
            widget_settings = {'text': '{0}'.format(basename),
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add a lineedit for plot labeling
            unique_widget_name = '_{0}_{1}_plot_label_lineedit'.format(popup_name, col)
            widget_settings = {'text': '',
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add an "color" lineedit
            unique_widget_name = '_{0}_{1}_color_lineedit'.format(popup_name, col)
            widget_settings = {'text': 'b',
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add an "xlim" lineedit
            unique_widget_name = '_{0}_{1}_xlim_lineedit'.format(popup_name, col)
            widget_settings = {'text': '-10:360',
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            # Add an "step2deg" lineedit
            unique_widget_name = '_{0}_{1}_degsperpoint_lineedit'.format(popup_name, col)
            widget_settings = {'text': '1.0',
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row = 3
        getattr(self, popup_name).show()

    def _build_pol_input_dicts(self):
        list_of_input_dicts = []
        pol_settings = ['xlim', 'color', 'degsperpoint', 'plot_label']
        for selected_file, col in self.selected_files_col_dict.items():
            input_dict = {'measurements': {'data_path': selected_file}}
            for setting in pol_settings:
                identity_string = '{0}_{1}'.format(col, setting)
                print(identity_string)
                for widget in [x for x in dir(self) if identity_string in x]:
                    if 'lineedit' in widget:
                        widget_text = str(getattr(self, widget).text())
                        if 'xlim' in widget:
                            widget_text = (int(widget_text.split(':')[0]), int(widget_text.split(':')[1]))
                        input_dict['measurements'][setting] = widget_text
            list_of_input_dicts.append(copy(input_dict))
        pprint(list_of_input_dicts)
        return list_of_input_dicts

    def _plot_polcurve(self):
        selected_files = list(set(self.selected_files))
        list_of_input_dicts = self._build_pol_input_dicts()
        pprint(list_of_input_dicts)
        pol = POLCurve()
        pol.run(list_of_input_dicts)

