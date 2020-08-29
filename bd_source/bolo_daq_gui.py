import sys
import nidaqmx
import chardet
import imageio
import smtplib
import serial
import simplejson
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
from PyPDF2 import PdfFileMerger
from pprint import pprint, pformat
from datetime import datetime
from copy import copy
from PyQt5 import QtCore, QtGui, QtWidgets

# Settings and Widgets
from bd_settings.bd_global_settings import settings
from bd_tools.xy_collector import XYCollector
from bd_tools.fridge_cycle import FridgeCycle
from bd_tools.data_plotter import DataPlotter
from bd_tools.lakeshore_372 import LakeShore372
from bd_tools.configure_daq import ConfigureDAQ
from bd_tools.cosmic_rays import CosmicRays
from bd_tools.beam_mapper import BeamMapper
from bd_tools.time_constant import TimeConstant
from bd_tools.agilent_e3634a import AgilentE3634A
from bd_tools.com_port_utility import ComPortUtility
from bd_tools.configure_bolo_daq import ConfigureBoloDAQ
from bd_tools.polarization_efficiency import PolarizationEfficiency
from bd_tools.configure_stepper_motor import ConfigureStepperMotor
from bd_tools.fourier_transform_spectrometer import FourierTransformSpectrometer
from bd_tools.stanford_research_systems_sr830_dsp import StanfordResearchSystemsSR830DSP
# Libraries
from bd_lib.fourier import Fourier
from bd_lib.bolo_daq import BoloDAQ
from bd_lib.bolo_serial import BoloSerial
from GuiBuilder.gui_builder import GuiBuilder

#from RT_Curves.plot_rt_curves import RTCurve
#from IV_Curves.plot_iv_curves import IVCurve
#from FTS_Curves.plot_fts_curves import FTSCurve
#from Beam_Maps.beam_mapper_tools import BeamMapperTools
#from POL_Curves.plot_pol_curves import PolCurve
#from TAU_Curves.plot_tau_curves import TAUCurve
#from FTS_DAQ.fts_daq import FTSDAQ
#from FTS_DAQ.analyzeFTS import FTSanalyzer
#from LockIn.lock_in import LockIn
#from PowerSupply.power_supply import PowerSupply
#from FridgeCycle.fridge_cycle import FridgeCycle


