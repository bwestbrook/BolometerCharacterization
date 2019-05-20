import os
import numpy as np
import pylab as pl
import scipy.fftpack
from pprint import pprint
from copy import copy, deepcopy
from scipy.signal import blackman, hanning


class Fourier():
    '''
    This is a custom class of python function used to conver interferogram data into Spectra for bolometers
    '''
    def __init__(self):
        '''
        init for the Fourier class
        '''
        self.mesg = 'hey'

    def convert_IF_to_FFT_data(self, position_vector, efficiency_vector, scan_param_dict, data_selector='Right', quick_plot=False):
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
        if 'measurements' in scan_param_dict:
            step_size = float(scan_param_dict['measurements']['step_size'])
            steps_per_point = int(scan_param_dict['measurements']['steps_per_point'])
        else:
            step_size = float(scan_param_dict['distance_per_step'])
            steps_per_point = int(scan_param_dict['step_size'])
        position_vector = np.asarray(position_vector)
        efficiency_vector = np.asarray(efficiency_vector)
        efficiency_left_data, efficiency_right_data, position_left_data, position_right_data =\
            self.split_data_into_left_right_points(position_vector, efficiency_vector)
        if data_selector == 'All':
            efficiency_vector = efficiency_vector
            position_vector = position_vector
        elif data_selector == 'Right':
            efficiency_vector = efficiency_right_data
            position_vector = position_right_data
        elif data_selector == 'Left':
            efficiency_vector = efficiency_left_data
            position_vector = position_left_data
        efficiency_vector, position_vector = self.prepare_data_for_fft(efficiency_vector, position_vector,
                                                                       remove_polynomial=2, apodization_type='boxcar', zero_fill=True)
        fft_freq_vector, fft_vector, fft_psd_vector = self.manual_fourier_transform(efficiency_vector, step_size, steps_per_point, quick_plot=quick_plot)
        if data_selector in ('Right', 'Left'):
            phase_corrected_fft_vector = self.phase_correct_data(efficiency_vector, fft_vector, quick_plot=False)
        else:
            phase_corrected_fft_vector = fft_vector
        quick_plot = False
        if quick_plot:
            pl.plot(fft_vector, label='unphase corrected')
            pl.plot(phase_corrected_fft_vector, label='phase corrected')
            pl.legend()
            pl.show()
        return fft_freq_vector, fft_vector, phase_corrected_fft_vector, position_vector, efficiency_vector

    def split_data_into_left_right_points(self, position_vector, efficiency_vector):
        efficiency_left_data = efficiency_vector[position_vector < 0]
        efficiency_right_data = efficiency_vector[position_vector >= 0]
        position_left_data = position_vector[position_vector < 0]
        position_right_data = position_vector[position_vector >= 0]
        return efficiency_left_data, efficiency_right_data, position_left_data, position_right_data

    def make_data_symmetric(self, right_data, position=False):
        left_data = right_data[::-1]
        if position:
            left_data = left_data * -1
        full_array = np.append(left_data, right_data)
        return full_array

    def remove_polynomial(self, data, n=1, return_fit=False):
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

    def phase_correct_data(self, efficiency_data, fft_vector, quick_plot=False):
        '''
        https://github.com/larsyunker/FTIR-python-tools/blob/master/FTIR.py
        '''
        center_burst = self.extract_center_burst(efficiency_data)
        rotated_center_burst = self.rotate_if_data(center_burst)
        phase_correction_fft_vector = np.fft.fft(rotated_center_burst)
        phase_vector = np.arctan(phase_correction_fft_vector.imag/phase_correction_fft_vector.real)
        phase_vector = np.interp(np.arange(len(fft_vector)), np.linspace(0, len(fft_vector), len(phase_vector)), phase_vector)
        phase_corrected_fft_vector = fft_vector * np.exp(-np.complex(0,1) * phase_vector).real
        if quick_plot:
            #pl.plot(phase_vector, label='phase vector')
            pl.plot(center_burst)
            #pl.plot(phase_corrected_fft_vector.real, label='phase corrected real')
            #pl.plot(phase_corrected_fft_vector.imag, label='phase corrected imag')
            #pl.plot(np.abs(phase_corrected_fft_vector) **2, label='psd')
            pl.legend()
            pl.show()
        return phase_corrected_fft_vector

    def zero_fill(self, apodized_efficiency_vector, next_power_of_two=None):
        if next_power_of_two is None:
            next_power_of_two = self.next_power_of_two(len(apodized_efficiency_vector))
        zeros_to_pad = int(next_power_of_two - len(apodized_efficiency_vector) / 2)
        apodized_efficiency_vector = np.insert(apodized_efficiency_vector, -1, np.zeros(zeros_to_pad))
        apodized_efficiency_vector = np.insert(apodized_efficiency_vector, 0, np.zeros(zeros_to_pad))
        np.put(apodized_efficiency_vector, -1, 0) # errant bad values being added here)
        return apodized_efficiency_vector

    def extract_center_burst(self, apodized_efficiency_vector, symmetric=True, quick_plot=False):
        '''
        Takes data between the last data point to be 0.3 max signal
        '''
        start_of_center_burst_index = np.where(np.abs(apodized_efficiency_vector) > 0.8)[-1][0]
        end_of_center_burst_index = np.where(np.abs(apodized_efficiency_vector) > 0.8)[-1][-1]
        pl.plot(np.abs(apodized_efficiency_vector))
        pl.show()
        import ipdb;ipdb.set_trace()
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

    def rotate_if_data(self, apodized_efficiency_vector, quick_plot=False):
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

    def prepare_data_for_fft(self, efficiency_vector, position_vector,
                             remove_polynomial=None, apodization_type=None,
                             zero_fill=False, quick_plot=False):
        '''
        This function will apply a window function to the data
        Inputs:
            - postion_vector:  position vector (in mm) (assumed to be symmetric about 0)
            - efficiency_data:  efficiency data to be apodized
        Notes: Following this prescription: https://www.essentialftir.com/fftTutorial.html, apodization is before
        '''
        # Subtract polynomial First
        if remove_polynomial is not None:
            apodized_efficiency_vector = self.remove_polynomial(efficiency_vector, n=remove_polynomial)
        apodized_efficiency_vector = self.make_data_symmetric(apodized_efficiency_vector)
        position_vector = self.make_data_symmetric(position_vector, position=True)
        # Make data symmetric for the window function
        if apodization_type is not None:
            N = apodized_efficiency_vector.size
            window_function = getattr(scipy.signal.windows, apodization_type)(N) / np.max(apodized_efficiency_vector)
            apodized_efficiency_vector = window_function* apodized_efficiency_vector
        # Zero-fill the FFT to the nearest next largest power of 2
        if zero_fill:
            apodized_efficiency_vector = self.zero_fill(apodized_efficiency_vector)
            position_vector = self.zero_fill(position_vector)
        if quick_plot:
            pl.plot(position_vector, apodized_efficiency_vector)
            pl.show()
        return apodized_efficiency_vector, position_vector

    def next_power_of_two(self, length):
        return 1 if length == 0 else 2**(length - 1).bit_length()

    def compute_fourier_transform_new(self, position_vector, efficiency_data, distance_per_step, steps_per_point, quick_plot=False):
        print()
        print()
        print('position_vector')
        print(position_vector)
        print('efficiency_data')
        print(efficiency_data)
        print('steps_per_point')
        print(steps_per_point)
        print('distance_per_step')
        print(distance_per_step)
        print()
        print()
        return position_vector, efficiency_data

    def manual_fourier_transform(self, efficiency_vector, steps_per_point,
                                 distance_per_point=250.39, speed_of_light=2.998e8, quick_plot=False):
        fft_vector = np.fft.fft(efficiency_vector)
        fft_psd_vector = np.abs(fft_vector) ** 2
        # convert to m then divide by speed of light to get lambda, 2 is nyquist sampling
        resolution = 2 * steps_per_point * distance_per_point * 1e-9 / speed_of_light
        fft_freq_vector = np.fft.fftfreq(fft_psd_vector.size, resolution)
        if quick_plot:
            pos_freq_selector = fft_freq_vector > 0
            pl.plot(fft_freq_vector[pos_freq_selector] * 1e-9, fft_psd_vector[pos_freq_selector])
            pl.show()
            pl.plot(fft_freq_vector[pos_freq_selector] * 1e-9, fft_vector[pos_freq_selector].real)
            pl.show()
        return fft_freq_vector, fft_vector, fft_psd_vector

    def compute_fourier_transform(self, position_vector, efficiency_vector, distance_per_step, steps_per_point, quick_plot=False):
        N = efficiency_vector.size
        total_steps = int(np.max(position_vector) - np.min(position_vector))
        total_distance = total_steps * distance_per_step
        resolution = ((3 * 10 ** 8) / total_distance) # Hz
        resolution = steps_per_point * distance_per_step / (10 ** 12)
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


    def top_hat(self, t, x_l=0000000, x_h=20000000):
        t
        s = []
        for pos in t:
            if x_l < pos < x_h:
                s.append(1)
            else:
                s.append(0)
        return np.asarray(s)

    def simulated_if(self):
        if_vector = []
        with open('sample_if.if', 'r') as fh:
            for line in fh.readlines():
                val = line.replace('\n','')
                if_vector.append(val)
        if_vector = np.asarray(if_vector)
        return if_vector

    def actual_if_data(self):
        with open('./Data/2019_04_26/SQ6_13-35-Wit-S3-150B_MedRes_16.if', 'r') as fh:
            for line in fh.readlines():
                val = line.replace('\n','')
                if_vector.append(val)
        return if_vector

    def run_test(self, data_points=700, steps_per_point=500, spacing=10.39):
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


    def _ask_user_if_they_want_to_quit(self):
        '''
        A simple method to stop the code without setting a trace with the option of quittting
        '''
        quit_boolean = input('Press q to q(uit), any other key to continue:\n')
        if quit_boolean == 'q':
            exit()

