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

    def __init__(self, available_daqs, status_bar, screen_resolution, monitor_dpi, csm_widget_dict):
        '''
        '''
        super(BeamMapper, self).__init__()
        self.status_bar = status_bar
        self.available_daqs = available_daqs
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.daq = BoloDAQ()
        self.csm_widget_x = csm_widget_dict['X']
        self.csm_widget_y = csm_widget_dict['Y']
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.bm_add_common_widgets()

    def bm_add_common_widgets(self):
        '''
        '''
        # Sample Name
        sample_name_header_label = QtWidgets.QLabel('Sample Name:', self)
        self.layout().addWidget(sample_name_header_label, 8, 0, 1, 1)
        self.sample_name_lineedit = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.sample_name_lineedit, 8, 1, 1, 3)
        # Buttons
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        #start_pushbutton.clicked.connect(self.c_start_stop)
        self.layout().addWidget(start_pushbutton, 12, 0, 1, 4)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        #save_pushbutton.clicked.connect(self.xyc_save)
        self.layout().addWidget(save_pushbutton, 13, 0, 1, 4)

    def bd_close_beam_mapper(self):
        '''
        Closes the panel with a warning if data is being collected
        '''
        global continue_run
        if continue_run:
            self.gb_quick_message('Taking data!!!\nPlease stop taking data before closing single channel FTS!')
        else:
            self.beam_mapper_popup.close()
            continue_run = False

    def bd_beam_mapper(self):
        '''
        Opens the panel
        '''
        if not hasattr(self, 'lock_in'):
            self.lock_in = LockIn()
        if not hasattr(self, 'beam_mapper_popup'):
            self.gb_create_popup_window('beam_mapper_popup')
        else:
            self.gb_initialize_panel('beam_mapper_popup')
        self.gb_build_panel(settings.beam_mapper_build_dict)
        for combobox_widget, entry_list in self.beam_mapper_combobox_entry_dict.items():
           self.gb_populate_combobox(combobox_widget, entry_list)
        self.draw_time_stream([0] * 5, -1, -1, '_beam_mapper_popup_time_stream_label')
        self.beam_mapper_popup.showMaximized()
        self.initialize_beam_mapper()
        meta_data = self.bd_get_all_meta_data(popup='beam_mapper')
        scan_params = self.bd_get_all_params(meta_data, settings.beam_mapper_params, 'beam_mapper')
        scan_params = self.get_grid(scan_params)
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

    def bd_initialize_beam_mapper(self):
        '''
        Updates the panel based on inputs of desired grid
        '''
        if len(str(self.sender().whatsThis())) == 0:
            return None
        else:
            meta_data = self.bd_get_all_meta_data(popup='beam_mapper')
            scan_params = self.bd_get_all_params(meta_data, settings.beam_mapper_params, 'beam_mapper')
            scan_params = self.get_grid(scan_params)
            if scan_params is not None and len(scan_params) > 0:
                #self.bmt.simulate_beam(scan_params, 'temp_files/temp_beam.png')
                #image = QtGui.QPixmap('temp_files/temp_beam.png')
                #getattr(self, '_beam_mapper_popup_2D_plot_label').setPixmap(image)
                n_points_x = int(scan_params['n_points_x'])
                n_points_y = int(scan_params['n_points_y'])
                getattr(self,'_beam_mapper_popup_n_points_x_label').setText(str(n_points_x))
                getattr(self,'_beam_mapper_popup_n_points_y_label').setText(str(n_points_y))

    def bd_get_grid(self, scan_params):
        '''
        Sets up a gride to place data points into base on specfied params
        '''

        if self.gb_is_float(scan_params['end_x_position']) \
                and self.gb_is_float(scan_params['end_y_position']) \
                and self.gb_is_float(scan_params['end_y_position']) \
                and self.gb_is_float(scan_params['start_x_position']) \
                and self.gb_is_float(scan_params['start_y_position']) \
                and self.gb_is_float(scan_params['step_size_x'], enforce_positive=True) \
                and self.gb_is_float(scan_params['step_size_y'], enforce_positive=True):
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

    def bd_plot_beam_map(self, x_ticks, y_ticks, Z, scan_params):
        '''
        '''
        fig, ax = self.bd_create_blank_fig(left=0.02, bottom=0.19, right=0.98, top=0.9,
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

    def bd_take_beam_map(self):
        '''
        Executes a data taking run
        '''
        global continue_run
        global pause_run
        continue_run = True
        pause_run = False
        meta_data = self.bd_get_all_meta_data()
        scan_params = self.bd_get_all_params(meta_data, settings.beam_mapper_params, 'beam_mapper')
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
        self.get_raw_data_save_path()
        direction = -1
        if self.raw_data_path is not None:
            start_time = datetime.now()
            getattr(self, '_beam_mapper_popup_start_pushbutton').setDisabled(True)
            with open(self.raw_data_path[0], 'w') as data_handle:
                count = 1
                with open(self.raw_data_path[0].replace('.dat', '.json'), 'w') as meta_data_handle:
                    simplejson.dump(meta_data, meta_data_handle)
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
                        data_time_stream, mean, min_, max_, std = self.daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                                                                         sample_rate=scan_params['sample_rate'], active_daqs=self.active_daqs)
                        self.draw_time_stream(data_time_stream, min_, max_,'_beam_mapper_popup_time_stream_label')
                        Z_datum = mean
                        if direction == -1:
                            self.stds[len(y_scan) -1 - j][i] = std
                            Z_data[len(y_scan) - 1- j][i] = Z_datum
                        else:
                            self.stds[j][i] = std
                            Z_data[j][i] = Z_datum
                        self.plot_beam_map(x_ticks, y_ticks, Z_data, scan_params)
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
        self.update_log()


