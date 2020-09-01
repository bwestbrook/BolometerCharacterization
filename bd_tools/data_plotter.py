import os
import pylab as pl
import numpy as np
import matplotlib.pyplot as plt
from copy import copy
from pprint import pprint
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class DataPlotter(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, status_bar, screen_resolution, monitor_dpi, data_folder):
        super(DataPlotter, self).__init__()
        self.data_folder = data_folder
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.plot_count = 0
        self.data_types = [
            'x_data',
            'xerr',
            'y_data',
            'yerr',
            ]
        self.dp_controls()
        self.dp_plot_input()
        self.loaded_file_data_rows = []
        self.include_in_plot_list = []
        self.data_type_plot_dict = {
            'IV': {
                'x_label_lineedit_1': 'Voltage ($\mu$V)',
                'y_label_lineedit_1': 'Current ($\mu$A)',
                'x_label_lineedit_2': '',
                'y_label_lineedit_2': ''
                },
            'RT': {
                'x_label_lineedit_1': 'Temperature ($m K$)',
                'y_label_lineedit_1': 'Resistance ($m \Omega$)',
                'x_label_lineedit_2': '',
                'y_label_lineedit_2': ''
                },
            'Beam Map': {
                'x_label_lineedit_1': 'X Position ($m m$)',
                'y_label_lineedit_1': 'Y Position ($m m$)',
                'x_label_lineedit_2': '',
                'y_label_lineedit_2': ''
                },
            'FTS': {
                'x_label_lineedit_1': 'X Position ($m m$)',
                'y_label_lineedit_1': 'Response ($V$)',
                'x_label_lineedit_2': 'Frequency ($GHz$)',
                'y_label_lineedit_2': 'Response ($V$)',
                },
            'Cosmic Rays': {
                'x_label_lineedit_1': 'Time ($s$)',
                'y_label_lineedit_1': 'SQUID Output ($V$)',
                'x_label_lineedit_2': 'Time ($s$)',
                'y_label_lineedit_2': 'SQUID Output ($V$)',
                },
            'Custom': {
                'x_label_lineedit_1': '',
                'y_label_lineedit_1': '',
                'x_label_lineedit_2': '',
                'y_label_lineedit_2': '',
                },
            }
        self.dp_tab_bar()

    ########################
    # Gui Setup 
    ########################

    def dp_tab_bar(self):
        '''
        '''
        self.data_type_tab_bar = QtWidgets.QTabBar(self)
        for data_type in self.data_type_plot_dict:
            self.data_type_tab_bar.addTab(data_type)
        self.data_type_tab_bar.currentChanged.connect(self.dp_update_input)
        self.layout().addWidget(self.data_type_tab_bar, 0, 0, 1, 8)
        self.data_type_tab_bar.setCurrentIndex(1)
        self.data_type_tab_bar.setCurrentIndex(0)

    def dp_controls(self):
        '''
        '''
        load_pushbutton = QtWidgets.QPushButton('Load', self)
        load_pushbutton.setFixedHeight(load_pushbutton.sizeHint().height() * 5)
        self.layout().addWidget(load_pushbutton, 1, 6, 3, 1)
        load_pushbutton.clicked.connect(self.dp_load_data)
        plot_pushbutton = QtWidgets.QPushButton('Plot', self)
        plot_pushbutton.setFixedHeight(plot_pushbutton.sizeHint().height() * 5)
        self.layout().addWidget(plot_pushbutton, 1, 7, 3, 1)
        plot_pushbutton.clicked.connect(self.dp_plot)

    def dp_plot_input(self):
        '''
        '''
        # X label 1
        x_header_label_1 = QtWidgets.QLabel('X Label 1', self)
        self.layout().addWidget(x_header_label_1, 1, 0, 1, 1)
        self.x_label_lineedit_1 = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.x_label_lineedit_1, 1, 1, 1, 2)
        # X label 2
        x_header_label_2 = QtWidgets.QLabel('X Label 2', self)
        self.layout().addWidget(x_header_label_2, 1, 3, 1, 1)
        self.x_label_lineedit_2 = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.x_label_lineedit_2, 1, 4, 1, 2)
        y_header_label_1 = QtWidgets.QLabel('Y Label 1', self)
        self.layout().addWidget(y_header_label_1, 2, 0, 1, 1)
        self.y_label_lineedit_1 = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.y_label_lineedit_1, 2, 1, 1, 2)
        y_header_label_2 = QtWidgets.QLabel('Y Label 2', self)
        self.layout().addWidget(y_header_label_2, 2, 3, 1, 1)
        self.y_label_lineedit_2 = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.y_label_lineedit_2, 2, 4, 1, 2)
        title_header_label = QtWidgets.QLabel('Title', self)
        self.layout().addWidget(title_header_label, 3, 0, 1, 1)
        self.title_lineedit = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.title_lineedit, 3, 1, 1, 5)

    ########################
    # Information Handling 
    ########################

    def dp_update_input(self):
        '''
        '''
        data_type = self.data_type_tab_bar.tabText(self.data_type_tab_bar.currentIndex())
        for widget, text in self.data_type_plot_dict[data_type].items():
            getattr(self, widget).setText(text)
        self.title_lineedit.setText('')
        if hasattr(self, 'data'):
            if data_type in ('RT', 'IV'):
                for column in range(self.data.shape[1]):
                    getattr(self, 'column_{0}_data_type'.format(column)).setCurrentIndex(column)

    ########################
    # Loading and Plotting 
    ########################

    def dp_update_include_in_plot_list(self):
        '''
        '''
        data_row = self.sender().text().split(' ')[0]
        if self.sender().isChecked():
            self.include_in_plot_list.append(data_row)
        else:
            self.include_in_plot_list.remove(data_row)

    def dp_load_data(self):
        '''
        '''
        data_type = self.data_type_tab_bar.tabText(self.data_type_tab_bar.currentIndex())
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
        if len(file_path) > 0:
            for data_row in range(100):
                load_panel_widget = QtWidgets.QWidget()
                grid = QtWidgets.QGridLayout()
                load_panel_widget.setLayout(grid)
                if hasattr(self, 'load_panel_widget_{0}'.format(data_row)):
                    pass
                else:
                    setattr(self, 'load_panel_widget_{0}'.format(data_row), load_panel_widget)
                    break
            self.layout().addWidget(load_panel_widget, data_row + 7, 0, 1, 8)
            try:
                data = np.loadtxt(file_path, dtype=np.float, delimiter=',')
            except ValueError:
                data = np.loadtxt(file_path, dtype=np.float, delimiter='\t')
            self.loaded_file_data_rows.append(data_row)
            setattr(self, 'data_{0}'.format(data_row), data)
        else:
            return None
        if data_type == 'Beam Map':
            import ipdb;ipdb.set_trace()
        else:
            j = 0
            for column in range(8):
                data_type_combobox = QtWidgets.QComboBox(self)
                data_type_combobox.addItem('')
                for data_type in self.data_types:
                    data_type_combobox.addItem(data_type)
                setattr(self, 'data_{0}_column_{1}_data_type'.format(data_row, column), data_type_combobox)
                load_panel_widget.layout().addWidget(data_type_combobox, 1, column, 1, 1)
                if j < 4:
                    getattr(self, 'data_{0}_column_{1}_data_type'.format(data_row, column)).setCurrentIndex(j + 1)
                j += 1
                data_multiply_lineedit = QtWidgets.QLineEdit('1.0', self)
                data_multiply_lineedit.setValidator(QtGui.QDoubleValidator(-1e24, 1e24, 8, data_multiply_lineedit))
                setattr(self, 'data_{0}_multiply_column_{1}'.format(data_row, column), data_multiply_lineedit)
                load_panel_widget.layout().addWidget(data_multiply_lineedit, 2, column, 1, 1)
            for column in range(data.shape[1]):
                data_preview = ''.join(['{0:.6f}\n'.format(x) for x in data.T[column]])
                column_textedit = QtWidgets.QTextEdit('', self)
                column_textedit.setReadOnly(True)
                if load_panel_widget.layout().itemAtPosition(6, column) is not None:
                    load_panel_widget.layout().itemAtPosition(6, column).widget().setParent(None)
                column_textedit.setText(data_preview)
                load_panel_widget.layout().addWidget(column_textedit, 3, column, 1, 1)
            self.dp_add_file_plot_options(load_panel_widget, file_path, data_row)

    def dp_add_file_plot_options(self, load_panel_widget, file_path, data_row):
        '''
        '''
        setattr(self, 'load_data_label_{0}'.format(data_row), load_panel_widget)
        # Data Labeling and Identifying
        basename = os.path.basename(file_path).replace('.txt', '').replace('.dat', '')
        self.title_lineedit.setText(basename)
        loaded_data_label = QtWidgets.QLabel('No Data Loaded', load_panel_widget)
        loaded_data_label.setAlignment(QtCore.Qt.AlignCenter)
        load_panel_widget.layout().addWidget(loaded_data_label, 0, 0, 1, 8)
        loaded_data_info_string = '::: Data #: {0} ::: Full File Path {1} :::'.format(data_row, file_path)
        loaded_data_label.setText(loaded_data_info_string)
        loaded_data_label.setStyleSheet('QLabel {color: blue}')
        loaded_data_label.setFont(self.size_14_font)
        data_row_label_header_label = QtWidgets.QLabel('Data Label:', load_panel_widget)
        load_panel_widget.layout().addWidget(data_row_label_header_label, 5, 1, 1, 1)
        data_row_label_lineedit = QtWidgets.QLineEdit('', self)
        data_row_label_lineedit.setText(basename)
        load_panel_widget.layout().addWidget(data_row_label_lineedit, 5, 2, 1, 3)
        setattr(self, 'data_row_plot_label_{0}'.format(data_row), data_row_label_lineedit)
        # Include in Plot
        self.include_in_plot_checkbox = QtWidgets.QCheckBox('{0} ::: Include in plot?'.format(data_row), load_panel_widget)
        load_panel_widget.layout().addWidget(self.include_in_plot_checkbox, 5, 0, 1, 1)
        self.include_in_plot_checkbox.clicked.connect(self.dp_update_include_in_plot_list)
        self.include_in_plot_checkbox.click()
        # Divide by
        divide_by_header_label = QtWidgets.QLabel('Divide Y by:', load_panel_widget)
        load_panel_widget.layout().addWidget(divide_by_header_label, 4, 1, 1, 1)
        divide_by_combobox = QtWidgets.QComboBox(load_panel_widget)
        load_panel_widget.layout().addWidget(divide_by_combobox, 4, 2, 1, 1)
        divide_by_combobox.addItem('')
        for data_row in self.loaded_file_data_rows:
            divide_by_combobox.addItem(str(data_row))
        setattr(self, 'divide_by_{0}_combobox'.format(data_row), divide_by_combobox)
        # Data Scaling
        scale_x_pushbutton = QtWidgets.QPushButton('{0} ::: Scale X'.format(data_row), load_panel_widget)
        load_panel_widget.layout().addWidget(scale_x_pushbutton, 4, 0, 1, 1)
        scale_y_pushbutton = QtWidgets.QPushButton('{0} ::: Scale Y'.format(data_row), load_panel_widget)
        load_panel_widget.layout().addWidget(scale_y_pushbutton, 4, 3, 1, 1)
        # Data Clipping
        data_clip_lo_header_label = QtWidgets.QLabel('Data Clip Lo (%):', load_panel_widget)
        load_panel_widget.layout().addWidget(data_clip_lo_header_label, 4, 4, 1, 1)
        data_clip_lo_lineedit = QtWidgets.QLineEdit('0.0', load_panel_widget)
        load_panel_widget.layout().addWidget(data_clip_lo_lineedit, 4, 5, 1, 1)
        setattr(self, 'data_clip_{0}_lo_lineedit'.format(data_row), data_clip_lo_lineedit)
        data_clip_hi_header_label = QtWidgets.QLabel('Data Clip Hi (%):', load_panel_widget)
        load_panel_widget.layout().addWidget(data_clip_hi_header_label, 4, 6, 1, 1)
        data_clip_hi_lineedit = QtWidgets.QLineEdit('0.0', load_panel_widget)
        load_panel_widget.layout().addWidget(data_clip_hi_lineedit, 4, 7, 1, 1)
        setattr(self, 'data_clip_{0}_hi_lineedit'.format(data_row), data_clip_hi_lineedit)
        # Close 
        close_file_pushbutton = QtWidgets.QPushButton('Close File {0}'.format(data_row), self)
        close_file_pushbutton.clicked.connect(self.dp_close_open_file)
        load_panel_widget.layout().addWidget(close_file_pushbutton, 7, 0, 1, 8)
        self.dp_update_input()

    def dp_close_open_file(self):
        '''
        '''
        data_row = self.sender().text().split(' ')[-1]
        getattr(self, 'load_panel_widget_{0}'.format(data_row)).setParent(None)
        getattr(self, 'load_panel_widget_{0}'.format(data_row))
        self.loaded_file_data_rows.remove(int(data_row))

    def dp_get_and_check_data(self):
        '''
        '''
        data_dict = {}
        for data_row in self.loaded_file_data_rows:
            data = getattr(self, 'data_{0}'.format(data_row))
            data_dict[data_row] = {}
            for data_type in self.data_types:
                for column in range(data.shape[1]):
                    column_data_type = getattr(self, 'data_{0}_column_{1}_data_type'.format(data_row, column)).currentText()
                    data_multiply_value = float(getattr(self, 'data_{0}_multiply_column_{1}'.format(data_row, column)).text())
                    if column_data_type == data_type:
                        row_data_type = '{0}_{1}'.format(data_type, data_row)
                        setattr(self, row_data_type, data.T[column] * data_multiply_value)
                        data_dict[data_row].update({data_type: data.T[column] * data_multiply_value})
                        label = getattr(self, 'data_row_plot_label_{0}'.format(data_row)).text()
                        data_clip_lo = float(getattr(self, 'data_clip_{0}_lo_lineedit'.format(data_row)).text()) / 100.0
                        data_clip_hi = float(getattr(self, 'data_clip_{0}_hi_lineedit'.format(data_row)).text()) / 100.0
                        divide_by = getattr(self, 'divide_by_{0}_combobox'.format(data_row)).currentText()
                        plot_dict = {
                            'label': label,
                            'data_clip_lo': data_clip_lo,
                            'data_clip_hi': data_clip_hi,
                            'divide_by': divide_by
                            }
                        data_dict[data_row].update(plot_dict)
            if ('x_data' in data_dict[data_row] and 'y_data' in data_dict[data_row]) and not ('xerr' in data_dict[data_row] and 'yerr' in data_dict[data_row]):
                data_dict[data_row]['xerr'] = None
                data_dict[data_row]['yerr'] = None
            elif ('x_data' in data_dict[data_row] and 'y_data' in data_dict[data_row]) and 'xerr' not in data_dict[data_row]:
                data_dict[data_row]['xerr'] = None
            elif ('x_data' in data_dict[data_row] and 'y_data' in data_dict[data_row]) and 'yerr' not in data_dict[data_row]:
                data_dict[data_row]['yerr'] = None
            #elif len(data_dict) == len(self.data_types):
                #self.gb_quick_message('Please check your data input!', msg_type='Warning')
                #return {}
        return data_dict

    def dp_plot(self):
        '''
        '''
        x_label_1 = self.x_label_lineedit_1.text()
        y_label_1 = self.y_label_lineedit_1.text()
        x_label_2 = self.x_label_lineedit_2.text()
        y_label_2 = self.y_label_lineedit_2.text()
        title = self.title_lineedit.text()
        fig, ax = self.db_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.5)
        data_dict = self.dp_get_and_check_data()
        if len(data_dict) > 0:
            for data_row in self.loaded_file_data_rows:
                if str(data_row) in self.include_in_plot_list:
                    # Divide the data  
                    divide_by = data_dict[data_row]['divide_by']
                    print(len(divide_by), divide_by)
                    if len(divide_by) > 0:
                        if len(data_dict[data_row]['y_data']) == len(data_dict[int(divide_by)]['y_data']):
                            print
                            y_data = np.asarray(data_dict[data_row]['y_data']) / np.asarray(data_dict[int(divide_by)]['y_data'])
                            y_data = list(y_data)
                        else:
                            y_data = data_dict[data_row]['y_data']
                            self.gb_quick_message('Cannot deivide data with different lengths', msg_type='Warning')
                    else:
                        y_data = data_dict[data_row]['y_data']
                    # Clip the data
                    data_clip_lo = data_dict[data_row]['data_clip_lo']
                    data_clip_hi = data_dict[data_row]['data_clip_hi']
                    lo_index = int(len(data_dict[data_row]['x_data']) * data_clip_lo)
                    hi_index = int(len(data_dict[data_row]['x_data']) * (1 - data_clip_hi))
                    x_data = data_dict[data_row]['x_data'][lo_index:hi_index]
                    xerr = data_dict[data_row]['xerr'][lo_index:hi_index]
                    y_data = y_data[lo_index:hi_index]
                    yerr = data_dict[data_row]['yerr'][lo_index:hi_index]
                    label = data_dict[data_row]['label']
                    ax.errorbar(x_data, y_data, xerr=xerr, yerr=yerr, marker='.', linestyle='-', lw=5, label=label)
            ax.tick_params(axis='x', labelsize=16)
            ax.tick_params(axis='y', labelsize=16)
            ax.set_xlabel(x_label_1, fontsize=16)
            ax.set_ylabel(y_label_1, fontsize=16)
            ax.set_title(title, fontsize=16)
            pl.legend(fontsize=16, loc='best')
        pl.show()
        pl.close()

    def db_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.25,
                             left=0.07, right=0.98, top=0.95, bottom=0.12, multiple_axes=False,
                             aspect=None):
        '''
        '''
        if frac_screen_width is None and frac_screen_height is None:
            fig = pl.figure()
        else:
            width = (frac_screen_width * self.screen_resolution.width()) / self.monitor_dpi
            height = (frac_screen_height * self.screen_resolution.height()) / self.monitor_dpi
            fig = pl.figure(figsize=(width, height))
        self.plot_count += 1
        if not multiple_axes:
            if aspect is None:
                ax = fig.add_subplot(111, label='plot_{0}'.format(self.plot_count))
            else:
                ax = fig.add_subplot(111, aspect=aspect, label='plot_{0}'.format(self.plot_count))
        else:
            ax = None
        fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
        return fig, ax
