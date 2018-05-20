import os
import matplotlib
import sys
import pylab as pl
import numpy as np
from copy import copy
from pprint import pprint
from foreground_plotter import ForegroundPlotter
from numerical_processing import Fourier


class FTSCurve():

    def __init__(self):
        self.fourier = Fourier()

    def load_simulation_data(self, data_path):
        '''
        Inputs:
            data_path:  the path to the .fft data file (string)
        Outputs:
            frequency_vector: the extracted frequency vector
            transmission_vector: the extracted frequency vector
        Returns a frequency and transmission vector from the data file
        produced by Toki's LabView software
        '''
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            frequency_vector = np.zeros(len(lines))
            transmission_vector = np.zeros(len(lines))
            for i, line in enumerate(lines):
                frequency = line.split('\t')[0]
                transmission = line.split('\t')[1].strip('\n')
                transmission = 10.0 ** (float(transmission)/10.0)
                np.put(frequency_vector, i, float(frequency))
                np.put(transmission_vector, i, float(transmission))
        normalized_transmission_vector = transmission_vector / max(transmission_vector)
        return frequency_vector, transmission_vector, normalized_transmission_vector


    def save_FFT_data(self, frequency_vector, transmission_vector, save_path):
        '''
        Inputs:
            data_vector: the data vector to write to file
            save_path: path to save the data file to
        Outputs:
            None
        Returns a frequency and transmission vector from the data file
        produced by Toki's LabView software
        '''
        with open(save_path, 'w') as file_handle:
            for i, frequency in enumerate(frequency_vector):
                transmission = transmission_vector[i]
                line = '{0} \t {1}\n'.format(frequency, transmission)
                file_handle.write(line)


    def load_FFT_data(self, data_path, smoothing_factor=0.01, xlim_clip=(10, 600)):
        '''
        Inputs:
            data_path:  the path to the .fft data file (string)
        Outputs:
            frequency_vector: the extracted frequency vector
            transmission_vector: the extracted frequency vector
        Returns a frequency and transmission vector from the data file
        produced by Toki's LabView software
        '''
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            frequency_vector = np.zeros(len(lines))
            transmission_vector = np.zeros(len(lines))
            for i, line in enumerate(lines):
                if ',' in line:
                    frequency = line.split(', ')[0]
                    transmission = line.split(', ')[1]
                else:
                    frequency = line.split('\t')[0]
                    transmission = line.split('\t')[1]
                if float(xlim_clip[0]) < float(frequency) < float(xlim_clip[1]):
                    np.put(frequency_vector, i, frequency)
                    np.put(transmission_vector, i, transmission)
        transmission_vector = transmission_vector[frequency_vector != 0.0]
        frequency_vector = frequency_vector[frequency_vector != 0.0]
        if smoothing_factor > 0.0:
            transmission_vector = self.running_mean(transmission_vector, smoothing_factor=smoothing_factor)
        normalized_transmission_vector = transmission_vector / max(transmission_vector)
        return frequency_vector, transmission_vector, normalized_transmission_vector

    def load_IF_data(self, data_path):
        '''
        Inputs:
            data_path:  the path to the .if data file (string)
        Outputs:
            position_vector: the extracted frequency vector
            signal_vector: the extracted frequency vector
        Returns a frequency and transmission vector from the data file
        produced by Toki's LabView software
        '''
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            signal_vector = np.zeros(len(lines))
            position_vector = np.zeros(len(lines))
            for i, line in enumerate(lines):
                position = line.split('\t')[0]
                signal = line.split('\t')[1]
                np.put(position_vector, i, position)
                np.put(signal_vector, i, signal)
        print position_vector, signal_vector
        return position_vector, signal_vector

    def plot_IF_data(self, position_vector, signal_vector, color='b',
                     label='', fig=None, plot_if=False, plot_fft=False,
                     scan_param_dict={}):
        if fig is None:
            fig = pl.figure()
            fig.add_subplot(311)
            fig.add_subplot(312)
            fig.add_subplot(313)
            ax1 = fig.get_axes()[0]
            ax2 = fig.get_axes()[1]
            ax3 = fig.get_axes()[2]
            fig.subplots_adjust(hspace=0.26, bottom=0.12, top =0.96, left=0.16, right=0.84)
        frequency_vector, transmission_vector, symmetric_position_vector, symmetric_signal_vector  = self.fourier.convert_IF_to_FFT_data(position_vector,
                                                                                                                                         signal_vector,
                                                                                                                                         scan_param_dict=scan_param_dict,
                                                                                                                                         quick_plot=False)
        ax1.set_xlabel('Mirror Position', fontsize=14)
        ax1.set_ylabel('IF Signal ', fontsize=14)
        ax1.plot(position_vector, signal_vector, color, label=label, lw=2)
        ax2.plot(symmetric_position_vector, symmetric_signal_vector, color, label=label, lw=2)
        if plot_fft:
            self.plot_FFT_data(frequency_vector, transmission_vector, fig=fig, xlim=(0, 1200))
        pl.show()
        return fig

    def plot_FFT_data(self, frequency_vector, transmission_vector, color='b',
                      title='', label='', xlim=(100,400), fig=None, add_FFT=False,
                      add_atmosphere=False, save_data=True):
        '''
        This function will take the output of Load_FFT_Data
        '''
        if fig is None:
            fig = pl.figure(figsize=(8,4))
            fig.add_subplot(111)
            fig.subplots_adjust(hspace=0.26, bottom=0.15, top =0.90, left=0.16, right=0.70)
            ax = fig.get_axes()[0]
        else:
            ax = fig.get_axes()[0]
        if add_atmosphere:
            ax = self.add_atmospheric_lines(ax)
            add_atmosphere = False
        print 'plotting freq and tran vector'
        ax.plot(frequency_vector, transmission_vector, color, label=label, lw=1, alpha=0.8)
        ax.tick_params(labelsize=14)
        ax.set_xlabel('Frequency (GHz)', fontsize=14)
        ax.set_ylabel('Normalized Transmission', fontsize=14)
        ax.set_xlim(xlim)
        ax.set_title(title)
        ax.set_ylim((-0.05, 1.05))
        # Add Legend
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, numpoints=1,
                  borderaxespad=0.0, loc=2,
                  bbox_to_anchor=(1.01, 1.0))
        return fig, ax, add_atmosphere


    def _ask_user_if_they_want_to_quit(self):
        quit_boolean = raw_input('Press q to q(uit), any other key to continue:\n')
        if quit_boolean == 'q':
            exit()

        N = int(smoothing_factor * len(vector))

    def running_mean(self, vector, smoothing_factor=0.01):
        N = int(smoothing_factor * len(vector))
        averaged_vector = np.zeros(len(vector))
        for i, value in enumerate(vector):
            low_index = i
            hi_index = i + N
            if hi_index > len(vector) - 1:
                hi_index = len(vector) - 1
            averaged_value = np.mean(vector[low_index:hi_index])
            if np.isnan(averaged_value):
                np.put(averaged_vector, i, 0.0)
            else:
                np.put(averaged_vector, i, averaged_value)
        return averaged_vector

    def add_atmospheric_lines(self, ax):
        frequencies, transmissions = [], []
        with open('./Atmospheric_Modeling/chajnantor.dat', 'r') as atm_file_handle:
            for line in atm_file_handle.readlines():
                frequency = float(line.split(', ')[0])
                frequencies.append(frequency)
                transmission = float(line.split(', ')[1])
                transmissions.append(transmission)
        ax.plot(frequencies, transmissions, 'k', alpha=0.5, label='ATM Model')
        return ax

    def divide_out_optical_element_response(self, frequency_vector, normalized_transmission_vector,
                                            optical_element='mmf', frequency_=350, transmission_threshold=0.15,
                                            bs_thickness=10, quick_plot=False):
        '''
        This divides out the mmf filter response between 40 and 450 GHz (data our side of this is too noisy)
        Inputs:
            frequency_vector: the frequency vector on to which the mmf data that will interpolated
            mmf_frequency_vector: the native frequency vector of the mmf data that will interpolated
            normalized_transmission_vector: FFT data to divide the response out of
            normalized_mmf_transmission_vector: FFT data from the mmf which will be divided into the other vector
            band_edges: approximated band_edges where you want to divide out the frequency response (default is for 350 band most affected by the mmf)
        Outputs:
            corrected_transmission_vector: the divided spectra with the response removed
        '''
        if optical_element == 'bs':
            bs_transmission_file_name = '{0}_mil_beamsplitter_efficiency.dat'.format(bs_thickness)
            bs_transmission_path = os.path.join('.\\FTS_Curves\\Output\\Beam_Splitter_Efficiency', bs_transmission_file_name)
            element_frequency_vector = []
            element_transmission_vector = []
            with open(bs_transmission_path, 'r') as bs_file_handle:
                for line in bs_file_handle.readlines():
                    element_frequency = line.split('\t')[0]
                    element_transmission = line.split('\t')[1].strip('\n')
                    if float(element_transmission) > transmission_threshold:
                        element_frequency_vector.append(element_frequency)
                        element_transmission_vector.append(element_transmission)

        # Make a copy for before and after comparison
        corrected_transmission_vector = copy(normalized_transmission_vector)

        # Interpolate the optical element to the bolo transmission data and then divide it out
        transmission_vector_to_divide = np.interp(frequency_vector, element_frequency_vector,
                                                  element_transmission_vector)
        corrected_transmission_vector = normalized_transmission_vector / transmission_vector_to_divide

        # Renormalize the vector after the division
        corrected_transmission_vector = corrected_transmission_vector / np.max(corrected_transmission_vector)
        if quick_plot:
            fig = pl.figure()
            ax1 = fig.add_subplot(111)
            ax1.plot(frequency_vector, normalized_transmission_vector, 'r', lw=3, label='Input')
            ax1.plot(frequency_vector, corrected_transmission_vector, 'b', label='Corrected')
            ax1.plot(element_frequency_vector, element_transmission_vector, 'g', alpha=0.75, label='Element')
            ax1.set_xlabel('Frequency (GHz)', fontsize=16)
            ax1.set_ylabel('Response', fontsize=16)
            ax1.set_title('Division Inspection for {0}'.format(optical_element), fontsize=16)
            ax1.set_ylim(-1, 2)
            for axis in fig.get_axes():
                handles, labels = axis.get_legend_handles_labels()
                axis.legend(handles, labels, numpoints=1, loc='best')
            pl.show()
        return corrected_transmission_vector

    def _ask_user_if_they_want_to_quit(self):
        quit_boolean = raw_input('Press q to q(uit), any other key to continue:\n')
        if quit_boolean == 'q':
            exit()

    def close_fig(self):
        pl.close()

    def run(self, list_of_input_dicts, save_fft=True, run_open_comparison=False,
            add_atmosphere=False, add_foreground=False, fig=None):
        fig = None
        plot_if = False
        plot_fft = False
        for dict_ in list_of_input_dicts:
            if '.if' == dict_['measurements']['data_path'][-3:]:
                plot_if = True
            elif '.fft' == dict_['measurements']['data_path'][-4:]:
                plot_fft = True
        for dict_ in list_of_input_dicts:
            data_path = dict_['measurements']['data_path']
            label = dict_['measurements']['plot_label']
            title = dict_['measurements']['plot_title']
            color = dict_['measurements']['color']
            xlim_plot = dict_['measurements']['xlim_plot']
            xlim_clip = dict_['measurements']['xlim_clip']
            divide_bs_5 = dict_['measurements']['divide_bs_5']
            divide_bs_10 = dict_['measurements']['divide_bs_10']
            add_atmosphere = dict_['measurements']['add_atm_model']
            smoothing_factor = float(dict_['measurements']['smoothing_factor'])
            if data_path[-4:] == '.fft':
                frequency_vector, transmission_vector, normalized_transmission_vector = self.load_FFT_data(data_path, smoothing_factor=smoothing_factor,
                                                                                                           xlim_clip=xlim_clip)
                if run_open_comparison:
                    open_data_path = dict_['open_air']['data_path']
                    data_path = dict_['measurements']['data_path']
                    open_frequency_vector, open_transmission_vector, open_normalized_transmission_vector = self.load_FFT_data(open_data_path)
                    divided_transmission_vector = transmission_vector / open_transmission_vector
                elif divide_bs_5:
                    divided_transmission_vector = self.divide_out_optical_element_response(frequency_vector, normalized_transmission_vector,
                                                                                           optical_element='bs', bs_thickness=5)
                elif divide_bs_10:
                    divided_transmission_vector = self.divide_out_optical_element_response(frequency_vector, normalized_transmission_vector,
                                                                                           optical_element='bs', bs_thickness=10)
                else:
                    divided_transmission_vector = normalized_transmission_vector
                if save_fft and len(label) > 0:
                    save_path = './FTS_Curves/temp/{0}.fft'.format(label)
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    self.save_FFT_data(frequency_vector, transmission_vector, save_path)
                fig, ax, add_atmosphere = self.plot_FFT_data(frequency_vector, divided_transmission_vector, color=color, title=title, label=label, xlim=xlim_plot,
                                                             fig=fig, add_atmosphere=add_atmosphere)
            elif data_path[-3:] == '.if':
                plot_fft = True
                position_vector, signal_vector = self.load_IF_data(data_path)
                fig = self.plot_IF_data(position_vector, signal_vector, color=color, label=label, fig=fig,
                                        plot_if=plot_if, plot_fft=plot_fft, scan_param_dict=dict_)
        if len(title) > 0:
            fig.savefig('./FTS_Curves/temp/{0}.png'.format(title))
        elif len(label) > 0:
            fig.savefig('./FTS_Curves/temp/{0}.png'.format(label))
        fig.savefig('./FTS_Curves/temp/try.png')
        pl.show(fig)
        return fig


