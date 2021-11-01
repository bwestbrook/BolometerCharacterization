import time
import shutil
import scipy
import os
import simplejson
import pylab as pl
import numpy as np
import pickle as pkl
from copy import copy
from datetime import datetime
from pprint import pprint
from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import *
from bd_lib.fast_fourier_transform import FastFourierTransform
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class NoiseAnalyzer(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, daq_settings, squid_calibration_dict, status_bar, data_folder, screen_resolution, monitor_dpi):
        '''
        '''
        super(NoiseAnalyzer, self).__init__()
        self.data_folder = data_folder
        self.status_bar = status_bar
        self.daq_settings = daq_settings
        self.squid_calibration_dict = squid_calibration_dict
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.today = datetime.now()
        self.today_str = datetime.strftime(self.today, '%Y_%m_%d')
        self.squid_gains = {
                '5': '1e-2',
                '50': '1e-1',
                '500': '1',
                }
        self.na_update_samples()
        self.na_daq_panel()
        self.fft = FastFourierTransform()
        self.qthreadpool = QThreadPool()
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.na_update_progress)

    def na_update_squids(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'squids_settings.json'), 'r') as fh:
            self.squid_calibration_dict = simplejson.load(fh)

    def na_update_samples(self):
        '''
        '''
        with open(os.path.join('bd_settings', 'samples_settings.json'), 'r') as fh:
            self.samples_settings = simplejson.load(fh)

    def na_daq_panel(self):
        '''
        '''
        self.device_combobox = self.gb_make_labeled_combobox(label_text='DAQ Device:')
        for device in self.daq_settings:
            self.device_combobox.addItem(device)
        self.device_combobox.setCurrentIndex(1)
        self.device_combobox.activated.connect(self.na_update_sample_name)
        self.layout().addWidget(self.device_combobox, 0, 0, 1, 1)
        self.daq_combobox = self.gb_make_labeled_combobox(label_text='DAQ Ch 1 Data:')
        for daq in range(0, 4):
            self.daq_combobox.addItem(str(daq))
        self.daq_combobox.activated.connect(self.na_update_sample_name)
        self.layout().addWidget(self.daq_combobox, 0, 1, 1, 1)
        self.int_time_lineedit = self.gb_make_labeled_lineedit(label_text='Int Time (ms):', lineedit_text='100')
        self.int_time_lineedit.textChanged.connect(self.na_update_sample_name)
        self.layout().addWidget(self.int_time_lineedit, 0, 2, 1, 1)
        self.sample_rate_lineedit = self.gb_make_labeled_lineedit(label_text='Sample Rate (Hz)', lineedit_text='5000')
        self.sample_rate_lineedit.textChanged.connect(self.na_update_sample_name)
        self.layout().addWidget(self.sample_rate_lineedit, 0, 3, 1, 1)
        # Chan 1
        self.channel_settings_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.channel_settings_label, 1, 2, 1, 2)
        # Chan 2
        # Sample Name
        self.sample_name_combobox = self.gb_make_labeled_combobox('Sample Name:')
        self.layout().addWidget(self.sample_name_combobox, 3, 0, 1, 1)
        for sample in sorted(self.samples_settings):
            self.sample_name_combobox.addItem(str(sample))
        self.sample_name_combobox.activated.connect(self.na_update_sample_name)
        self.sample_name_lineedit = self.gb_make_labeled_lineedit('Sample Name:')
        self.layout().addWidget(self.sample_name_lineedit, 4, 0, 1, 2)

        self.gain_select_combobox = self.gb_make_labeled_combobox('SQUID Gain:')
        for gains in self.squid_gains:
            self.gain_select_combobox.addItem(gains)
        self.gain_select_combobox.activated.connect(self.na_update_sample_name)
        self.layout().addWidget(self.gain_select_combobox, 3, 2, 1, 1)
        self.squid_calibration_label = self.gb_make_labeled_label('SQ Calibration (uA/V)')
        self.layout().addWidget(self.squid_calibration_label, 3, 3, 1, 1)
        self.apply_calibration_checkbox = QtWidgets.QCheckBox('Apply Calibration?')
        self.apply_calibration_checkbox.setChecked(True)
        self.layout().addWidget(self.apply_calibration_checkbox, 4, 2, 1, 1)
        # Plot and Data Panel
        # Plots
        self.ts_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.ts_label, 6, 0, 1, 2)
        self.fft_label = QtWidgets.QLabel('', self)
        self.layout().addWidget(self.fft_label, 6, 2, 1, 2)
        # Plot Settings
        self.plot_clip_low_lineedit = self.gb_make_labeled_lineedit(label_text='Plot Clip Low (Hz)', lineedit_text='0.01')
        self.plot_clip_low_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e6, 2, self.plot_clip_low_lineedit))
        self.layout().addWidget(self.plot_clip_low_lineedit, 7, 0, 1, 1)
        self.plot_clip_high_lineedit = self.gb_make_labeled_lineedit(label_text='Plot Clip High (Hz)', lineedit_text='1e6')
        self.plot_clip_high_lineedit.setValidator(QtGui.QDoubleValidator(0, 1e6, 2, self.plot_clip_high_lineedit))
        self.layout().addWidget(self.plot_clip_high_lineedit, 7, 1, 1, 1)
        # Bin edges
        self.noise_bin_low_edge_lineedit = self.gb_make_labeled_lineedit(label_text='Noise Bin Low Edge (Hz)')
        self.noise_bin_low_edge_lineedit.setText('3.0')
        self.noise_bin_low_edge_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.noise_bin_low_edge_lineedit))
        self.layout().addWidget(self.noise_bin_low_edge_lineedit, 7, 2, 1, 1)
        self.noise_bin_high_edge_lineedit = self.gb_make_labeled_lineedit(label_text='Noise Bin High Edge (Hz)')
        self.noise_bin_high_edge_lineedit.setText('10.0')
        self.noise_bin_high_edge_lineedit.setValidator(QtGui.QDoubleValidator(0, 1200, 2, self.noise_bin_high_edge_lineedit))
        self.layout().addWidget(self.noise_bin_high_edge_lineedit, 7, 3, 1, 1)
        self.in_band_noise_label = QtWidgets.QLabel('In Band Noise (pA/sqrt(Hz)): np.nan', self)
        self.layout().addWidget(self.in_band_noise_label, 8, 0, 1, 1)
        # Buttons
        start_pushbutton = QtWidgets.QPushButton('Start', self)
        start_pushbutton.clicked.connect(self.na_collector)
        self.layout().addWidget(start_pushbutton, 10, 0, 1, 4)
        plot_pushbutton = QtWidgets.QPushButton('Plot', self)
        plot_pushbutton.clicked.connect(self.na_plot)
        self.layout().addWidget(plot_pushbutton, 11, 0, 1, 4)
        save_pushbutton = QtWidgets.QPushButton('Save', self)
        save_pushbutton.clicked.connect(self.na_save)
        self.layout().addWidget(save_pushbutton, 12, 0, 1, 4)
        # Connect to functions after placing widgets
        self.daq_combobox.activated.connect(self.na_update_sample_name)
        self.device_combobox.activated.connect(self.na_update_sample_name)
        self.na_update_sample_name()

    def na_update_sample_name(self):
        '''
        '''
        self.na_update_samples()
        self.na_update_squids()
        self.device = self.device_combobox.currentText()
        self.channel = self.daq_combobox.currentIndex()
        self.int_time = int(self.int_time_lineedit.text())
        self.sample_rate = int(self.sample_rate_lineedit.text())
        info_str = 'Sample Rate (Hz): {0} :::: '.format(self.sample_rate)
        info_str += 'Int Time (ms): {0}'.format(self.int_time)
        self.channel_settings_label.setText(info_str)
        sample_key = self.sample_name_combobox.currentText()
        sample_name = self.samples_settings[sample_key]
        self.sample_name_lineedit.setText(sample_name)
        gain = float(self.squid_gains[self.gain_select_combobox.currentText()])
        squid = sample_key.split('-')[0]
        for squid in self.squid_calibration_dict:
            if sample_key in squid:
                squid_calibration = float(self.squid_calibration_dict[squid])
                break
        squid_calibration *= gain
        self.squid_calibration_label.setText('{0:.6f}'.format(squid_calibration))

    ###########
    # Running
    ###########

    def na_collector(self):
        '''
        '''
        self.na_update_sample_name()
        device = self.device_combobox.currentText()
        self.na_scan_file_name()
        signal_channels = [self.channel]
        int_time = int(self.int_time_lineedit.text())
        sample_rate = int(self.sample_rate_lineedit.text())
        self.data, self.stds = [], []
        daq = BoloDAQ(signal_channels=signal_channels,
                      int_time=int_time,
                      sample_rate=sample_rate,
                      device=device)
        self.data_dict = daq.run()
        #self.qthreadpool.start(daq.run)
        self.seconds_count = 0
        n_seconds = float(self.int_time) / 1000.0 + 0.5
        #self.na_update_progress(n_seconds)
        #with open('temp.pkl', 'rb') as fh:
            #data_dict = pkl.load(fh)
        #self.data_dict = pkl.loads(data_dict)
        self.ts = self.data_dict[self.channel]['ts']
        print('ha')
        self.na_plot()
        self.status_bar.progress_bar.setValue(100)

    def na_update_progress(self, n_seconds, update_interval=0.1):
        '''
        '''
        pct_range = 100. * np.arange(0, float(n_seconds), update_interval) / float(n_seconds)
        for pct in pct_range:
            self.status_bar.progress_bar.setValue(pct)
            time.sleep(update_interval)
            QtWidgets.QApplication.processEvents()

    def na_scan_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            folder_name = 'Noise_Scan_{0}'.format(str(i).zfill(3))
            self.folder_path = os.path.join(self.data_folder, folder_name)
            if not os.path.exists(self.folder_path):
                os.makedirs(self.folder_path)
                break

    def na_index_file_name(self):
        '''
        '''
        for i in range(1, 1000):
            file_name = '{0}_{1}.txt'.format(self.sample_name_lineedit.text(), str(i).zfill(3))
            save_path = os.path.join(self.folder_path, file_name)
            if not os.path.exists(save_path):
                break
        return save_path

    def na_save(self):
        '''
        '''
        save_path = self.na_index_file_name()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Data Save Location', save_path, filter=',*.txt,*.dat')[0]
        if len(save_path) > 0:
            self.na_plot()
            with open(save_path, 'w') as save_handle:
                for i, data in enumerate(self.ts):
                    line = '{0:.5f}\n'.format(data)
                    save_handle.write(line)
            if 'txt' in save_path:
                psd_save_path = save_path.replace('.txt', '_psd.txt')
            else:
                psd_save_path = save_path.replace('.dat', '_psd.dat')
            with open(psd_save_path, 'w') as save_handle:
                for i, freq in enumerate(self.fft_freq_vector):
                    psd = self.fft_psd_vector[i]
                    line = '{0:.5f}, {1:.16f}\n'.format(freq, psd)
                    save_handle.write(line)
            if 'txt' in save_path:
                fft_png_path = save_path.replace('.txt', '_fft.png')
                ts_png_path = save_path.replace('.txt', '_ts.png')
            else:
                fft_png_path = save_path.replace('.dat', '_fft.png')
                ts_png_path = save_path.replace('.dat', '_ts.png')
            temp_png_path = os.path.join('temp_files', 'temp_fft.png')
            shutil.copy(temp_png_path, fft_png_path)
            temp_png_path = os.path.join('temp_files', 'temp_ts.png')
            shutil.copy(temp_png_path, ts_png_path)
            save_path.replace('.dat', '_fft.png')
        else:
            self.gb_quick_message('Warning Data Not Written to File!', msg_type='Warning')

    def na_plot(self, save_path=None):
        '''
        '''
        #gain = float(self.squid_calibration_label.text())
        squid_calibration = float(self.squid_calibration_label.text())
        #squid_calibration *= gain
        squid_calibration *= 1e-6 # uA to A

        int_time = float(self.int_time_lineedit.text())
        ts_fig, ts_ax = self.na_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.5,
                                                 left=0.14, right=0.98, top=0.9, bottom=0.13, aspect=None)
        ts_ax.set_xlabel('Sample', fontsize=16)
        mean_subtracted_ts = self.ts - np.mean(self.ts)
        if self.apply_calibration_checkbox.isChecked():
            mean_subtracted_ts *= squid_calibration
            ts_ax.set_ylabel('Current (A)', fontsize=16)
        else:
            ts_ax.set_ylabel('Voltage (V)', fontsize=16)
        ts_ax.plot(mean_subtracted_ts, label='Mean Subtracted Time Stream')
        temp_png_path = os.path.join('temp_files', 'temp_ts.png')
        ts_fig.savefig(temp_png_path)
        image_to_display = QtGui.QPixmap(temp_png_path)
        self.ts_label.setPixmap(image_to_display)
        fft_fig, fft_ax = self.na_create_blank_fig(frac_screen_width=0.5, frac_screen_height=0.5,
                                                   left=0.15, right=0.98, top=0.9, bottom=0.13, aspect=None)
        fft_ax.set_xlabel('Frequency ($Hz$)', fontsize=16)
        fft_ax.set_ylabel('PSD ($pA / \sqrt{Hz}$)', fontsize=16)
        bin_low_edge = float(self.noise_bin_low_edge_lineedit.text())
        bin_high_edge = float(self.noise_bin_high_edge_lineedit.text())
        plot_clip_low = float(self.plot_clip_low_lineedit.text())
        plot_clip_high = float(self.plot_clip_high_lineedit.text())
        fft_ax.axvline(bin_low_edge, color='k')
        fft_ax.axvline(bin_high_edge, color='k')
        fft_ax.axvspan(bin_low_edge, bin_high_edge, alpha=0.33, color='c')

        nperseg = int(float(len(self.ts)) / 10.)
        ts_in_amps = self.ts * squid_calibration
        fft_freq_vector, fft_psd_vector = scipy.signal.welch(ts_in_amps, fs=float(self.sample_rate), nperseg=nperseg)
        fft_psd_vector *= 1e24 # A to pA
        fft_psd_vector = np.sqrt(fft_psd_vector) # CONVERSION to ASD

        ##############################################
        ##############################################
        ##############################################
        ##############################################
        print('sample rate')
        print(float(self.sample_rate)) # in Hz
        max_frequnecy = 0.5 * float(self.sample_rate)
        print('max freq')
        print(max_frequnecy)
        print('int time')
        int_time *= 1e-3
        print(int_time)
        #import ipdb;ipdb.set_trace()
        interval_length = 0.5 * int_time
        min_frequnecy = 1 / interval_length
        print('min freq')
        print(min_frequnecy)
        print('psd freq, min, max')
        print(min(fft_freq_vector[1:]), max(fft_freq_vector))
        print('len psd, nperseg')
        print(len(fft_freq_vector), nperseg)
        ##############################################
        ##############################################
        ##############################################
        ##############################################

        selector = np.where(fft_freq_vector > 0.0)
        mean_selector = np.where(np.logical_and(fft_freq_vector > bin_low_edge, fft_freq_vector < bin_high_edge))
        in_band_noise = np.mean(fft_psd_vector[mean_selector])
        label = 'In Band Noise (pA/sqrt(Hz)): {0:.3f}'.format(in_band_noise)
        noise_vector = np.asarray([in_band_noise] * len(fft_psd_vector))
        #fft_ax.plot(fft_freq_vector[mean_selector], noise_vector[mean_selector], color='r', label=label)
        self.in_band_noise_label.setText(label)
        print(fft_freq_vector, fft_psd_vector)
        print(fft_freq_vector[selector], fft_psd_vector[selector])
        fft_ax.loglog(fft_freq_vector[selector], fft_psd_vector[selector])
        fft_ax.set_xlim((plot_clip_low, plot_clip_high))
        pl.legend()
        temp_png_path = os.path.join('temp_files', 'temp_fft.png')
        fft_fig.savefig(temp_png_path)
        image_to_display = QtGui.QPixmap(temp_png_path)
        self.fft_label.setPixmap(image_to_display)
        if save_path is not None and save_path:
            if 'txt' in save_path:
                fft_fig_path = save_path.replace('.txt', '_fft.png')
                ts_fig_path = save_path.replace('.txt', '_ts.png')
            else:
                fft_fig_path = save_path.replace('.dat', '_fft.png')
                ts_fig_path = save_path.replace('.dat', '_ts.png')
            print(fft_fig_path)
            print(ts_fig_path)
            print(fft_fig_path)
        pl.close('all')
        self.fft_label.resize(self.fft_label.maximumSize())
        self.ts_label.resize(self.ts_label.maximumSize())
        self.fft_freq_vector = fft_freq_vector
        self.fft_psd_vector = fft_psd_vector

    def na_create_blank_fig(self, frac_screen_width=0.5, frac_screen_height=0.8,
                             left=0.18, right=0.98, top=0.95, bottom=0.08, n_axes=1,
                             aspect=None):
        if frac_screen_width is None and frac_screen_height is None:
            fig = pl.figure()
        else:
            width = (frac_screen_width * self.screen_resolution.width()) / self.monitor_dpi
            height = (frac_screen_height * self.screen_resolution.height()) / self.monitor_dpi
            fig = pl.figure(figsize=(width, height))
        fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
        if n_axes == 2:
            ax1 = fig.add_subplot(211, label='ch 1')
            ax2 = fig.add_subplot(212, label='ch 2')
            return fig, ax1, ax2
        else:
            ax = fig.add_subplot(111)
            return fig, ax
