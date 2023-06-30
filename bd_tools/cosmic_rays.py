import time
import os
import simplejson
import numpy as np
from copy import copy
from datetime import datetime
from scipy import signal

from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass
from bd_lib.mpl_canvas import MplCanvas
from bd_lib.cosmic_ray_analyzer import CosmicRayAnalyzer

class CosmicRays(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, status_bar, screen_resolution, monitor_dpi, data_folder):
        '''
        '''
        super(CosmicRays, self).__init__()
        self.cra = CosmicRayAnalyzer()
        self.mplc = MplCanvas(self, screen_resolution, monitor_dpi)
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        self.analysis_options_dict = {
            '01 POLY': {
                'defaultUse': False,
                'filterParams': {
                    'Order': 1,
                }
            },
            '02 BW-LP': {
                'defaultUse': False,
                'filterParams': {
                    'N Poles': 1,
                    'Cuttoff Freq': 10.0
                },
            },
            '03 BW-HP': {
                'defaultUse': True,
                'filterParams': {
                    'N Poles': 1,
                    'Cuttoff Freq': 10.0
                },
            },
            }
        self.daq = BoloDAQ()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.data_folder = data_folder
        self.n_samples = 4
        self.gains = ['1.0', '10.0', '100.0']
        self.cr_daq_panel()

    def cr_update_daq_settings(self, daq_settings):
        '''
        '''
        self.daq_settings = daq_settings

    def cr_daq_panel(self):
        '''
        '''
        # Device Select 
        self.device_combobox = self.gb_make_labeled_combobox('DAQ Device: ')
        for device in self.daq_settings:
            self.device_combobox.addItem(device)
        self.device_combobox.setCurrentIndex(1)
        self.layout().addWidget(self.device_combobox, 0, 0, 1, 1)
        # Sample Rate
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz): ')
        self.sample_rate_lineedit.setText('5000')
        self.sample_rate_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e7, 1, self.sample_rate_lineedit))
        self.layout().addWidget(self.sample_rate_lineedit, 0, 1, 1, 1)
        # Int Time 
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Integration Time (ms): ')
        self.int_time_lineedit.setText('1000')
        self.int_time_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e6, 1, self.int_time_lineedit))
        self.layout().addWidget(self.int_time_lineedit, 0, 2, 1, 1)
        # SamplDAQ Ch Select 
        for sample in range(1, self.n_samples + 1):
            daq_combobox = self.gb_make_labeled_combobox(label_text='DAQ {0}'.format(sample))
            for daq in range(0, 4):
                daq_combobox.addItem(str(daq))
            setattr(self, 'daq_{0}_combobox'.format(sample), daq_combobox)
            daq_combobox.setCurrentIndex(sample - 1)
            self.layout().addWidget(daq_combobox, 1, sample - 1, 1, 1)
            # SQUID  Selec
            squid_combobox = self.gb_make_labeled_combobox(label_text='SQUID:')
            for squid in range(1, 7):
                squid_combobox.addItem(str(squid))
            squid_combobox.setCurrentIndex(sample - 1)
            setattr(self, 'squid_{0}_combobox'.format(sample), squid_combobox)
            self.layout().addWidget(squid_combobox, 2, sample - 1, 1, 1)
            # Gains 
            gain_combobox = self.gb_make_labeled_combobox(label_text='Gain:')
            for gain in self.gains:
                gain_combobox.addItem(str(gain))
            self.layout().addWidget(gain_combobox, 3, sample - 1, 1, 1)
            setattr(self, 'gain_{0}_combobox'.format(sample), gain_combobox)
            # Bias 
            bias_lineedit = self.gb_make_labeled_lineedit(label_text='Bias Voltage (uV):')
            self.layout().addWidget(bias_lineedit, 4, sample - 1, 1, 1)
            setattr(self, 'bias_{0}_lineedit'.format(sample), bias_lineedit)
            # Sample Name 
            sample_name_lineedit = self.gb_make_labeled_lineedit(label_text='Sample {0} Name:'.format(sample))
            sample_name_lineedit.setText(str(sample))
            self.layout().addWidget(sample_name_lineedit, 5, sample - 1, 1, 1)
            setattr(self, 'sample_name_{0}_lineedit'.format(sample), sample_name_lineedit)
            #Mean
            mean_label = self.gb_make_labeled_label(label_text='Mean {0}:'.format(sample))
            self.layout().addWidget(mean_label, 6, sample - 1, 1, 1)
            setattr(self, 'mean_{0}_label'.format(sample), mean_label)
            #STD
            std_label = self.gb_make_labeled_label(label_text='STD {0}:'.format(sample))
            self.layout().addWidget(std_label, 7, sample - 1, 1, 1)
            setattr(self, 'std_{0}_label'.format(sample), std_label)
        self.data_set_name_lineedit = self.gb_make_labeled_lineedit(label_text='Data Set Name:')
        self.layout().addWidget(self.data_set_name_lineedit, 8, 0, 1, 3)
        # Analysis
        # Filtering Options
        for i, option in enumerate(self.analysis_options_dict):
            checkbox_unique_name = 'filter_{0}_checkbox'.format(option)
            checkbox = QtWidgets.QCheckBox(option.split(' ')[1])
            checkbox.setChecked(self.analysis_options_dict[option]['defaultUse'])
            checkbox.clicked.connect(self.cr_update_options)
            setattr(self, checkbox_unique_name, checkbox)
            self.layout().addWidget(checkbox, 9, i, 1, 1)
            for j, filter_param in enumerate(self.analysis_options_dict[option]['filterParams']):
                lineedit = self.gb_make_labeled_lineedit(
                        label_text=filter_param,
                        lineedit_text=str(self.analysis_options_dict[option]['filterParams'][filter_param])
                        )
                lineedit_unique_name = 'filter_{0}_{1}_lineedit'.format(option, filter_param)
                setattr(self, lineedit_unique_name, lineedit)
                self.layout().addWidget(lineedit, 10 + j, i, 1, 1)
        # Buttons
        self.plot_filter_only_checkbox = QtWidgets.QCheckBox('Plot Raw Data')
        self.plot_filter_only_checkbox.setChecked(True)
        self.layout().addWidget(self.plot_filter_only_checkbox, 9, 3, 1, 1)
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        start_pushbutton.clicked.connect(self.cr_start_stop)
        self.layout().addWidget(start_pushbutton, 12, 0, 1, 3)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        save_pushbutton.clicked.connect(self.cr_save)
        self.layout().addWidget(save_pushbutton, 13, 0, 1, 3)
        # Plot
        self.running_plot_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.running_plot_label, 0, 5, 13, 1)

    ###########
    # Running
    ###########

    def cr_start_stop(self):
        '''
        '''
        if 'Start' in self.sender().text():
            self.cr_scan_file_name()
            self.gb_save_meta_data(os.path.join(self.folder_path,  'scan.png'), 'png')
            self.sender().setText('Stop')
            self.started = True
            self.cr_collecter()
        else:
            self.sender().setText('Start')
            self.started = False

    def cr_collecter(self):
        '''
        '''
        device = self.device_combobox.currentText()
        int_time = float(self.int_time_lineedit.text())
        sample_rate = float(self.sample_rate_lineedit.text())
        squids, gains, biases, signal_channels, scan_time = self.cr_get_analyzer_input()
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=int_time,
                      sample_rate=sample_rate,
                      device=device)
        while self.started:
            data_dict = daq.run()
            for i, ch in enumerate(data_dict.keys()):
                setattr(self, 'data_{0}'.format(i + 1), [])
                setattr(self, 'stds_{0}'.format(i + 1), [])

                squid = squids[i]
                data = data_dict[ch]
                mean = data['mean']
                std = data['std']
                getattr(self, 'mean_{0}_label'.format(i + 1)).setText('Mean {0}: {1:.5f}'.format(squid, mean))
                getattr(self, 'std_{0}_label'.format(i + 1)).setText('STD {0}: {1:.5f}'.format(squid, mean))
                getattr(self, 'data_{0}'.format(i + 1)).extend(data['ts'])
                getattr(self, 'stds_{0}'.format(i + 1)).append(data['std'])
            #self.cra.cra_analyze(data_dict, squids, gains, biases, scan_time)
            save_path = self.cr_index_file_name()
            self.cr_plot(running=True, save_path=save_path)
            with open(save_path, 'w') as save_handle:
                data_1 = self.data_1
                for i, datum in enumerate(data_1):
                    line = ''
                    for j, ch in enumerate(data_dict.keys()):
                        if j < len(data_dict.keys()) - 1:
                            line += '{0:.6f}, '.format(getattr(self, 'data_{0}'.format(j + 1))[i])
                        else:
                            line += '{0:.6f}\n'.format(getattr(self, 'data_{0}'.format(j + 1))[i])
                    save_handle.write(line)
            QtWidgets.QApplication.processEvents()
            self.repaint()

    def cr_get_analyzer_input(self):
        '''
        '''
        scan_time = float(self.int_time_lineedit.text()) * 1e-3
        squids, gains, biases, signal_channels = [], [], [], []
        for sample in range(1, self.n_samples + 1):
            squids.append(getattr(self, 'squid_{0}_combobox'.format(sample)).currentText())
            gains.append(getattr(self, 'gain_{0}_combobox'.format(sample)).currentText())
            biases.append(getattr(self, 'bias_{0}_lineedit'.format(sample)).text())
            signal_channels.append(getattr(self, 'daq_{0}_combobox'.format(sample)).currentText())
        return squids, gains, biases, signal_channels, scan_time

    def cr_update_options(self):
        '''
        '''
        if self.sender().text() in self.analysis_options_dict:
            self.analysis_options_dict[self.sender().text()]['defaultUse'] = self.sender().isChecked()

    def cr_scan_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            folder_name = 'CR_Scan_{0}'.format(str(i).zfill(3))
            self.folder_path = os.path.join(self.data_folder, folder_name)
            if not os.path.exists(self.folder_path):
                os.makedirs(self.folder_path)
                break

    def cr_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}.txt'.format(self.data_set_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.folder_path, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def cr_save(self):
        '''
        '''
        save_path = self.cr_index_file_name()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter=',*.txt,*.dat')[0]
        if len(save_path) > 0:
            with open(save_path, 'w') as save_handle:
                for i, data_1 in enumerate(self.data_1):
                    line = '{0:.5f}, {1:.5f}\n'.format(self.data_1[i], self.data_2[i])
                    save_handle.write(line)
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')
        self.cr_plot()

    def cr_analyze(self, data):
        '''
        '''
        filters = []
        filtered_data = data
        for i, option in enumerate(self.analysis_options_dict):
            checkbox_unique_name = 'filter_{0}_checkbox'.format(option)
            checkbox = getattr(self, checkbox_unique_name)
            for j, filter_param in enumerate(self.analysis_options_dict[option]['filterParams']):
                lineedit = self.gb_make_labeled_lineedit(
                        label_text=filter_param,
                        lineedit_text=str(self.analysis_options_dict[option]['filterParams'][filter_param])
                        )
                lineedit_unique_name = 'filter_{0}_{1}_lineedit'.format(option, filter_param)
                lineedit = getattr(self, lineedit_unique_name)
                if filter_param == 'Order':
                    order = int(lineedit.text())
                elif filter_param == 'N Poles':
                    n_filter_poles = int(lineedit.text())
                elif filter_param == 'Cuttoff Freq':
                    cutoff_frequency = float(lineedit.text())
            if option == '01 POLY' and checkbox.isChecked():
                x_fits = np.asarray(range(len(data)))
                p_fits = np.polyfit(x_fits, data, order)
                y_fits = np.polyval(p_fits, x_fits)
                filtered_data = np.asarray(data) - y_fits
                filters.append(option)
            elif option == '02 BW-LP' and checkbox.isChecked():
                sos = signal.butter(n_filter_poles, cutoff_frequency, 'hp', output = 'sos', fs=5000)
                filtered = signal.sosfilt(sos, data)
                filters.append(option)
            elif option == '03 BW-HP' and checkbox.isChecked():
                sos = signal.butter(n_filter_poles, cutoff_frequency, 'lp', output = 'sos', fs=5000)
                filtered = signal.sosfilt(sos, data)
                filters.append(option)
        return filtered_data, filters


    def cr_plot(self, running=False, save_path=None):
        '''
        '''

        axes_names = ['Ch {0}'.format(i + 1) for i in range(self.n_samples)]
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
        axes[2].set_xlabel('Sample')
        title = self.data_set_name_lineedit.text()
        fig.suptitle(title)
        for i in range(1, self.n_samples + 1):
            data = getattr(self, 'data_{0}'.format(i))
            filtered_data, filters = self.cr_analyze(data)
            ax_title = getattr(self, 'sample_name_{0}_lineedit'.format(i)).text()
            #import ipdb;ipdb.set_trace()
            filter_label = ''
            for filter_type in filters:
                filter_label += filter_type.split(' ')[1]
                filter_label += '+\n'
            filter_label = filter_label[:-2]
            if self.plot_filter_only_checkbox.isChecked():
                axes[i - 1].plot(data, label='Raw Data {0}'.format(ax_title))
            if len(filters) > 0:
                axes[i - 1].plot(filtered_data, label=filter_label)
            axes[i - 1].set_title(ax_title)
            handles, labels = axes[i - 1].get_legend_handles_labels()
            axes[i - 1].legend(handles, labels, numpoints=1, frameon=True, fontsize=10, loc='best')
        if running:
            temp_png_path = os.path.join('temp_files', 'temp_cr.png')
            fig.savefig(temp_png_path)
            image_to_display = QtGui.QPixmap(temp_png_path)
            self.running_plot_label.setPixmap(image_to_display)
            if save_path is not None:
                fig.savefig(save_path.replace('txt', 'png'))
            for ax in fig.get_axes():
                ax.cla()

        else:
            title, okPressed = self.gb_quick_info_gather(title='Plot Title', dialog='What is the title of this plot?')
            ax1.set_title(title)
