import sys
import os
import subprocess
import shutil
import time
import numpy as np
import datetime
import pylab as pl
import json
from PyPDF2 import PdfFileMerger
from pprint import pprint
from copy import copy
from PyQt5 import QtCore, QtGui, QtWidgets
from libraries.gen_class import Class
from ba_settings.all_settings import settings
from RT_Curves.plot_rt_curves import RTCurve
from IV_Curves.plot_iv_curves import IVCurve
from FTS_Curves.plot_fts_curves import FTSCurve
from FTS_Curves.numerical_processing import Fourier
from POL_Curves.plot_pol_curves import POLCurve
from TAU_Curves.plot_tau_curves import TAUCurve
from Beam_Maps.plot_beam_maps import BeamMaps
from GuiBuilder.gui_builder import GuiBuilder


class GuiTemplate(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, analysis_types):
        super(GuiTemplate, self).__init__()
        self.grid = QtWidgets.QGridLayout()
        self.grid.setVerticalSpacing(0)
        self.setLayout(self.grid)
        self.__apply_settings__(settings)
        self._create_main_window('main_panel_widget')
        self.main_panel_widget.showMaximized()
        self.data_folder = './data'
        self.squid_channels = {'1': 25.2, '2': 27.3, '3': 30.0,
                               '4': 30.1, '5': 25.9, '6': 25.0}
        self.voltage_conversion_list = ['1e-4', '1e-5']
        self.grt_list = [25070, 25312, 29268]
        self.sample_res_factors = [0.1, 1.0, 10.0]
        self.grt_res_factors = [100.0, 1000.0]
        self.selected_files = []
        self.fts = FTSCurve()
        self.fourier = Fourier()
        self.fts_fig = None
        self.loaded_spectra_data_path = None
        self.analyze_interferogram = False

    def __apply_settings__(self, settings):
        for setting in dir(settings):
            if '__' not in setting:
                setattr(self, setting, getattr(settings, setting))

    def _create_main_window(self, name):
        self._create_popup_window(name)
        self._build_panel(settings.main_panel_build_dict)

    def _close_main(self):
        self.main_panel_widget.close()
        sys.exit()

    def _close_settings_popup(self, analysis_type):
        popup_name = '_{0}_settings_popup'.format(analysis_type)
        if hasattr(self, popup_name):
            getattr(self, popup_name).close()

    def _select_analysis_type(self):
        sender_name = str(self.sender().whatsThis())
        pushbuttons = ['_main_panel_polcurve_pushbutton', '_main_panel_ivcurve_pushbutton',
                       '_main_panel_rtcurve_pushbutton', '_main_panel_ftscurve_pushbutton',
                       '_main_panel_ifcurve_pushbutton', '_main_panel_taucurve_pushbutton',
                       '_main_panel_beammap_pushbutton']
        for pushbutton in pushbuttons:
            if sender_name == pushbutton:
                self.analysis_type = pushbutton.split('_')[3]
                getattr(self, '_build_{0}_settings_popup'.format(self.analysis_type))()

    def _select_files(self):
        data_paths = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open file', self.data_folder)[0]
        for data_path in data_paths:
            if str(data_path) not in self.selected_files:
                self.selected_files.append(str(data_path))
                print(str(data_path))
        selected_files_string = ',\n'.join(self.selected_files)
        getattr(self, '_main_panel_selected_file_label').setText(selected_files_string)

    def _clear_files(self):
        self.selected_files = []
        getattr(self, '_main_panel_selected_file_label').setText('')

    def _run_analysis(self):
        if not hasattr(self, 'analysis_type'):
            getattr(self, '_main_panel_selected_file_label').setText('Please Select a Analysis Type')
        else:
            getattr(self, '_plot_{0}'.format(self.analysis_type))()

    def _add_checkboxes(self, popup_name, name, list_, row, col):
        if type(list_) is dict:
            list_ = sorted(list_.keys())
        for i, item_ in enumerate(list_):
            reduced_name = name.replace(' ', '_').lower()
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
            if 'voltage_conversion_1e-4' in unique_widget_name:
                getattr(self, unique_widget_name).setCheckState(True)
        return 1

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

    def _build_ivcurve_settings_popup(self):
        popup_name = '{0}_settings_popup'.format(self.analysis_type)
        if hasattr(self, popup_name):
            self._initialize_panel(popup_name)
            self._build_panel(settings.ivcurve_popup_build_dict)
        else:
            self._create_popup_window(popup_name)
            self._build_panel(settings.ivcurve_popup_build_dict)
        row = 3
        self.selected_files_col_dict = {}
        for i, selected_file in enumerate(self.selected_files):
            col = 2 + i * 6
            basename = os.path.basename(selected_file)
            unique_widget_name = '_{0}_{1}_lineedit'.format(popup_name, basename)
            widget_settings = {'text': '{0}'.format(basename),
                               'position': (row, col, 1, 1)}
            row += 1
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            self.selected_files_col_dict[selected_file] = col
            row += self._add_checkboxes(popup_name, 'SQUID Channel', self.squid_channels, row, col)
            unique_widget_name = '_{0}_{1}_squid_conversion_lineedit'.format(popup_name, col)
            widget_settings = {'text': '',
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            row += self._add_checkboxes(popup_name, 'Voltage Conversion', self.voltage_conversion_list, row, col)
            unique_widget_name = '_{0}_{1}_label_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            row += 1
            unique_widget_name = '_{0}_{1}_v_fit_lo_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setText('7.0')
            row += 1
            unique_widget_name = '_{0}_{1}_v_fit_hi_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setText('15.0')
            row += 1
            unique_widget_name = '_{0}_{1}_v_plot_lo_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setText('4.5')
            row += 1
            unique_widget_name = '_{0}_{1}_v_plot_hi_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            print(unique_widget_name)
            getattr(self, unique_widget_name).setText('20.0')
            row += 1
            unique_widget_name = '_{0}_{1}_calibration_resistance_lineedit'.format(popup_name, col)
            widget_settings = {'text': '', 'width': 200,
                               'position': (row, col, 1, 1)}
            print(unique_widget_name)
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setText('0.5')
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
            getattr(self, unique_widget_name).setText('r')
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
            print(unique_widget_name)
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            unique_widget_name = '_{0}_{1}_loaded_spectra_label'.format(popup_name, col)
            print(unique_widget_name)
            widget_settings = {'text': '',
                               'position': (row, col + 1, 1, 1)}
            print(unique_widget_name)
            self._create_and_place_widget(unique_widget_name, **widget_settings)
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

    def _load_spectra(self):
        sender_str = str(self.sender().whatsThis())
        base = sender_str.split('_load')[0]
        data_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', self.data_folder)[0]
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

    #################################################
    # FTS/IF Curves 
    #################################################

    def _build_ifcurve_settings_popup(self):
        popup_name = 'ftscurve_settings_popup'
        self.analyze_interferogram = True
        self._build_ftscurve_settings_popup(popup_name=popup_name)

    def _close_fts(self):
        self.ftscurve_settings_popup.close()

    def _build_ftscurve_settings_popup(self, popup_name=None):
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
        json_path = self.selected_files[0].replace('.fft', '.json')
        distance_per_step = '250.39'
        step_size = '500'
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
            getattr(self, unique_widget_name).setCheckState(True)
            row += 1
            # Add an "local FFT" checkbox
            unique_widget_name = '_{0}_{1}_add_local_fft_checkbox'.format(popup_name, col)
            widget_settings = {'position': (row, col, 1, 2)}
            self._create_and_place_widget(unique_widget_name, **widget_settings)
            getattr(self, unique_widget_name).setCheckState(True)
            row += 1
            row = 3
        getattr(self, popup_name).show()

    def _build_fts_input_dicts(self):
        list_of_input_dicts = []
        fts_settings = ['smoothing_factor', 'xlim_plot', 'xlim_clip', 'divide_mmf', 'add_atm_model',
                        'divide_bs_5', 'divide_bs_10', 'step_size', 'steps_per_point', 'add_sim_band',
                        'add_co_lines', 'color', 'normalize', 'plot_title', 'plot_label', 'interferogram_data_select',
                        'plot_interferogram', 'add_local_fft']
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

    def __no_function(self):
        print('no function')

