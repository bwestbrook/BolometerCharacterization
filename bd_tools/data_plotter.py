import os
import shutil
import pylab as pl
import numpy as np
import pandas as pd
import matplotlib as mpl
from matplotlib.lines import Line2D
from matplotlib import rc
rc('text', usetex=True)
rc('text.latex', preamble=r'\usepackage{amssymb}')
import matplotlib.pyplot as plt
from copy import copy
from pprint import pprint
from scipy.optimize import curve_fit
from PyQt5 import QtCore, QtGui, QtWidgets
from bd_lib.mpl_canvas import MplCanvas
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class DataPlotter(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, status_bar, screen_resolution, monitor_dpi, data_folder):
        super(DataPlotter, self).__init__()
        self.data_folder = data_folder
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.mplc = MplCanvas(self, screen_resolution, monitor_dpi)
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.plot_count = 0
        self.data_types = [
            'x_data',
            'xerr',
            'y_data',
            'yerr',
            ]
        self.loaded_file_data_rows = []
        self.include_in_plot_list = []
        self.marker_styles = {
                '-': '',
                'o': '',
                '*': '',
                '.': '',
                }
        self.fit_types = {
                'Polynomial': 'p[0]*X**[N-1] + ...',
                'Exponential': 'A*eB*x + C',
                'Sinusoid': 'A*sin(B*x) + C',
                }
        self.dp_controls()
        self.dp_plot_input()

    ########################
    # Gui Setup 
    ########################

    def dp_controls(self):
        '''
        '''
        load_pushbutton = QtWidgets.QPushButton('Load', self)
        self.layout().addWidget(load_pushbutton, 0, 0, 1, 1)
        load_pushbutton.clicked.connect(self.dp_load_data)
        plot_pushbutton = QtWidgets.QPushButton('Replot', self)
        self.layout().addWidget(plot_pushbutton, 0, 1, 1, 1)
        plot_pushbutton.clicked.connect(self.dp_plot)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        self.layout().addWidget(save_pushbutton, 0, 2, 1, 1)
        save_pushbutton.clicked.connect(self.dp_save)

    def dp_plot_input(self):
        '''
        '''
        # Title
        self.title_lineedit = self.gb_make_labeled_lineedit(label_text='Title')
        self.layout().addWidget(self.title_lineedit, 1, 0, 1, 4)
        self.title_lineedit.returnPressed.connect(self.dp_plot)
        # X label 1
        self.x_label_lineedit_1 = self.gb_make_labeled_lineedit(label_text='X Label 1')
        self.layout().addWidget(self.x_label_lineedit_1, 2, 0, 1, 1)
        self.x_label_lineedit_1.returnPressed.connect(self.dp_plot)
        # X label 2
        self.x_label_lineedit_2 = self.gb_make_labeled_lineedit(label_text='X Label 2')
        self.layout().addWidget(self.x_label_lineedit_2, 2, 1, 1, 1)
        self.x_label_lineedit_2.returnPressed.connect(self.dp_plot)
        # Y label 1
        self.y_label_lineedit_1 = self.gb_make_labeled_lineedit(label_text='Y Label 1')
        self.layout().addWidget(self.y_label_lineedit_1, 2, 2, 1, 1)
        self.y_label_lineedit_1.returnPressed.connect(self.dp_plot)
        # Y label 2
        self.y_label_lineedit_2 = self.gb_make_labeled_lineedit(label_text='Y Label 2')
        self.layout().addWidget(self.y_label_lineedit_2, 2, 3, 1, 1)
        self.y_label_lineedit_2.returnPressed.connect(self.dp_plot)

        #### Plotting Option
        self.fontsize_lineedit = self.gb_make_labeled_lineedit(label_text='fontsize', lineedit_text='16')
        self.fontsize_lineedit.setValidator(QtGui.QIntValidator(2, 36, self.fontsize_lineedit))
        self.layout().addWidget(self.fontsize_lineedit, 3, 0, 1, 1)
        self.fontsize_lineedit.returnPressed.connect(self.dp_plot)
        self.ticksize_lineedit = self.gb_make_labeled_lineedit(label_text='ticksize', lineedit_text='14')
        self.ticksize_lineedit.setValidator(QtGui.QIntValidator(2, 36, self.ticksize_lineedit))
        self.ticksize_lineedit.returnPressed.connect(self.dp_plot)
        self.layout().addWidget(self.ticksize_lineedit, 3, 1, 1, 1)
        self.legend_checkbox = QtWidgets.QCheckBox('Legend?')
        self.legend_checkbox.setChecked(True)
        self.layout().addWidget(self.legend_checkbox, 3, 2, 1, 1)
        self.legend_checkbox.clicked.connect(self.dp_plot)
        self.transparent_checkbox = QtWidgets.QCheckBox('Transparent?')
        self.layout().addWidget(self.transparent_checkbox, 3, 3, 1, 1)
        self.transparent_checkbox.setChecked(False)
        self.transparent_checkbox.clicked.connect(self.dp_plot)

        #Subplot
        self.left_lineedit = self.gb_make_labeled_lineedit(label_text='Left', lineedit_text='0.1')
        self.left_lineedit.setValidator(QtGui.QDoubleValidator(0, 1, 4, self.left_lineedit))
        self.layout().addWidget(self.left_lineedit, 4, 0, 1, 1)
        self.left_lineedit.returnPressed.connect(self.dp_plot)
        self.right_lineedit = self.gb_make_labeled_lineedit(label_text='Right', lineedit_text='0.9')
        self.right_lineedit.setValidator(QtGui.QDoubleValidator(0, 1, 4, self.right_lineedit))
        self.layout().addWidget(self.right_lineedit, 4, 1, 1, 1)
        self.right_lineedit.returnPressed.connect(self.dp_plot)
        self.top_lineedit = self.gb_make_labeled_lineedit(label_text='Top', lineedit_text='0.9')
        self.top_lineedit.setValidator(QtGui.QDoubleValidator(0, 1, 4, self.top_lineedit))
        self.layout().addWidget(self.top_lineedit, 4, 2, 1, 1)
        self.top_lineedit.returnPressed.connect(self.dp_plot)
        self.bottom_lineedit = self.gb_make_labeled_lineedit(label_text='Bottom', lineedit_text='0.1')
        self.bottom_lineedit.setValidator(QtGui.QDoubleValidator(0, 1, 4, self.bottom_lineedit))
        self.layout().addWidget(self.bottom_lineedit, 4, 3, 1, 1)
        self.bottom_lineedit.returnPressed.connect(self.dp_plot)

        # Fig Size
        self.frac_screen_width_lineedit = self.gb_make_labeled_lineedit(label_text='Frac Screen Width', lineedit_text='0.5')
        self.frac_screen_width_lineedit.setValidator(QtGui.QDoubleValidator(0, 1, 4, self.frac_screen_width_lineedit))
        self.layout().addWidget(self.frac_screen_width_lineedit, 5, 0, 1, 1)
        self.frac_screen_width_lineedit.returnPressed.connect(self.dp_plot)
        self.frac_screen_height_lineedit = self.gb_make_labeled_lineedit(label_text='Frac Screen Height', lineedit_text='0.5')
        self.frac_screen_height_lineedit.setValidator(QtGui.QDoubleValidator(0, 1, 4, self.frac_screen_height_lineedit))
        self.frac_screen_height_lineedit.returnPressed.connect(self.dp_plot)
        self.layout().addWidget(self.frac_screen_height_lineedit, 5, 1, 1, 1)
        self.marker_style_combobox = self.gb_make_labeled_combobox(label_text='Marker Style')
        #import ipdb;ipdb.set_trace()
        for marker_style in Line2D.markers:
            print(marker_style)
            if not str(marker_style).isnumeric():
                self.marker_style_combobox.addItem(str(marker_style))
        self.marker_style_combobox.currentIndexChanged.connect(self.dp_plot)
        self.layout().addWidget(self.marker_style_combobox, 5, 2, 1, 1)
        self.marker_size_lineedit = self.gb_make_labeled_lineedit(label_text='Marker Size', lineedit_text='3')
        self.marker_size_lineedit.returnPressed.connect(self.dp_plot)
        self.layout().addWidget(self.marker_size_lineedit, 5, 3, 1, 1)
        #Data Clip
        self.data_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Lo', lineedit_text='0')
        self.data_clip_lo_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e8, 4, self.data_clip_lo_lineedit))
        self.layout().addWidget(self.data_clip_lo_lineedit, 6, 0, 1, 1)
        self.data_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Data Clip Hi', lineedit_text='1e8')
        self.data_clip_hi_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e8, 4, self.data_clip_hi_lineedit))
        self.layout().addWidget(self.data_clip_hi_lineedit, 6, 1, 1, 1)
        self.data_clip_lo_lineedit.returnPressed.connect(self.dp_plot)
        self.data_clip_hi_lineedit.returnPressed.connect(self.dp_plot)

        self.sample_clip_lo_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Clip Lo', lineedit_text='0')
        self.sample_clip_lo_lineedit.setValidator(QtGui.QIntValidator(0, 1000000, self.sample_clip_lo_lineedit))
        self.layout().addWidget(self.sample_clip_lo_lineedit, 6, 2, 1, 1)
        self.sample_clip_hi_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Clip Hi', lineedit_text='10000')
        self.sample_clip_hi_lineedit.setValidator(QtGui.QIntValidator(0, 1000000, self.sample_clip_hi_lineedit))
        self.layout().addWidget(self.sample_clip_hi_lineedit, 6, 3, 1, 1)
        self.sample_clip_lo_lineedit.returnPressed.connect(self.dp_plot)
        self.sample_clip_hi_lineedit.returnPressed.connect(self.dp_plot)

        #Add Fit 
        self.fit_select_combobox = self.gb_make_labeled_combobox(label_text='Fit Type')
        self.layout().addWidget(self.fit_select_combobox, 7, 0, 1, 1)
        for fit in self.fit_types:
            self.fit_select_combobox.addItem(fit)
        self.fit_select_combobox.currentIndexChanged.connect(self.dp_update_polyfit)
        self.fit_select_combobox.currentIndexChanged.connect(self.dp_plot)
        self.poly_fit_degree_combobox = self.gb_make_labeled_combobox(label_text='Poly Fit N')
        for i in range(100):
            self.poly_fit_degree_combobox.addItem(str(i))
        self.layout().addWidget(self.poly_fit_degree_combobox, 7, 1, 1, 1)
        self.poly_fit_degree_combobox.currentIndexChanged.connect(self.dp_plot)
        self.poly_fit_degree_combobox.setCurrentIndex(2)
        self.fit_select_checkbox = QtWidgets.QCheckBox('Add Fit?')
        self.fit_select_checkbox.setChecked(False)
        self.fit_select_checkbox.clicked.connect(self.dp_plot)
        self.layout().addWidget(self.fit_select_checkbox, 7, 2, 1, 1)
        self.fit_type_label = QtWidgets.QLabel()
        self.layout().addWidget(self.fit_type_label, 8, 0, 1, 1)
        self.fit_value_label = QtWidgets.QLabel()
        self.layout().addWidget(self.fit_value_label, 8, 2, 1, 1)

        # Pane to Plot
        self.plot_label = QtWidgets.QLabel()
        self.layout().addWidget(self.plot_label, 0, 5, 9, 1)

    ########################
    # Loading and Plotting 
    ########################


    def dp_update_polyfit(self):
        '''
        '''
        fit_type = self.fit_select_combobox.currentText()
        self.fit_type_label.setText(self.fit_types[fit_type])
        if fit_type == 'Polynomial':
            self.poly_fit_degree_combobox.setDisabled(False)
        else:
            self.poly_fit_degree_combobox.setDisabled(True)

    def dp_load_data(self):
        '''
        '''
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
        if len(file_path) > 0:
            if file_path.endswith('json') or file_path.endswith('txt'):
                df = pd.read_json(file_path)
                if df.shape[1] == 1:
                    x_label = df.keys()[0]
                    self.x_label_lineedit_1.setText(x_label)
                    x_data = np.asarray(df.index)
                    y_data = df[df.keys()[0]].values
                    x_err = np.zeros(len(x_data))
                    y_err = np.zeros(len(y_data))
                elif df.shape[1] == 2:
                    x_data = df[df.keys()[0]].values
                    y_data = df[df.keys()[1]].values
                    x_err = np.zeros(len(x_data))
                    y_err = np.zeros(len(y_data))
                elif df.shape[1] == 4:
                    x_data = df[df.keys()[0]].values
                    x_err = df[df.keys()[1]].values
                    y_data = df[df.keys()[2]].values
                    y_err = df[df.keys()[3]].values
                else:
                    self.gb_quick_message('Please load a json with (1) TOD, (2) XY, (4) XY with Errror data file', msg_type='Warning')
                    x_data = []
                    x_err = []
                    y_data = []
                    y_err = []
                data_dict = {
                    'x_data': x_data,
                    'x_err': x_err,
                    'y_data': y_data,
                    'y_err': y_err}
                self.df = pd.DataFrame.from_dict(data_dict)
            elif file_path.endswith('txt') or file_path.endswith('dat'):
                import ipdb;ipdb.set_trace()
            else:
                self.gb_quick_message('Please load a json or a data file (txt/dat)', msg_type='Warning')
        self.dp_plot()

    def dp_get_fit(self):
        '''
        '''
        sample_clip_lo = int(self.sample_clip_lo_lineedit.text())
        sample_clip_hi = int(self.sample_clip_hi_lineedit.text())
        data_clip_lo = float(self.data_clip_lo_lineedit.text())
        data_clip_hi = float(self.data_clip_hi_lineedit.text())
        if self.df.shape[1] == 2:
            x_data = self.df[self.df.keys()[0]].values[sample_clip_lo:sample_clip_hi]
            y_data = self.df[self.df.keys()[1]].values[sample_clip_lo:sample_clip_hi]
        elif self.df.shape[1] == 4:
            x_data = self.df[self.df.keys()[0]].values[sample_clip_lo:sample_clip_hi]
            y_data = self.df[self.df.keys()[2]].values[sample_clip_lo:sample_clip_hi]
        else:
            self.gb_quick_message('Please load a data with 2 or 4 columns', msg_type='Warning')
        data_selector = np.logical_and(data_clip_lo < x_data, x_data < data_clip_hi)
        x_data = x_data[data_selector]
        y_data = y_data[data_selector]
        x_fits = np.linspace(np.min(x_data), np.max(x_data), 100)
        if self.fit_select_combobox.currentText() == 'Polynomial':
            #Basic Poly Fit
            poly_fit_deg = int(self.poly_fit_degree_combobox.currentText())
            p_fits = np.polyfit(x_data, y_data, poly_fit_deg)
            y_fits = np.polyval(p_fits, x_fits)
            self.fit_value_label.setText(str(p_fits))
        elif self.fit_select_combobox.currentText() == 'Exponential':
            popt, pcov = curve_fit(self.dp_exponential, x_data, y_data)
            y_fits = self.dp_exponential(x_fits, *popt)
            self.fit_value_label.setText(str(popt))
        elif self.fit_select_combobox.currentText() == 'Sinusoid':
            popt, pcov = curve_fit(self.dp_sinusoid, x_data, y_data)
            y_fits = self.dp_sinusoid(x_fits, *popt)
            self.fit_value_label.setText(str(popt))
        return x_fits, y_fits

    def dp_exponential(self, x, A, B, C):
        '''
        '''
        y = A * np.exp(B * x) + C
        return y

    def dp_sinusoid(self, x, A, B, C):
        '''
        '''
        y = A * np.exp(B * x) + C
        return y


    def dp_plot(self):
        '''
        '''
        if not hasattr(self, 'df'):
            return None
        x_label = self.x_label_lineedit_1.text()
        y_label = self.y_label_lineedit_1.text()
        x_label_2 = self.x_label_lineedit_2.text()
        y_label_2 = self.y_label_lineedit_2.text()
        title = self.title_lineedit.text()
        fontsize = int(self.fontsize_lineedit.text())
        ticksize = int(self.ticksize_lineedit.text())
        left = float(self.left_lineedit.text())
        right = float(self.right_lineedit.text())
        top = float(self.top_lineedit.text())
        bottom = float(self.bottom_lineedit.text())
        frac_screen_width = float(self.frac_screen_width_lineedit.text())
        frac_screen_height = float(self.frac_screen_height_lineedit.text())
        fig, ax = self.mplc.mplc_create_basic_fig(
                left=left,
                right=right,
                bottom=bottom,
                top=top,
                frac_screen_height=frac_screen_height,
                frac_screen_width=frac_screen_width)
        if len(x_label_2) > 0:
            axx2 = ax.twiny()
            axx2.set_xlabel(x_label_2)
        if len(y_label_2) > 0:
            axy2 = ax.twinx()
            axy2.set_ylabel(y_label_2)
        marker_style = self.marker_style_combobox.currentText()
        marker_size = float(self.marker_size_lineedit.text())
        sample_clip_lo = int(self.sample_clip_lo_lineedit.text())
        sample_clip_hi = int(self.sample_clip_hi_lineedit.text())
        data_clip_lo = float(self.data_clip_lo_lineedit.text())
        data_clip_hi = float(self.data_clip_hi_lineedit.text())
        x_data = np.asarray(self.df['x_data'][0][sample_clip_lo:sample_clip_hi])
        y_data = np.asarray(self.df['y_data'][0][sample_clip_lo:sample_clip_hi])
        xerr = np.asarray(self.df['x_data'][1][sample_clip_lo:sample_clip_hi])
        yerr = np.asarray(self.df['y_data'][1][sample_clip_lo:sample_clip_hi])
        #self.qthreadpool.start(daq.run)
        print(x_data)
        try:
            data_selector = np.logical_and(data_clip_lo < np.asarray(x_data), np.asarray(x_data) < data_clip_hi)
            #import ipdb;ipdb.set_trace()
            x_data = x_data[data_selector]
            xerr = xerr[data_selector]
            y_data = y_data[data_selector]
            yerr = yerr[data_selector]
        except TypeError:
            data_selector = np.logical_and(data_clip_lo < np.asarray(x_data[0]), np.asarray(x_data[0]) < data_clip_hi)
            x_data = x_data[0][data_selector]
            xerr = x_data[1][data_selector]
            y_data = y_data[0][data_selector]
            yerr = y_data[1][data_selector]

        ax.errorbar(x_data, y_data, xerr=xerr, yerr=yerr, fmt=marker_style, ms=marker_size)
        ax.tick_params(axis='both', labelsize=ticksize)
        ax.set_xlabel(x_label, fontsize=fontsize)
        ax.set_ylabel(y_label, fontsize=fontsize)
        ax.set_title(title, fontsize=fontsize)
        temp_save_path = os.path.join('temp_files', 'temp_custom_xy.png')
        if self.fit_select_checkbox.isChecked():
            x_fits, y_fits = self.dp_get_fit()
            ax.plot(x_fits, y_fits, label='{0} Fit'.format(self.fit_select_combobox.currentText()))
        if self.legend_checkbox.isChecked() and False:
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels, numpoints=1, mode="expand", frameon=True, fontsize=10, bbox_to_anchor=(0, 0.1, 1, 1))
        fig.savefig(temp_save_path, transparent=self.transparent_checkbox.isChecked())
        image_to_display = QtGui.QPixmap(temp_save_path)
        self.plot_label.setPixmap(image_to_display)

    def dp_save(self):
        '''
        '''
        save_path = os.path.join('temp_files', 'temp_custom_xy.png')
        new_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', save_path, '.png')[0]
        print(save_path, new_path)
        shutil.copy(save_path, new_path)
        json_path = new_path.replace('png', 'json')
        self.df.to_json(json_path)

