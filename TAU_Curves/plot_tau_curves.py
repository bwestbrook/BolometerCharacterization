import pylab as pl
import numpy as np
import sys

class TAUCurves():

    def __init__(self):
        self.hi = 'hi'

    def load(self, path):
        with open(path, 'r') as fh:
            freq_vector, amp_vector, error_vector = [],[],[]
            for line in fh.readlines():
                split_line = line.split('\t')
                freq = float(split_line[0])
                amp = float(split_line[1])
                error = float(split_line[2].replace('\n', ''))
                print freq, amp, error
                freq_vector.append(freq)
                amp_vector.append(amp)
                error_vector.append(error)
        return freq_vector, amp_vector, error_vector

    def get_3db_point(self, freq_vector, amp_vector):
        amp_vector = np.asarray(amp_vector)
        freq_vector = np.asarray(freq_vector)
        three_3b_value = np.max(amp_vector) / 2.0
        idx = (np.abs(amp_vector - three_3b_value)).argmin()
        tau_in_hertz = freq_vector[idx]
        tau_in_ms = 1.0e3 / tau_in_hertz
        #import ipdb;ipdb.set_trace()
        return freq_vector, amp_vector, tau_in_hertz, tau_in_ms

    def plot(self, freq_vector, amp_vector, error_vector, tau_in_hertz='', color='', label=''):
        print amp_vector[0] / 2.0
        tau_in_ms = '{0:.3f} ms'.format(1.0e3 / tau_in_hertz)
        label += ' {0} Hz {1}'.format(tau_in_hertz, tau_in_ms)
        pl.semilogx(freq_vector, amp_vector / amp_vector[0], color=color)
        pl.errorbar(freq_vector, amp_vector / amp_vector[0], yerr=error_vector, label=label, color=color)
        title = 'V14-02 270GHz witness Tau data'
        pl.axvline(tau_in_hertz, color=color, alpha=0.5, lw=2)
        pl.xlabel('Modulation Frequency (Hz)')
        pl.ylabel('Normalized Amplitude')
        pl.title(title)
        pl.legend()

if __name__ == '__main__':
    path_1 = sys.argv[1]
    label_1 = sys.argv[2]
    path_2 = sys.argv[3]
    label_2 = sys.argv[4]
    path_3 = sys.argv[5]
    label_3 = sys.argv[6]
    freq_vector, amp_vector, error_vector = load(path_1)
    freq_vector, amp_vector, tau_in_hertz, tau_in_ms = get_3db_point(freq_vector, amp_vector)
    plot(freq_vector, amp_vector, error_vector, tau_in_hertz=tau_in_hertz, label=label_1, color='r')
    freq_vector_2, amp_vector_2, error_vector_2 = load(path_2)
    freq_vector_2, amp_vector_2, tau_in_hertz_2, tau_in_ms_2 = get_3db_point(freq_vector_2, amp_vector_2)
    plot(freq_vector_2, amp_vector_2, error_vector_2, tau_in_hertz=tau_in_hertz_2, label=label_2, color='b')
    freq_vector_3, amp_vector_3, error_vector_3 = load(path_3)
    freq_vector_3, amp_vector_3, tau_in_hertz_3, tau_in_ms_3 = get_3db_point(freq_vector_3, amp_vector_3)
    plot(freq_vector_3, amp_vector_3, error_vector_3, tau_in_hertz=tau_in_hertz_3, label=label_3, color='g')
    pl.show()
