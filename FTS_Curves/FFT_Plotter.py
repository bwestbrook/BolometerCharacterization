from copy import copy, deepcopy
from scipy.fftpack import fft, fftfreq, fftshift
from scipy.signal import blackman, hanning, medfilt
from scipy import interpolate
from settings import settings
from numerical_processing import Fourier, BeamSplitter
import matplotlib as mpl
import pylab as pl
import numpy as np
import sys
import os


class DataLoading():
    '''
    This class does all of the data loading and analysis
    '''
    def __init__(self, pos_for_40, pos_for_60, pos_for_90, pos_for_150, pos_for_220, pos_for_280, pos_for_350):
        self.hello = 'hello'
        self.pos_for_40 = pos_for_40
        self.pos_for_60 = pos_for_60
        self.pos_for_90 = pos_for_90
        self.pos_for_150 = pos_for_150
        self.pos_for_220 = pos_for_220
        self.pos_for_280 = pos_for_280
        self.pos_for_350 = pos_for_350
        self.band_edges_dict = {40: (10, 90), 60: (25, 110), 90: (70, 140), 150: (75, 200),
                                220: (140, 320), 280: (100, 400), 350: (225, 600)}
        self.band_edges_dict_tight = {40: (10, 90), 60: (25, 110), 90: (70, 140), 150: (105, 200),
                                      220: (140, 320), 280: (100, 360), 350: (225, 390)}
        self.data_plotting = DataPlotting(pos_for_40, pos_for_60, pos_for_90, pos_for_150, pos_for_220, pos_for_280, pos_for_350)


    def return_data_query_dicts(self, frequencies=['220'], pixels=['Tetraplexer'], dates=['2015_06_16'],
                                wafers=['BW1_8'], dies=['3_5'], for_poster=True):
        '''
        Inputs:
            frequencies (list) - a list of frequencies you wish to plot
            pixels (list) - a list of pixel types.  A common index between list will be plotted together
            dates (list) - a list of dates on which data was taken
            dies (list) - a list of dies you wish to plot
            wafers (list) - a list of wafers you wish to plot
        Outputs:
            list_of_dicts and list of dictionaries contiaining all of the paths and labels needed to plot the data
            in a nice way
        '''
        colors = ['g', 'b', 'r', 'k', 'm']
        list_of_dicts = []
        for j, frequency in enumerate(frequencies):
            dict_ = {}
            pixel = pixels[j]
            date = dates[j]
            wafer = wafers[j]
            die = dies[j]
            dict_.update({'frequency': frequency})
            dict_.update({'pixel': pixel})
            dict_.update({'simulations': {'data_path': "Simulations/{0}_{1}_Transmission.dat".format(frequency, pixel),
                                          'label': '{0} {1} (Sim)'.format(frequency, pixel)}})
            dict_.update({'measurements': {'data_path': "Data/{0}/{1}/Wafer_{2}_Die_{3}/{4}/ToLoad".format(pixel, date, wafer, die, frequency),
                                           'data_path_if': "./Data/{0}/{1}/Wafer_{2}_Die_{3}/{4}/ToLoad".format(pixel, date, wafer, die, frequency),
                                           'mmf_fft_path': "./Output/MMF_Transmission/12icm_Filter_Transmission.fft",
                                           'bs_fft_path': "./Output/Beam_Splitter_Efficiency/5_mil_beamsplitter_efficiency.dat"}})
            if for_poster:
                dict_['measurements'].update({'label': '{0} Band'.format(frequency), 'color': '#BD0470'})
            else:
                dict_['measurements'].update({'label': '{0} {1}'.format(frequency, pixel), 'color': '#BD0470'})
            if str(frequency) == '40':
                if pixel == 'LF_Triplexer':
                    dict_['simulations'].update({'color': 'b'})
                    dict_['measurements'].update({'color': '#E61011'})
            if str(frequency) == '60':
                if pixel == 'LF_Triplexer':
                    dict_['simulations'].update({'color': 'm'})
                    dict_['measurements'].update({'color': '#E63710'})
            if str(frequency) == '90':
                if pixel == 'Tetraplexer':
                    dict_['simulations'].update({'color': 'k'})
                    dict_['measurements'].update({'color': '#A2E610'})
                elif pixel == 'LF_Triplexer':
                    dict_['simulations'].update({'color': 'k'})
                    dict_['measurements'].update({'color': '#E67E10'})
            if str(frequency) == '150':
                if pixel == 'Tetraplexer':
                    dict_['simulations'].update({'color': '#4605ED'})
                    dict_['measurements'].update({'color': '#10E614'})
                elif pixel == 'PB2':
                    dict_['simulations'].update({'color': '#4605ED'})
                    dict_['measurements'].update({'color': '#10E614'})
            if str(frequency) == '220':
                if pixel == 'Tetraplexer':
                    dict_['simulations'].update({'color': 'm'})
                    dict_['measurements'].update({'color': '#10E66D'})
                elif pixel == 'HF_Triplexer':
                    dict_['simulations'].update({'color': 'g'})
                    dict_['measurements'].update({'color': '#1AAABA'})
            if str(frequency) == '280':
                if pixel == 'Tetraplexer':
                    dict_['simulations'].update({'color': 'c'})
                    dict_['measurements'].update({'color': '#13BF86'})
                elif pixel == 'HF_Triplexer':
                    dict_['simulations'].update({'color': 'r'})
                    dict_['measurements'].update({'color': '#1372BF'})
            if str(frequency) == '350':
                if pixel == 'HF_Triplexer':
                    dict_['simulations'].update({'color': 'k'})
                    dict_['measurements'].update({'color': '#1341BF'})
                elif pixel == 'DsDp':
                    dict_['simulations'].update({'color': 'y'})
                    dict_['measurements'].update({'color': '#6C2FAD'})
            list_of_dicts.append(deepcopy(dict_))
        return list_of_dicts


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


    def load_optical_element_data(self, data_path, optical_element='mmf'):
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
                np.put(frequency_vector, i, float(frequency))
                np.put(transmission_vector, i, float(transmission))
        if optical_element == 'mmf':
            band_selector_1 = np.logical_and(frequency_vector < 450, frequency_vector > 150)
            mmf_zero_selector = np.logical_and(frequency_vector < 450, frequency_vector > 400)
            normalized_transmission_vector = (transmission_vector - np.median(transmission_vector[mmf_zero_selector]))
            normalized_transmission_vector = normalized_transmission_vector / max(normalized_transmission_vector[band_selector_1])
        elif optical_element == 'beam_splitter':
            normalized_transmission_vector = transmission_vector / max(transmission_vector)
        return frequency_vector, transmission_vector, normalized_transmission_vector


    def load_FFT_data(self, data_path, frequency_, hybrid, smooth=True):
        '''
        Inputs:
            data_path:  the path to the .fft data file (string)
        Outputs:
            frequency_vector: the extracted frequency vector
            transmission_vector: the extracted frequency vector
        Returns a frequency and transmission vector from the data file
        produced by Toki's LabView software
        '''
        band_edges = self.band_edges_dict[int(frequency_)]
        for file_name in os.listdir(data_path):
            if file_name[-3:] == 'fft':
                data_path = os.path.join(data_path, file_name)
        with open(data_path, 'r') as file_handle:
                lines = file_handle.readlines()
                frequency_vector = np.zeros(len(lines))
                transmission_vector = np.zeros(len(lines))
                for i, line in enumerate(lines):
                        frequency = line.split('\t')[0]
                        transmission = line.split('\t')[1]
                        np.put(frequency_vector, i, frequency)
                        np.put(transmission_vector, i, transmission)
        if smooth:
            transmission_vector = medfilt(transmission_vector, settings.smoothing_factor)
        normalized_transmission_vector = transmission_vector / max(transmission_vector)
        if hybrid:
            band_edge_low = band_edges[0]
            band_edge_high = band_edges[1]
            band_selector = np.logical_and(frequency_vector > band_edge_low, frequency_vector < band_edge_high)
            frequency_vector = np.extract(band_selector, frequency_vector)
            transmission_vector = np.extract(band_selector, transmission_vector)
            normalized_transmission_vector = np.extract(band_selector, normalized_transmission_vector)
        return frequency_vector, transmission_vector, normalized_transmission_vector


    def load_IF_data(self, data_path, distance_per_step=250.39e-9):
        '''
        Inputs:
            data_path:  the path to the .if data file (string)
            distance_per_step: for converstion to physical units
               - Default value is 250.39e-9 m (Bill's FTS)
        Outputs:
            x_position_vector: the extracted x position vector in mm
            transmission_vector: the extracted frequency vector
        Returns a frequency and transmission vector from the inteferogram data and the input
        params of the FTS setup being used
        '''
        for file_name in os.listdir(data_path):
            if file_name[-2:] == 'if':
                data_path = os.path.join(data_path, file_name)
        with open(data_path, 'r') as file_handle:
                lines = file_handle.readlines()
                position_vector = np.zeros(len(lines))
                transmission_vector = np.zeros(len(lines))
                for i, line in enumerate(lines):
                    stepper_position = float(line.split('\t')[0]) * distance_per_step * 1e3
                    transmission = float(line.split('\t')[1])
                    np.put(position_vector, i, stepper_position)
                    np.put(transmission_vector, i, transmission)
        return position_vector, transmission_vector


    def divide_out_optical_element_response(self, frequency_vector, optical_element_frequency_vector,
                                            optical_element_transmission_vector, normalized_transmission_vector,
                                            optical_element='mmf', frequency_=350, transmission_threshold=0.1,
                                            quick_plot=True):
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
        corrected_transmission_vector = copy(normalized_transmission_vector)
        band_edges = self.band_edges_dict_tight[int(frequency_)]
        band_lower = self.band_edges_dict_tight[int(frequency_)][0]
        band_upper = self.band_edges_dict_tight[int(frequency_)][1]
        # Select the data out of the band
        band_selector_element = np.logical_and(optical_element_frequency_vector > band_lower, optical_element_frequency_vector < band_upper)
        band_selector_data = np.logical_and(frequency_vector > band_lower, frequency_vector < band_upper)
        # Select the data of the optical element with at least 10% transmission
        band_selector_element = np.logical_and(band_selector_element, optical_element_transmission_vector > transmission_threshold)
        # Interpolate the optical element to the bolo transmission data and then divide it out
        if np.sum(band_selector_element) == 0:
            transmission_vector_to_divide = np.ones(frequency_vector[band_selector_data].size)
        else:
            transmission_vector_to_divide = np.interp(frequency_vector[band_selector_data], optical_element_frequency_vector[band_selector_element],
                                                      optical_element_transmission_vector[band_selector_element])
        corrected_transmission_vector[band_selector_data] = normalized_transmission_vector[band_selector_data] / transmission_vector_to_divide
        # Renormalize the vector after the division
        corrected_transmission_vector = corrected_transmission_vector / np.max(corrected_transmission_vector)
        if quick_plot:
            fig = mpl.pyplot.figure()
            ax1 = fig.add_subplot(111)
            ax1.plot(frequency_vector, normalized_transmission_vector, 'r', lw=3, label='Input')
            ax1.plot(frequency_vector, corrected_transmission_vector, 'b', label='Corrected')
            ax1.plot(frequency_vector[band_selector_data], transmission_vector_to_divide, 'c.', ms=3.0, label='Divisor Interp')
            ax1.set_xlabel('Frequency (GHz)', fontsize=16)
            ax1.set_ylabel('Response', fontsize=16)
            ax1.set_title('Division Inspection for {0}'.format(optical_element), fontsize=16)
            ax1.set_ylim(-1, 2)
            for axis in fig.get_axes():
                handles, labels = axis.get_legend_handles_labels()
                axis.legend(handles, labels, numpoints=1, loc='best')
            fig.show()
            self.data_plotting._ask_user_if_they_want_to_quit()
        return corrected_transmission_vector


    def find_nearest_specific_value(self, pixel, frequency):
        '''
        A simple function to match the 'generic' band name with it's specific/accurate band center
        '''
        specific_band_vals = self.data_plotting.color_and_limits_dict.keys()
        specific_band_vals = sorted([float(band_val) for band_val in specific_band_vals])
        index_ = np.abs(np.asarray(specific_band_vals) - float(frequency)).argmin()
        specific_band_val = specific_band_vals[index_]
        return specific_band_val