class BoloDAQGui(QtWidgets.QMainWindow, GuiBuilder):

    def __init__(self, screen_resolution, qt_app):
        '''
        '''
        super(BoloDAQGui, self).__init__()
        self.qt_app = qt_app
        self.__apply_settings__(settings)
        self.screen_resolution = screen_resolution
        grid = QtWidgets.QGridLayout()
        self.splash_screen = QtWidgets.QSplashScreen()
        self.splash_screen_image_path = os.path.join('bd_settings', 'BoloPic.JPG')
        q_splash_image = QtGui.QPixmap(self.splash_screen_image_path)
        x_scale = int(self.screen_resolution.width() * 0.4)
        y_scale = int(self.screen_resolution.height() * 0.5)
        q_splash_image = q_splash_image.scaled(x_scale, y_scale, QtCore.Qt.KeepAspectRatio)
        self.splash_screen.setPixmap(q_splash_image)
        self.splash_screen.show()
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setWhatsThis('cw_panel')
        self.central_widget.setLayout(grid)
        self.setCentralWidget(self.central_widget)
        self.grid = self.central_widget.layout()
        self.simulated_bands_folder = './FTS_Curves/Simulations'
        self.sample_dict_folder = './Sample_Dicts'
        grid = QtWidgets.QGridLayout()
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setWhatsThis('cw_panel')
        self.central_widget.setLayout(grid)
        self.setCentralWidget(self.central_widget)
        self.tool_and_menu_bar_json_path = os.path.join('bd_settings', 'tool_and_menu_bars.json')
        self.gb_setup_menu_and_tool_bars(self.tool_and_menu_bar_json_path)
        self.selected_files = []
        self.current_stepper_position = 100
        self.user_desktop_path = os.path.expanduser('~')
        self.monitor_dpi = 120.0
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = './Data/{0}'.format(self.today_str)
        self.squid_channels = settings.xy_collector_combobox_entry_dict['_xy_collector_popup_squid_select_combobox']
        self.voltage_conversion_list = settings.xy_collector_combobox_entry_dict['_xy_collector_popup_voltage_factor_combobox']
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        self.raw_data_path = None
        #self.fts_analyzer = FTSanalyzer()
        #self.fts = FTSCurve()
        #self.fourier = Fourier()
        self.bd_setup_status_bar()
        self.loaded_spectra_data_path = None
        self.ls372_widget = None
        self.bd_get_active_serial_ports()
        self.bd_configure_daq()
        self.splash_screen.close()
        self.move(50, 50)
        self.show()

    ##################################################################################
    #### Start up Tasks ##############################################################
    ##################################################################################

    def __apply_settings__(self, settings):
        for setting in dir(settings):
            if '__' not in setting:
                setattr(self, setting, getattr(settings, setting))

    def bd_close_main(self):
        '''
        '''
        self.close()

    def bd_get_available_daqs(self):
        '''
        '''
        if hasattr(self, 'available_daqs'):
            return None
        self.daq = BoloDAQ()
        if not hasattr(self, 'active_daqs'):
            self.bd_get_active_daqs()
        self.available_daqs = {}
        self.splash_screen.showMessage('Configure NIDAQ: Deterimining all available daqs')
        QtWidgets.QApplication.processEvents()
        for device, configuration_dict in self.active_daqs.items():
            available = True
            for i in range(2):
                for j in range(8):
                    self.splash_screen.showMessage("Configuring NIDAQ: Checking if {0}:::ch{1} is available ({2}/2)".format(device, j, i + 1))
                    QtWidgets.QApplication.processEvents()
                    try:
                        vol_ts, vol_mean, vol_min, vol_max, vol_std = self.daq.get_data(signal_channel=j,
                                                                                        int_time=100,
                                                                                        sample_rate=1000,
                                                                                        device=device)
                    except nidaqmx.errors.DaqError:
                        self.splash_screen.showMessage("Configuring NIDAQ {0}:::ch{1} is not available".format(device, j))
                        QtWidgets.QApplication.processEvents()
                        available = False
                        break
            if available:
                self.available_daqs[device] = configuration_dict
        n_devices = len(self.available_daqs)
        devices = list(self.available_daqs.keys())
        self.status_bar.showMessage('Found {0} available devices: {1}'.format(n_devices, devices))

    def bd_get_active_daqs(self):
        '''
        '''
        if os.path.exists(os.path.join('bd_settings', 'daq_settings.json')):
            with open(os.path.join('bd_settings', 'daq_settings.json'), 'r') as json_handle:
                self.active_daqs = simplejson.load(json_handle)
        else:
            self.active_daqs = self.daq.get_active_daqs()


    def bd_setup_status_bar(self):
        '''
        '''
        custom_widgets = []
        #custom_widgets.append(custom_widget)
        permanant_messages = ['Bolo DAQ B.W. 2020']
        self.gb_add_status_bar(permanant_messages=permanant_messages , add_saved=True, custom_widgets=custom_widgets)

    #################################################
    # Com ports
    #################################################

    def bd_get_active_serial_ports(self):
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
        self.active_ports = []
        for port in ports:
            self.splash_screen.showMessage('Checking COM Port {0}'.format(port))
            try:
                s = serial.Serial(port)
                s.close()
                self.active_ports.append(port)
            except (OSError, serial.SerialException):
                pass
        self.active_ports
        #self.bd_get_com_device_types()

    def bd_get_com_device_types(self):
        '''
        '''
        self.lab_devices = [
            'Model372',
            'E3634A',
            ]
        self.com_port_dict = {}
        active_ports = copy(self.active_ports)
        for device in self.lab_devices:
            for active_port in active_ports:
                print()
                print(self.active_ports)
                print(device, active_port)
                serial_com = BoloSerial(port=active_port, device=device, splash_screen=self.splash_screen)
                id_string = serial_com.write_read('*IDN? ')
                self.splash_screen.showMessage("Checking to see what's connected to COM{0} ::: ID = {1}".format(device, id_string))
                print(device in str(id_string))
                print(device)
                print(id_string, type(id_string))
                if device in str(id_string):
                    if not device in self.com_port_dict:
                        self.com_port_dict[device] = comport
                        active_ports.pop(active_port)
                        break
                    else:
                        import ipdb;ipdb.set_trace()
                serial_com.close()
        pprint(self.com_port_dict)


    def bd_configure_com_ports(self):
        '''
        '''
        self.active_ports

    #################################################
    # Logging and File Management
    #################################################

    def bd_final_plot(self):
        print('Dummy Function')

    def bd_create_log(self):
        date_str = datetime.strftime(datetime.now(), '%Y_%m_%d')
        log_file_name = 'Data_Log_{0}.txt'.format(date_str)
        self.data_log_path = os.path.join(self.data_folder, log_file_name)
        if not os.path.exists(self.data_log_path):
            header = 'Data log for {0}\n'.format(date_str)
            with open(self.data_log_path, 'w') as data_log_handle:
                data_log_handle.write(header)

    def bd_update_log(self):
        if not hasattr(self, 'data_log_path'):
            self.bd_create_log()
        if hasattr(self, 'raw_data_path') and self.raw_data_path is not None:
            temp_log_file_name = 'temp_log.txt'
            notes = self.gb_quick_info_gather()
            response = self.gb_quick_message('Use Data in Analysis?', add_yes=True, add_no=True)
            if response == QtWidgets.QMessageBox.Yes:
                self.bd_copy_file_to_analysis_folder()
            with open(temp_log_file_name, 'w') as temp_log_handle:
                with open(self.data_log_path, 'r') as log_handle:
                    for line in log_handle.readlines():
                        temp_log_handle.write(line)
                    new_line = '{0}\t{1}\n'.format(self.raw_data_path[0], notes)
                    temp_log_handle.write(new_line)
            shutil.copy(temp_log_file_name, self.data_log_path)

    def bd_copy_file_to_analysis_folder(self):
        for_analysis_folder = os.path.join(self.data_folder, 'For_Analysis')
        if not os.path.exists(for_analysis_folder):
            os.makedirs(for_analysis_folder)
        data_path = self.raw_data_path[0]
        if '.if' in data_path:
            data_path = data_path.replace('.if', '.fft')
        shutil.copy(data_path, for_analysis_folder)
        #import ipdb;ipdb.set_trace()


    def bd_connect_to_com_port(self, com_port=None):
        sender_whats_this_str = str(self.sender().whatsThis())
        current_string, position_string, velocity_string, acceleration_string = 'NA', 'NA', 'NA', 'NA'
        if type(self.sender()) == QtWidgets.QComboBox:
            com_port = self.get_com_port(combobox=sender_whats_this_str)
            if len(com_port) == 0:
                return None
        elif com_port is not None and type(com_port) is str:
            com_port = com_port
        else:
            message = 'Not a combobox sender and no comport explicitly specificied, no connection made'
            print(message, com_port)
            self.gb_quick_message(message)
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
            self.gb_quick_message(message)
            error = True
        else:
            message = 'Successful connection to stepper motor on {0}\n'.format(com_port)
            message += 'Current: {0} (A)\n'.format(current_string)
            message += 'Velocity: {0} (mm/s)\n'.format(velocity_string)
            message += 'Acceleration: {0} (mm/s/s)\n'.format(acceleration_string)
            message += 'Position: {0} (steps)\n'.format(position_string)
            message += 'You can change these motor stettings using the "User Move Stepper" App'
