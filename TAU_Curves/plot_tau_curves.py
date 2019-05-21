import pylab as pl
import numpy as np
import sys
from pprint import pprint
from scipy.optimize import leastsq, curve_fit

class TAUCurve():

    def __init__(self, list_of_input_dicts):
        self.hi = 'hi'
        self.input_dicts = list_of_input_dicts

    def load(self, path):
        with open(path, 'r') as fh:
            freq_vector, amp_vector, error_vector = [],[],[]
            for line in fh.readlines():
                split_line = line.split('\t')
                freq = float(split_line[0])
                amp = float(split_line[1])
                error = float(split_line[2].replace('\n', ''))
                print(freq, amp, error)
                freq_vector.append(freq)
                amp_vector.append(amp)
                error_vector.append(error)
        return freq_vector, amp_vector, error_vector

    def get_3db_point(self, freq_vector, amp_vector):
        amp_vector = np.asarray(amp_vector)
        freq_vector = np.asarray(freq_vector)
        three_3b_value = np.max(amp_vector) / np.sqrt(2.0)
        idx = (np.abs(amp_vector - three_3b_value)).argmin()
        tau_in_hertz = freq_vector[idx]
        tau_in_ms = 1.e3 / tau_in_hertz
        return freq_vector, amp_vector, tau_in_hertz, tau_in_ms, idx

    def arb_single_pol(self, omega_0):
        def arb_roll_off(x):
            value = np.sqrt(1.0 / (1 + (x / omega_0)^2))
            return value
        return arb_roll_off

    def test_single_pol(self, x_val, amp_0, f_0):
        amp = amp_0 * np.sqrt(1.0 / (1 + (x_val / f_0) ** 2))
        return amp

    def fit_single_pol(self, freq_vector, amp_vector, fit_params):
        if len(freq_vector) <= 1:
            return None
        else:
            fit_params = curve_fit(self.test_single_pol, freq_vector, amp_vector, p0=fit_params)
            return fit_params[0]

    def plot(self, freq_vector, amp_vector, error_vector, idx, fig=None, ax=None,
             tau_in_hertz='', color='', label=''):
        if fig is None and ax is None:
            pl.semilogx(freq_vector, amp_vector / amp_vector[0], color='w', linestyle='None')
            pl.errorbar(freq_vector, amp_vector / amp_vector[0], yerr=error_vector / amp_vector[0], label=label,
                        marker='o', ms=5.0, linestyle='None', color=color)
            pl.xlabel('Modulation Frequency (Hz)')
            pl.ylabel('Normalized Amplitude')
        else:
            ax.semilogx(freq_vector, amp_vector / amp_vector[0], color='w', linestyle='None')
            ax.errorbar(freq_vector, amp_vector / amp_vector[0], yerr=error_vector / amp_vector[0], label=label,
                        marker='o', ms=5.0, linestyle='None', color=color)
            ax.set_xlabel('Modulation Frequency (Hz)')
            ax.set_ylabel('Normalized Amplitude')
        return fig, ax

    def run(self):
        for input_dict in self.input_dicts:
            title = input_dict['title']
            freq_vector, amp_vector, error_vector = self.load(input_dict['data_path'])
            freq_vector, amp_vector, tau_in_hertz, tau_in_ms, idx = self.get_3db_point(freq_vector, amp_vector)
            label = 'Data'
            color = input_dict['color']
            self.plot(freq_vector, amp_vector, error_vector, idx,
                      tau_in_hertz=tau_in_hertz, color=color)
            f_0_guess = tau_in_hertz
            amp_0_guess = 1.0
            fit_params = self.fit_single_pol(freq_vector, amp_vector / amp_vector[0],
                                             fit_params=[amp_0_guess, f_0_guess])
            test_freq_vector = np.arange(1.0, 250, 0.1)
            fit_amp = self.test_single_pol(test_freq_vector, fit_params[0], fit_params[1])
            fit_3db_data = self.get_3db_point(test_freq_vector, fit_amp)
            fit_3db_point_hz = fit_3db_data[2]
            fit_3db_point = 1e3 / (2 * np.pi * fit_3db_point_hz)
            fit_idx = fit_3db_data[-1]
            pl.plot(test_freq_vector[fit_idx], fit_amp[fit_idx],
                    marker='*', ms=15.0, color=color, alpha=0.5, lw=2)
            label = '$\\tau$={0:.2f} ms ({1} Hz) @ $V_b$={2} $\mu$V'.format(fit_3db_point, fit_3db_point_hz,
                                                                            input_dict['vbias'])
            pl.plot(test_freq_vector, fit_amp, color=color, alpha=0.7, label=label)
            title += '\n$\\tau$ vs $V_b$'
            pl.title(title)
            pl.ylim((0, 2.5))
            #pl.legend(bbox_to_anchor=(0.15, 0.0, 1, 1))
            pl.legend()
        pl.show()

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