class DataPlotting():
    '''
    This class contains all of the plotting functions used to analyze this data
    '''

    def __init__(self, pos_for_40, pos_for_60, pos_for_90, pos_for_150, pos_for_220, pos_for_280, pos_for_350):
        self.hello = 'hello'
        self.hybrid = False
        self.pos_for_40 = pos_for_40
        self.pos_for_60 = pos_for_60
        self.pos_for_90 = pos_for_90
        self.pos_for_150 = pos_for_150
        self.pos_for_220 = pos_for_220
        self.pos_for_280 = pos_for_280
        self.pos_for_350 = pos_for_350
        if len(list(set(settings.pixels))) > 1:
            self.hybrid = True
        self.color_and_limits_dict = {40: {'position': pos_for_40, 'band_color': '#49BDBF', 'line_color': '#49BDBF', 'half_band_width': 0.19},
                                      60: {'position': pos_for_60, 'band_color': '#CC07DE', 'line_color': '#1CC07DE', 'half_band_width': 0.19},
                                      90: {'position': pos_for_90, 'band_color': '#1372BF', 'line_color': '#1372BF', 'half_band_width': 0.19},
                                      150: {'position': pos_for_150, 'band_color': '#10A315', 'line_color': '#10A315', 'half_band_width': 0.16},
                                      220: {'position': pos_for_220, 'band_color': '#8812E3', 'line_color': '#8812E3', 'half_band_width': 0.16},
                                      280: {'position': pos_for_280, 'band_color': '#12E382', 'line_color': '#12E382', 'half_band_width': 0.12},
                                      350: {'position': pos_for_350, 'band_color': '#E31212', 'line_color': '#E31212', 'half_band_width': 0.11}}
        self.plotting_dict = {'LF_Triplexer': {'xlims': (20, 130), 'x1ticks': (40, 60, 90,), 'band_labels': (40, 60, 90)},
                              'Tetraplexer': {'xlims': (40, 350), 'x1ticks': (90, 150, 220, 280)},
                              'PB2': {'xlims': (40, 220), 'x1ticks': (90, 150,)},
                              'HF_Triplexer': {'xlims': (140, 425), 'x1ticks': (220, 280, 350)}}
        if self.hybrid:
            self.plotting_dict = {'LF_Triplexer': {'xlims': (10, 240), 'x1ticks': (40, 62, 93)},
                                  'Tetraplexer': {'xlims': (50, 550), 'x1ticks': (93, 145, 200, 269)},
                                  'HF_Triplexer': {'xlims': (150, 450), 'x1ticks': (200, 269, 340)},
                                  'Hybrid': {'xlims': (100, 400), 'x1ticks': (150, 220, 280, 350)}}


    def plot_IF_data(self, position_vector, transmission_vector,
                     color='b', lw=1, fig=None):
        '''
        Overview:
            This function will take the output of Load_FFT_Data
        Inputs:
            position_vector: the x_position vector (in mm)
            transmission_vector: equal in length to position vector showing FTS transmission
        Outputs:
            fig: a pyplot fig object of the IF data
        '''
        if fig is None:
            fig = mpl.pyplot.figure(figsize=(10, 5))
        ax2 = fig.add_subplot(212)
        ax2.plot(position_vector, transmission_vector, color, label='IF Data', lw=lw)
        fig.subplots_adjust(bottom=0.15, top =0.96, left=0.13, right=0.68, hspace=0.44)
        ax2.tick_params(labelsize=20)
        ax2.set_xlabel('X position (mm)', fontsize=16)
        ax2.set_ylabel('Transmission', fontsize=16)
        ax2.tick_params(labelsize=12)
        return fig


    def plot_FFT_data(self, frequency_vector, transmission_vector, color='b', label='', lw=1, data_only=True, fig=None,
                      pixel='HF_Triplexer'):
        '''
        This function will take the output of Load_FFT_Data
        '''
        if fig is None:
            if pixel == 'Hybrid':
                fig = mpl.pyplot.figure(figsize=(10, 5))
            else:
                fig = mpl.pyplot.figure(figsize=(10., 5.))
        if data_only:
            ax1 = fig.add_subplot(211)
            ax1.set_xlabel('Frequency (GHz)', fontsize=16)
            ax1.set_ylabel('Normalized \n Transmission', fontsize=16)
            ax1.tick_params(labelsize=12)
        else:
            ax1 = fig.add_subplot(111)
            ax1.set_xlabel('Frequency (GHz)', fontsize=20)
            ax1.set_ylabel('Peak Normalized', fontsize=20)
            ax1.tick_params(labelsize=14)
        if pixel == 'Hybrid':
            if '40' in label:
                label = '40 LF'
            elif '60' in label:
                label = '60 LF'
            elif '90' in label:
                label = '90 LF | MF'
            elif '150' in label:
                label = '150 MF'
            elif '220' in label:
                label = '220 MF | HF'
            elif '280' in label:
                label = '280 MF | HF'
            elif '350' in label:
                label = '350 HF'
            ax1.semilogx(frequency_vector, transmission_vector, color, lw=lw)
        else:
            if label is not None:
                label = label.strip(' {0}'.format(pixel))
                if 'Sim' in label:
                    label = 'Simulation'
                ax1.plot(frequency_vector, transmission_vector, color, label=label, lw=lw)
            else:
                ax1.plot(frequency_vector, transmission_vector, color, lw=lw)
        return fig

    def add_ticks_legend_to_FFT_plot(self, fig, pixel):
        '''
        This function does some mojo with adding xticks and vspans and legends for nice plotting
        Inputs:
            fig: to add stuf to
        Outputs:
            fig: same instance but with new stuff
        '''
        ax1 = fig.get_axes()[0]
        xlims = list(self.plotting_dict[pixel]['xlims'])
        x1ticks = list(self.plotting_dict[pixel]['x1ticks'])
        data_loading = DataLoading(self.pos_for_40, self.pos_for_60, self.pos_for_90, self.pos_for_150, self.pos_for_220, self.pos_for_280, self.pos_for_350)
        for i, x_val in enumerate(x1ticks):
            alpha = 0.10
            raw_val = copy(x_val)
            band_half_width_percentage = self.color_and_limits_dict[x_val]['half_band_width']
            x_position = self.color_and_limits_dict[x_val]['position']
            color = self.color_and_limits_dict[x_val]['band_color']
            x_low = x_val - x_val * band_half_width_percentage
            x_high = x_val + x_val * band_half_width_percentage
            ax1.text(x_position, 0.125, '{0}'.format(raw_val), fontsize=22, color='k')
            if pixel == 'Hybrid' and False:
                ax1.axvline(x_low, color='k', alpha=alpha * 2.)
                ax1.axvline(x_high, color='k', alpha=alpha * 2.)
                if i in (0, 1):
                    if i == 0:
                        ax1.axvspan(x_low, x_high, color=color, alpha=alpha, label='LF_Triplexer')
                    else:
                        ax1.axvspan(x_low, x_high, color=color, alpha=alpha)
                elif i in (2,):
                    ax1.axvspan(x_low, x_high, ymin=0.0, ymax=0.5, color=color, alpha=alpha)
                    color = self.color_and_limits_dict[x_val]['band_color']
                    ax1.axvspan(x_low, x_high, ymin=0.5, ymax=1.0, color=color, alpha=alpha)
                elif i in (3,):
                    ax1.axvspan(x_low, x_high, color=color, alpha=alpha, label='MF_Tetraplexer')
                elif i in (4,):
                    ax1.axvspan(x_low, x_high, ymin=0.5, ymax=1.0, color=color, alpha=alpha)
                    color = self.color_and_limits_dict[x_val]['band_color']
                    ax1.axvspan(x_low, x_high, ymin=0.0, ymax=0.5, color=color, alpha=alpha)
                elif i in (5,):
                    ax1.axvspan(x_low, x_high, ymin=0.0, ymax=0.5, color=color, alpha=alpha)
                    color = self.color_and_limits_dict[x_val]['band_color']
                    ax1.axvspan(x_low, x_high, ymin=0.5, ymax=1.0, color=color, alpha=alpha)
                elif i in (6,):
                    ax1.axvspan(x_low, x_high, color=color, alpha=alpha, label='HF_Triplexer')
        x1ticklabels = [str(xtick) for xtick in x1ticks]
        ax1.set_xlim(xlims)
        if pixel is 'Hybrid':
            ax1.set_xticks([150, 350])
            ax1.set_xticklabels(['150', '350'])
        #else:
            ##ax1.set_xticks([125, 175, 250, 300])
            #ax1.set_xticklabels(['125', '175', '250', '300'])
        if pixel == 'Hybrid':
            fig.subplots_adjust(bottom=0.17, top =0.94, left=0.09, right=0.72)
        else:
            fig.subplots_adjust(bottom=0.15, top =0.94, left=0.16, right=0.72)
        ax1.set_ylim([-0.01, 1.0])
        all_handles, all_labels = [], []
        for j, axis in enumerate(fig.get_axes()):
            handles, labels = axis.get_legend_handles_labels()
            all_handles.extend(handles)
            all_labels.extend(labels)
        ax1.legend(all_handles, all_labels, numpoints=1, loc=2, bbox_to_anchor=(1.0, 1.01))
        return fig

    def add_foregrounds_to_plot(self, fig, frequency_vector, ell=100):
        '''
        Overview: Adds foregrounds to plot on twinx axis from Charlie
        Inputs:
            fig: matplotlib fig instance containing the axis to twin as the main axis
            frequency_vector: a frequency vector to input to the intensity function
        Outputs:
            fig: with a new axis added
        '''
        ax1 = fig.get_axes()[0]
        twin_ax = ax1.twinx()
        frequencies = np.arange(10e9, 1e12, 100e6)
        sync_intensities = np.zeros(frequencies.size)
        dust_intensities = np.zeros(frequencies.size)
        for i, nu in enumerate(frequencies):
            sync_intensity = syncAngPowSpec(1, nu, 100)
            dust_intensity = dustAngPowSpec(1, nu, 100)
            np.put(sync_intensities, i, sync_intensity)
            np.put(dust_intensities, i, dust_intensity)
        twin_ax.loglog(frequencies / 1e9, sync_intensities * 1e12,  color='#9C0631', alpha=0.5, lw=13, label='Synchrotron')
        twin_ax.loglog(frequencies / 1e9, dust_intensities * 1e12, color='k', alpha=0.5, lw=13, label='Dust')
        twin_ax.set_yticks([])
        return fig

    def _ask_user_if_they_want_to_quit(self):
        quit_boolean = raw_input('Press q to q(uit), any other key to continue:\n')
        if quit_boolean == 'q':
            exit()


