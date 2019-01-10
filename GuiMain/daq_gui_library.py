import sys
import json
import os
import subprocess
import shutil
import time
import numpy as np
import datetime
import pylab as pl
import matplotlib.pyplot as plt
import time
import threading
from Tkinter import *
from PyPDF2 import PdfFileMerger
from pprint import pprint
from datetime import datetime
from copy import copy
from PyQt4 import QtCore, QtGui
from libraries.gen_class import Class
from ba_settings.all_settings import settings
from RT_Curves.plot_rt_curves import RTCurve
from IV_Curves.plot_iv_curves import IVCurve
from FTS_Curves.plot_fts_curves import FTSCurve
from FTS_Curves.numerical_processing import Fourier
from POL_Curves.plot_pol_curves import POLCurve
from TAU_Curves.plot_tau_curves import TAUCurve
from FTS_DAQ.fts_daq import FTSDAQ
from BeamMapping.beam_map_daq import BeamMapDAQ
from Motor_Driver.stepper_motor import stepper_motor
from FTS_DAQ.analyzeFTS import FTSanalyzer
#from DAQ.daq import DAQ
from realDAQ.daq import DAQ


#Global variables
continue_run = True
root = Tk()

class DAQGuiTemplate(QtGui.QWidget):


    def __init__(self, screen_resolution):
        super(DAQGuiTemplate, self).__init__()
        self.grid = QtGui.QGridLayout()
        self.grid.setVerticalSpacing(0)
        self.setLayout(self.grid)
        self.__apply_settings__(settings)
        self._create_main_window('daq_main_panel_widget')
        self.data_folder = './data'
        self.sample_dict_folder = './Sample_Dicts'
        self.selected_files = []
        self.current_stepper_position = 100
        self.daq = DAQ()
        self.user_desktop_path = os.path.expanduser('~')
        self.fts_analyzer = FTSanalyzer()
        self.fts_daq = FTSDAQ()
        self.real_daq = DAQ()
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

    def __apply_settings__(self, settings):
        for setting in dir(settings):
            if '__' not in setting:
                setattr(self, setting, getattr(settings, setting))

    def _create_main_window(self, name):
        self._create_popup_window(name)
        self._build_panel(settings.daq_main_panel_build_dict)

    def _close_main(self):
        self.daq_main_panel_widget.close()
        sys.exit()

    def _dummy(self):
        print 'Dummy Function'

    def _final_plot(self):
        print 'Dummy Function'

    #################################################
    # Stepper Motor and Com ports
    #################################################

    def _connect_to_com_port(self, beammapper=None, single_channel_fts=None):
        combobox = str(self.sender().whatsThis())
        print self.sender()
        print self.sender().whatsThis()
        current_string, position_string,velocity_string = '0','0','0'
        if type(self.sender()) == QtGui.QComboBox:
            com_port = self._get_com_port(combobox=combobox)
            connection = combobox.replace('current_com_port_combobox','successful_connection_header_label')
            if com_port in ['COM1', 'COM8','COM2','COM3']:
                if not hasattr(self, 'sm_{0}'.format(com_port)):
                    setattr(self, 'sm_{0}'.format(com_port), stepper_motor(com_port))
                    import ipdb;ipdb.set_trace()
                    current_string = getattr(self, 'sm_{0}'.format(com_port)).get_motor_current().strip('CC=')
                    position_string = getattr(self, 'sm_{0}'.format(com_port)).get_position().strip('SP=')
                    velocity_string = getattr(self, 'sm_{0}'.format(com_port)).get_velocity().strip('VE=')
                else:
                    current_string, position_string,velocity_string = '0','0','0'
            getattr(self,connection).setText('Successful Connection to '+ com_port +'!' )
        else:
            print 'not a combobox'
            #popup = str(self.sender().currentText())
            #if popup == 'Pol Efficiency':
                #com_port = 'COM6'
                #connection = '_pol_efficiency_popup_successful_connection_header_label'
            #elif popup == 'Beam Mapper':
                #if beammapper == 1:
                    #com_port = 'COM6'
                    #connection = '_beam_mapper_popup_x_successful_connection_header_label'
                    #popup_combobox = '_beam_mapper_popup_x_current_com_port_combobox'
                    #getattr(self, popup_combobox).setCurrentIndex(0)
		#elif beammapper == 2:
                    #com_port = 'COM2'
                    #connection = '_beam_mapper_popup_y_successful_connection_header_label'
                    #popup_combobox = '_beam_mapper_popup_y_current_com_port_combobox'
                    #getattr(self, popup_combobox).setCurrentIndex(1)
            #elif popup == 'Single Channel Fts':
                 #if single_channel_fts == 1:
                    #com_port = 'COM6'
                    #connection = '_single_channel_fts_popup_successful_connection_header_label'
                    #popup_combobox = '_single_channel_fts_popup_current_com_port_combobox'
                    #getattr(self, popup_combobox).setCurrentIndex(0)
            #elif single_channel_fts == 2:
                    #com_port = 'COM2'
                    #connection = '_single_channel_fts_popup_grid_successful_connection_header_label'
                    #popup_combobox = '_single_channel_fts_popup_grid_current_com_port_combobox'
            #elif popup == 'User Move Stepper':
                #com_port = 'COM6'
                #connection = '_user_move_stepper_popup_successful_connection_header_label'
        #port_number = int(com_port.strip('COM')) - 1
        #init_string = '/dev/ttyUSB{0}'.format(port_number)
        return current_string, position_string, velocity_string

    def _get_com_port(self, combobox):
        com_port = str(getattr(self, combobox).currentText())
        return com_port

    #################################################
    # Generica Control Function (Common to all DAQ Types)
    #################################################

    def _create_sample_dict_path(self):
        self.sample_dict = {}
        for i in range(1, 7):
            widget = '_daq_main_panel_set_sample_{0}_lineedit'.format(i)
            sample_name = str(getattr(self, widget).text())
            self.sample_dict[str(i)] = sample_name
        sample_dict_path = './Sample_Dicts/{0}.json'.format(self.today_str)
        with open(sample_dict_path, 'w') as sample_dict_file_handle:
            json.dump(self.sample_dict, sample_dict_file_handle)
        getattr(self, '_daq_main_panel_set_sample_dict_path_label').setText('Set Path @ {0}'.format(sample_dict_path))

    def _set_sample_dict_path(self):
        sample_dict_path = str(QtGui.QFileDialog.getOpenFileName(self, directory=self.sample_dict_folder, filter='*.json'))
        with open(sample_dict_path, 'r') as sample_dict_file_handle:
            self.sample_dict = json.load(sample_dict_file_handle)
        getattr(self, '_daq_main_panel_set_sample_dict_path_label').setText(sample_dict_path)
        getattr(self, '_daq_main_panel_set_sample_dict_path_label').setText('Set Path @ {0}'.format(sample_dict_path))
        for i in range(1, 7):
            widget = '_daq_main_panel_set_sample_{0}_lineedit'.format(i)
            sample_name = getattr(self, widget).setText(self.sample_dict[str(i)])

    def _get_raw_data_save_path(self):
        sender = str(self.sender().whatsThis())
        if 'xy_collector' in sender:
            run_mode = str(getattr(self, '_xy_collector_popup_mode_combobox').currentText())
            plot_params = self._get_params_from_xy_collector()
            squid = plot_params['squid']
            label = plot_params['label']
            temp = plot_params['temp']
            drift = plot_params['drift']
            if run_mode == 'IV':
                suggested_file_name = 'SQ{0}_{1}_IVCurve_Raw_{2}_'.format(squid, label, temp.replace('.', 'p'))
            elif run_mode == 'RT':
                suggested_file_name = 'SQ{0}_{1}_RTCurve_Raw_{2}_'.format(squid, label, drift)
            indicies = []
            last_index = '00'
            for file_name in os.listdir(self.data_folder):
                if suggested_file_name in file_name and '.dat' in file_name:
                    appendix = file_name.split(suggested_file_name)[1]
                    if len(appendix) == 6:
                        last_index = appendix.replace('.dat', '')
            new_index = '{0}'.format(int(last_index) + 1).zfill(2)
            suggested_file_name = '{0}{1}.dat'.format(suggested_file_name, new_index)
            path = os.path.join(self.data_folder, suggested_file_name)
            set_to_widget = '_xy_collector_popup_raw_data_path_label'
        if 'time_constant' in sender:
            path = os.path.join(self.data_folder, 'test.dat')
            set_to_widget = '_time_constant_popup_raw_data_path_label'
        data_name = str(QtGui.QFileDialog.getSaveFileName(self, 'Raw Data Save Location', path, '.dat'))
        if len(data_name) > 0:
            self.raw_data_path = os.path.join(self.data_folder, data_name)
            self.plotted_data_path = self.raw_data_path.replace('.dat', '_plotted.png')
            self.parsed_data_path = self.raw_data_path.replace('.dat', '_calibrated.dat')
        else:
            self.raw_data_path = None
            self.plotted_data_path = None
            self.parsed_data_path = None

    def _get_plotted_data_save_path(self):
        data_name = str(QtGui.QFileDialog.getSaveFileName(self, 'Plotted Data Save Location', self.data_folder))
        self.plotted_data_path = os.path.join(self.data_folder, data_name)
        getattr(self, '_final_plot_popup_plot_path_label').setText(self.plotted_data_path)

    def _get_parsed_data_save_path(self):
        data_name = str(QtGui.QFileDialog.getSaveFileName(self, 'Parsed Data Save Location', self.data_folder))
        self.parsed_data_path = os.path.join(self.data_folder, data_name)
        getattr(self, '_final_plot_popup_data_path_label').setText(self.parsed_data_path)

    def _launch_daq(self):
        function_name = '_'.join(str(' ' + self.sender().text()).split(' ')).lower()
        getattr(self, function_name)()

    def populate_combobox(self, unique_combobox_name, entries):
        for entry_str in entries:
            entry = QtCore.QString(entry_str)
            getattr(self, unique_combobox_name).addItem(entry)

    def _get_all_scan_params(self, popup=None):
        if popup is None:
            popup = str(self.sender().whatsThis()).split('_popup')[0]

        function = '_get_all{0}_scan_params'.format(popup)
        if hasattr(self, function):
            return getattr(self, function)()

    def _draw_time_stream(self,data_time_stream, min_, max_, label,integration_time=1000):
         fig = pl.figure(figsize=(3,1.5))
         ax = fig.add_subplot(111)
         yticks = np.linspace(min_,max_,5)
         yticks = [round(x,2) for x in yticks]
         ax.set_yticks(yticks)
         ax.set_yticklabels(yticks,fontsize = 6)
         num = len(data_time_stream)
         time = np.linspace(0,integration_time,num)
         xticks = np.linspace(0,integration_time,5)
         ax.set_xticks(xticks)
         ax.set_xticklabels(xticks,fontsize = 6)
         fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
         ax.plot(time,data_time_stream)
         ax.set_title('Timestream')
         ax.set_xlabel('Integration time(ms)')
         ax.set_ylabel('Amplitude')
         fig.savefig('temp_files/temp_ts.png')
         pl.close('all')
         image = QtGui.QPixmap('temp_files/temp_ts.png')
         image = image.scaled(600, 300)
         getattr(self, label).setPixmap(image)

    def _stop(self):
        global continue_run
        print self.sender().whatsThis()
        if 'xy_collector' in str(self.sender().whatsThis()):
            getattr(self, '_xy_collector_popup_start_pushbutton').setFlat(False)
            getattr(self, '_xy_collector_popup_start_pushbutton').setText('Start')
            getattr(self, '_xy_collector_popup_save_pushbutton').setFlat(False)
        elif 'multimeter' in str(self.sender().whatsThis()):
            getattr(self, '_multimeter_popup_get_data_pushbutton').setFlat(False)
            getattr(self, '_multimeter_popup_get_data_pushbutton').setText('Get Data')
        self.repaint()
        continue_run = False

    def _pause(self):
        global continue_run
        continue_run = False

    def _force_min_time(self, min_value=40.0):
        value = float(str(self.sender().text()))
        if value < min_value:
            self.sender().setText(str(40))

    def _quick_message(self, msg=''):
        message_box = QtGui.QMessageBox()
        message_box.setText(msg)
        message_box.exec_()

    def _create_blank_fig(self, frac_sreen_width=0.5, frac_sreen_height=0.3,
                          left=0.12, right=0.98, top=0.8, bottom=0.23):
        width = (frac_sreen_width * float(self.screen_resolution.width())) / self.monitor_dpi
        height = (frac_sreen_height * float(self.screen_resolution.height())) / self.monitor_dpi
        fig = pl.figure(figsize=(width, height))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
        return fig, ax

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
        self.raw_data_path = str(QtGui.QFileDialog.getOpenFileName(self, directory=data_folder))
        self.parsed_data_path = self.raw_data_path.replace('.dat', '_calibrated.dat')
        self.plotted_data_path = self.raw_data_path.replace('.dat', '_plotted.png')
        plot_params = self._get_params_from_xy_collector()
        self.xdata, self.ydata, self.ystd = [], [], []
        with open(self.raw_data_path, 'r') as data_file_handle:
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
            print 'bad mode found {0}'.format(mode)

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
            self.plotted_data_path = self.raw_data_path.replace('.dat', '_plotted.png')
            self.parsed_data_path = self.raw_data_path.replace('.dat', '_calibrated.dat')
            getattr(self, '_final_plot_popup_plot_path_label').setText(self.plotted_data_path)
            getattr(self, '_final_plot_popup_data_path_label').setText(self.parsed_data_path)
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
            plot_params = self._get_params_from_xy_collector()
            if plot_params['mode'] == 'IV':
                self._final_iv_plot()
            elif plot_params['mode'] == 'RT':
                self._final_rt_plot()
        elif sender == '_time_constant_popup_save_pushbutton':
            self.temp_plot_path = './temp_files/temp_iv_png.png'
            self.active_fig.savefig(self.temp_plot_path)
            self._adjust_final_plot_popup('tau')
        else:
            print sender
            print 'need to be configured'
            self._adjust_final_plot_popup('new')

    def _final_rt_plot(self):
        plot_params = self._get_params_from_xy_collector()
        rtc = RTCurve([])
        invert = getattr(self, '_xy_collector_popup_invert_output_checkbox').isChecked()
        normal_res = float(str(getattr(self, '_xy_collector_popup_sample_res_lineedit').text()))
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
        plot_params = self._get_params_from_xy_collector()
        label = plot_params['label']
        fit_clip = plot_params['fit_clip']
        data_clip = plot_params['data_clip']
        voltage_factor = plot_params['voltage_factor']
        squid_conversion = plot_params['squid_conversion']
        ivc = IVCurve([])
        title = '{0} @ {1}'.format(plot_params['label'], plot_params['temp'])
        v_bias_real, i_bolo_real, i_bolo_std = ivc.convert_IV_to_real_units(np.asarray(self.xdata), np.asarray(self.ydata),
                                                                            stds=np.asarray(self.ystd),
                                                                            squid_conv=squid_conversion,
                                                                            v_bias_multiplier=voltage_factor,
                                                                            determine_calibration=False,
                                                                            clip=fit_clip, label=label)
        if hasattr(self, 'parsed_data_path'):
            with open(self.parsed_data_path, 'w') as parsed_data_handle:
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


    #################################################
    #################################################
    # DAQ TYPE SPECFIC CODES
    #################################################
    #################################################

    #################################################
    # MULTIMETER
    #################################################

    def _update_multimeter(self, channel='1', title='', xlabel='', ylabel=''):
        fig, ax = self._create_blank_fig()
        grt_serial = str(getattr(self, '_multimeter_popup_grt_serial_{0}_combobox'.format(channel)).currentText())
        grt_range = str(getattr(self, '_multimeter_popup_grt_range_{0}_combobox'.format(channel)).currentText())
        if len(grt_serial) > 1:
            rtc = RTCurve([])
            voltage_factor = float(self.multimeter_voltage_factor_range_dict[grt_range])
            temp_data = 1e3 * rtc.resistance_to_temp_grt(self.mm_data * voltage_factor, serial_number=grt_serial)
            ax.plot(temp_data)
            temp_data_std = np.std(temp_data)
            temp_data_mean = np.mean(temp_data)
            getattr(self, '_multimeter_popup_data_point_mean_{0}_label'.format(channel)).setText('{0:.4f}'.format(temp_data_mean))
            getattr(self, '_multimeter_popup_data_point_std_{0}_label'.format(channel)).setText('{0:.4f}'.format(temp_data_std))
        else:
            ax.plot(self.mm_data)
            getattr(self, '_multimeter_popup_data_point_mean_{0}_label'.format(channel)).setText('{0:.4f}'.format(self.mm_mean))
            getattr(self, '_multimeter_popup_data_point_std_{0}_label'.format(channel)).setText('{0:.4f}'.format(self.mm_data_std))
        ax.set_title(title, fontsize=10)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel('CH{0} Output'.format(channel), fontsize=10)
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
                                                                                                                      sample_rate=sample_rate_1)
            self._update_multimeter(channel='1')
            self.mm_data, self.mm_mean, self.mm_data_min, self.mm_data_max, self.mm_data_std = self.real_daq.get_data(signal_channel=daq_channel_2,
                                                                                                                      integration_time=integration_time_2,
                                                                                                                      sample_rate=sample_rate_2)
            self._update_multimeter(channel='2')
            root.update()

    def _multimeter(self):
        if not hasattr(self, 'multimeter_popup'):
            self._create_popup_window('multimeter_popup')
        else:
            self._initialize_panel('multimeter_popup')
        self._build_panel(settings.multimeter_popup_build_dict)
        for combobox_widget, entry_list in self.multimeter_combobox_entry_dict.iteritems():
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

    def _close_multimeter(self):
        self.multimeter_popup.close()

    #################################################
    # XY COLLECTOR
    #################################################

    def _draw_x(self, title='', xlabel='', ylabel=''):
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

    def _draw_xy_collector(self, title='', xlabel='', ylabel=''):
        e_bars = getattr(self, '_xy_collector_popup_include_errorbars_checkbox').isChecked()
        fig, ax = self._create_blank_fig()
        ax.plot(self.xdata, self.ydata)
        if e_bars:
            ax.errorbar(self.xdata, self.ydata, self.ystd, marker='.', linestyle='None')
        ax.set_title(title, fontsize=10)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        save_path = 'temp_files/temp_iv.png'
        fig.savefig(save_path)
        pl.close('all')
        image_to_display = QtGui.QPixmap(save_path)
        getattr(self, '_xy_collector_popup_xydata_label').setPixmap(image_to_display)
        self.repaint()

    def _get_params_from_xy_collector(self):
        mode = str(getattr(self, '_xy_collector_popup_mode_combobox').currentText())
        voltage_factor = float(str(getattr(self, '_xy_collector_popup_voltage_factor_combobox').currentText()))
        squid = str(getattr(self, '_xy_collector_popup_squid_select_combobox').currentText())
        squid_conversion = str(getattr(self, '_xy_collector_popup_squid_conversion_label').text())
        squid_conversion = float(squid_conversion.split(' ')[0])
        label = str(getattr(self, '_xy_collector_popup_sample_name_lineedit').text())
        fit_clip_lo = float(str(getattr(self, '_xy_collector_popup_fit_clip_lo_lineedit').text()))
        fit_clip_hi = float(str(getattr(self, '_xy_collector_popup_fit_clip_hi_lineedit').text()))
        data_clip_lo = float(str(getattr(self, '_xy_collector_popup_data_clip_lo_lineedit').text()))
        data_clip_hi = float(str(getattr(self, '_xy_collector_popup_data_clip_hi_lineedit').text()))
        e_bars = getattr(self, '_xy_collector_popup_include_errorbars_checkbox').isChecked()
        temp = str(getattr(self, '_xy_collector_popup_sample_temp_combobox').currentText())
        drift = str(getattr(self, '_xy_collector_popup_sample_drift_direction_combobox').currentText())
        fit_clip = (fit_clip_lo, fit_clip_hi)
        data_clip = (data_clip_lo, data_clip_hi)
        return {'mode': mode, 'squid': squid, 'squid_conversion': squid_conversion,
                'voltage_factor': voltage_factor, 'label': label, 'temp': temp, 'drift': drift,
                'fit_clip': fit_clip, 'data_clip': data_clip, 'e_bars': e_bars}

    def _update_in_xy_mode(self):
        run_mode = str(getattr(self, '_xy_collector_popup_mode_combobox').currentText())
        if run_mode == 'IV':
            self._draw_x(title='X data', xlabel='Sample', ylabel='Bias Voltage (V)')
            self._draw_y(title='Y data', xlabel='Sample', ylabel='SQUID Output Voltage (V)')
            self._draw_xy_collector(title='IV Curve', xlabel='Bias Voltage ($\mu$V)', ylabel='SQUID Output Voltage (V)')
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

    def _update_squid_calibration(self):
        selected_squid = str(getattr(self, '_xy_collector_popup_squid_select_combobox').currentText())
        squid_calibration = settings.squid_calibration_dict[selected_squid]
        squid_str = '{0} (uA/V)'.format(squid_calibration)
        getattr(self, '_xy_collector_popup_squid_conversion_label').setText(squid_str)
        if hasattr(self, 'sample_dict') > 0 and selected_squid in self.sample_dict:
            getattr(self, '_xy_collector_popup_sample_name_lineedit').setText(self.sample_dict[selected_squid])

    def _update_xy_collector_buttons_sizes(self):
        width = 0.1 * float(self.screen_resolution.width())
        height = 0.1 * float(self.screen_resolution.height())
        settings.xy_collector_build_dict['_xy_collector_popup_daq_channel_x_combobox'].update({'width': width})
        settings.xy_collector_build_dict['_xy_collector_popup_daq_channel_y_combobox'].update({'width': width})
        settings.xy_collector_build_dict['_xy_collector_popup_squid_select_combobox'].update({'width': width})
        settings.xy_collector_build_dict['_xy_collector_popup_voltage_factor_combobox'].update({'width': width})
        settings.xy_collector_build_dict['_xy_collector_popup_sample_name_lineedit'].update({'width': width})
        settings.xy_collector_build_dict['_xy_collector_popup_daq_integration_time_combobox'].update({'width': width})
        #settings.xy_collector_build_dict['_xy_collector_popup_start_pushbutton'].update({'height': height})
        #settings.xy_collector_build_dict['_xy_collector_popup_pause_pushbutton'].update({'height': height})
        #settings.xy_collector_build_dict['_xy_collector_popup_save_pushbutton'].update({'height': height})
        #settings.xy_collector_build_dict['_xy_collector_popup_close_pushbutton'].update({'height': height})

    def _close_xy_collector(self):
        self.xy_collector_popup.close()

    def _run_xy_collector(self):
        global continue_run
        continue_run = True
        self._get_raw_data_save_path()
        if self.raw_data_path is not None:
            sender_text = str(self.sender().text())
            self.sender().setFlat(True)
            getattr(self, '_xy_collector_popup_save_pushbutton').setFlat(True)
            self.sender().setText('Taking Data')
            daq_channel_x = getattr(self,'_xy_collector_popup_daq_channel_x_combobox').currentText()
            daq_channel_y = getattr(self, '_xy_collector_popup_daq_channel_y_combobox').currentText()
            integration_time = int(float(str(getattr(self, '_xy_collector_popup_daq_integration_time_combobox').currentText())))
            sample_rate = int(float(str(getattr(self, '_xy_collector_popup_daq_sample_rate_combobox').currentText())))
            self.xdata, self.ydata, self.xstd, self.ystd = np.asarray([]), np.asarray([]), np.asarray([]), np.asarray([])
            run_mode = str(getattr(self, '_xy_collector_popup_mode_combobox').currentText())
            if run_mode == 'RT':
                rtc = RTCurve([])
                grt_range = str(getattr(self, '_xy_collector_popup_grt_range_combobox').currentText())
                voltage_factor = float(self.multimeter_voltage_factor_range_dict[grt_range])
            with open(self.raw_data_path, 'w') as data_handle:
                while continue_run:
                    x_data, x_mean, x_min, x_max, x_std = self.real_daq.get_data(signal_channel=daq_channel_x,
                                                                                 integration_time=integration_time,
                                                                                 sample_rate=sample_rate)
                    if run_mode == 'RT':
                        if 3.0 < x_mean * voltage_factor < 600:
                            x_data = 1e3 * rtc.resistance_to_temp_grt(x_data * voltage_factor, serial_number=29268)
                        else:
                            x_data = [np.nan]
                        x_mean = np.mean(x_data)
                        x_min = np.min(x_data)
                        x_max = np.max(x_data)
                        x_std = np.std(x_data)
                    y_data, y_mean, y_min, y_max, y_std = self.real_daq.get_data(signal_channel=daq_channel_y,
                                                                                 integration_time=integration_time,
                                                                                 sample_rate=sample_rate)
                    if run_mode == 'IV' and x_mean < 0.0:
                        x_mean *= -1
                        x_data = x_data -2 * x_data
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
                    self._update_in_xy_mode()
                    root.update()

    def _xy_collector(self):
        if not hasattr(self, 'xy_collector_popup'):
            self._create_popup_window('xy_collector_popup')
        else:
            self._initialize_panel('xy_collector_popup')
        self._update_xy_collector_buttons_sizes()
        self._build_panel(settings.xy_collector_build_dict)
        for combobox_widget, entry_list in self.xy_collector_combobox_entry_dict.iteritems():
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
        getattr(self, '_xy_collector_popup_daq_sample_rate_combobox').setCurrentIndex(2)
        getattr(self, '_xy_collector_popup_grt_range_combobox').setCurrentIndex(3)
        getattr(self, '_xy_collector_popup_include_errorbars_checkbox').setChecked(True)


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
        vbias = str(getattr(self, '_time_constant_popup_voltage_bias_lineedit').text())
        bolo_name = str(getattr(self, '_time_constant_popup_bolo_name_lineedit').text())
        # Use The Tc library to plot the restul
        fig, ax = self._create_blank_fig()
        tc = TAUCurve([])
        color = 'r'
        freq_vector, amp_vector, error_vector = tc.load(self.raw_data_path)
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
            fig.subplots_adjust(left=0.1, right=0.95, top=0.90, bottom=0.2)
            ax.plot(test_freq_vector[fit_idx], fit_amp[fit_idx],
                    marker='*', ms=15.0, color=color, alpha=0.5, lw=2)
            label = '$\\tau$={0:.2f} ms ({1} Hz) @ $V_b$={2} $\mu$V'.format(fit_3db_point, fit_3db_point_hz, vbias)
            ax.plot(test_freq_vector, fit_amp, color=color, alpha=0.7, label=label)
        title = '{0}\n$\\tau$ vs $V_b$'.format(bolo_name)
        ax.set_title(title)
        ax.legend()
        fig.savefig(self.plotted_data_path)
        image_to_display = QtGui.QPixmap(self.plotted_data_path)
        getattr(self, '_time_constant_popup_all_data_monitor_label').setPixmap(image_to_display)
        self.temp_plot_path = self.plotted_data_path
        self.active_fig = fig

    def _delete_last_point(self):
        if not hasattr(self, 'raw_data_path'):
            self._quick_message(msg='Please set a data Path First')
        else:
            if os.path.exists(self.raw_data_path):
                with open(self.raw_data_path, 'r') as data_handle:
                    existing_lines = data_handle.readlines()
            if len(existing_lines) == 0:
                self._quick_message(msg='You must take at least one data point to delete the last one!')
            else:
                with open(self.raw_data_path, 'w') as data_handle:
                    for line in existing_lines[:-1]:
                        data_handle.write(line)
                self._plot_time_constant()

    def _close_time_constant(self):
        self.time_constant_popup.close()

    def _take_time_constant_data_point(self):
        if not hasattr(self, 'raw_data_path'):
            self._quick_message(msg='Please set a data Path First')
            self._get_raw_data_save_path()
            self._take_time_constant_data_point()
        else:
            # check if the file exists and append it
            if os.path.exists(self.raw_data_path):
                with open(self.raw_data_path, 'r') as data_handle:
                    existing_lines = data_handle.readlines()
            else:
                existing_lines = []
            # Grab new data
            daq_channel = getattr(self,'_time_constant_popup_daq_select_combobox').currentText()
            integration_time = int(float(str(getattr(self, '_time_constant_popup_daq_integration_time_combobox').currentText())))
            sample_rate = int(float(str(getattr(self, '_time_constant_popup_daq_sample_rate_combobox').currentText())))
            y_data, y_mean, y_min, y_max, y_std = self.real_daq.get_data(signal_channel=daq_channel,
                                                                         integration_time=integration_time,
                                                                         sample_rate=sample_rate)
            frequency = float(str(getattr(self, '_time_constant_popup_frequency_select_combobox').currentText()))
            data_line = '{0}\t{1}\t{2}\n'.format(frequency, y_mean, y_std)
            # Append the data and rewrite to file
            existing_lines.append(data_line)
            with open(self.raw_data_path, 'w') as data_handle:
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
        for combobox_widget, entry_list in self.time_constant_combobox_entry_dict.iteritems():
            self.populate_combobox(combobox_widget, entry_list)
        getattr(self, '_time_constant_popup_daq_select_combobox').setCurrentIndex(6)
        getattr(self, '_time_constant_popup_daq_sample_rate_combobox').setCurrentIndex(2)
        self.time_constant_popup.showMaximized()
        self._plot_tau_data_point([])

    #################################################
    # POL EFFICIENCY
    #################################################


    def _close_pol_efficiency(self):
        self.pol_efficiency_popup.close()

    def _pol_efficiency(self):
        if not hasattr(self, 'pol_efficiency_popup'):
            self._create_popup_window('pol_efficiency_popup')
        else:
            self._initialize_panel('pol_efficiency_popup')
        self._build_panel(settings.pol_efficiency_build_dict)
        for combobox_widget, entry_list in self.pol_efficiency_combobox_entry_dict.iteritems():
            self.populate_combobox(combobox_widget, entry_list)
        self._connect_to_com_port()
        self.pol_efficiency_popup.showMaximized()
        self.pol_efficiency_popup.setWindowTitle('POL EFFICIENCY')
        self._update_pol_efficiency_popup()
        self._blank_pol_plot()
        getattr(self, '_pol_efficiency_popup_save_pushbutton').setDisabled(True)
        self._draw_time_stream([0]*5, -1, -1,'_pol_efficiency_popup_time_stream_label')



    def _update_pol_efficiency_popup(self):
        scan_params = self._get_all_scan_params(popup='_pol_efficiency')
        if type(scan_params) is not dict:
            return None
        if 'starting_angle' in scan_params and 'ending_angle' in scan_params:
            start_angle = scan_params['starting_angle']
            end_angle = scan_params['ending_angle']
            step_size = scan_params['step_size']
            num_steps = (end_angle - start_angle) / step_size
            getattr(self,'_pol_efficiency_popup_number_of_steps_label').setText(str(num_steps))
            getattr(self,'_pol_efficiency_popup_position_slider_min_label').setText(str(start_angle))
            getattr(self,'_pol_efficiency_popup_position_slider_max_label').setText(str(end_angle))
            getattr(self, '_pol_efficiency_popup_position_monitor_slider').setMinimum(start_angle)
            getattr(self, '_pol_efficiency_popup_position_monitor_slider').setMaximum(end_angle)
        self.pol_efficiency_popup.repaint()

    def _close_pol_efficiency(self):
        self.pol_efficiency_popup.close()

    def _run_pol_efficiency(self):
        scan_params = self._get_all_pol_efficiency_scan_params()
        self.take_pol_efficiency(scan_params,1)

    def get_simulated_data(self, datatype, current_position, noise=10):
        '''
        noise is in percent and is of the max-min of data
        '''
        in_degree = current_position*np.pi/180
        dev = (np.random.randn()-0.5)*2/100*noise
        simulated_data = np.sin(in_degree) + dev
        return simulated_data


    def _blank_pol_plot(self):
        fig = pl.figure(figsize=(3,1.5))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
        ax.plot([0]*5)
        ax.set_title('POL EFFICICENCY', fontsize=12)
        ax.set_xlabel('Angle', fontsize=10)
        ax.set_ylabel('Amplitude', fontsize=10)
        fig.savefig('temp_files/temp_pol.png')
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_pol.png')
        image = image.scaled(600,300)
        getattr(self, '_pol_efficiency_popup_data_label').setPixmap(image)

    def take_pol_efficiency(self, scan_params, noise=10):
        global continue_run
        continue_run = True
        com_port = self._get_com_port('_pol_efficiency_popup_current_com_port_combobox')
        stepnum = (scan_params['ending_angle']-scan_params['starting_angle'])/scan_params['step_size']+1
        self.xdata = np.linspace(scan_params['starting_angle'],scan_params['ending_angle'],stepnum)
        self.ydata = []
        angles = []
        self.stds = []
        i = 0
        while continue_run and i < len(self.xdata):
            step = self.xdata[i]
