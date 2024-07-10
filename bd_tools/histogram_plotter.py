import os
import json
import pylab as pl
import numpy as np
import pickle as pkl
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
        self.data_dict = {}
        self.units = [
            'm$\Omega$',
            '$\Omega$',
            'mK',
            ''
                ]
        self.display_radius = 5.0
        self.dl_lf_intra_pixel_offsets = {
                '30B': (0.5 *np.sqrt(2), -0.5 *np.sqrt(2)),
                '30D': (0.5 *np.sqrt(2), 0.5 *np.sqrt(2)),
                '30T': (0, 1),
                '40B': (-0.5 *np.sqrt(2), 0.5 *np.sqrt(2)),
                '40D': (-0.5 *np.sqrt(2), -0.5 *np.sqrt(2)),
                '40T': (0, -1)
                }
        self.hp_data_input_panel()


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
        self.plot_all_checkbox = QtWidgets.QCheckBox('Plot All?')
        self.layout().addWidget(self.plot_all_checkbox, 1, 3, 1, 1)
        self.param_to_hist_lineedit = self.gb_make_labeled_lineedit(label_text='Param2Hist')
        self.layout().addWidget(self.param_to_hist_lineedit, 1, 4, 1, 1)

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
        self.data_multiplier_lineedit = self.gb_make_labeled_lineedit(label_text='Data Multiplier')
        self.data_multiplier_lineedit.setText('1.0')
        self.layout().addWidget(self.data_multiplier_lineedit, 2, 4, 1, 1)
        self.xlim_pad_lineedit = self.gb_make_labeled_lineedit(label_text='Xlim Pad')
        self.xlim_pad_lineedit.setText('20.0')
        self.layout().addWidget(self.xlim_pad_lineedit, 3, 4, 1, 1)


        # Make nice plots
        self.plot_data_push_button = QtWidgets.QPushButton('Plot Data')
        self.plot_data_push_button.clicked.connect(self.hp_plot)
        self.layout().addWidget(self.plot_data_push_button, 4, 0, 1, 1)
        self.x_label_lineedit = self.gb_make_labeled_lineedit(label_text='X LABEL')
        self.layout().addWidget(self.x_label_lineedit, 4, 1, 1, 1)
        self.title_lineedit = self.gb_make_labeled_lineedit(label_text='Title')
        self.layout().addWidget(self.title_lineedit, 4, 2, 1, 1)
        self.font_size_lineedit = self.gb_make_labeled_lineedit(label_text='Font Size', lineedit_text='18')
        self.layout().addWidget(self.font_size_lineedit, 4, 3, 1, 1)
        self.unit_combobox = self.gb_make_labeled_combobox(label_text='Units', add_lineedit=True)
        for unit in self.units:
            self.unit_combobox.addItem(unit)
        self.layout().addWidget(self.unit_combobox, 4, 4, 1, 1)
        # pritn the data
        self.input_data_display_label = self.gb_make_labeled_label(label_text='Loaded Data')
        self.layout().addWidget(self.input_data_display_label, 5, 0, 1, 3)

    def hp_load_data(self):
        '''
        '''
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Data File')[0]
        if not os.path.exists(file_path):
            return None
        if file_path.endswith('.npy'):
            self.hp_load_pton_npy(file_path)
        else:
            with open(file_path, 'r') as fh:
                data_dict = json.load(fh)
            float_data = []
            self.data_dict = {}
            for label, data in data_dict.items():
                for datum in data:
                    multiplier = float(self.data_multiplier_lineedit.text())
                    datum *= multiplier
                    if not self.gb_is_float(datum):
                        self.gb_quick_message('Please only load jsons with floats for data in the lists')
                        return None
                    if label in self.data_dict:
                        self.data_dict[label].append(datum)
                    else:
                        self.data_dict[label] = [datum]
            self.hp_load_labels()
            self.input_data_display_label.setText(str(self.data_dict)[0:100])
            #self.hp_plot()

    def hp_load_pton_npy(self, file_path):
        '''
        '''
        data_dict = np.load(file_path, allow_pickle=True).item() #)['data']
        name = 'Pton Lp2r1 5E Tc'
        self.data_dict = {}
        if len(self.param_to_hist_lineedit.text()) > 0:
            param_to_hist = self.param_to_hist_lineedit.text()
        else:
            param_to_hist = 'delta_psat'
        all_xs = []
        all_ys = []
        all_delta_psats = []
        for bias_line in data_dict:
            for smurf_board in data_dict[bias_line]:
                for param in data_dict[bias_line][smurf_board]:
                    value = data_dict[bias_line][smurf_board][param]
                    if param == param_to_hist and 'tes_id' in data_dict[bias_line][smurf_board]:
                        tes_id = data_dict[bias_line][smurf_board]['tes_id']
                        pixel = data_dict[bias_line][smurf_board]['pixel']
                        pixel_name = '{0}-{1}'.format(pixel, tes_id)
                        if pixel in [16, 17, 19]:
                            print(pixel_name, value)
                        if param_to_hist not in self.data_dict:
                            self.data_dict[param_to_hist] = [value]
                        else:
                            self.data_dict[param_to_hist].append(value)
                        x_center = data_dict[bias_line][smurf_board]['x_mm']
                        y_center = data_dict[bias_line][smurf_board]['y_mm']
                        x = x_center + self.dl_lf_intra_pixel_offsets[tes_id][0] * self.display_radius
                        y = y_center + self.dl_lf_intra_pixel_offsets[tes_id][1] * self.display_radius
                        #import ipdb;ipdb.set_trace()
                        all_xs.append(x)
                        all_ys.append(y)
                        all_delta_psats.append(value)
        save_path = os.path.join('bd_histogram_data', name.replace(' ', '_') + '.json')
        with open(save_path, 'w') as fh:
            json.dump(self.data_dict, fh)
        fig = pl.figure()
        ax = fig.add_subplot(111)
        cm = ax.scatter(np.asarray(all_xs), np.asarray(all_ys), s=100, c=np.asarray(all_delta_psats), cmap='jet')
        ax.set_title('$\Delta P_{sat}$ Heat Map for 10J')
        ax.set_xlabel('X Pos (mm)')
        ax.set_ylabel('Y Pos (mm)')
        pl.legend()
        pl.colorbar(cm, label='Resitance (k$\Omega$)')
        pl.show()


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
        fig = pl.figure(figsize=(10,5))
        ax_plot = fig.add_subplot(121)
        ax_legend = fig.add_subplot(122)
        ax_legend.set_axis_off()
        if self.gb_is_float(self.font_size_lineedit.text()):
            font_size = int(self.font_size_lineedit.text())
        x_label = self.x_label_lineedit.text()
        title = self.title_lineedit.text()
        unit = self.unit_combobox.currentText()
        all_data = []
        for label, data in self.data_dict.items():
            std = np.std(data)
            mean = np.mean(data)
            label = '{0} {1:.2f} +/- {2:.2f} {3} [N={4}]'.format(label, mean, std, unit, len(data))
            ax_plot.hist(data, label=label)
            for datum in data:
                all_data.append(datum)
        std = np.std(all_data)
        mean = np.mean(all_data)
        ax_plot.tick_params(labelsize=font_size)
        ax_plot.tick_params(labelsize=font_size)
        if self.plot_all_checkbox.isChecked():
            label = 'All'
            label = '{0} {1:.2f} +/- {2:.2f} {3} [N={4}]'.format(label, mean, std, unit, len(all_data))
            ax_plot.hist(all_data, alpha=0.5, color='y', label=label)
            ax_plot.hist(all_data, alpha=0.5, color='k', label=None, histtype='step')
        ax_plot.set_xlabel(x_label, fontsize=font_size)
        ax_plot.set_ylabel('Count', fontsize=font_size)
        ax_plot.set_title(title, fontsize=font_size)
        pl.subplots_adjust(left=0.08, right=1.0, bottom=0.15, wspace=0.0)
        handles, labels = ax_plot.get_legend_handles_labels()
        ax_legend.legend(handles, labels, numpoints=1, mode="expand", frameon=True, fontsize=14, bbox_to_anchor=(0, 0.0, 1, 1))
        xlim_pad = float(self.xlim_pad_lineedit.text())
        ax_plot.set_xlim((np.min(all_data) - xlim_pad, np.max(all_data) + xlim_pad))
        pl.show()

    def hp_plot_so_wafer(self):
        '''
        '''
        all_xs = []
        all_ys = []
        all_resistances = []
        fig = pl.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        ax.set_aspect('equal')
        all_pixel_resistance_dict = {}
        all_pixel_resistance_small_dict = {}
        pixel_resistance_dict = {}
        info_dict = {}
        pixel_resistances = []
        intra_pixel_resistances = []
        for i in self.df.index:#[0:6]:
            x_center = self.map_df['x_mm'][i]
            y_center = self.map_df['y_mm'][i]
            tes_id = self.map_df['tes_id'][i]
            pixel = self.map_df['pixel'][i]
            resistance = self.df['R (kohms)'][i]
            info_dict[tes_id] = resistance
            x = x_center + self.dl_lf_intra_pixel_offsets[tes_id][0] * self.display_radius
            y = y_center + self.dl_lf_intra_pixel_offsets[tes_id][1] * self.display_radius
            if i % 6 == 0 and i > 0:
                prev_pixel = self.map_df['pixel'][i - 6]
                x_pos = x_center - 0.15 * self.display_radius
                y_pos = y_center - 0.15 * self.display_radius
                ax.text(x_pos, y_pos, 'P{0}'.format(pixel))
                info_dict.update({
                        'values': pixel_resistances,
                        'mean': np.mean(pixel_resistances),
                        'std': np.std(pixel_resistances)
                        })
                if len(pixel_resistances) == 6:
                    intra_pixel_resistance = np.asarray(pixel_resistances) - np.min(pixel_resistances)
                    intra_pixel_resistances.append(intra_pixel_resistance)
                all_pixel_resistance_dict[str(prev_pixel)] = info_dict
                all_pixel_resistance_small_dict[str(prev_pixel)] = info_dict['mean']
                self.wy_analyze_pixel(prev_pixel, pixel_resistances, info_dict)
                pixel_resistances = []
                info_dict = {}
            if resistance in ['open', 'Open']:
                resistance = 80
                label = None
                handles, labels = ax.get_legend_handles_labels()
                if "Open" not in labels:
                    label = "Open"
                ax.plot(x, y, 'o', ms=3, color='k', label=label)
            else:
                all_xs.append(x)
                all_ys.append(y)
                all_resistances.append(float(resistance))
                pixel_resistances.append(float(resistance))
            x_pos = x_center - 0.2 * self.display_radius
            y_pos = y_center - 0.2 * self.display_radius
            ax.text(x, y, '{0}'.format(tes_id), fontsize=6)
        intra_pixel_resistances = np.asarray(intra_pixel_resistances)
        pprint(all_pixel_resistance_small_dict)
        for i in range(6):
            intra_pixel_value = intra_pixel_resistances.T[i][np.abs(intra_pixel_resistances.T[i] - np.mean(intra_pixel_resistances.T[i])) < 1]
        cm = ax.scatter(np.asarray(all_xs), np.asarray(all_ys), s=100, c=np.asarray(all_resistances), cmap='jet')
        wafer_name = self.wafer_name_lineedit.text()
        ax.set_title('Resistance Heat Map for {0}'.format(wafer_name))
        ax.set_xlabel('X Pos (mm)')
        ax.set_ylabel('Y Pos (mm)')
        pl.legend()
        pl.colorbar(cm, label='Resitance (k$\Omega$)')
        pl.show()
