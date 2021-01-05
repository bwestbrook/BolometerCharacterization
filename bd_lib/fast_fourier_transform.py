import os
import numpy as np
import pylab as pl
import scipy.fftpack
from pprint import pprint
from copy import copy, deepcopy
from scipy.signal import blackman, hanning

class FastFourierTransform():

    def __init__(self):
        '''
        '''
        self.dog = 'dog'

    def fast_fourier_transform(self, vector, resolution, quick_plot=False):
        '''
        '''
        #vector = [np.sin(3*x) for x in range(1000)]
        fft_vector = np.fft.rfft(vector)
        fft_psd_vector = np.abs(fft_vector) ** 2
        fft_freq_vector = np.fft.fftfreq(fft_psd_vector.size, resolution)
        print()
        print()
        print(max(fft_freq_vector), resolution)
        if quick_plot:
            pos_freq_selector = fft_freq_vector > 0
            pl.plot(fft_freq_vector[pos_freq_selector] * 1e-9, fft_psd_vector[pos_freq_selector])
            pl.show()
            pl.plot(fft_freq_vector[pos_freq_selector] * 1e-9, fft_vector[pos_freq_selector].real)
            pl.show()
        return fft_freq_vector, fft_vector, fft_psd_vector

    def compute_fourier_transform(self, position_vector, efficiency_vector, distance_per_step, mirror_interval, quick_plot=False):
        '''
        '''
        fft_freq_vector, fft_psd, normalized_fft_psd = self.manual_fourier_transform(apodized_efficiency_vector, resolution)
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