#        for i, step in enumerate(self.xdata):
            data_point = self.get_simulated_data(int, step, noise=noise)
            angles.append(step)
            if step != 0:
                getattr(self, 'sm_{0}'.format(com_port)).finite_rotation(scan_params['step_size'])
                time.sleep(scan_params['pause_time']/1000)
            current_angle = getattr(self, 'sm_{0}'.format(com_port)).get_position()
            data_time_stream, mean, min_, max_, std = self.real_daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                                                        sample_rate=scan_params['sample_rate'],central_value=data_point)
            self.ydata.append(mean)
            self.stds.append(std)
            getattr(self,'_pol_efficiency_popup_mean_label').setText('{0:.3f}'.format(mean))
            getattr(self,'_pol_efficiency_popup_current_angle_label').setText(str(step))
            getattr(self,'_pol_efficiency_popup_std_label').setText('{0:.3f}'.format(std))
            start = scan_params['starting_angle']
            end = scan_params['ending_angle']

            self._draw_time_stream(data_time_stream, min_, max_, '_pol_efficiency_popup_time_stream_label',int(scan_params['integration_time']))
            fig = pl.figure(figsize=(3,2))
            ax = fig.add_subplot(111)
            fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
            ax.plot(angles,self.ydata)
            ax.set_title('POL EFFICICENCY', fontsize=12)
            yticks = np.linspace(min(self.ydata),max(self.ydata),5)
            yticks = [round(x,2) for x in yticks]
            ax.set_yticks(yticks)
            ax.set_yticklabels(yticks,fontsize = 6)
            xticks = np.linspace(start,end,5)
            ax.set_xticks(xticks)
            ax.set_xlabel('Angle', fontsize=10)
            ax.set_ylabel('Amplitude', fontsize=10)
            fig.savefig('temp_files/temp_pol.png')
            pl.close('all')
            image = QtGui.QPixmap('temp_files/temp_pol.png')
            image = image.scaled(600,400)
            getattr(self, '_pol_efficiency_popup_data_label').setPixmap(image)
            self.pol_efficiency_popup.repaint()
            getattr(self, '_pol_efficiency_popup_position_monitor_slider').setSliderPosition(step)
            i += 1
            root.update()
        getattr(self, '_pol_efficiency_popup_save_pushbutton').setEnabled(True)