class Run():

    def __init__(self):
        self.hello = 'hello'
        self.hybrid = False
        self.both = settings.both
        self.data = settings.data
        self.co_plot = settings.co_plot
        self.pos_for_40 = settings.pos_for_40
        self.pos_for_60 = settings.pos_for_60
        self.pos_for_90 = settings.pos_for_90
        self.pos_for_150 = settings.pos_for_150
        self.pos_for_220 = settings.pos_for_220
        self.pos_for_280 = settings.pos_for_280
        self.pos_for_350 = settings.pos_for_350
        self.position_dictionary = {40: self.pos_for_40, 60: self.pos_for_60, 90: self.pos_for_90,
                                    150: self.pos_for_150, 220: self.pos_for_220, 280: self.pos_for_220,
                                    350: self.pos_for_350}
        self.data_loading = DataLoading(self.pos_for_40, self.pos_for_60, self.pos_for_90, self.pos_for_150, self.pos_for_220, self.pos_for_280, self.pos_for_350)
        self.data_plotting = DataPlotting(self.pos_for_40, self.pos_for_60, self.pos_for_90, self.pos_for_150, self.pos_for_220, self.pos_for_280, self.pos_for_350)
        if len(list(set(settings.pixels))) > 1:
            self.co_plot = True
            self.both = False
            self.data = False
            self.hybrid = True


    def process_all_input_dicts(self, list_of_dicts, divide_beam_splitter_response=True, divide_mmf_response=True,
                                data=True, co_plot=False, simulations=False, both=False, hybrid=False, savefig=True):
        '''
        This loops through the list of dictionaries returned by return_data_query_dicts
        and plots them according to the kwargs
            - data (Boolean) will plot the FFT data
            - simulation (Boolean) will plot the simulated data
            - both (Boolean) will plot the FFT and simulation data
            - co_plot (Boolean) will overplot mulitple frequencies FFT and simulation data
        '''
        fourier = Fourier()
        print data, co_plot, simulations, both
        fig = None
        frequencies = []
        pixels = []
        data_only = False
        for i, dict_ in enumerate(list_of_dicts):
            if self.hybrid:
                pixel = 'Hybrid'
            else:
                pixel = dict_['pixel']
            frequency = dict_['frequency']
            sim_color = dict_['simulations']['color']
            sim_label = dict_['simulations']['label']
            label = dict_['measurements']['label']
            color = self.data_plotting.color_and_limits_dict[int(frequency)]['band_color']
            data_path = dict_['measurements']['data_path']
            data_path_if = dict_['measurements']['data_path_if']
            sim_data_path = dict_['simulations']['data_path']
            mmf_fft_data_path = dict_['measurements']['mmf_fft_path']
            bs_fft_data_path = dict_['measurements']['bs_fft_path']
            # Load all of the data needed to plot things
            if_position_vector, if_transmission_vector = self.data_loading.load_IF_data(data_path_if)
            mmf_frequency_vector, mmf_transmission_vector, normalized_mmf_transmission_vector =\
                self.data_loading.load_optical_element_data(mmf_fft_data_path, optical_element='mmf')
            bs_frequency_vector, bs_transmission_vector, normalized_bs_transmission_vector =\
                self.data_loading.load_optical_element_data(bs_fft_data_path, optical_element='beam_splitter')
            #sim_frequency_vector, sim_transmission_vector, sim_normalized_transmission_vector =\
                #self.data_loading.load_simulation_data(sim_data_path)
            frequency_vector, transmission_vector, normalized_transmission_vector =\
                self.data_loading.load_FFT_data(data_path, frequency, hybrid)
            # Do some numerical procesing on the data
            fft_frequency_vector, fft_transmission_vector =\
                fourier.convert_IF_to_FFT_data(if_position_vector, if_transmission_vector, quick_plot=False)
            if float(frequency) < 100:
                settings.divide_mmf_response = False
            else:
                settings.divide_mmf_response = True
            if settings.divide_mmf_response:
                normalized_transmission_vector= self.data_loading.divide_out_optical_element_response(frequency_vector, mmf_frequency_vector,
                                                                                                      mmf_transmission_vector, normalized_transmission_vector,
                                                                                                      optical_element='mmf', frequency_=frequency,
                                                                                                      transmission_threshold=0.1, quick_plot=False)
            if settings.divide_beam_splitter_response:
                normalized_transmission_vector= self.data_loading.divide_out_optical_element_response(frequency_vector, bs_frequency_vector,
                                                                                                      bs_transmission_vector, normalized_transmission_vector,
                                                                                                      optical_element='beam_splitter', frequency_=frequency,
                                                                                                      transmission_threshold=0.1, quick_plot=False)
            if settings.simulations:
                fig = self.data_plotting.plot_FFT_data(sim_frequency_vector, sim_normalized_transmission_vector, color=color,
                                                       data_only=data_only, lw=2, label=label, fig=fig, pixel=pixel)
            elif self.both and not self.co_plot:
                data_frequency_vector, data_transmission_vector, data_normalized_transmission_vector =\
                    frequency_vector, transmission_vector, normalized_transmission_vector
                fig = self.data_plotting.plot_FFT_data(data_frequency_vector, data_normalized_transmission_vector, data_only=data_only,
                                                       color=color, label=label, fig=None, pixel=pixel)
                fig = self.data_plotting.plot_FFT_data(sim_frequency_vector, sim_normalized_transmission_vector, data_only=data_only,
                                                       color=sim_color, label=sim_label, fig=fig, lw=2, pixel=pixel)
            elif self.co_plot:
                if i < 3:
                    color = 'k'
                    if i == 0:
                        label = 'Before Radiation'
                    else:
                        label = None
                else:
                    color = 'r'
                    if i == 3:
                        label = 'After Radiation'
                    else:
                        label = None
                print
                print
                print i, color
                print
                print
                fig = self.data_plotting.plot_FFT_data(frequency_vector, normalized_transmission_vector,
                                                       color=color, label=label, fig=fig, data_only=data_only, pixel=pixel)
                if self.both:
                    fig = self.data_plotting.plot_FFT_data(sim_frequency_vector, sim_normalized_transmission_vector, data_only=data_only,
                                                           color=sim_color, label=sim_label, fig=fig, lw=2, pixel=pixel)
            elif self.data:
                if not co_plot and not both and not simulations:
                    data_only = True
                #fig = plot_FFT_data(fft_frequency_vector, fft_transmission_vector, color='g', label='python fft')
                #fig = self.data_plotting.plot_FFT_data(fft_frequency_vector, fft_transmission_vector, color=color,
                                                       #data_only=data_only, label=label, fig=fig, pixel=pixel)
                fig = self.data_plotting.plot_FFT_data(frequency_vector, normalized_transmission_vector, color=color,
                                                       data_only=data_only, label=label, fig=fig, pixel=pixel)
                fig = self.data_plotting.plot_IF_data(if_position_vector, if_transmission_vector, color=color, fig=fig)
            frequencies.append(str(frequency))
            pixels.append(str(pixel))
        #fig = self.data_plotting.add_foregrounds_to_plot(fig, frequency_vector)
        fig = self.data_plotting.add_ticks_legend_to_FFT_plot(fig, pixel)
        if savefig:
            frequencies_str = '_'.join(frequencies)
            pixels_str = '_'.join(list(set(pixels)))
            if data_only:
                save_str = './Output/FFT_Data_Only_{0}_GHz_{1}.pdf'.format(frequencies_str, pixels_str)
            elif co_plot:
                save_str = './Output/FFT_Co_Plot_{0}_GHz_{1}.pdf'.format(frequencies_str, pixels_str)
            else:
                save_str = './Output/FFT_{0}_GHz_{1}.pdf'.format(frequencies_str, pixels_str)
            print 'Saving figure to {0}'.format(save_str, pad_inches=-0.1)
            fig.savefig(save_str)
        fig.show()
        self.data_plotting._ask_user_if_they_want_to_quit()

    def run(self):
        list_of_dicts = self.data_loading.return_data_query_dicts(settings.frequencies, settings.pixels, settings.dates,
                                                                  settings.wafers, settings.dies, settings.for_poster)
        print list_of_dicts
        self.process_all_input_dicts(list_of_dicts, data=settings.data, co_plot=settings.co_plot, simulations=settings.simulations,
                                     both=settings.both, divide_mmf_response=settings.divide_mmf_response,
                                     divide_beam_splitter_response=settings.divide_beam_splitter_response)



if __name__ == '__main__':
    run = Run()
    run.run()
