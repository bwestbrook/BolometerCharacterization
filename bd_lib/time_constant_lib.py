import pylab as pl
import numpy as np
import sys
from pprint import pprint
from scipy.optimize import leastsq, curve_fit

class TimeConstantLib():

    def __init__(self):
        '''
        '''
        self.hi = 'hi'

    def tcl_get_3db_point(self, freq_vector, amp_vector):
        '''
        '''
        amp_vector = np.asarray(amp_vector)
        freq_vector = np.asarray(freq_vector)
        three_3b_value = np.max(amp_vector) / np.sqrt(2.0)
        idx = (np.abs(amp_vector - three_3b_value)).argmin()
        tau_in_hertz = freq_vector[idx]
        tau_in_ms = 1.e3 / tau_in_hertz
        return freq_vector, amp_vector, tau_in_hertz, tau_in_ms, idx

    def tcl_arb_single_pol(self, omega_0):
        '''
        '''
        def tcl_arb_roll_off(x):
            value = np.sqrt(1.0 / (1 + (x / omega_0)^2))
            return value
        return tcl_arb_roll_off

    def tcl_test_single_pol(self, x_val, amp_0, f_0):
        '''
        '''
        amp = amp_0 * np.sqrt(1.0 / (1 + (x_val / f_0) ** 2))
        return amp

    def tcl_fit_single_pol(self, freq_vector, amp_vector, fit_params):
        '''
        '''
        if len(freq_vector) <= 1:
            return None
        else:
            fit_params = curve_fit(self.test_single_pol, freq_vector, amp_vector, p0=fit_params)
            return fit_params[0]

    def tcl_plot(self, freq_vector, amp_vector, error_vector, idx, fig=None, ax=None,
                 tau_in_hertz='', color='', label=''):
        '''
        '''
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