#        return steps, data


    def read_file(self, filename):
        x, y = np.loadtxt(filename, unpack=True)
        return x,y

    def _get_all_pol_efficiency_scan_params(self):
        scan_params = {}
        for pol_efficiency_setting in settings.pol_int_run_settings:
            pull_from_widget_name = '_pol_efficiency_popup_{0}_lineedit'.format(pol_efficiency_setting)
            if hasattr(self, pull_from_widget_name):
                value = getattr(self, pull_from_widget_name).text()
                if len(str(value)) == 0:
                    value = 0
                else:
                    value = int(value)
                scan_params[pol_efficiency_setting] = value
        for pol_efficiency_setting in settings.pol_pulldown_run_settings:
            pull_from_widget_name = '_pol_efficiency_popup_{0}_combobox'.format(pol_efficiency_setting)
            if hasattr(self, pull_from_widget_name):
                value = str(getattr(self, pull_from_widget_name).currentText())
                scan_params[pol_efficiency_setting] = value
        return scan_params


    #################################################
    # USER MOVE STEPPER
    #################################################

    def _close_user_move_stepper(self):
        self.user_move_stepper_popup.close()

    def _user_move_stepper(self):
        if not hasattr(self, 'user_move_stepper_popup'):
            self._create_popup_window('user_move_stepper_popup')
        else:
            self._initialize_panel('user_move_stepper_popup')
        self._build_panel(settings.user_move_stepper_build_dict)
        for combobox_widget, entry_list in self.user_move_stepper_combobox_entry_dict.iteritems():
            self.populate_combobox(combobox_widget, entry_list)
        current_string, position_string, velocity_string = self._connect_to_com_port()
        getattr(self, '_user_move_stepper_popup_current_act_label').setText(current_string)
        getattr(self,'_user_move_stepper_popup_velocity_act_label').setText(velocity_string)
        getattr(self,'_user_move_stepper_popup_current_position_label').setText(position_string)
        #self._update_stepper_position()
        self.user_move_stepper_popup.showMaximized()
        self.user_move_stepper_popup.setWindowTitle('User Move Stepper')

    def _add_comports_to_user_move_stepper(self):
        for i, com_port in enumerate(settings.com_ports):
            com_port_entry = QtCore.QString(com_port)
            getattr(self, '_user_move_stepper_popup_current_com_port_combobox').addItem(com_port_entry)

    def _set_velocity(self):
        com_port = self._get_com_port('_user_move_stepper_popup_current_com_port_combobox')
        speed =  str(getattr(self, '_user_move_stepper_popup_velocity_set_lineedit').text())
        getattr(self, 'sm_{0}'.format(com_port)).set_speed(float(speed))
        actual = getattr(self, 'sm_{0}'.format(com_port)).get_velocity().strip('VE=')
        getattr(self,'_user_move_stepper_popup_velocity_act_label').setText(str(actual))

    def _set_current(self):
        com_port = self._get_com_port('_user_move_stepper_popup_current_com_port_combobox')
        current =  getattr(self, '_user_move_stepper_popup_current_set_lineedit').text()
        getattr(self, 'sm_{0}'.format(com_port)).set_current(float(current))
        actual =  getattr(self, 'sm_{0}'.format(com_port)).get_motor_current().strip('CC=')
        getattr(self,'_user_move_stepper_popup_current_act_label').setText(str(actual))

    def _move_stepper(self):
        move_to_pos = int(str(getattr(self, '_user_move_stepper_popup_move_to_position_lineedit').text()))
        com_port = self._get_com_port('_user_move_stepper_popup_current_com_port_combobox')
        getattr(self, 'sm_{0}'.format(com_port)).move_to_position(move_to_pos)
        self._update_stepper_position()

    def _reset_stepper_zero(self):
        com_port = self._get_com_port()
        self.stepper.stepper_position_dict[com_port] = 0
        self._update_stepper_position()
        getattr(self, '_user_move_stepper_popup_lineedit').setText(str(0))

    def _get_stepper_position(self):
        com_port = self._get_com_port()
        stepper_position = self.stepper.stepper_position_dict[com_port]
        return stepper_position

    def _update_stepper_position(self):
        com_port = self._get_com_port('_user_move_stepper_popup_current_com_port_combobox')
        stepper_position = getattr(self, 'sm_{0}'.format(com_port)).get_position().strip('SP=')
        header_str = '{0} Current Position:'.format(com_port)
        getattr(self, '_user_move_stepper_popup_current_position_header_label').setText(header_str)
        getattr(self, '_user_move_stepper_popup_current_position_label').setText(str(stepper_position))

    #################################################
    # SINGLE CHANNEL FTS BILLS
    #################################################

    def _close_single_channel_fts(self):
        self.single_channel_fts_popup.close()

    def _single_channel_fts(self):
        self.fts_daq = FTSDAQ()
        self.fourier = Fourier()
        if not hasattr(self, 'single_channel_fts_popup'):
            self._create_popup_window('single_channel_fts_popup')
        else:
            self._initialize_panel('single_channel_fts_popup')
        self._build_panel(settings.single_channel_fts_build_dict)
        for unique_combobox, entries in settings.combobox_entry_dict.iteritems():
            self.populate_combobox(unique_combobox, entries)
        self._update_single_channel_fts()
        self._connect_to_com_port(single_channel_fts=1)
        self._connect_to_com_port(single_channel_fts=2)
        self. _blank_fts_plot()
        getattr(self, '_single_channel_fts_popup_save_pushbutton').setDisabled(True)
        self.single_channel_fts_popup.showMaximized()
        self.single_channel_fts_popup.setWindowTitle('Single Channel FTS')
        self._draw_time_stream([0]*5, -1, -1,'_single_channel_fts_popup_time_stream_label')

    def _get_all_single_channel_fts_scan_params(self):
        scan_params = {}
        for fts_run_setting in settings.fts_int_run_settings:
            pull_from_widget_name = '_single_channel_fts_popup_{0}_lineedit'.format(fts_run_setting)
            if hasattr(self, pull_from_widget_name):
                value = getattr(self, pull_from_widget_name).text()
                if len(str(value)) == 0:
                    value = 0
                else:
                    value = int(value)
                scan_params[fts_run_setting] = value
        for fts_run_setting in settings.fts_pulldown_run_settings:
            pull_from_widget_name = '_single_channel_fts_popup_{0}_combobox'.format(fts_run_setting)
            if hasattr(self, pull_from_widget_name):
                value = str(getattr(self, pull_from_widget_name).currentText())
                scan_params[fts_run_setting] = value
        for fts_run_setting in settings.fts_float_run_settings:
            pull_from_widget_name = '_single_channel_fts_popup_{0}_lineedit'.format(fts_run_setting)
            if hasattr(self, pull_from_widget_name):
                value = getattr(self, pull_from_widget_name).text()
                if len(str(value)) == 0:
                    value = 0
                else:
                    value = float(value)
                scan_params[fts_run_setting] = value
        return scan_params

    def _compute_fft(self, positions, data, scan_params):
        frequency_vector, fft_vector = self.fourier.convert_IF_to_FFT_data(positions, data)
        fig = pl.figure(figsize=(3.5,1.5))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.24, right=0.99, top=0.80, bottom=0.35)
        ax.plot(frequency_vector, fft_vector)
        ax.set_xlabel('Frequency (GHz)')
        ax.set_ylabel('Amplitude')
        ax.set_title('Spectra')
        fig.savefig('temp_files/temp_fft.png')
        del fig
        image = QtGui.QPixmap('tempfft.png')
        image = image.scaled(350, 175)
        getattr(self, '_single_channel_fts_popup_fft_label').setPixmap(image)

    def _compute_resolution_and_max_frequency(self, scan_params):
        total_steps = scan_params['ending_position'] - scan_params['starting_position']
        total_distance = total_steps * scan_params['DistPerStep'] #nm
        min_distance = scan_params['step_size'] * scan_params['DistPerStep'] #nm
        nyquist_distance = 2 * min_distance
        highest_frequency = ((2.99792458 * 10 ** 8) / nyquist_distance) / (10 ** 9) # GHz

        resolution = ((3 * 10 ** 8) / total_distance) / (10 ** 9) # GHz
        resolution = '{0:.4}'.format(0.5 * resolution * 1e9)
        highest_frequency = '{0:.4}'.format(0.5 * highest_frequency * 1e9)
        return resolution, highest_frequency

    def _update_single_channel_fts(self):
        scan_params = self._get_all_scan_params(popup='_single_channel_fts')
        if type(scan_params) is not dict:
            return None
        # Update Slider
        if 'starting_position' in scan_params and 'ending_position' in scan_params:
            resolution, highest_frequency = self._compute_resolution_and_max_frequency(scan_params)
            resolution_widget = '_single_channel_fts_popup_resolution_label'
            getattr(self, resolution_widget).setText(resolution)
            highest_frequency_widget = '_single_channel_fts_popup_highest_frequency_label'
            getattr(self, highest_frequency_widget).setText(highest_frequency)
            num_steps = (scan_params['ending_position']-scan_params['starting_position'])/scan_params['step_size']
            getattr(self, '_single_channel_fts_popup_number_of_steps_label').setText(str(num_steps))
            self._update_slider_setup(scan_params)
        self.single_channel_fts_popup.repaint()

    def _update_slider(self, slider_pos):
        print slider_pos

    def _apodize(self):
        scan_params = self._get_all_single_channel_fts_scan_params()
        self.apodization = scan_params['apodization_type']
        print self.apodization

    def _update_slider_setup(self, scan_params):
        min_slider = '_single_channel_fts_popup_position_slider_min_label'
        max_slider = '_single_channel_fts_popup_position_slider_max_label'
        getattr(self, min_slider).setText(str(scan_params['starting_position']))
        getattr(self, max_slider).setText(str(scan_params['ending_position']))
        slider = '_single_channel_fts_popup_position_monitor_slider'
        getattr(self, slider).setMinimum(scan_params['starting_position'])
        getattr(self, slider).setMaximum(scan_params['ending_position'])
        com_port = self._get_com_port('_single_channel_fts_popup_current_com_port_combobox')
        motor_position = 0
        getattr(self, slider).setSliderPosition(motor_position)
        getattr(self, slider).sliderPressed.connect(self._dummy)
        self.starting_position = scan_params['starting_position']

    def _blank_fts_plot(self):
        data = [0]*5
        fig = pl.figure(figsize=(3,1.5))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
        ax.plot(data)
        ax.set_xlabel('Mirror Position (m)',fontsize = 10)
        ax.set_ylabel('Amplitude',fontsize = 10)
        ax.set_title('Interferogram')
        fig.savefig('temp_files/temp_int.png')
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_int.png')
        image = image.scaled(600,300)
        getattr(self, '_single_channel_fts_popup_interferogram_label').setPixmap(image)


    def _rotate_grid(self):
        polar_com_port = self._get_com_port('_single_channel_fts_popup_grid_current_com_port_combobox')
        angle = getattr(self,'_single_channel_fts_popup_desired_grid_angle_lineedit').text()
        getattr(self, 'sm_{0}'.format(polar_com_port)).finite_rotation(int(angle))


    def _run_fts(self):
        global continue_run
        continue_run = True
        scan_params = self._get_all_scan_params(popup='_single_channel_fts')
        linear_com_port = self._get_com_port('_single_channel_fts_popup_current_com_port_combobox')
        self._apodize()
        positions, data, self.stds = [], [], []
        pause = int(scan_params['pause_time'])/1000
        #dummy_x, dummy_y = self.fts_daq.simulate_inteferogram(scan_params['starting_position'], scan_params['ending_position'],scan_params['step_size'])
        amplitude = self.fts_daq.read_inteferogram('SQ5_Pix101_90T_Spectra_09.if',1)
        i = 0
        helper = np.arange(scan_params['starting_position'], scan_params['ending_position'] + scan_params['step_size'], scan_params['step_size'])
        while continue_run and i < len(helper):
            position = helper[i]