class BeamSplitter():

    def __init__(self):
        self.msg = 'dog are cool'


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
        frequency_vector = np.arange(0, 1.5e12, 100e6)
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
        pl.plot(frequency_vector, efficiency_vector, '-r', label='{0} mil'.format(thickness))
        pl.xlabel('Frequency [GHz]')
        pl.ylabel('Efficiency')
        pl.title('BeamSplitter')
        pl.legend(loc='best')
        pl.xlim
        pl.show()

    def save_beam_splitter_efficiency(self, frequency_vector, efficiency_vector, thickness):
        '''
        This funciton saves the beamsplitter data to a ./Output/{0}_mil_beamsplitter_efficiency.dat
        Inputs:
            frequency_vector: as returned by create_beams_splitter_efficiency_data
            efficiency_vector: as returned by create_beams_splitter_efficiency_data
        Outputs:
            None
        '''
        save_path = './Output/Beam_Splitter_Efficiency/{0}_mil_beamsplitter_efficiency.dat'.format(thickness)
        with open(save_path, 'w') as file_handle:
            for i, frequency in enumerate(frequency_vector):
                efficiency = efficiency_vector[i]
                line = '{0}\t{1}\n'.format(float(frequency), float(efficiency))
                file_handle.write(line)
        return None

    def run(self, plot_data=True, save_data=True, plot_example=False):
        '''
        A simple run/test option
        '''
        thickness = 10  # mils
        save_path = './Output/temp.dat'
        if plot_example:
            example_path = './Simulations/BeamSplitter10mil.dat'
            example_frequency_vector, example_efficiency_vector = self.load_example(example_path)
            self.plot_beam_splitter_efficiency(example_frequency_vector, example_efficiency_vector, 10)
        frequency_vector, efficiency_vector = self.create_beam_splitter_response(save_path, thickness)
        if save_data:
            print('saving')
            self.save_beam_splitter_efficiency(frequency_vector / 1e9, efficiency_vector, thickness)
        if plot_data:
            self.plot_beam_splitter_efficiency(frequency_vector / 1e9, efficiency_vector, thickness)


if __name__ == '__main__':
    #bs = BeamSplitter()
    #bs.run()
    fourier = Fourier()
    fourier.run_test()
