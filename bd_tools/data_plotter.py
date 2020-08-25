import os
import pylab as pl
import numpy as np
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
        self.data_types = [
            'x_data',
            'xerr',
            'y_data',
            'yerr',
            ]
        self.dp_plot_input()
        self.dp_controls()
        self.loaded_data_file_count = 0
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
        n_subplots_header_label = QtWidgets.QLabel('N Subplots', self)
        self.layout().addWidget(n_subplots_header_label, 4, 0, 1, 1)
        self.n_subplots_combobox = QtWidgets.QComboBox( self)
        self.layout().addWidget(self.n_subplots_combobox, 4, 1, 1, 7)
        for i in range(1, 3):
            self.n_subplots_combobox.addItem(str(i))
        load_pushbutton = QtWidgets.QPushButton('Load', self)
        self.layout().addWidget(load_pushbutton, 5, 0, 1, 8)
        load_pushbutton.clicked.connect(self.dp_load_data)
        plot_pushbutton = QtWidgets.QPushButton('Plot', self)
        self.layout().addWidget(plot_pushbutton, 6, 0, 1, 8)
        plot_pushbutton.clicked.connect(self.dp_plot)

    def dp_plot_input(self):
        '''
        '''
        # X label 1
        x_header_label_1 = QtWidgets.QLabel('X Label 1', self)
        self.layout().addWidget(x_header_label_1, 1, 0, 1, 1)
        self.x_label_lineedit_1 = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.x_label_lineedit_1, 1, 1, 1, 3)
        # X label 2
        x_header_label_2 = QtWidgets.QLabel('X Label 2', self)
        self.layout().addWidget(x_header_label_2, 1, 4, 1, 1)
        self.x_label_lineedit_2 = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.x_label_lineedit_2, 1, 5, 1, 3)
        y_header_label_1 = QtWidgets.QLabel('Y Label 1', self)
        self.layout().addWidget(y_header_label_1, 2, 0, 1, 1)
        y_header_label_2 = QtWidgets.QLabel('Y Label 2', self)
        self.layout().addWidget(y_header_label_2, 2, 2, 1, 1)
        self.y_label_lineedit_1 = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.y_label_lineedit_1, 2, 1, 1, 1)
        self.y_label_lineedit_2 = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.y_label_lineedit_2, 2, 3, 1, 1)
        title_header_label = QtWidgets.QLabel('Title', self)
        self.layout().addWidget(title_header_label, 3, 0, 1, 1)
        self.title_lineedit = QtWidgets.QLineEdit('', self)
        self.layout().addWidget(self.title_lineedit, 3, 1, 1, 1)

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

    def dp_get_input(self):
        '''
        '''
        x_label_1 = self.x_label_lineedit_1.text()
        y_label_1 = self.y_label_lineedit_1.text()
        x_label_2 = self.x_label_lineedit_2.text()
        y_label_2 = self.y_label_lineedit_2.text()
        title = self.title_lineedit.text()
        n_subplots = self.n_subplots_combobox.currentText()
        return x_label_1, x_label_2, y_label_1, y_label_2, title, n_subplots

    ########################
    # Loading and Plotting 
    ########################

    def dp_load_data(self):
        '''
        '''
        n_subplots = int(self.n_subplots_combobox.currentText())
        data_type = self.data_type_tab_bar.tabText(self.data_type_tab_bar.currentIndex())
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
        if len(file_path) > 0:
            for i in range(100):
                load_panel_widget = QtWidgets.QWidget()
                grid = QtWidgets.QGridLayout()
                load_panel_widget.setLayout(grid)
                if hasattr(self, 'load_panel_widget_{0}'.format(i)):
                    pass
                else:
                    setattr(self, 'load_panel_widget_{0}'.format(i), load_panel_widget)
                    print(self, 'load_panel_widget_{0}'.format(i))
                    break
            self.layout().addWidget(load_panel_widget, i + 7, 0, 1, 8)
            try:
                data = np.loadtxt(file_path, dtype=np.float, delimiter=',')
            except ValueError:
                data = np.loadtxt(file_path, dtype=np.float, delimiter='\t')
            setattr(self, 'data_{0}'.format(i), data)
            self.loaded_data_file_count += 1
            basename = os.path.basename(file_path).replace('.txt', '').replace('.dat', '')
            self.title_lineedit.setText(basename)
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
                setattr(self, 'data_{0}_column_{1}_data_type'.format(i, column), data_type_combobox)
                load_panel_widget.layout().addWidget(data_type_combobox, 0, column, 1, 1)
                if j < 4:
                    getattr(self, 'data_{0}_column_{1}_data_type'.format(i, column)).setCurrentIndex(j + 1)
                j += 1
            for column in range(data.shape[1]):
                data_preview = ''.join(['{0:.6f}\n'.format(x) for x in data.T[column]])
                column_textedit = QtWidgets.QTextEdit('', self)
                column_textedit.setReadOnly(True)
                if load_panel_widget.layout().itemAtPosition(6, column) is not None:
                    load_panel_widget.layout().itemAtPosition(6, column).widget().setParent(None)
                column_textedit.setText(data_preview)
                load_panel_widget.layout().addWidget(column_textedit, 1, column, 1, 1)
        column_label_header_label = QtWidgets.QLabel('Data Label:', self)
        load_panel_widget.layout().addWidget(column_label_header_label, 2, 0, 1, 7)
        column_label_lineedit = QtWidgets.QLineEdit('', self)
        column_label_lineedit.setText(basename)
        load_panel_widget.layout().addWidget(column_label_lineedit, 2, 1, 1, 7)
        setattr(self, 'column_plot_label_{0}'.format(i), column_label_lineedit)
        self.dp_update_input()
        loaded_data_label = QtWidgets.QLabel('No Data Loaded', self)
        setattr(self, 'load_data_label_{0}'.format(i), load_panel_widget)
        load_panel_widget.layout().addWidget(loaded_data_label, 5, 0, 1, 8)
        loaded_data_label.setText(file_path)
        close_file_pushbutton = QtWidgets.QPushButton('Close File {0}'.format(i), self)
        close_file_pushbutton.clicked.connect(self.dp_close_open_file)
        load_panel_widget.layout().addWidget(close_file_pushbutton, 3, 0, 1, 8)


    def dp_close_open_file(self):
        '''
        '''
        data_row = self.sender().text().split(' ')[-1]
        print(data_row)
        print(self, 'load_panel_widget_{0}'.format(data_row))
        getattr(self, 'load_panel_widget_{0}'.format(data_row)).setParent(None)
        getattr(self, 'load_panel_widget_{0}'.format(data_row))

    def dp_get_and_check_data(self):
        '''
        '''
        data_dict = {}
        for data_row in range(self.loaded_data_file_count):
            data = getattr(self, 'data_{0}'.format(data_row))
            i = 0
            data_dict[data_row] = {}
            for data_type in self.data_types:
                for column in range(data.shape[1]):
                    column_data_type = getattr(self, 'data_{0}_column_{1}_data_type'.format(data_row, column)).currentText()
                    if column_data_type == data_type:
                        row_data_type = '{0}_{1}'.format(data_type, data_row)
                        setattr(self, row_data_type, data.T[column])
                        data_dict[data_row].update({data_type: data.T[column]})
                        label = getattr(self, 'column_plot_label_{0}'.format(data_row)).text()
                        data_dict[data_row].update({'label': label})
            if ('x_data' in data_dict[data_row] and 'y_data' in data_dict[data_row]) and not ('xerr' in data_dict[data_row] and 'yerr' in data_dict[data_row]):
                data_dict[data_row]['xerr'] = None
                data_dict[data_row]['yerr'] = None
            elif ('x_data' in data_dict[data_row] and 'y_data' in data_dict[data_row]) and 'xerr' not in data_dict[data_row]:
                data_dict[data_row]['xerr'] = None
            elif ('x_data' in data_dict[data_row] and 'y_data' in data_dict[data_row]) and 'yerr' not in data_dict[data_row]:
                data_dict[data_row]['yerr'] = None
            elif len(data_dict) == len(self.data_types):
                self.gb_quick_message('Please check your data input!', msg_type='Warning')
                return {}
        return data_dict

    def dp_plot(self):
        '''
        '''
        x_label_1, x_label_2, y_label_1, y_label_2, title, n_subplots = self.dp_get_input()
        pl.close('all')
        data_dict = self.dp_get_and_check_data()
        if len(data_dict) > 0:
            if n_subplots == '1':
                fig, ax = self.db_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.5)
                for data_row in range(self.loaded_data_file_count):
                    x_data = data_dict[data_row]['x_data']
                    xerr = data_dict[data_row]['xerr']
                    y_data = data_dict[data_row]['y_data']
                    yerr = data_dict[data_row]['yerr']
                    label = data_dict[data_row]['label']
                    ax.errorbar(x_data, y_data, xerr=xerr, yerr=yerr, marker='.', linestyle='-', lw=5, label=label)
                ax.set_xlabel(x_label_1, fontsize=16)
                ax.set_ylabel(y_label_1, fontsize=16)
                ax.set_title(title, fontsize=16)
            else:
                import ipdb;ipdb.set_trace()
            pl.legend(fontsize=16, loc=2)
            pl.show()

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
        pl.xticks(fontsize=14)
        pl.yticks(fontsize=14)
        if not multiple_axes:
            if aspect is None:
                ax = fig.add_subplot(111)
            else:
                ax = fig.add_subplot(111, aspect=aspect)
        else:
            ax = None
        fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
        return fig, ax