#        for i,position in enumerate( np.arange(scan_params['starting_position'], scan_params['ending_position'] + scan_params['step_size'], scan_params['step_size'])):
            getattr(self, 'sm_{0}'.format(linear_com_port)).move_to_position(position)
            time.sleep(pause)
            #data_time_stream, mean, min_, max_, std = self.daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
            #                                                            sample_rate=scan_params['sample_rate'],central_value = amplitude[i])

            data_time_stream, mean, min_, max_, std = self.real_daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                                                             sample_rate=scan_params['sample_rate'],central_value = amplitude[i])
            self.stds.append(std)
            getattr(self, '_single_channel_fts_popup_std_label').setText('{0:.3f}'.format(std))
            getattr(self, '_single_channel_fts_popup_mean_label').setText('{0:.3f}'.format(mean))
            getattr(self, '_single_channel_fts_popup_current_position_label').setText('{0:.3f}'.format(position))
            self._draw_time_stream(data_time_stream, min_, max_,'_single_channel_fts_popup_time_stream_label',int(scan_params['integration_time']))
            positions.append(position * scan_params['DistPerStep'])
            data.append(mean)
            fig = pl.figure(figsize=(3.5,1.5))
            ax = fig.add_subplot(111)
            fig.subplots_adjust(left=0.24, right=0.95, top=0.80, bottom=0.35)
            ax.plot(positions, data)
            yticks = np.linspace(min(data),max(data),5)
            yticks = [round(x,2) for x in yticks]
            xticks = np.linspace(positions[0],positions[-1],5)
            xticks = [round(x,2) for x in xticks]
            ax.set_xticks(xticks)
            ax.set_xticklabels(xticks,fontsize = 6)
            ax.set_yticks(yticks)
            ax.set_yticklabels(yticks,fontsize = 6)
            ax.set_xlabel('Mirror Position (in)')
            ax.set_ylabel('Amplitude')
            ax.set_title('Inteferogram')
            fig.savefig('temp_files/temp_int.png')
            pl.close('all')
            image = QtGui.QPixmap('temp_files/temp_int.png')
            image = image.scaled(600, 300)
            getattr(self, '_single_channel_fts_popup_interferogram_label').setPixmap(image)
            self.single_channel_fts_popup.repaint()
            getattr(self, '_single_channel_fts_popup_position_monitor_slider').setSliderPosition(position)
            i += 1
            root.update() 
        self.posFreqArray,self.FTArrayPosFreq = self.fts_analyzer.analyzeBolo(positions, data,apodization=self.apodization)
        image = QtGui.QPixmap('temp_files/temp_fft.png')
        image = image.scaled(600, 300)
        getattr(self, '_single_channel_fts_popup_fft_label').setPixmap(image)
        self.xdata = positions
        self.ydata = data
        getattr(self, '_single_channel_fts_popup_save_pushbutton').setEnabled(True)


    #################################################
    # BEAM MAPPER
    #################################################

    def _close_beam_mapper(self):
        '''
        Description: Closes the Beam Mapper popup window
        Input: None
        Output: None
        '''

        self.beam_mapper_popup.close()

    def _beam_mapper(self):
        self.beam_map_daq = BeamMapDAQ()
        if not hasattr(self, 'beam_mapper_popup'):
            self._create_popup_window('beam_mapper_popup')
        else:
            self._initialize_panel('beam_mapper_popup')
        self._build_panel(settings.beam_mapper_build_dict)
        for combobox_widget, entry_list in self.beam_mapper_combobox_entry_dict.iteritems():
            self.populate_combobox(combobox_widget, entry_list)
        self._connect_to_com_port(beammapper=1)
        self._connect_to_com_port(beammapper=2)
        self._draw_time_stream([0]*5, -1, -1,'_beam_mapper_popup_time_stream_label')
        self.beam_mapper_popup.showMaximized()
        self._initialize_beam_mapper()
        self.beam_mapper_popup.repaint()
        getattr(self, '_beam_mapper_popup_save_pushbutton').setDisabled(True)


    def _get_all_beam_mapper_scan_params(self):
        scan_params = {}
        for beam_map_setting in settings.beam_map_int_settings:
            pull_from_widget_name = '_beam_mapper_popup_{0}_lineedit'.format(beam_map_setting)
            if hasattr(self, pull_from_widget_name):
                value = getattr(self, pull_from_widget_name).text()
                if len(str(value)) == 0:
                    value = 0
                else:
                    value = int(value)
                scan_params[beam_map_setting] = value
        for beam_map_setting in settings.beam_map_pulldown_run_settings:
            pull_from_widget_name = '_beam_mapper_popup_{0}_combobox'.format(beam_map_setting)
            if hasattr(self, pull_from_widget_name):
                value = str(getattr(self, pull_from_widget_name).currentText())
                scan_params[beam_map_setting] = value
        scan_params = self._get_grid(scan_params)
        return scan_params

    def _get_grid(self, scan_params):
        x_total = scan_params['end_x_position'] - scan_params['start_x_position']
        x_steps = scan_params['step_size_x']
        n_points_x = (scan_params['end_x_position']-scan_params['start_x_position'])/scan_params['step_size_x']
        n_points_y = (scan_params['end_y_position']-scan_params['start_y_position'])/scan_params['step_size_y']
        scan_params['n_points_x'] = n_points_x
        scan_params['n_points_y'] = n_points_y
        scan_params['x_total'] = x_total
        getattr(self, '_beam_mapper_popup_total_x_label').setText('{0} in'.format(str(x_total)))
        y_total = scan_params['end_y_position'] - scan_params['start_y_position']
        y_steps = scan_params['step_size_y']
        getattr(self, '_beam_mapper_popup_total_y_label').setText('{0} in'.format(str(y_total)))
        scan_params['y_total'] = y_total
        return scan_params

    def _create_beam_grid(self, scan_params):
        fig = pl.figure(figsize=(3,3))
        ax = fig.add_subplot(111)
        #fig.savefig('temp_files/temp_beam_map.png')
        pl.close('all')

    def _initialize_beam_mapper(self):
        if len(str(self.sender().whatsThis())) == 0:
            return None
        else:
            scan_params = self._get_all_scan_params(popup='_beam_mapper')
            if scan_params is not None and len(scan_params) > 0:
                self.beam_map_daq.simulate_beam(scan_params)
                image = QtGui.QPixmap('temp_files/temp_beam.png')
                image = image.scaled(600, 300)
                getattr(self, '_beam_mapper_popup_2D_plot_label').setPixmap(image)
                n_points_x= scan_params['n_points_x']
                n_points_y= scan_params['n_points_y']
                getattr(self,'_beam_mapper_popup_n_points_x_label').setText(str(n_points_x))
                getattr(self,'_beam_mapper_popup_n_points_y_label').setText(str(n_points_y))

    def _take_beam_map(self):
        global continue_run
        continue_run = True
        scan_params = self._get_all_scan_params(popup='_beam_mapper')
        x_grid = np.linspace(scan_params['start_x_position'], scan_params['end_x_position'],  scan_params['n_points_x'])
        y_grid = np.linspace(scan_params['start_y_position'], scan_params['end_y_position'],  scan_params['n_points_y'])
        X, Y = np.meshgrid(x_grid, y_grid)
        Z_data = np.zeros(shape=X.shape)
        self.stds = np.zeros(shape=X.shape)
        X_sim, Y_sim, Z_sim = self.beam_map_daq.simulate_beam(scan_params)
        i = 0
        while continue_run and i < len(x_grid):
            x_pos = x_grid[i]
