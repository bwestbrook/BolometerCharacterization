import os
import json
import pylab as pl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from copy import copy
from pprint import pprint
from bd_lib.mpl_canvas import MplCanvas
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class CosmicRayViewer(QtWidgets.QWidget, GuiBuilder):


    def __init__(self, status_bar, screen_resolution, monitor_dpi, data_folder):
        '''
        '''
        super(CosmicRayViewer, self).__init__()
        self.mplc = MplCanvas(self, screen_resolution, monitor_dpi)
        self.data_folder = data_folder
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.crv_data_input_panel()

    def crv_data_input_panel(self):
        '''
        '''
        # Load the data
        self.load_data_push_button = QtWidgets.QPushButton('Load Data')
        self.load_data_push_button.clicked.connect(self.crv_load_data)
        self.layout().addWidget(self.load_data_push_button, 0, 0, 1, 1)
        self.data_set_combobox = self.gb_make_labeled_combobox('Data Set:')
        self.layout().addWidget(self.data_set_combobox, 0, 1, 1, 2)
        self.data_set_combobox.currentIndexChanged.connect(self.crv_plot)
        self.prev_pushbutton = QtWidgets.QPushButton('Prev')
        self.layout().addWidget(self.prev_pushbutton, 1, 1, 1, 1)
        self.next_pushbutton = QtWidgets.QPushButton('Next')
        self.layout().addWidget(self.next_pushbutton, 1, 2, 1, 1)
        self.next_pushbutton.clicked.connect(self.crv_change_file)
        self.prev_pushbutton.clicked.connect(self.crv_change_file)
        # Make nice plots
        self.plot_data_push_button = QtWidgets.QPushButton('Plot Data')
        self.plot_data_push_button.clicked.connect(self.crv_plot_pl)
        self.layout().addWidget(self.plot_data_push_button, 4, 0, 1, 1)
        self.title_lineedit = self.gb_make_labeled_lineedit(label_text='Title')
        self.layout().addWidget(self.title_lineedit, 4, 1, 1, 1)
        self.font_size_lineedit = self.gb_make_labeled_lineedit(label_text='Font Size', lineedit_text='12')
        self.layout().addWidget(self.font_size_lineedit, 4, 2, 1, 1)
        self.main_plot_label = QtWidgets.QLabel()
        self.layout().addWidget(self.main_plot_label, 5, 0, 1, 3)

    def crv_change_file(self):
        '''
        '''
        current_index = int(self.data_set_combobox.currentIndex())
        if self.sender().text() == 'Next':
            if current_index == self.data_set_combobox.count() - 1:
                current_index = current_index
            else:
                current_index += 1
        elif self.sender().text() == 'Prev':
            if current_index == 0:
                current_index = current_index
            else:
                current_index -= 1
        print('after', current_index)
        self.data_set_combobox.setCurrentIndex(current_index)

    def crv_load_data(self):
        '''
        '''

        data_folder = QtWidgets.QFileDialog.getExistingDirectory(self, 'Open Data Folder', self.data_folder)
        if not os.path.exists(data_folder):
            return None
        for file_name in os.listdir(data_folder):
            if 'txt' in file_name:
                print(file_name.split('.')[0].split('_')[-1])
                file_path = os.path.join(data_folder, file_name)
                self.data_set_combobox.addItem(file_path)
        self.crv_plot()

    def crv_load(self):
        '''
        '''
        file_path = self.data_set_combobox.currentText()
        df = pd.read_csv(file_path)
        return df

    def crv_plot_pl(self, frac_screen_width=0.7, frac_screen_height=0.5):
        '''
        '''
        if self.gb_is_float(self.font_size_lineedit.text()):
            font_size = int(self.font_size_lineedit.text())

        width = (frac_screen_width * self.screen_resolution.width()) / self.monitor_dpi # in pixels
        height = (frac_screen_height * self.screen_resolution.height()) / self.monitor_dpi # in pixels
        print(width, height)
        title = self.title_lineedit.text()
        df = self.crv_load()
        fig = pl.figure(figsize=(width, height))
        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(223)
        ax4 = fig.add_subplot(224)
        fig.subplots_adjust(
            left=0.08,
            right=0.98,
            top=0.95,
            bottom=0.08,
            wspace=0.25,
            hspace=0.25)
        ax1.set_ylabel('V')
        ax3.set_ylabel('V')
        ax3.set_xlabel('Sample')
        ax4.set_xlabel('Sample')
        axes = fig.get_axes()
        for i in range(4):
            #import ipdb;ipdb.set_trace()
            ch_voltage = df[df.columns[i]].values
            axes[i].plot(ch_voltage)
        pl.xticks(fontsize=font_size)
        pl.yticks(fontsize=font_size)
        pl.title(title, fontsize=font_size)
        pl.show()

    def crv_plot(self):
        '''
        '''
        if self.gb_is_float(self.font_size_lineedit.text()):
            font_size = int(self.font_size_lineedit.text())
        title = self.title_lineedit.text()
        df = self.crv_load()
        fig =self.mplc.mplc_create_cr_paneled_plot(
            name='Cosmic Rays',
            left=0.08,
            right=0.98,
            top=0.95,
            bottom=0.08,
            frac_screen_width=0.5,
            frac_screen_height=0.6,
            wspace=0.25,
            hspace=0.25)
        axes = fig.get_axes()
        axes[0].set_ylabel('V')
        axes[2].set_ylabel('V')
        axes[2].set_xlabel('Sample')
        axes[3].set_xlabel('Sample')
        for i in range(4):
            ch_voltage = df[df.columns[i]].values
            axes[i].plot(ch_voltage)
        fig.suptitle(title, fontsize=font_size)
        temp_png_path = os.path.join('temp_files', 'temp_cr.png')
        fig.savefig(temp_png_path)
        image_to_display = QtGui.QPixmap(temp_png_path)
        self.main_plot_label.setPixmap(image_to_display)

