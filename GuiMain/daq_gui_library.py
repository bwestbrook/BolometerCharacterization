import sys
import os
import subprocess
import shutil
import time
import numpy as np
import datetime
import pylab as pl
import time
from PyPDF2 import PdfFileMerger
from pprint import pprint
from copy import copy
from PyQt4 import QtCore, QtGui
from libraries.gen_class import Class
from ba_settings.all_settings import settings
from RT_Curves.plot_rt_curves import RTCurve
from IV_Curves.plot_iv_curves import IVCurve
from FTS_Curves.plot_fts_curves import FTSCurve
from FTS_Curves.numerical_processing import Fourier
from POL_Curves.plot_pol_curves import POLCurve
from Stepper_Motor.stepper import Stepper
from FTS_DAQ.fts_daq import FTSDAQ
from BeamMapping.beam_map_daq import BeamMapDAQ
from DAQ.daq import DAQ


class GuiTemplate(QtGui.QWidget):

    def __init__(self):
        super(GuiTemplate, self).__init__()
        self.grid = QtGui.QGridLayout()
        self.grid.setVerticalSpacing(0)
        self.setLayout(self.grid)
        self.__apply_settings__(settings)
        self._create_main_window('daq_main_panel_widget')
        self.data_folder = './data'
        self.selected_files = []
        self.current_stepper_position = 100
        self.daq_main_panel_widget.show()
        self.daq = DAQ()

    def __apply_settings__(self, settings):
        for setting in dir(settings):
            if '__' not in setting:
                setattr(self, setting, getattr(settings, setting))

    def _create_main_window(self, name):
        self._create_popup_window(name)
        self._build_panel(settings.daq_main_panel_build_dict)
        self._add_daq_types_to_combobox()

    def _close_main(self):
        self.daq_main_panel_widget.close()
        sys.exit()

    def _dummy(self):
        print 'Dummy Function'

    def _add_daq_types_to_combobox(self):
        for daq_function in settings.daq_functions:
            daq_combo_box_string = ' '.join(daq_function.split('_'))[1:].title()
            entry = QtCore.QString(daq_combo_box_string)
            getattr(self, '_daq_main_panel_daq_select_combobox').addItem(entry)

    def _launch_daq(self):
        function_name = '_'.join(str(' ' + self.sender().currentText()).split(' ')).lower()
        getattr(self, function_name)()

    def populate_combobox(self, unique_combobox_name, entries):
        for entry_str in entries:
            entry = QtCore.QString(entry_str)
            getattr(self, unique_combobox_name).addItem(entry)

    def _get_com_port(self):
        com_port = str(getattr(self, '_user_move_stepper_popup_current_com_port_combobox').currentText())
        return com_port

    def _get_all_scan_params(self, popup=None):
        if popup is None:
            popup = str(self.sender().whatsThis()).split('_popup')[0]

        function = '_get_all{0}_scan_params'.format(popup)
        if hasattr(self, function):
            return getattr(self, function)()

    #################################################
    #################################################
    # DAQ TYPE SPECFIC CODES 
    #################################################
    #################################################

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
        self._add_comports_to_user_move_stepper()
        self._update_stepper_position()
        self.user_move_stepper_popup.show()
        self.user_move_stepper_popup.setWindowTitle('User Move Stepper')

    def _add_comports_to_user_move_stepper(self):
        for i, com_port in enumerate(settings.com_ports):
            if i == 0:
                self.stepper = Stepper(comport_entry)
            com_port_entry = QtCore.QString(com_port)
            getattr(self, '_user_move_stepper_popup_current_com_port_combobox').addItem(com_port_entry)

    def _connect_to_com_port(self):
        com_port = self._get_com_port()
        self.stepper.connect_to_com_port(com_port)
        #### SOME CODE HERE TO CONNECT TO BACKEND ####
        #### SOME CODE HERE TO CONNECT TO BACKEND ####
        #### SOME CODE HERE TO CONNECT TO BACKEND ####
        #### SOME CODE HERE TO CONNECT TO BACKEND ####
        #### SOME CODE HERE TO CONNECT TO BACKEND ####
        connected_to_com_port = self.stepper.connect_to_com_port(com_port)
        #### SOME CODE HERE TO CONNECT TO BACKEND ####
        #### SOME CODE HERE TO CONNECT TO BACKEND ####
        #### SOME CODE HERE TO CONNECT TO BACKEND ####
        #### SOME CODE HERE TO CONNECT TO BACKEND ####
        #### SOME CODE HERE TO CONNECT TO BACKEND ####
        old_stepper_position = self._get_stepper_position()
        move_to_position = getattr(self, '_user_move_stepper_popup_lineedit').setText(str(old_stepper_position))
        self._update_stepper_position()

    def _move_stepper(self):
        move_to_position = int(str(getattr(self, '_user_move_stepper_popup_lineedit').text()))
        old_stepper_position = self._get_stepper_position()
        com_port = self._get_com_port()
        print 'Code would physically get this to move {0} from {1} to {2}'.format(com_port, old_stepper_position,
                                                                                  move_to_position)
        self.stepper.stepper_position_dict[com_port] = move_to_position
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
        com_port = self._get_com_port()
        stepper_position = self.stepper.stepper_position_dict[com_port]
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
        self.single_channel_fts_popup.show()
        self.single_channel_fts_popup.setWindowTitle('Single Channel FTS')

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
            # Update Slider
            self._update_slider_setup(scan_params)
        self.single_channel_fts_popup.repaint()

    def _update_slider(self, slider_pos):
        print slider_pos

    def _update_slider_setup(self, scan_params):
        min_slider = '_single_channel_fts_popup_position_slider_min_label'
        max_slider = '_single_channel_fts_popup_position_slider_max_label'
        getattr(self, min_slider).setText(str(scan_params['starting_position']))
        getattr(self, max_slider).setText(str(scan_params['ending_position']))
        slider = '_single_channel_fts_popup_position_monitor_slider'
        getattr(self, slider).setSliderPosition(0)
        getattr(self, slider).setRange(0, scan_params['starting_position'] + scan_params['ending_position'])
        getattr(self, slider).setTickInterval(scan_params['step_size'])
        getattr(self, slider).sliderPressed.connect(self._dummy)
        self.starting_position = scan_params['starting_position']

    def _run_fts(self):
        scan_params = self._get_all_scan_params(popup='_single_channel_fts')
        positions, data = [], []
        for position in np.arange(scan_params['starting_position'], scan_params['ending_position'],
                                  scan_params['step_size']):
            data_time_stream, mean, min_, max_, std = self.daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                                                        sample_rate=scan_params['sample_rate'])
            getattr(self, '_single_channel_fts_popup_std_label').setText(str(std))
            getattr(self, '_single_channel_fts_popup_mean_label').setText(str(mean))
            getattr(self, '_single_channel_fts_popup_current_position_label').setText(str(position))
            image = QtGui.QPixmap('temp_files/temp_ts.png')
            image = image.scaled(350, 175)
            getattr(self, '_single_channel_fts_popup_time_stream_label').setPixmap(image)
            positions.append(position * scan_params['DistPerStep'] * 1e-9)
            data.append(mean)
            fig = pl.figure(figsize=(3.5,1.5))
            ax = fig.add_subplot(111)
            fig.subplots_adjust(left=0.24, right=0.99, top=0.80, bottom=0.35)
            ax.plot(positions, data)
            ax.set_xlabel('Mirror Position (m)')
            ax.set_ylabel('Amplitude')
            ax.set_title('Interferogram')
            fig.savefig('temp_files/temp_int.png')
            pl.close('all')
            image = QtGui.QPixmap('temp_files/temp_int.png')
            image = image.scaled(350, 175)
            getattr(self, '_single_channel_fts_popup_interferogram_label').setPixmap(image)
            self.single_channel_fts_popup.repaint()
            getattr(self, '_single_channel_fts_popup_position_monitor_slider').setSliderPosition(position)
        self._compute_fft(positions, data, scan_params)
        image = QtGui.QPixmap('temp_files/temp_fft.png')
        image = image.scaled(350, 175)
        getattr(self, '_single_channel_fts_popup_fft_label').setPixmap(image)

    #################################################
    # BEAM MAPPER 
    #################################################

    def _close_beam_mapper(self):
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
        self.beam_mapper_popup.show()
        self._initialize_beam_mapper()
        self.beam_mapper_popup.repaint()

    def _get_all_beam_mapper_scan_params(self):
        scan_params = {}
        for beam_map_setting in settings.beam_map_int_settings:
            pull_from_widget_name = '_beam_mapper_popup_{0}_lineedit'.format(beam_map_setting)
            print beam_map_setting
            print pull_from_widget_name
            print hasattr(self, pull_from_widget_name)
            print
            print
            print
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
        x_steps = x_total / scan_params['n_points_x']
        scan_params['step_size_x'] = x_steps
        scan_params['x_total'] = x_total
        getattr(self, '_beam_mapper_popup_step_size_x_label').setText('{0} cm'.format(str(x_steps)))
        getattr(self, '_beam_mapper_popup_total_x_label').setText('{0} cm'.format(str(x_total)))
        y_total = scan_params['end_y_position'] - scan_params['start_y_position']
        y_steps = y_total / scan_params['n_points_y']
        getattr(self, '_beam_mapper_popup_step_size_y_label').setText('{0} cm'.format(str(y_steps)))
        getattr(self, '_beam_mapper_popup_total_y_label').setText('{0} cm'.format(str(y_total)))
        scan_params['step_size_y'] = y_steps
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
                image = image.scaled(350, 175)
                getattr(self, '_beam_mapper_popup_2D_plot_label').setPixmap(image)

    def _take_beam_map(self):
        scan_params = self._get_all_scan_params(popup='_beam_mapper')
        x_grid = np.linspace(scan_params['start_x_position'], scan_params['end_x_position'],  scan_params['n_points_x'])
        y_grid = np.linspace(scan_params['start_y_position'], scan_params['end_y_position'],  scan_params['n_points_y'])
        X, Y = np.meshgrid(x_grid, y_grid)
        Z_data = np.zeros(shape=X.shape)
        X_sim, Y_sim, Z_sim = self.beam_map_daq.simulate_beam(scan_params)
        for i, x_pos in enumerate(x_grid):
            for j, y_pos in enumerate(y_grid):
                print x_pos, y_pos
                central_value = Z_sim[i][j]
                data_time_stream, mean, min_, max_, std = self.daq.get_data(signal_channel=scan_params['signal_channel'], integration_time=scan_params['integration_time'],
                                                                            sample_rate=scan_params['sample_rate'], central_value=central_value)
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
                image = QtGui.QPixmap('temp_files/temp_ts.png')
                image = image.scaled(350, 175)
                getattr(self, '_beam_mapper_popup_time_stream_label').setPixmap(image)
                image = QtGui.QPixmap('temp_files/temp_beam.png')
                image = image.scaled(350, 175)
                getattr(self, '_beam_mapper_popup_2D_plot_label').setPixmap(image)
                getattr(self, '_beam_mapper_popup_data_mean_label').setText(str(mean))
                getattr(self, '_beam_mapper_popup_x_position_label').setText(str(x_pos))
                getattr(self, '_beam_mapper_popup_y_position_label').setText(str(y_pos))
                self.beam_mapper_popup.repaint()



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
                print
                print
                print unique_widget_name
                for widget_param, widget_param_value in widget_settings.iteritems():
                    print widget_param, widget_param_value
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
