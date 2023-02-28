import os
import json
import pylab as pl
import numpy as np
import matplotlib.pyplot as plt
from copy import copy
from pprint import pprint
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class HistogramPlotter(QtWidgets.QWidget, GuiBuilder):


    def __init__(self, status_bar, screen_resolution, monitor_dpi, data_folder):
        '''
        '''
        super(HistogramPlotter, self).__init__()
        self.data_folder = data_folder
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.hp_data_input_panel()
        self.data_dict = {}


    def hp_data_input_panel(self):
        '''
        '''
        # Load the data
        self.load_data_push_button = QtWidgets.QPushButton('Load Data')
        self.load_data_push_button.clicked.connect(self.hp_load_data)
        self.layout().addWidget(self.load_data_push_button, 0, 0, 1, 1)

        # Add new data on the fly
        self.add_data_push_button = QtWidgets.QPushButton('Add Data')
        self.add_data_push_button.clicked.connect(self.hp_add_data)
        self.layout().addWidget(self.add_data_push_button, 1, 0, 1, 1)
        self.input_data_label_lineedit = self.gb_make_labeled_lineedit(label_text='Label')
        self.layout().addWidget(self.input_data_label_lineedit, 1, 1, 1, 1)
        self.input_data_lineedit = self.gb_make_labeled_lineedit(label_text='Data')
        self.layout().addWidget(self.input_data_lineedit, 1, 2, 1, 1)

        # Modify existing data on the fly
        self.modify_data_push_button = QtWidgets.QPushButton('Modify Data')
        self.modify_data_push_button.clicked.connect(self.hp_modify_data)
        self.layout().addWidget(self.modify_data_push_button, 2, 0, 1, 1)
        self.delete_data_push_button = QtWidgets.QPushButton('Delete Data')
        self.delete_data_push_button.clicked.connect(self.hp_delete_data)
        self.layout().addWidget(self.delete_data_push_button, 2, 1, 1, 1)
        self.load_data_label_combobox = self.gb_make_labeled_combobox(label_text='Labels')
        self.layout().addWidget(self.load_data_label_combobox, 2, 2, 1, 1)
        self.modify_data_lineedit = self.gb_make_labeled_lineedit(label_text='New Data')
        self.layout().addWidget(self.modify_data_lineedit, 2, 3, 1, 1)
        self.load_data_label_combobox.currentIndexChanged.connect(self.update_modify_lineedit)


        # Make nice plots
        self.plot_data_push_button = QtWidgets.QPushButton('Plot Data')
        self.plot_data_push_button.clicked.connect(self.hp_plot)
        self.layout().addWidget(self.plot_data_push_button, 4, 0, 1, 1)
        self.x_label_lineedit = self.gb_make_labeled_lineedit(label_text='X LABEL')
        self.layout().addWidget(self.x_label_lineedit, 4, 1, 1, 1)
        self.title_lineedit = self.gb_make_labeled_lineedit(label_text='Title')
        self.layout().addWidget(self.title_lineedit, 4, 2, 1, 1)
        self.font_size_lineedit = self.gb_make_labeled_lineedit(label_text='Font Size', lineedit_text='12')
        self.layout().addWidget(self.font_size_lineedit, 4, 3, 1, 1)
        # pritn the data
        self.input_data_display_label = self.gb_make_labeled_label(label_text='Loaded Data')
        self.layout().addWidget(self.input_data_display_label, 5, 0, 1, 3)

    def hp_load_data(self):
        '''
        '''
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r') as fh:
            data_dict = json.load(fh)
        float_data = []
        self.data_dict = {}
        for label, data in data_dict.items():
            for datum in data:
                if not self.gb_is_float(datum):
                    self.gb_quick_message('Please only load jsons with floats for data in the lists')
                    return None
                if label in self.data_dict:
                    self.data_dict[label].append(datum)
                else:
                    self.data_dict[label] = [datum]
                print(self.data_dict)
        self.hp_load_labels()
        self.input_data_display_label.setText(str(self.data_dict))
        #self.hp_plot()

    def hp_load_labels(self):
        '''
        '''
        combobox = self.load_data_label_combobox
        existing_items = []
        for i in range(combobox.count()):
            existing_items.append(combobox.itemText(i))
        items = self.data_dict.keys()
        for item in sorted(items):
            if item not in existing_items:
                combobox.addItem(str(item))
        combobox.setCurrentIndex(-1)
        combobox.setCurrentIndex(0)

    def update_modify_lineedit(self):
        '''
        '''
        current_label = self.load_data_label_combobox.currentText()
        if len(current_label) == 0:
            return None
        if current_label not in self.data_dict:
            current_data = []
        else:
            current_data = self.data_dict[current_label]
        self.modify_data_lineedit.setText(str(current_data))

    def hp_modify_data(self):
        '''
        '''
        data_label = self.load_data_label_combobox.currentText()
        new_data_value = self.modify_data_lineedit.text()
        new_data_value = new_data_value.strip(']').strip('[')
        new_data_value = new_data_value.strip('[')
        new_data = []
        for datum in new_data_value.split(', '):
            if not self.gb_is_float(datum.strip()):
                self.gb_quick_message('Please only enter floats')
                return None
            new_data.append(float(datum.strip()))
        self.data_dict[data_label] = new_data

    def hp_delete_data(self):
        '''
        '''
        data_label = self.load_data_label_combobox.currentText()
        msg = 'Delete all data for {0}?'.format(data_label)
        response = self.gb_quick_message(msg=msg, add_cancel=True, add_yes=True)
        if response == QtWidgets.QMessageBox.Yes:
            self.data_dict.pop(data_label)
            idx = self.load_data_label_combobox.findText(data_label)
            self.load_data_label_combobox.removeItem(idx)
        self.hp_load_labels()
        self.input_data_display_label.setText(str(self.data_dict))

    def hp_add_data(self):
        '''
        '''
        data_label = self.input_data_label_lineedit.text()
        data_value = self.input_data_lineedit.text()
        if not self.gb_is_float(data_value):
            self.gb_quick_message('Please only enter floats')
            return None
        else:
            data_value = float(data_value)
        if data_label in self.data_dict:
            self.data_dict[data_label].append(data_value)
        else:
            self.data_dict[data_label] = [data_value]
        self.input_data_display_label.setText(str(self.data_dict))
        self.hp_load_labels()



    def hp_plot(self):
        '''
        '''
        if self.gb_is_float(self.font_size_lineedit.text()):
            font_size = int(self.font_size_lineedit.text())
        x_label = self.x_label_lineedit.text()
        title = self.title_lineedit.text()
        all_data = []
        for label, data in self.data_dict.items():
            std = np.std(data)
            mean = np.mean(data)
            label = '{0} ({1:.2f}|{2:.3f}) $\Omega$'.format(label, mean, std)
            pl.hist(data, label=label)
            for datum in data:
                all_data.append(datum)
        std = np.std(all_data)
        mean = np.mean(all_data)
        label = '{0} ({1:.2f}|{2:.3f}) $\Omega$'.format('All', mean, std)
        pl.hist(all_data, alpha=0.2, label=label)

        pl.xlabel(x_label, fontsize=font_size)
        pl.ylabel('Count', fontsize=font_size)
        pl.title(title, fontsize=font_size)
        pl.legend()
        pl.show()