#        for i, x_pos in enumerate(x_grid):
            for j, y_pos in enumerate(y_grid):
                central_value = Z_sim[i][j]
                data_time_stream, mean, min_, max_, std = self.real_daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                                                            sample_rate=scan_params['sample_rate'], central_value=central_value)
                self.stds[j][i]=std
                Z_datum = mean
                Z_data[j][i] = Z_datum
                fig = pl.figure()
                ax = fig.add_subplot(111)
                ax.pcolor(X, Y, Z_data)
                ax.set_title('BEAM DATA', fontsize=12)
                ax.set_xlabel('Position (cm)', fontsize=12)
                ax.set_ylabel('Position (cm)', fontsize=12)
                fig.savefig('temp_files/temp_beam.png')
                pl.close('all')
                self._draw_time_stream(data_time_stream, min_, max_,'_beam_mapper_popup_time_stream_label')
                image = QtGui.QPixmap('temp_files/temp_beam.png')
                image = image.scaled(600, 300)
                getattr(self, '_beam_mapper_popup_2D_plot_label').setPixmap(image)
                getattr(self, '_beam_mapper_popup_data_mean_label').setText('{0:.3f}'.format(mean))
                getattr(self, '_beam_mapper_popup_x_position_label').setText('{0:.3f}'.format(x_pos))
                getattr(self, '_beam_mapper_popup_y_position_label').setText('{0:.3f}'.format(y_pos))
                getattr(self, '_beam_mapper_popup_data_std_label').setText('{0:.3f}'.format(std))
                self.beam_mapper_popup.repaint()
                i += 1
                root.update()
        self.X = X
        self.Y = Y
        self.Z_data = Z_data
        self.x_grid = x_grid
        self.y_grid = y_grid
        getattr(self, '_beam_mapper_popup_save_pushbutton').setEnabled(True)

    #################################################
    # WIDGET GENERATORS AND FUNCTIONS
    #################################################

    def _initialize_panel(self, panel=None):
        panel = getattr(self, panel)
        for index in reversed(range(panel.layout().count())):
            widget = panel.layout().itemAt(index).widget()
            widget.setParent(None)

    def _unpack_widget_function(self, function_text):
        if function_text is None:
            return None
        if '.' in function_text:
            if len(function_text.split('.')) == 2:
                base_function, attribute_function = function_text.split('.')
                base_function = getattr(self, base_function)
                widget_function = getattr(base_function, attribute_function)
        else:
            widget_function = getattr(self, function_text)
        return widget_function

    def _build_panel(self, build_dict, parent=None):
        for unique_widget_name, widget_settings in build_dict.iteritems():
            widget_settings_copy = copy(build_dict['_common_settings'])
            if unique_widget_name != '_common_settings':
                widget_settings_copy.update(widget_settings)
                widget_settings_copy.update({'parent': parent})
                for widget_param, widget_param_value in widget_settings.iteritems():
                    if 'function' == widget_param:
                        widget_function = self._unpack_widget_function(widget_param_value)
                        widget_settings_copy.update({'function':  widget_function})

                self._create_and_place_widget(unique_widget_name, **widget_settings_copy)

    def _create_popup_window(self, name):
        popup_window = QtGui.QWidget()
        popup_window.setGeometry(100, 100, 400, 200)
        popup_window.setLayout(QtGui.QGridLayout())
        setattr(self, name, popup_window)

    def _create_and_place_widget(self,
                                 unique_widget_name,
                                 parent=None,
                                 function=None,
                                 text=None,
                                 font=None,
                                 color=None,
                                 width=None,
                                 height=None,
                                 layout=None,
                                 url=None,
                                 orientation=None,
                                 tick_interval=None,
                                 tick_range=None,
                                 check_state=None,
                                 word_wrap=None,
                                 pixmap=None,
                                 alignment=None,
                                 keep_aspect_ratio=True,
                                 image_scale=(100, 100),
                                 widget_alignment=None,
                                 position=None,
                                 place_widget=True,
                                 **widget_setttings):
        widget_type = self.widget_to_object_dict[unique_widget_name.split('_')[-1]]
        if orientation is not None and widget_type == 'QSlider':
            widget = QtGui.QSlider(getattr(QtCore.Qt, orientation))
            widget.setTracking(True)
        else:
            if parent is not None:
                widget = getattr(QtGui, widget_type)(parent)
            else:
                widget = getattr(QtGui, widget_type)()
        if function is not None:
            if widget_type == 'QSlider':
                widget.valueChanged.connect(function)
            elif widget_type in ('QPushButton', 'QCheckBox'):
                widget.clicked.connect(function)
            elif widget_type in ('QLineEdit', 'QTextEdit'):
                widget.textChanged.connect(function)
            elif widget_type in ('QComboBox',):
                widget.activated.connect(function)
        if text is not None:
            if url is not None:
                text = '<a href=\"{0}\">{1}</a>'.format(url, text)
                widget.setOpenExternalLinks(True)
            widget.setText(text)
        if font is not None:
            widget.setFont(getattr(self, '{0}_font'.format(font)))
        if width is not None:
            widget.setFixedWidth(width)
        if height is not None:
            widget.setFixedHeight(height)
        if word_wrap is not None:
            widget.setWordWrap(word_wrap)
        if color is not None:
            widget.setStyleSheet('%s {color: %s}' % (widget_type, color))
        if pixmap is not None:
            image = QtGui.QPixmap(pixmap)
            if keep_aspect_ratio:
                image = image.scaled(image_scale[0], image_scale[1], QtCore.Qt.KeepAspectRatio)
            else:
                image = image.scaled(image_scale[0], image_scale[1])
            widget.setPixmap(image)
        if alignment is not None:
            qt_alignment = getattr(QtCore.Qt, 'Align{0}'.format(alignment))
            widget.setAlignment(qt_alignment)
        if layout is not None:
            widget.setLayout(getattr(QtGui, layout)())
        if tick_interval is not None:
            widget.setTickInterval(1)
        if tick_range is not None:
            widget.setRange(tick_range[0], tick_range[1])
        if check_state is not None:
            widget.setCheckState(check_state)
        if place_widget:
            row, col, row_span, col_span = position[0], position[1], position[2], position[3]
            if 'widget' in unique_widget_name:
                if widget_alignment is not None:
                    self.grid.addWidget(widget, row, col, row_span, col_span,
                                        getattr(QtCore.Qt, widget_alignment))
                else:
                    self.grid.addWidget(widget, row, col, row_span, col_span)
            else:
                if 'panel' in unique_widget_name:
                    panel = '{0}_{1}'.format(unique_widget_name.split('_panel')[0][1:], 'panel_widget')
                if 'popup' in unique_widget_name:
                    panel = '{0}_{1}'.format(unique_widget_name.split('_popup')[0][1:], 'popup')
                if 'panel' in unique_widget_name and 'popup' in unique_widget_name and widget_type != 'QWidget':
                    panel = '_{0}_{1}'.format(unique_widget_name.split('_panel')[0][1:], 'panel')
                if widget_alignment is not None:
                    getattr(self, panel).layout().addWidget(widget, row, col, row_span, col_span,
                                                            getattr(QtCore.Qt, widget_alignment))
                else:
                    getattr(self, panel).layout().addWidget(widget, row, col, row_span, col_span)
        else:
            widget.close()
        setattr(self, unique_widget_name, widget)
        widget.setWhatsThis(unique_widget_name)
        return widget
