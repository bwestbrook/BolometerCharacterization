import os
import numpy as np
import pylab as pl
import scipy.fftpack
from pprint import pprint
from copy import copy, deepcopy
from scipy.signal import blackman
#, hanning

class FourierTransformSpectroscopy():
    '''
    This is a custom class of python function used to conver interferogram data into Spectra for bolometers
    '''
    def __init__(self):
        '''
        init for the Fourier class
        '''
        super(FourierTransformSpectroscopy, self).__init__()
        self.bands = self.ftsy_get_bands()
        self.optical_elements = self.ftsy_get_optical_elements()

    def ftsy_get_bands(self):
        '''
        '''
        self.bands = {
            '': {
                'Active': False,
                'Band Center': '',
                'Project': '',
                'Freq Column': 'NA',
                'Transmission Column': 'NA',
                'Header Lines': 'NA',
                'Path': 'NA',
                },
            '90': {
                'Active': False,
                'Band Center': 90,
                'Project': 'Simons Array',
                'Freq Column': 0,
                'Transmission Column': 1,
                'Header Lines': 1,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'PB2abcBands.csv')
                },
            '150': {
                'Active': False,
                'Band Center': 150,
                'Project': 'Simons Array',
                'Freq Column': 0,
                'Transmission Column': 2,
                'Header Lines': 1,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'PB2abcBands.csv')
                },
            'SO30': {
                'Active': False,
                'Band Center': 30,
                'Project': 'Simons Observatory',
                'Freq Column': 0,
                'Transmission Column': 3,
                'Header Lines': 2,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'Nitride_Lumped_Diplexer_030_05_040_08_MoreWider20190226_300GHz.csv')
                },
            'SO40': {
                'Active': False,
                'Band Center': 40,
                'Project': 'Simons Observatory',
                'Freq Column': 0,
                'Transmission Column': 4,
                'Header Lines': 2,
                'Path': os.path.join('bd_lib', 'simulated_bands', 'Nitride_Lumped_Diplexer_030_05_040_08_MoreWider20190226_300GHz.csv')
                }
            }
        return self.bands

    def ftsy_get_optical_elements(self):
        '''
        '''
        self.optical_elements = {
            '5mil Beam Splitter': {
                'Active': False,
                'Path': os.path.join('bd_lib', 'optical_elements', '5_mil_beamsplitter_efficiency.dat')
                },
            '10mil Beam Splitter': {
                'Active': False,
                'Path': os.path.join('bd_lib', 'optical_elements', '10_mil_beamsplitter_efficiency.dat')
                },
            '40mil Beam Splitter': {
                'Active': False,
                'Path': os.path.join('bd_lib', 'optical_elements', '40_mil_beamsplitter_efficiency.dat')
                },
            '60mil Beam Splitter': {
                'Active': False,
                'Path': os.path.join('bd_lib', 'optical_elements', '60_mil_beamsplitter_efficiency.dat')
                },
            '12icm 576 MMF': {
                'Active': False,
                'Path': os.path.join('bd_lib', 'optical_elements', '10_mil_beamsplitter_efficiency.dat')
                },
            }
        return self.optical_elements

    def ftsy_load_simulated_band(self, data_clip_lo, data_clip_hi, band):
        '''
        '''
        data_path = self.bands[band]['Path']
        freq_idx = self.bands[band]['Freq Column']
        trans_idx = self.bands[band]['Transmission Column']
        header_lines = self.bands[band]['Header Lines']
        print(freq_idx, trans_idx)
        print(freq_idx, trans_idx)
        print(freq_idx, trans_idx)
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            frequency_vector = np.zeros([])
            transmission_vector = np.zeros([])
            for i, line in enumerate(lines):
                if i > header_lines:
                    print(line)
                    try:
                        if ',' in line:
                            frequency = line.split(',')[freq_idx].strip()
                            transmission = line.split(',')[trans_idx].strip()
                        else:
                            frequency = line.split('\t')[freq_idx].strip()
                            transmission = line.split('\t')[trans_idx].strip()
                        #import ipdb;ipdb.set_trace()
                        if float(data_clip_lo) < float(frequency) * 1e9 < float(data_clip_hi) and self.ftsy_is_float(transmission):
                            frequency_vector = np.append(frequency_vector, float(frequency))
                            transmission_vector = np.append(transmission_vector, float(transmission))
                    except ValueError:
                        pass
        return frequency_vector, transmission_vector

    def ftsy_is_float(self, value):
        '''
        '''
        try:
            float(value)
            return True
        except ValueError:
            return False

    def ftsy_load_optical_element_response(self, path, threshhold=0.1):
        '''
        '''
        if path is None:
            return None, None
        element_frequency_vector = []
        element_transmission_vector = []
        with open(path, 'r') as bs_file_handle:
            for line in bs_file_handle.readlines():
                element_frequency = line.split(',')[0]
                element_transmission = line.split(',')[1].strip('\n')
                element_frequency_vector.append(float(element_frequency) * 1e9) # GHz
                if float(element_transmission) > threshhold:
                    element_transmission_vector.append(float(element_transmission))
                else:
                    element_transmission_vector.append(threshhold)
        element_transmission_vector = np.asarray(element_transmission_vector)
        #/ np.max(element_transmission_vector)
        return np.asarray(element_frequency_vector), element_transmission_vector

    def ftsy_divide_out_optical_element_response(self, frequency_vector, normalized_transmission_vector,
                                                 optical_element=None, path=None, threshhold=0.1):
        '''
        '''
        element_frequency_vector, element_transmission_vector = self.ftsy_load_optical_element_response(path, threshhold)
        #if np.max(frequency_vector) > 1e6:
            #frequency_vector *= 1e-12
        # Make a copy for before and after comparison
        corrected_transmission_vector = copy(normalized_transmission_vector)
        freq_selector = np.where(frequency_vector > 0)
        element_freq_selector = np.where(element_frequency_vector < np.max(frequency_vector))
        #import ipdb;ipdb.set_trace()
        transmission_vector_to_divide = np.interp(frequency_vector[freq_selector], element_frequency_vector[element_freq_selector], element_transmission_vector[element_freq_selector])
        corrected_transmission_vector = normalized_transmission_vector[freq_selector] / transmission_vector_to_divide
        normalized_corrected_transmission_vector = corrected_transmission_vector / np.max(corrected_transmission_vector)
        frequency_vector = frequency_vector[freq_selector]
        return frequency_vector, normalized_corrected_transmission_vector

    def ftsy_convert_IF_to_FFT_data(self, position_vector, efficiency_vector, mirror_interval,
                                    distance_per_step=250.39e9, data_selector='All',
                                    apodization_type='BOXCAR', quick_plot=False):
        '''
        Returns a frequency and efficiency vector from the inteferogram data and the input
        params of the FTS setup being used
        Inputs:
            position_vector:  as returned by load_IF_data
            efficiency_vector:  as returned by load_IF_data
            distance_per_step: for converstion to physical units
               - Default value is 250.39 nm (Bill's FTS)
        Outputs:
            frequency_vector: the extracted frequency vector
            efficiency_vector: the extracted frequency vector

        '''
        position_vector = np.asarray(position_vector)
        efficiency_vector = np.asarray(efficiency_vector)
        efficiency_left_data, efficiency_right_data, position_left_data, position_right_data =\
            self.ftsy_split_data_into_left_right_points(position_vector, efficiency_vector)
        if data_selector == 'All':
            efficiency_vector = efficiency_vector
            position_vector = position_vector
        elif data_selector == 'Right':
            efficiency_vector = efficiency_right_data
            position_vector = position_right_data
            efficiency_vector = self.ftsy_make_data_symmetric(efficiency_vector, is_right=True)
            position_vector = self.ftsy_make_data_symmetric(position_vector, is_right=True, position=True)
        elif data_selector == 'Left':
            efficiency_vector = efficiency_left_data
            position_vector = position_left_data
            efficiency_vector = self.ftsy_make_data_symmetric(efficiency_vector, is_right=False)
            position_vector = self.ftsy_make_data_symmetric(position_vector, is_right=False, position=True)
        efficiency_vector, position_vector = self.ftsy_prepare_data_for_fft(efficiency_vector, position_vector,
                                                                            remove_polynomial=5, apodization_type=apodization_type,
                                                                            zero_fill=True, quick_plot=False)
        fft_freq_vector, fft_vector, fft_psd_vector = self.ftsy_manual_fourier_transform(efficiency_vector, mirror_interval, quick_plot=quick_plot)
        phase_corrected_fft_vector = fft_vector
        #self.ftsy_phase_correct_data(efficiency_vector, fft_vector, quick_plot=False)
        quick_plot = False
        if quick_plot:
            pl.plot(fft_vector, label='unphase corrected')
            pl.plot(phase_corrected_fft_vector, label='phase corrected')
            pl.legend()
            pl.show()
        return fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector

    def ftsy_compute_delta_power_and_bandwidth_at_window(self, frequency_vector, normalized_transmission_vector,
                                                         data_clip_lo=0, data_clip_hi=600,
                                                         t_source_low=77, t_source_high=300,
                                                         boltzmann_constant=1.38e-23):
        '''
        '''
        integrated_bandwidth = self.ftsy_integrate_spectra_bandwidth(frequency_vector, normalized_transmission_vector,
                                                                     data_clip_lo=data_clip_lo, data_clip_hi=data_clip_hi)
        delta_power = boltzmann_constant * (t_source_high - t_source_low) * integrated_bandwidth  # in W
        return delta_power, integrated_bandwidth

    def ftsy_integrate_spectra_bandwidth(self, frequency_vector, normalized_transmission_vector, data_clip_lo=0, data_clip_hi=600):
        '''
        '''
        selector = np.logical_and(np.where(frequency_vector > data_clip_lo, True, False), np.where(frequency_vector < data_clip_hi, True, False))
        integrated_bandwidth = np.trapz(normalized_transmission_vector[selector], frequency_vector[selector])
        return integrated_bandwidth

    def ftsy_running_mean(self, vector, smoothing_factor=0.01):
        '''
        '''
        if smoothing_factor == 0.0:
            return vector
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

    def ftsy_find_if_zero(self, y_data):
        '''
        '''
        zero_index = np.where(y_data == np.max(y_data))[0][0]
        return zero_index

    def ftsy_symmeterize_interferogram(self, x_data, y_data, copy_left=True, steps_per_in=1e-5):
        '''
        '''
        zero_index = self.ftsy_find_if_zero(y_data)
        interval = np.abs(x_data[-2] - x_data[-1])
        if copy_left:
            half_x_data = x_data[zero_index: -1]
            half_y_data = y_data[zero_index: -1]
        sym_y_data = self.ftsy_make_data_symmetric(half_y_data, is_right=True)
        size = int(len(sym_y_data) / 2)
        sym_x_data = np.arange(-size, size + 1, 1) * interval * steps_per_in
        return sym_x_data, sym_y_data

    def ftsy_make_data_symmetric(self, data, is_right=True, position=False):
        '''
        '''
        if is_right:
            left_data = data[::-1]
            right_data = data
        else:
            right_data = data[::-1]
            left_data = data
        if position:
            left_data = left_data * -1
        full_array = np.append(left_data, right_data[1:])
        return full_array

    def ftsy_split_data_into_left_right_points(self, position_vector, efficiency_vector):
        '''
        '''
        print(position_vector, efficiency_vector)
        efficiency_left_data = efficiency_vector[position_vector < 0]
        efficiency_right_data = efficiency_vector[position_vector >= 0]
        position_left_data = position_vector[position_vector < 0]
        position_right_data = position_vector[position_vector >= 0]
        return efficiency_left_data, efficiency_right_data, position_left_data, position_right_data

    def ftsy_remove_polynomial(self, data, n=1, return_fit=False):
        '''
        Removes an nth order poly nomial
        Inputs:
            data: to remvoe polynomial
            n: order of polynomial to remove (default n=1)
            return_fit: Return fit values
        Outputs:
            data_with_first_order_poly_removed
        '''
        x_vector = np.arange(data.size)
        fit_vals = np.polyfit(x_vector, data, n)
        poly_fit = np.polyval(fit_vals, x_vector)
        poly_subtracted = data - poly_fit
        return poly_subtracted

    def ftsy_phase_correct_data(self, efficiency_data, fft_vector, quick_plot=False):
        '''
        https://github.com/larsyunker/FTIR-python-tools/blob/master/FTIR.py
        '''
        try:
            center_burst = self.extract_center_burst(efficiency_data)
            rotated_center_burst = self.rotate_if_data(center_burst)
            phase_correction_fft_vector = np.fft.fft(rotated_center_burst)
            phase_vector = np.arctan(phase_correction_fft_vector.imag/phase_correction_fft_vector.real)
            phase_vector = np.interp(np.arange(len(fft_vector)), np.linspace(0, len(fft_vector), len(phase_vector)), phase_vector)
            phase_corrected_fft_vector = fft_vector * np.exp(-np.complex(0,1) * phase_vector).real
        except IndexError:
            phase_corrected_fft_vector = fft_vector
        if (phase_corrected_fft_vector == np.nan).any():
            print('post phase correct with catch')
            #import ipdb;ipdb.set_trace()
        print('post phase correct')
        #import ipdb;ipdb.set_trace()
        if quick_plot:
            #pl.plot(phase_vector, label='phase vector')
            pl.plot(center_burst)
            #pl.plot(phase_corrected_fft_vector.real, label='phase corrected real')
            #pl.plot(phase_corrected_fft_vector.imag, label='phase corrected imag')
            #pl.plot(np.abs(phase_corrected_fft_vector) **2, label='psd')
            pl.legend()
            pl.show()
        return phase_corrected_fft_vector

    def ftsy_zero_fill_position_vector(self, position_vector, next_power_of_two=None):
        if next_power_of_two is None:
            next_power_of_two = self.ftsy_next_power_of_two(len(position_vector))
        zeros_to_pad = int(next_power_of_two - len(position_vector) / 2)
        #import ipdb;ipdb.set_trace()
        interval = position_vector[1] - position_vector[0]
        zero_left_positions = np.arange(position_vector[0] - (zeros_to_pad + 1) * interval, position_vector[0], interval)
        zero_right_positions = np.arange(position_vector[-1] + interval, position_vector[-1] + zeros_to_pad * interval, interval)
        # Add right then left
        zero_filled_position_vector = np.insert(position_vector, len(position_vector), zero_right_positions)
        zero_filled_position_vector = np.insert(zero_filled_position_vector, 0, zero_left_positions)
        #print(len(apodized_efficiency_vector))
        quick_plot = False
        if quick_plot:
            pl.plot(dog, color='r', label='before zero fill')
            pl.plot(apodized_efficiency_vector, color='b', label='after zero fill')
            pl.legend()
            pl.show()
        return zero_filled_position_vector

    def ftsy_zero_fill(self, apodized_efficiency_vector, next_power_of_two=None):
        if next_power_of_two is None:
            next_power_of_two = self.ftsy_next_power_of_two(len(apodized_efficiency_vector))
        dog = copy(apodized_efficiency_vector)
        #print(len(apodized_efficiency_vector))
        zeros_to_pad = int(next_power_of_two - len(apodized_efficiency_vector) / 2)
        apodized_efficiency_vector = np.insert(apodized_efficiency_vector, len(apodized_efficiency_vector), np.zeros(zeros_to_pad))
        apodized_efficiency_vector = np.insert(apodized_efficiency_vector, 0, np.zeros(zeros_to_pad))
        #print(len(apodized_efficiency_vector))
        quick_plot = False
        if quick_plot:
            pl.plot(dog, color='r', label='before zero fill')
            pl.plot(apodized_efficiency_vector, color='b', label='after zero fill')
            pl.legend()
            pl.show()
        return apodized_efficiency_vector

    def ftsy_extract_center_burst(self, apodized_efficiency_vector, symmetric=True, quick_plot=False):
        '''
        Takes data between the last data point to be 0.3 max signal
        '''
        start_of_center_burst_index = np.where(np.abs(apodized_efficiency_vector) > 0.8)[-1][0]
        end_of_center_burst_index = np.where(np.abs(apodized_efficiency_vector) > 0.8)[-1][-1]
        #pl.plot(np.abs(apodized_efficiency_vector))
        #pl.show()
        #import ipdb;ipdb.set_trace()
        center_burst = np.zeros(len(apodized_efficiency_vector))
        if symmetric:
            start = int(len(apodized_efficiency_vector) / 2) - end_of_center_burst_index
            end = int(len(apodized_efficiency_vector) / 2) + end_of_center_burst_index
            print(start, end)
            center_burst = apodized_efficiency_vector[start_of_center_burst_index:end_of_center_burst_index]
        else:
            center_burst = apodized_efficiency_vector[0:end_of_center_burst_index]
        center_burst = self.zero_fill(center_burst, next_power_of_two=2049)
        if quick_plot:
            print(end_of_center_burst_index, len(apodized_efficiency_vector), symmetric)
            pl.plot(apodized_efficiency_vector, label='input')
            pl.plot(center_burst, label='center')
            pl.legend()
            pl.show()
        return center_burst

    def ftsy_rotate_if_data(self, apodized_efficiency_vector, quick_plot=False):
        '''
        put the right half at begining of array and left half at end of the array
        '''
        rotated_array = np.asarray([])
        mid_point = int(len(apodized_efficiency_vector) / 2)
        rotated_array = np.insert(rotated_array, 0, apodized_efficiency_vector[mid_point:-1])
        rotated_array = np.insert(rotated_array, -1, apodized_efficiency_vector[:mid_point])
        if quick_plot:
            pl.plot(apodized_efficiency_vector, label='input')
            pl.plot(rotated_arary, label='rotated')
            pl.show()
        return rotated_array

    def ftsy_prepare_data_for_fft(self, efficiency_vector, position_vector,
                                  remove_polynomial=1, apodization_type='TRIANGULAR',
                                  zero_fill=True, quick_plot=False):
        '''
        This function will apply a window function to the data
        Inputs:
            - postion_vector:  position vector (in mm) (assumed to be symmetric about 0)
            - efficiency_data:  efficiency data to be apodized
        Notes: Following this prescription: https://www.essentialftir.com/fftTutorial.html, apodization is before
        '''
        # Subtract polynomial First
        if remove_polynomial is not None:
            apodized_efficiency_vector = self.ftsy_remove_polynomial(efficiency_vector, n=remove_polynomial)
        # Apply the window function
        if apodization_type is not None:
            N = apodized_efficiency_vector.size
            if apodization_type in ('TRIANGULAR', 'Triangular'):
                apodization_function = 'triang'
            elif apodization_type in ('BOXCAR', 'Boxcar'):
                apodization_function = 'boxcar'
            else:
                apodization_function = 'boxcar'
            window_function = getattr(scipy.signal.windows, apodization_function)(N) / np.max(apodized_efficiency_vector)
            apodized_efficiency_vector = np.max(efficiency_vector) * window_function * apodized_efficiency_vector
        # Zero-fill the FFT to the nearest next largest power of 2
        if zero_fill:
            apodized_efficiency_vector = self.ftsy_zero_fill(apodized_efficiency_vector)
            position_vector = self.ftsy_zero_fill_position_vector(position_vector)
        quick_plot= False
        if quick_plot:
            pl.plot(position_vector, apodized_efficiency_vector, label='after')
            pl.legend()
            pl.show()
        return apodized_efficiency_vector, position_vector

    def ftsy_next_power_of_two(self, length):
        '''
        '''
        return 1 if length == 0 else 2**(length - 1).bit_length()

    def ftsy_compute_fourier_transform_new(self, position_vector, efficiency_data, distance_per_step, mirror_interval, quick_plot=False):
        '''
        '''
        print()
        print()
        print('position_vector')
        print(position_vector)
        print('efficiency_data')
        print(efficiency_data)
        print('mirror_interval')
        print(mirror_interval)
        print('distance_per_step')
        print(distance_per_step)
        print()
        print()
        return position_vector, efficiency_data

    def ftsy_manual_fourier_transform(self, efficiency_vector, mirror_interval,
                                      distance_per_point=250.39, speed_of_light=2.998e8, quick_plot=False):
        '''
        '''
        fft_vector = np.fft.fft(efficiency_vector)
        fft_psd_vector = np.abs(fft_vector) ** 2
        # convert to m then divide by speed of light to get lambda, 2 is nyquist sampling
        print(type(mirror_interval))
        resolution = 2 * float(mirror_interval) * distance_per_point * 1e-9 / speed_of_light
        fft_freq_vector = np.fft.fftfreq(fft_psd_vector.size, resolution)
        if quick_plot:
            pos_freq_selector = fft_freq_vector > 0
            pl.plot(fft_freq_vector[pos_freq_selector] * 1e-9, fft_psd_vector[pos_freq_selector])
            pl.show()
            pl.plot(fft_freq_vector[pos_freq_selector] * 1e-9, fft_vector[pos_freq_selector].real)
            pl.show()
        return fft_freq_vector, fft_vector, fft_psd_vector

    def ftsy_compute_fourier_transform(self, position_vector, efficiency_vector, distance_per_step, mirror_interval, quick_plot=False):
        '''
        '''
        N = efficiency_vector.size
        total_steps = int(np.max(position_vector) - np.min(position_vector))
        total_distance = total_steps * distance_per_step
        resolution = ((3 * 10 ** 8) / total_distance) # Hz
        resolution = float(mirror_interval) * distance_per_step / (10 ** 12)
        print(resolution)
        print(resolution)
        print(resolution)
        fft_freq_vector, fft_psd, normalized_fft_psd = self.manual_fourier_transform(apodized_efficiency_vector, resolution)
        print(np.min(fft_freq_vector))
        print(np.max(fft_freq_vector))
        if quick_plot:
            fig = pl.figure(figsize=(10, 5))
            fig.subplots_adjust(bottom=0.15, top =0.96, left=0.13, right=0.68, hspace=0.44)
            ax1 = fig.add_subplot(211)
            ax2 = fig.add_subplot(212)
            pos_freq_selector = np.where(fft_freq_vector > 0)
            ax1.plot(fft_freq_vector[pos_freq_selector], normalized_fft_psd[pos_freq_selector], label='Spectra')
            ax2.plot(position_vector, apodized_efficiency_vector, label='IF Data')
            ax1.set_xlabel('Frequency (GHz)', fontsize=16)
            ax1.set_ylabel('Normalized \n efficiency', fontsize=16)
            ax2.set_xlabel('X position (mm)', fontsize=16)
            ax2.set_ylabel('efficiency', fontsize=16)
            ax1.tick_params(labelsize=12)
            for axis in fig.get_axes():
                handles, labels = axis.get_legend_handles_labels()
                axis.legend(handles, labels, numpoints=1, loc=2, bbox_to_anchor=(1.01, 1.0))
            fig.savefig('temp_fft.png')
            pl.show()
        return fft_freq_vector, fft_vector


    def ftys_top_hat(self, t, x_l=0000000, x_h=20000000):
        t
        s = []
        for pos in t:
            if x_l < pos < x_h:
                s.append(1)
            else:
                s.append(0)
        return np.asarray(s)

    def ftys_simulated_if(self):
        if_vector = []
        with open('sample_if.if', 'r') as fh:
            for line in fh.readlines():
                val = line.replace('\n','')
                if_vector.append(val)
        if_vector = np.asarray(if_vector)
        return if_vector

    def ftys_actual_if_data(self):
        with open('./Data/2019_04_26/SQ6_13-35-Wit-S3-150B_MedRes_16.if', 'r') as fh:
            for line in fh.readlines():
                val = line.replace('\n','')
                if_vector.append(val)
        return if_vector

    def ftys_run_test(self, data_points=700, mirror_interval=500, spacing=10.39):
        '''
        Special Notes: For real number inputs is n the complex conjugate of N - n.
        '''
        sampling_interval = 500 * 250.39
        t = np.linspace(0, sampling_interval * data_points, data_points)
        t = np.linspace(-sampling_interval * data_points / 2, sampling_interval * data_points / 2, data_points)
        s1 = np.sin(40 * 2 * np.pi * t) + 0.5 * np.sin(90 * 2 * np.pi * t)
        #s = self.top_hat(t)
        #s = self.simulated_if()
        s = self.actual_if_data()
        s1 = np.sinc(t - 20000000)
        s1 = 0
        #s = np.sinc(t)
        #s = s1 + s2
        #s = s ** 2
        fft = np.fft.fft(s)
        for i in range(2):
            print("Value at index {}:\t{}".format(i, fft[i + 1]), "\nValue at index {}:\t{}".format(fft.size -1 - i, fft[-1 - i]))
        fig = pl.figure(figsize=(10, 5))
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)
        ax1.plot(s)
        T = t[1] - t[0]  # sampling interval 
        N = s.size
        f = np.linspace(0, 1 / T, N) # 1/T = frequency
        with open('inverse.if', 'w') as fh:
            for val in fft[:N // 2]:
                fh.write('{0}\n'.format(val))
        ax2.plot(f[:N // 2], np.abs(fft)[:N //2] * 1 / N)
        #ax2.plot(f[:N // 2], fft[:N //2] * 1 / N)
        fig.show()
        self._ask_user_if_they_want_to_quit()



class BeamSplitter():

    def __init__(self):
        self.msg = 'dog are cool'
        self.fts = FourierTransformSpectroscopy()

    def load_example(self, example_path):
        example_frequency_vector = []
        example_efficiency_vector = []
        with open(example_path, 'r') as file_handle:
            for line in file_handle.readlines():
                example_frequency = float(line.split('\t')[0])
                example_efficiency = float(line.split('\t')[1])
                example_frequency_vector.append(example_frequency)
                example_efficiency_vector.append(example_efficiency)
        return np.asarray(example_frequency_vector), np.asarray(example_efficiency_vector)

    def create_beam_splitter_response(self, save_path, thickness, index=1.83):
        '''
        This makes an analytic calculation of a beam splitters response
        from 1 to 1000 GHz with 0.1 GHz resolution.
        Inputs:
            save_path: the path to save the output too
            thickness: the thickness of a beam splitter with index=index (in mils)
            index: the index of refraction of the beam splitter
        Outputs:
            beam_splitter_response vector: the response of a beam splitter with thickness=thickness
        '''
        frequency_vector = np.arange(0, 1.5e12, 10e6)
        thickness = 2.54e-5 * thickness  # from mils to m
        print('Mylar beam splitter (n={0}) thickness {1} in meters'.format(index, thickness))
        reflectivity = ((index - 1) / (index + 1)) ** 2
        c = 2.99792458e8  # m / s 
        efficiency_vector = np.zeros(frequency_vector.size)
        with open(save_path, 'w') as file_handle:
            for i, frequency in enumerate(frequency_vector):
                inv_lambda = frequency / c
                index_term = np.sqrt(index ** 2 - 1./2.)
                cosine_argument = 2 * np.pi * (inv_lambda * thickness * index_term + 1./4.)
                efficiency_val = 8 * (1 - reflectivity) ** 2 * reflectivity * (np.cos(cosine_argument)) ** 2
                np.put(efficiency_vector, i, efficiency_val)
        return frequency_vector, efficiency_vector

    def plot_beam_splitter_efficiency(self, frequency_vector, efficiency_vector, thickness):
        pl.plot(frequency_vector, efficiency_vector, '-', label='{0} mil'.format(thickness))
        pl.xlabel('Frequency [GHz]')
        pl.ylabel('Efficiency')
        pl.title('BeamSplitter')
        #pl.xlim
        #pl.show()

    def save_beam_splitter_efficiency(self, frequency_vector, efficiency_vector, thickness):
        '''
        This funciton saves the beamsplitter data to a ./Output/{0}_mil_beamsplitter_efficiency.dat
        Inputs:
            frequency_vector: as returned by create_beams_splitter_efficiency_data
            efficiency_vector: as returned by create_beams_splitter_efficiency_data
        Outputs:
            None
        '''
        if 'bd_lib' in os.listdir('.'):
            save_path = os.path.join('bd_lib', 'optical_elements', '{0}_mil_beamsplitter_efficiency.dat'.format(thickness))
        else:
            save_path = os.path.join('optical_elements', '{0}_mil_beamsplitter_efficiency.dat'.format(thickness))
        with open(save_path, 'w') as file_handle:
            for i, frequency in enumerate(frequency_vector):
                efficiency = efficiency_vector[i]
                line = '{0},{1}\n'.format(float(frequency), float(efficiency))
                file_handle.write(line)
        return None

    def run(self, plot_data=True, save_data=True, plot_example=False):
        '''
        A simple run/test option
        '''
        thicknesses = [5, 10, 45, 55, 65]
        thicknesses = range(5, 100, 1)
        for thickness in thicknesses:
            if 'bd_lib' in os.listdir('.'):
                save_path = os.path.join('bd_lib', 'optical_elements', '{0}_mil_beamsplitter_efficiency.dat'.format(thickness))
            else:
                save_path = os.path.join('optical_elements', '{0}_mil_beamsplitter_efficiency.dat'.format(thickness))
            frequency_vector, efficiency_vector = self.create_beam_splitter_response(save_path, thickness)
            if save_data:
                print('saving')
                self.save_beam_splitter_efficiency(frequency_vector / 1e9, efficiency_vector, thickness)
            if plot_data:
                self.plot_beam_splitter_efficiency(frequency_vector / 1e9, efficiency_vector, thickness)
        #freq, band = self.fts.ftsy_load_simulated_band(0, 100e9, 'SO30')
        #print(freq, band)
        #pl.plot(freq, band, label='SO40')
        #freq, band = self.fts.ftsy_load_simulated_band(0, 100e9, 'SO40')
        print(freq, band)
        #pl.plot(freq, band, label='SO40')
        #pl.xlim((0, 100))
        #pl.legend(loc='best')
        ##pl.show()

if __name__ == '__main__':
    ftsy = FourierTransformSpectroscopy()
    band = 'SO40'
    data_clip_lo = 0
    data_clip_hi = 80 * 1e9
    t_source_low = 9
    t_source_high = 14
    fft_frequency_vector_simulated, fft_vector_simulated = ftsy.ftsy_load_simulated_band(data_clip_lo, data_clip_hi, band)
    simulated_delta_power, simulated_integrated_bandwidth = ftsy.ftsy_compute_delta_power_and_bandwidth_at_window(fft_frequency_vector_simulated * 1e9, fft_vector_simulated,
                                                                                                                  data_clip_lo=data_clip_lo, data_clip_hi=data_clip_hi,
                                                                                                                  t_source_low=t_source_low, t_source_high=t_source_high)
    label = 'Chop {0:.2f}K to {1:.1f}K\n{2:.2f}pW {3:.2f}GHz'.format(t_source_low, t_source_high, simulated_delta_power * 1e12, simulated_integrated_bandwidth * 1e-9)
    title = 'Band pass and Power for {0} {1}K to {2}K'.format(band, t_source_low, t_source_high)
    pl.plot(fft_frequency_vector_simulated, fft_vector_simulated, label=label)
    pl.title(title)
    pl.legend()
    pl.show()
    #fourier = Fourier()
    #fourier.run_test()
