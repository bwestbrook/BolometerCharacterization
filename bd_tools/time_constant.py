import time
import os
import simplejson
import pylab as pl
import numpy as np
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class TimeConstant(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, available_daqs, status_bar, screen_resolution, monitor_dpi):
        super(TimeConstant, self).__init__()
        self.status_bar = status_bar
        self.available_daqs = available_daqs
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.tc_add_common_widgets()

    def tc_add_common_widgets(self):
        '''
        '''
        # Sample Name
        sample_name_header_label = QtWidgets.QLabel('Sample Name:', self)
        self.layout().addWidget(sample_name_header_label, 8, 0, 1, 1)
        self.sample_name_lineedit = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.sample_name_lineedit, 8, 1, 1, 3)
        # Buttons
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        #start_pushbutton.clicked.connect(self.xyc_start_stop)
        self.layout().addWidget(start_pushbutton, 12, 0, 1, 4)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        #save_pushbutton.clicked.connect(self.xyc_save)
        self.layout().addWidget(save_pushbutton, 13, 0, 1, 4)

    #######################
    # Data Taking 
    ######################


    def tc_plot_tau_data_point(self, ydata):
        integration_time = int(float(str(getattr(self, '_time_constant_popup_daq_integration_time_combobox').currentText())))
        sample_rate = int(float(str(getattr(self, '_time_constant_popup_daq_sample_rate_combobox').currentText())))
        fig, ax = self.bd_create_blank_fig()
        ax.plot(ydata)
        ax.set_ylabel('Channel Voltage Output (V)')
        ax.set_xlabel('Time (ms)')
        temp_tau_save_path = './temp_files/temp_tau_data_point.png'
        fig.savefig(temp_tau_save_path)
        image_to_display = QtGui.QPixmap(temp_tau_save_path)
        getattr(self, '_time_constant_popup_data_point_monitor_label').setPixmap(image_to_display)


    def tc_delete_last_point(self):
        if not hasattr(self, 'raw_data_path'):
            self.gb_quick_message(msg='Please set a data Path First')
        else:
            if os.path.exists(self.raw_data_path[0]):
                with open(self.raw_data_path[0], 'r') as data_handle:
                    existing_lines = data_handle.readlines()
            if len(existing_lines) == 0:
                self.gb_quick_message(msg='You must take at least one data point to delete the last one!')
            else:
                with open(self.raw_data_path[0], 'w') as data_handle:
                    for line in existing_lines[:-1]:
                        data_handle.write(line)
                self.plot_time_constant()

    def tc_clear_time_constant_data(self):
        self.plot_tau_data_point([])
        self.plot_time_constant(real_data=False)
        delattr(self, 'raw_data_path')

    def tc_get_params_from_time_constant(self):
        squid = str(getattr(self, '_time_constant_popup_squid_select_combobox').currentText())
        label = str(getattr(self, '_time_constant_popup_sample_name_lineedit').text())
        signal_voltage = str(getattr(self, '_time_constant_popup_signal_voltage_lineedit').text())
        voltage_bias = str(getattr(self, '_time_constant_popup_voltage_bias_lineedit').text())
        frequency = str(getattr(self, '_time_constant_popup_frequency_select_combobox').currentText())
        return {'squid': squid, 'voltage_bias': voltage_bias,
                'signal_voltage': signal_voltage, 'label': label,
                'frequency': frequency}


    def tc_take_time_constant_data_point(self):
        if hasattr(self, 'raw_data_path') and self.raw_data_path is not None:
            print('Active Data Path Found')
            print(self.raw_data_path[0])
        else:
            self.get_raw_data_save_path()
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
            y_data, y_mean, y_min, y_max, y_std = self.daq.get_data(signal_channel=daq_channel,
                                                                         integration_time=integration_time,
                                                                         sample_rate=sample_rate,
                                                                         active_daqs=self.active_daqs)
            frequency = float(str(getattr(self, '_time_constant_popup_frequency_select_combobox').currentText()))
            data_line = '{0}\t{1}\t{2}\n'.format(frequency, y_mean, y_std)
            # Append the data and rewrite to file
            existing_lines.append(data_line)
            with open(self.raw_data_path[0], 'w') as data_handle:
                for line in existing_lines:
                    data_handle.write(line)
            getattr(self, '_time_constant_popup_data_point_mean_label').setText('{0:.3f}'.format(y_mean))
            getattr(self, '_time_constant_popup_data_point_std_label').setText('{0:.3f}'.format(y_std))
            self.plot_tau_data_point(y_data)
            self.plot_time_constant()

    #######################
    # Saving and Plotting
    ######################

    def tc_save(self):
        '''
        '''

    def tc_plot_time_constant(self, real_data=True):
        # Grab input from the Time Constant Popup
        plot_params = self.get_params_from_time_constant()
        label = plot_params['label']
        voltage_bias = plot_params['voltage_bias']
        signal_voltage = plot_params['signal_voltage']
        # Use The Tc library to plot the restul
        fig, ax = self.bd_create_blank_fig()
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
