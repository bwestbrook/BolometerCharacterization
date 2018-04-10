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

    def convert_IF_to_FFT_data(self, position_vector, efficiency_vector, scan_param_dict, quick_plot=True):
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
        step_size =float(scan_param_dict['measurements']['step_size'])
        steps_per_point = int(scan_param_dict['measurements']['steps_per_point'])
        position_vector = np.asarray(position_vector)
        efficiency_vector = np.asarray(efficiency_vector)
        efficiency_left_data, efficiency_right_data, position_left_data, position_right_data =\
            self.split_data_into_left_right_points(position_vector, efficiency_vector)
        symmetric_position_data = self.make_data_symmetric(position_right_data, position=True)
        symmetric_efficiency_data = self.make_data_symmetric(efficiency_right_data)
        poly_subtracted_data = self.remove_polynomial(symmetric_efficiency_data)
        xf = np.arange(symmetric_efficiency_data.size)
        frequency_vector, fft_vector = self.compute_fourier_transform(symmetric_position_data, poly_subtracted_data, step_size,
                                                                      steps_per_point, quick_plot=quick_plot)
        return frequency_vector, fft_vector, symmetric_position_data, poly_subtracted_data

    def split_data_into_left_right_points(self, position_vector, efficiency_vector):
        efficiency_left_data = efficiency_vector[position_vector < 0]
        efficiency_right_data = efficiency_vector[position_vector >= 0]
        poly_removed_efficiency_data = self.remove_polynomial(efficiency_right_data, n=1)
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

    def apply_window_to_data(self, position_vector, efficiency_data, apodization_type='Triangular'):
        '''
        This function will apply a window function to the data
        Inputs:
            - postion_vector:  position vector (in mm) (assumed to be symmetric about 0)
            - efficiency_data:  efficiency data to be apodized
        '''
        if apodization_type == 'Triangular':
            N = position_vector.size
            window_function = np.bartlett(N)
            apodized_efficiency_vector = window_function * efficiency_data
        return apodized_efficiency_vector

    def compute_fourier_transform(self, position_vector, efficiency_data, distance_per_step, steps_per_point, quick_plot=False):
        N = efficiency_data.size
        T = distance_per_step * steps_per_point
        x_vector = np.linspace(0.0, N * T, N)
        frequency_vector = np.linspace(0.0, 1.0 / (2 * np.pi * T), N / 2)
        # some important factors
        print
        print
        print 'FFT Setup'
        print 'real distance per point is {0} nm ({1} m)'.format(T, T * 1e-9)
        print 'number of points in data is {0}'.format(N)
        print
        print
        frequency_vector = frequency_vector * 3e8
        apodized_efficiency_vector = self.apply_window_to_data(position_vector, efficiency_data)
        fft_vector = scipy.fftpack.rfft(apodized_efficiency_vector)
        normalized_fft_vector = (2.0 / N) * np.abs(fft_vector[0: N / 2])
        peak_normalized_fft_vector = normalized_fft_vector / np.max(normalized_fft_vector)
        # Plot the fourier transform
        if quick_plot:
            fig = pl.figure(figsize=(10, 5))
            fig.subplots_adjust(bottom=0.15, top =0.96, left=0.13, right=0.68, hspace=0.44)
            ax1 = fig.add_subplot(211)
            ax2 = fig.add_subplot(212)
            ax1.plot(frequency_vector / 1e9, peak_normalized_fft_vector, label='Spectra')
            ax2.plot(position_vector, efficiency_data, label='IF Data')
            ax1.set_xlabel('Frequency (GHz)', fontsize=16)
            ax1.set_ylabel('Normalized \n efficiency', fontsize=16)
            ax2.set_xlabel('X position (mm)', fontsize=16)
            ax2.set_ylabel('efficiency', fontsize=16)
            ax1.tick_params(labelsize=12)
            for axis in fig.get_axes():
                handles, labels = axis.get_legend_handles_labels()
                axis.legend(handles, labels, numpoints=1, loc=2, bbox_to_anchor=(1.01, 1.0))
            fig.savefig('temp_fft.png')
        return frequency_vector, peak_normalized_fft_vector

    def run_test(self, data_points=1000, spacing=150.):
        N = data_points
        T = spacing
        # Based on the sample spacing and the number of points build a frequency vector 
        x_vector = np.linspace(0.0, N * T, N)
        frequency_vector = np.linspace(0.0, 1.0 / (2.0 * T), N / 2)
        # Create Some Test Data 
        y_vector = np.sin(x_vector)
        # Compute the FFT of the test data
        fft_vector = scipy.fftpack.fft(y_vector)
        normalized_fft_vector = (2.0 / N) * np.abs(fft_vector[0: N / 2])
        # Create the figure and plot the data
        fig = pl.figure(figsize=(10, 5))
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)
        ax1.plot(x_vector, y_vector)
        ax2.plot(frequency_vector, normalized_fft_vector)
        fig.show()
        self._ask_user_if_they_want_to_quit()


    def _ask_user_if_they_want_to_quit(self):
        '''
        A simple method to stop the code without setting a trace with the option of quittting
        '''
        quit_boolean = raw_input('Press q to q(uit), any other key to continue:\n')
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
        print 'Mylar beam splitter (n={0}) thickness {1} in meters'.format(index, thickness)
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
            print 'saving'
            self.save_beam_splitter_efficiency(frequency_vector / 1e9, efficiency_vector, thickness)
        if plot_data:
            self.plot_beam_splitter_efficiency(frequency_vector / 1e9, efficiency_vector, thickness)


if __name__ == '__main__':
    bs = BeamSplitter()
    bs.run()
    #fourier = Fourier()
    #fourier.run_test()
