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

class BeamMapper(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, csm_widget_dict, srs_widget):
        '''
        '''
        super(BeamMapper, self).__init__()
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.srs_widget = srs_widget
        self.daq = BoloDAQ()
        self.com_port_x = csm_widget_dict['X']['com_port']
        self.com_port_y = csm_widget_dict['Y']['com_port']
        self.csm_widget_x = csm_widget_dict['X']['widget']
        self.csm_widget_y = csm_widget_dict['Y']['widget']
        self.start_scan_wait_time = 5.0
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid_2 = QtWidgets.QGridLayout()
        self.bm_plot_panel = QtWidgets.QWidget(self)
        self.bm_plot_panel.setFixedWidth(0.7 * screen_resolution.width())
        self.bm_plot_panel.setLayout(grid_2)
        self.layout().addWidget(self.bm_plot_panel, 0, 5, 20, 1)
        self.bm_configure_input_panel()
        self.bm_configure_plot_panel()
        self.bm_plot_time_stream([0], -1.0, 1.0)
        self.bm_plot_beam_map([], [], [], running=True)

    def bm_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings
        self.bm_update_scan_params()

    def bm_configure_input_panel(self):
        '''
        '''
        welcome_header_label = QtWidgets.QLabel('Welcome to Beam Mapper', self)
        welcome_header_label.setFixedWidth(0.3 * self.screen_resolution.width())
        self.layout().addWidget(welcome_header_label, 0, 0, 1, 4)
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
        #Pause Time 
        pause_time_header_label = QtWidgets.QLabel('Pause Time (ms):', self)
        self.layout().addWidget(pause_time_header_label, 4, 0, 1, 1)
        self.pause_time_lineedit = QtWidgets.QLineEdit('100', self)
        self.pause_time_lineedit.setValidator(QtGui.QIntValidator(0, 25000, self.pause_time_lineedit))
        self.layout().addWidget(self.pause_time_lineedit, 4, 1, 1, 1)
        # Stepper Motor Selection
        stepper_motor_x_header_label = QtWidgets.QLabel('Stepper Motor X: {0}'.format(self.com_port_x), self)
        self.layout().addWidget(stepper_motor_x_header_label, 5, 0, 1, 1)
        self.stepper_x_settings_label = QtWidgets.QLabel('Stepper X Settings', self)
        self.layout().addWidget(self.stepper_x_settings_label, 6, 0, 1, 1)
        stepper_motor_y_header_label = QtWidgets.QLabel('Stepper Motor Y: {0}'.format(self.com_port_y), self)
        self.layout().addWidget(stepper_motor_y_header_label, 5, 2, 1, 1)
        self.stepper_y_settings_label = QtWidgets.QLabel('Stepper Y Settings', self)
        self.layout().addWidget(self.stepper_y_settings_label, 6, 2, 1, 1)
        ######
        # Scan Params
        ######
        #Start Scan
        start_position_x_header_label = QtWidgets.QLabel('Start Position X:', self)
        self.layout().addWidget(start_position_x_header_label, 7, 0, 1, 1)
        self.start_position_x_lineedit = QtWidgets.QLineEdit('-30000', self)
        self.start_position_x_lineedit.setValidator(QtGui.QIntValidator(-500000, 0, self.start_position_x_lineedit))
        self.start_position_x_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.start_position_x_lineedit, 7, 1, 1, 1)
        start_position_y_header_label = QtWidgets.QLabel('Start Position Y:', self)
        self.layout().addWidget(start_position_y_header_label, 7, 2, 1, 1)
        self.start_position_y_lineedit = QtWidgets.QLineEdit('-30000', self)
        self.start_position_y_lineedit.setValidator(QtGui.QIntValidator(-500000, 0, self.start_position_y_lineedit))
        self.start_position_y_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.start_position_y_lineedit, 7, 3, 1, 1)
        #End Scan
        end_position_x_header_label = QtWidgets.QLabel('End Position X:', self)
        self.layout().addWidget(end_position_x_header_label, 8, 0, 1, 1)
        self.end_position_x_lineedit = QtWidgets.QLineEdit('30000', self)
        self.end_position_x_lineedit.setValidator(QtGui.QIntValidator(0, 300000, self.end_position_x_lineedit))
        self.end_position_x_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.end_position_x_lineedit, 8, 1, 1, 1)
        end_position_y_header_label = QtWidgets.QLabel('End Position Y:', self)
        self.layout().addWidget(end_position_y_header_label, 8, 2, 1, 1)
        self.end_position_y_lineedit = QtWidgets.QLineEdit('30000', self)
        self.end_position_y_lineedit.setValidator(QtGui.QIntValidator(0, 300000, self.end_position_y_lineedit))
        self.end_position_y_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.layout().addWidget(self.end_position_y_lineedit, 8, 3, 1, 1)
        #Step Size 
        step_size_x_header_label = QtWidgets.QLabel('Step Size X (steps):', self)
        self.layout().addWidget(step_size_x_header_label, 9, 0, 1, 1)
        self.step_size_x_lineedit = QtWidgets.QLineEdit('3000', self)
        self.step_size_x_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.step_size_x_lineedit.setValidator(QtGui.QIntValidator(1, 200000, self.step_size_x_lineedit))
        self.layout().addWidget(self.step_size_x_lineedit, 9, 1, 1, 1)
        step_size_y_header_label = QtWidgets.QLabel('Step Size Y (steps):', self)
        self.layout().addWidget(step_size_y_header_label, 9, 2, 1, 1)
        self.step_size_y_lineedit = QtWidgets.QLineEdit('3000', self)
        self.step_size_y_lineedit.textChanged.connect(self.bm_update_scan_params)
        self.step_size_y_lineedit.setValidator(QtGui.QIntValidator(1, 200000, self.step_size_y_lineedit))
        self.layout().addWidget(self.step_size_y_lineedit, 9, 3, 1, 1)
        #Scan Info size
        self.scan_info_label = QtWidgets.QLabel('Scan Info', self)
        self.layout().addWidget(self.scan_info_label, 11, 1, 1, 1)
        self.bm_update_scan_params()
        sample_name_header_label = QtWidgets.QLabel('Sample Name:', self)
        self.layout().addWidget(sample_name_header_label, 12, 0, 1, 1)
        self.sample_name_lineedit = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.sample_name_lineedit, 12, 1, 1, 3)
        # Zero Lock in
        self.zero_lock_in_checkbox = QtWidgets.QCheckBox('Zero Lock In?', self)
        self.zero_lock_in_checkbox.setChecked(True)
        self.layout().addWidget(self.zero_lock_in_checkbox, 13, 0, 1, 1)
        ######
        # Control Buttons 
        ######
        self.start_pushbutton = QtWidgets.QPushButton('Start', self)
        self.layout().addWidget(self.start_pushbutton, 14, 0, 1, 4)
        self.start_pushbutton.clicked.connect(self.bm_start_stop_scan)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.layout().addWidget(save_pushbutton, 15, 0, 1, 4)
        save_pushbutton.clicked.connect(self.bm_save)
        spacer_label = QtWidgets.QLabel(' ', self)
        spacer_label.setFixedWidth(0.3 * self.screen_resolution.width())
        self.layout().addWidget(spacer_label, 16, 0, 10, 4)

    def bm_configure_plot_panel(self):
        '''
        '''
        self.beam_map_plot_label = QtWidgets.QLabel('', self.bm_plot_panel)
        self.beam_map_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.bm_plot_panel.layout().addWidget(self.beam_map_plot_label, 0, 0, 1, 4)
        self.time_stream_plot_label = QtWidgets.QLabel('', self.bm_plot_panel)
        self.time_stream_plot_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.bm_plot_panel.layout().addWidget(self.time_stream_plot_label, 1, 0, 1, 4)
        data_mean_header_label = QtWidgets.QLabel('Data Mean (V):', self.bm_plot_panel)
        data_mean_header_label.setAlignment(QtCore.Qt.AlignRight)
        self.bm_plot_panel.layout().addWidget(data_mean_header_label, 2, 0, 1, 1)
        self.data_mean_label = QtWidgets.QLabel('', self.bm_plot_panel)
        self.bm_plot_panel.layout().addWidget(self.data_mean_label, 2, 1, 1, 1)
        data_std_header_label = QtWidgets.QLabel('Data STD (V):', self.bm_plot_panel)
        data_std_header_label.setAlignment(QtCore.Qt.AlignRight)
        self.bm_plot_panel.layout().addWidget(data_std_header_label, 2, 2, 1, 1)
        self.data_std_label = QtWidgets.QLabel('', self.bm_plot_panel)
        self.bm_plot_panel.layout().addWidget(self.data_std_label, 2, 3, 1, 1)

    ##############################################################################
    # Scanning 
    ##############################################################################

    def bm_update_scan_params(self):
        '''
        '''
        end_x = int(self.end_position_x_lineedit.text())
        start_x = int(self.start_position_x_lineedit.text())
        step_size_x = int(self.step_size_x_lineedit.text())
        end_y = int(self.end_position_y_lineedit.text())
        start_y = int(self.start_position_y_lineedit.text())
        step_size_y = int(self.step_size_y_lineedit.text())
        pause_time = float(self.pause_time_lineedit.text())
        if step_size_x > 0:
            n_x_data_points = int((end_x - start_x) / step_size_x)
        else:
            n_x_data_points = np.nan
        if step_size_y > 0:
            n_y_data_points = int((end_y - start_y) / step_size_y)
        else:
            n_y_data_points = np.nan
        n_data_points = n_y_data_points * n_y_data_points
        information_string = '{0} x {1} scan {2} total points'.format(n_x_data_points, n_y_data_points, n_data_points)
        self.scan_info_label.setText(information_string)
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
        self.scan_settings_dict.update(self.daq_settings[device][signal_channel])
        daq_settings_str = ''
        for setting, value in self.daq_settings[device][signal_channel].items():
            daq_settings_str += ' '.join([x.title() for x in setting.split('_')])
            if setting == 'int_time':
                daq_settings_str += ' (ms): '
            if setting == 'sample_rate':
                daq_settings_str += ' (Hz): '
            daq_settings_str += '{0} ::: '.format(value)
        self.daq_settings_label.setText(daq_settings_str)
        sm_settings_str = ''
        self.scan_settings_dict.update(self.csm_widget_x.stepper_settings_dict)
        for setting, value in self.csm_widget_x.stepper_settings_dict.items():
            sm_settings_str += ' '.join([x.title() for x in setting.split('_')])
            sm_settings_str += ': {0}\n'.format(value)
        self.stepper_x_settings_label.setText(sm_settings_str)
        sm_settings_str = ''
        self.scan_settings_dict.update(self.csm_widget_y.stepper_settings_dict)
        for setting, value in self.csm_widget_y.stepper_settings_dict.items():
            sm_settings_str += ' '.join([x.title() for x in setting.split('_')])
            sm_settings_str += ': {0}\n'.format(value)
        self.stepper_y_settings_label.setText(sm_settings_str)

    def bm_start_stop_scan(self):
        '''
        '''
        if self.sender().text() == 'Start':
            self.bm_update_scan_params()
            self.sender().setText('Stop')
            self.started = True
            self.bm_scan()
        else:
            self.sender().setText('Start')
            self.started = False

    def bm_scan(self):
        '''
        '''
        device = self.scan_settings_dict['device']
        signal_channel = self.scan_settings_dict['signal_channel']
        int_time = self.scan_settings_dict['int_time']
        sample_rate = self.scan_settings_dict['sample_rate']
        pause_time = self.scan_settings_dict['pause_time']
        total_points = self.scan_settings_dict['n_data_points']
        start_x = self.scan_settings_dict['start_x']
        start_y = self.scan_settings_dict['start_y']
        end_x = self.scan_settings_dict['end_x']
        end_y = self.scan_settings_dict['end_y']
        step_size_x = self.scan_settings_dict['step_size_x']
        step_size_y = self.scan_settings_dict['step_size_y']
        x_grid = np.arange(start_x, end_x + step_size_x, step_size_x)
        y_grid = np.arange(start_y, end_y + step_size_y, step_size_y)
        x_ticks = [str(int(x * 1e-3)) for x in x_grid]
        y_ticks = [str(int(x * 1e-3)) for x in y_grid]
        y_grid_reversed = np.flip(y_grid)
        X, Y = np.meshgrid(x_grid, y_grid)
        Z_data = np.zeros(shape=X.shape)
        self.z_stds = np.zeros(shape=X.shape)
        direction = -1
        start_time = datetime.now()
        count = 1
        i = 0
        while i < len(x_grid) and self.started:
            x_pos = x_grid[i]
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
                self.csm_widget_y.csm_set_position(position=int(y_pos), verbose=False)
                print(x_pos, y_pos)
                act_y_pos = y_pos
                if i == 0 and j == 0: #sleep extra long on the first point
                    time.sleep(self.start_scan_wait_time)
                    self.status_bar.showMessage('Waiting {0} to move mirrors to start position'.format(self.start_scan_wait_time))
                    QtWidgets.QApplication.processEvents()
                else:
                    time.sleep(pause_time * 1e-3)
                if self.zero_lock_in_checkbox.isChecked():
                    self.srs_widget.srs_zero_lock_in_phase()
                time.sleep(pause_time * 1e-3)
                data_time_stream, mean, min_, max_, std = self.daq.get_data(signal_channel=signal_channel, int_time=int_time,
                                                                            sample_rate=sample_rate, device=device)
                self.bm_plot_time_stream(data_time_stream, min_, max_)
                Z_datum = mean
                if direction == -1:
                    self.z_stds[len(y_scan) -1 - j][i] = std
                    Z_data[len(y_scan) - 1- j][i] = Z_datum
                else:
                    self.z_stds[j][i] = std
                    Z_data[j][i] = Z_datum
                self.bm_plot_beam_map( x_ticks, y_ticks, Z_data, running=True)
                self.data_mean_label.setText('{0:.6f}'.format(mean))
                self.data_std_label.setText('{0:.6f}'.format(std))
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
                self.repaint()
                count += 1
                j += 1
            if i + 1 == len(x_grid):
                self.started = False
                self.start_pushbutton.setText('Start')
            i += 1

    ##############################################################################
    # Saving and plotting
    ##############################################################################

    def bm_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}.dat'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def bm_save(self):
        '''
        '''
        save_path = self.fts_index_file_name()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter='*.txt,*.dat')[0]
        if len(if_save_path) > 0:
            with open(save_path, 'w') as save_handle:
                for i, x_data in enumerate(self.x_data):
                    line = '{0:.5f}, {1:.5f}, {2:.5f}, {3:.5f}\n'.format(self.x_data[i], self.x_stds[i], self.y_data[i], self.y_stds[i], self.z_data[i], self.z_stds[i])
                    save_handle.write(line)
        else:
            self.gb_quick_message('Warning {0} Data Not Written to File!'.format(suffix), msg_type='Warning')

    def bm_plot_time_stream(self, ts, min_, max_):
        '''
        '''
        fig, ax = self.bm_create_blank_fig(left=0.12, bottom=0.26, right=0.98, top=0.93,
                                           frac_screen_width=0.7, frac_screen_height=0.25)
        ax.plot(ts)
        ax.set_xlabel('Samples', fontsize=14)
        ax.set_ylabel('($V$)', fontsize=14)
        fig.savefig('temp_files/temp_ts.png', transparent=True)
        pl.close('all')
        image = QtGui.QPixmap('temp_files/temp_ts.png')
        self.time_stream_plot_label.setPixmap(image)

    def bm_plot_beam_map(self, x_ticks, y_ticks, Z, running=False):
        '''
        '''
        fig, ax = self.bm_create_blank_fig(left=0.02, bottom=0.11, right=0.98, top=0.95,
                                           frac_screen_width=0.65, frac_screen_height=0.65,
                                           aspect='equal')
        #ax_image = ax.imshow(Z)
        if len(x_ticks) > 0:
            ax_image = ax.pcolormesh(Z)
            ax.set_title('BEAM DATA', fontsize=16)
            ax.set_xlabel('X Position (k-steps)', fontsize=14)
            ax.set_ylabel('Y Position (k-steps)', fontsize=14)
            x_tick_locs = [0.5 + x for x in range(len(x_ticks))]
            y_tick_locs = [0.5 + x for x in range(len(x_ticks))]
            ax.set_xticks(x_tick_locs)
            ax.set_yticks(y_tick_locs)
            ax.set_xticklabels(x_ticks, rotation=35, fontsize=10)
            ax.set_yticklabels(y_ticks, fontsize=10)
            color_bar = fig.colorbar(ax_image, ax=ax)
        if running:
            fig.savefig('temp_files/temp_beam.png', transparent=True)
            pl.close('all')
            image = QtGui.QPixmap('temp_files/temp_beam.png')
            self.beam_map_plot_label.setPixmap(image)
        else:
            pl.show()

    def bm_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.8,
                             left=0.18, right=0.98, top=0.95, bottom=0.08, n_axes=1,
                             aspect=None):
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
            ax1.tick_params(axis='x', labelsize=16)
            ax1.tick_params(axis='y', labelsize=16)
            ax2.tick_params(axis='x', labelsize=16)
            ax2.tick_params(axis='y', labelsize=16)
            return fig, ax1, ax2
        else:
            if aspect is None:
                ax = fig.add_subplot(111)
            else:
                ax = fig.add_subplot(111, aspect=aspect)
            ax.tick_params(axis='x', labelsize=16)
            ax.tick_params(axis='y', labelsize=16)
            return fig, ax