#            self.gb_quick_message(message)
            error = False
        if 'user_move_stepper' in sender_whats_this_str and not error:
            if self.gb_is_float(position_string):
                getattr(self, '_user_move_stepper_popup_current_position_label').setText('{0} (steps)'.format(position_string))
                getattr(self, '_user_move_stepper_popup_move_to_position_lineedit').setText('{0}'.format(position_string))
                getattr(self, '_user_move_stepper_popup_stepper_slider').setSliderPosition(int(position_string))
            if self.gb_is_float(current_string, enforce_positive=True):
                getattr(self, '_user_move_stepper_popup_actual_current_label').setText('{0} (A)'.format(current_string))
                getattr(self, '_user_move_stepper_popup_set_current_to_lineedit').setText('{0}'.format(current_string))
            if self.gb_is_float(velocity_string, enforce_positive=True):
                getattr(self, '_user_move_stepper_popup_actual_velocity_label').setText('{0} (mm/s)'.format(velocity_string))
                getattr(self, '_user_move_stepper_popup_set_velocity_to_lineedit').setText('{0}'.format(velocity_string))
            if self.gb_is_float(acceleration_string, enforce_positive=True):
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

    def bd_verify_params(self):
        sender = str(self.sender().whatsThis())
        if '_single_channel_fts' in sender:
            meta_data = self.bd_get_all_meta_data(popup='_single_channel_fts')
            scan_params = self.bd_get_all_params(meta_data, settings.fts_scan_params, 'single_channel_fts')
            params_str = pformat(scan_params, indent=2)
        if '_pol_efficiency' in sender:
            meta_data = self.bd_get_all_meta_data(popup='_pol_efficiency')
            scan_params = self.bd_get_all_params(meta_data, settings.pol_efficiency_scan_params, 'pol_efficiency')
            params_str = pformat(scan_params, indent=2)
        response = self.gb_quick_message(params_str, add_cancel=True, add_apply=True)
        if response == QtWidgets.QMessageBox.Cancel:
            return True
        elif response == QtWidgets.QMessageBox.Apply:
            return False

    #################################################
    # Generica Control Function (Common to all DAQ Types)
    #################################################

    def bd_create_sample_dict_path(self):
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
            self.gb_quick_message('Please Record Pump and Oil Level\nNew info not saved!')
            return None
        sample_dict_path = './Sample_Dicts/{0}.json'.format(self.today_str)
        response = None
        if total_len_of_names == 0 and os.path.exists(sample_dict_path):
            warning_msg = 'Warning! {0} exists and you are '.format(sample_dict_path)
            warning_msg += 'going to overwrite with blank names for all channels'
            response = self.gb_quick_info_gather(warning_msg)
            #response = self.gb_quick_message(warning_msg, add_save=True, add_cancel=True)

            if response == QtWidgets.QMessageBox.Save:
                with open(sample_dict_path, 'w') as sample_dict_file_handle:
                    simplejson.dump(self.sample_dict, sample_dict_file_handle)
                getattr(self, '_daq_main_panel_set_sample_dict_path_label').setText('Set Path @ {0}'.format(sample_dict_path))
        else:
            with open(sample_dict_path, 'w') as sample_dict_file_handle:
                simplejson.dump(self.sample_dict, sample_dict_file_handle)
            getattr(self, '_daq_main_panel_set_sample_dict_path_label').setText('Set Path @ {0}'.format(sample_dict_path))

    def bd_update_meta_data(self, meta_data=None):
        if 'xy_collector' in self.sender().whatsThis():
            meta_data = self.bd_get_all_meta_data(popup='xy_collector')
        elif 'single_channel_fts' in self.sender().whatsThis():
            meta_data = self.bd_get_all_meta_data(popup='single_channel_fts')
        if self.raw_data_path is not None and meta_data is not None:
            with open(self.raw_data_path[0].replace('.dat', '.json'), 'w') as meta_data_handle:
                simplejson.dump(meta_data, meta_data_handle)

    def bd_get_all_meta_data(self, popup=None):
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

    #################################################
    #################################################
    # DAQ TYPE SPECFIC CODES
    #################################################
    #################################################

    #################################################
    # Fridge Cycle
    #################################################

    def bd_fridge_cycle(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        self.fridge_cycle_widget = FridgeCycle(self.status_bar)
        self.central_widget.layout().addWidget(self.fridge_cycle_widget, 0, 0, 1, 1)

    #################################################
    # Configure DAQ
    #################################################

    def bd_configure_daq(self):
        '''
        '''
        self.bd_get_available_daqs()
        self.gb_initialize_panel('central_widget')
        self.configure_daq_widget = ConfigureDAQ(self.available_daqs, self.status_bar)
        self.central_widget.layout().addWidget(self.configure_daq_widget, 0, 0, 1, 1)

    #################################################
    # Data Plotter 
    #################################################

    def bd_data_plotter(self):
        self.gb_initialize_panel('central_widget')
        self.data_plotter_widget = DataPlotter(self.status_bar, self.screen_resolution, self.monitor_dpi, self.data_folder)
        self.central_widget.layout().addWidget(self.data_plotter_widget, 0, 0, 1, 1)

    #################################################
    # XY COLLECTOR
    #################################################

    def bd_xy_collector(self):
        '''
        Opens the panel and sets som defaults
        '''
        self.gb_initialize_panel('central_widget')
        self.xyc_widget = XYCollector(self.available_daqs, self.status_bar, self.screen_resolution, self.monitor_dpi)
        self.central_widget.layout().addWidget(self.xyc_widget, 0, 0, 1, 1)

    #################################################
    # Configure Stepper Motors
    #################################################

    def bd_configure_stepper_motor(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        dialog = 'Select the comport for the stepper motor you wish to configure'
        stepper_motor_ports = ['COM12', 'COM13', 'COM14']
        com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=stepper_motor_ports)
        if not hasattr(self, 'sm_{0}'.format(com_port)) and okPressed:
            csm_widget = ConfigureStepperMotor(com_port, self.status_bar)
            csm_serial_com = csm_widget.csm_get_serial_com()
            setattr(self, 'sm_{0}'.format(com_port), csm_serial_com)
        elif okPressed:
            serial_com = getattr(self, 'sm_{0}'.format(com_port))
            csm_widget = ConfigureStepperMotor(com_port, self.status_bar, serial_com=serial_com)
        else:
            return None
        self.central_widget.layout().addWidget(csm_widget, 0, 0, 1, 1)
        self.status_bar.showMessage('Ready!')

    #################################################
    # Lakeshore
    #################################################

    def bd_lakeshore_372(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        dialog = 'Select the comport for the Lakeshore'
        if not hasattr(self, 'lakeshore_serial_com'):
            if self.ls_372_widget is None:
                #com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=self.active_ports)
                #okPressed = True
                #if okPressed:
                com_port = 'COM6'
                self.lakeshore_com_port = com_port
                self.ls_372_widget = LakeShore372(com_port, self.status_bar)
        if self.ls_372_widget is not None:
            self.central_widget.layout().addWidget(self.ls_372_widget, 0, 0, 1, 1)

    #################################################
    # COSMIC RAYS
    #################################################

    def bd_cosmic_rays(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        if not hasattr(self, 'cosmic_ray_widget'):
            self.cosmic_ray_widget = CosmicRays(self.available_daqs, self.status_bar, self.screen_resolution, self.monitor_dpi)
        self.cosmic_ray_widget.cr_display_daq_settings()
        self.central_widget.layout().addWidget(self.cosmic_ray_widget, 0, 0, 1, 1)

    #################################################
    # TIME CONSTANT 
    #################################################

    def bd_time_constant(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        if not hasattr(self, 'time_constant_widget'):
            self.time_constant_widget = TimeConstant(self.available_daqs, self.status_bar, self.screen_resolution, self.monitor_dpi)
        #self.time_constant_widget.tc_display_daq_settings()
        self.central_widget.layout().addWidget(self.time_constant_widget, 0, 0, 1, 1)

    #################################################
    # BEAM MAPPER 
    #################################################

    def bd_beam_mapper(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        stepper_motor_ports = ['COM13', 'COM14']
        self.csm_widget_dict = {}
        for dim in ('X', 'Y'):
            dialog = 'Select the comport for the {0} stepper motor you wish to configure'.format(dim)
            sm_com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=stepper_motor_ports)
            if not hasattr(self, 'sm_{0}'.format(sm_com_port)) and okPressed:
                csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar)
                csm_serial_com = csm_widget.csm_get_serial_com()
                setattr(self, 'sm_{0}'.format(sm_com_port), csm_serial_com)
            elif okPressed:
                serial_com = getattr(self, 'sm_{0}'.format(sm_com_port))
                csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar, serial_com=serial_com)
            else:
                return None
            stepper_motor_ports.pop(stepper_motor_ports.index(sm_com_port))
            self.csm_widget_dict[dim] = csm_widget
        if not hasattr(self, 'beam_mapper_widget'):
            self.beam_mapper_widget = BeamMapper(self.available_daqs, self.status_bar, self.screen_resolution, self.monitor_dpi, self.csm_widget_dict)
        #self.time_constant_widget.tc_display_daq_settings()
        self.central_widget.layout().addWidget(self.beam_mapper_widget, 0, 0, 1, 1)

    #################################################
    # Polarization Efficiency
    #################################################

    def bd_polarization_efficiency(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        dialog = 'Select the comport for the X stepper motor you wish to configure'
        stepper_motor_ports = ['COM12']
        sm_com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=stepper_motor_ports)
        if not hasattr(self, 'sm_{0}'.format(sm_com_port)) and okPressed:
            csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar)
            csm_serial_com = csm_widget.csm_get_serial_com()
            setattr(self, 'sm_{0}'.format(sm_com_port), csm_serial_com)
        elif okPressed:
            serial_com = getattr(self, 'sm_{0}'.format(sm_com_port))
            csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar, serial_com=serial_com)
        else:
            return None
        if not hasattr(self, 'polarization_efficiency_widget'):
            self.polarization_efficiency_widget = PolarizationEfficiency(self.available_daqs, self.status_bar, self.screen_resolution, self.monitor_dpi, csm_widget)
        #self.polarization_efficiency_widget.pe_display_daq_settings()
        self.central_widget.layout().addWidget(self.polarization_efficiency_widget, 0, 0, 1, 1)

    #################################################
    # SINGLE CHANNEL FTS BILLS
    #################################################

    def bd_fts(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        dialog = 'Select the comport for the stepper motor you wish to configure'
        stepper_motor_ports = ['COM12']
        sm_com_port, okPressed = self.gb_quick_static_info_gather(title='', dialog=dialog, items=stepper_motor_ports)
        if not hasattr(self, 'sm_{0}'.format(sm_com_port)) and okPressed:
            csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar)
            csm_serial_com = csm_widget.csm_get_serial_com()
            setattr(self, 'sm_{0}'.format(sm_com_port), csm_serial_com)
        elif okPressed:
            serial_com = getattr(self, 'sm_{0}'.format(sm_com_port))
            csm_widget = ConfigureStepperMotor(sm_com_port, self.status_bar, serial_com=serial_com)
        else:
            return None
        if not hasattr(self, 'fts_widget'):
            self.fts_widget = FourierTransformSpectrometer(self.available_daqs, self.status_bar, self.screen_resolution, self.monitor_dpi, csm_widget)
        self.central_widget.layout().addWidget(self.fts_widget, 0, 0, 1, 1)

    #################################################
    # Configure the GUI
    #################################################

    def bd_configure_bolo_daq(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        if not hasattr(self, 'configure_bolo_daq_widget'):
            self.configure_bolo_daq_widget = ConfigureBoloDAQ(self.available_daqs, self.status_bar, self.screen_resolution, self.monitor_dpi)
        #self.time_constant_widget.tc_display_daq_settings()
        self.central_widget.layout().addWidget(self.configure_bolo_daq_widget, 0, 0, 1, 1)

    #################################################
    # Lock in SRS SR830 DSP
    #################################################

    def bd_stanford_research_systems_sr830_dsp(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        if not hasattr(self, 'srs_sr830dsp_widget'):
            self.srs_sr830dsp_widget = StanfordResearchSystemsSR830DSP(self.available_daqs, self.status_bar, self.screen_resolution, self.monitor_dpi)
        #self.time_constant_widget.tc_display_daq_settings()
        self.central_widget.layout().addWidget(self.srs_sr830dsp_widget, 0, 0, 1, 1)

    #################################################
    # Comport Utility
    #################################################

    def bd_com_port_utility(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        if not hasattr(self, 'com_port_utility_widget'):
            self.com_port_utility_widget = ComPortUtility(self.available_daqs, self.status_bar, self.screen_resolution, self.monitor_dpi)
        #self.time_constant_widget.tc_display_daq_settings()
        self.central_widget.layout().addWidget(self.com_port_utility_widget, 0, 0, 1, 1)

    #################################################
    # Power Supply Agilent E3634A
    #################################################

    def bd_agilent_e3634a(self):
        '''
        '''
        self.gb_initialize_panel('central_widget')
        if not hasattr(self, 'agilent_e3634a_widget'):
            self.agilent_e3634a_widget = AgilentE3634A(self.available_daqs, self.status_bar, self.screen_resolution, self.monitor_dpi)
        #self.time_constant_widget.tc_display_daq_settings()
        self.central_widget.layout().addWidget(self.agilent_e3634a_widget, 0, 0, 1, 1)

if __name__ == '__main__':
    qt_app = QtWidgets.QApplication(sys.argv)
    qt_app.setFont(QtGui.QFont('SansSerif', 10))
    screen_resolution = qt_app.desktop().screenGeometry()
    gui = BoloDAQGui(screen_resolution, qt_app)
    gui.show()
    exit(qt_app.exec_())