if __name__ == '__main__':
    dict_12icm = {'filter_name': '12icm',
                  'open_air': {'data_path': "./Data/MMF/2015_03_20/003_OpenAir_High_Res../FST_Curves/temp/fft",
                               'label': 'Open Trans', 'color': 'r'},
                  'measurements': {'data_path': "./Data/MMF/2015_03_20/004_576_12icm_High_Res.fft",
                                   'label': 'Raw Trans', 'color': 'b'}}
    dict_14icm = {'filter_name': '14icm',
                  'open_air': {'data_path': "2015_03_20\\003_OpenAir_High_Res.fft",
                               'label': 'Open Trans', 'color': 'g'},
                  'measurements': {'data_path': "2015_03_20\\010_576_14icm_High_Res.fft",
                                   'label': 'Raw Trans', 'color': 'm'}}
    dict_18icm = {'filter_name': '18icm',
                  'open_air': {'data_path': "2015_03_20\\003_OpenAir_High_Res.fft",
                               'label': 'Open Trans', 'color': 'k'},
                  'measurements': {'data_path': "2015_03_20\\011_576_18icm_High_Res.fft",
                                   'label': 'Raw Trans', 'color': 'm'}}
    list_of_input_dicts = [dict_12icm]
    fts = FTSCurve(list_of_input_dicts)
    fts.run()
