from mpl_toolkits.mplot3d.axes3d import Axes3D
from scipy.signal import medfilt2d
from scipy.optimize import leastsq, curve_fit
import time
import matplotlib
import numpy as np
import pylab as pl
import matplotlib.cm as cm
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt


def load_pol_efficiency_data(data_path):
    with open(data_path, 'r') as file_handle:
        lines = file_handle.readlines()
        x_position_vector = np.zeros(len(lines))
        amplitude_vector = np.zeros(len(lines))
        for i, line in enumerate(lines):
            data_ = line.split('\t')
            x_position = data_[0]
            amplitude_value = data_[1]
            np.put(x_position_vector, i, x_position)
            np.put(amplitude_vector, i, amplitude_value)
    data_dict = {'x_position': x_position_vector, 'amplitude': amplitude_vector}
    return data_dict


def parse_data(data_dict):
    normalized_amplitude = data_dict['amplitude'] / np.max(data_dict['amplitude'])
    x_position_raw = data_dict['x_position']
    angle_vector = x_position_raw
    initial_fit_params = moments(normalized_amplitude)
    fit_params = fit_sine(x_position_raw, normalized_amplitude, initial_fit_params)
    initial_fit = np.zeros(len(x_position_raw))
    fit = np.zeros(len(x_position_raw))
    angle_vector = np.zeros(len(x_position_raw))
    for i, x_val in enumerate(x_position_raw):
        fit_val = test_sine(x_val, fit_params[0], fit_params[1], fit_params[2], fit_params[3])
        initial_fit_val = test_sine(x_val, initial_fit_params[0], initial_fit_params[1],
                                    initial_fit_params[2], initial_fit_params[3])
        angle_ = (x_val / fit_params[1]) * 2 * np.pi
        np.put(fit, i, fit_val)
        np.put(initial_fit, i, initial_fit_val)
        np.put(angle_vector, i, angle_)
    efficiency = (np.min(normalized_amplitude) / 1.0 ) * 100.0
    processed_data_dict = {'x_position': x_position_raw,
                           'angle_vector': np.rad2deg(angle_vector),
                           'fit': fit,
                           'initial_fit': initial_fit,
                           'normalized_amplitude': normalized_amplitude,
                           'efficiency': efficiency}
    return processed_data_dict


def plot_polarization_efficiency(data_dict, frequency, pixel, fig=None):
    # crete a figure if needed
    if fig is None:
            fig = plt.figure(figsize=(7.25,6))
    ax = fig.add_subplot(111)
    ax.tick_params(labelsize=18)
    # Create the color map
    ax.plot(data_dict['angle_vector'], data_dict['normalized_amplitude'], '-', ms=5.0, label='Data', lw=3)
    ax.plot(data_dict['angle_vector'], data_dict['fit'], label='Fit', lw=2)
    # Basic Plotting Options 
    ax.set_xlabel('Polarizing Grid Position ($^{\circ}$)', fontsize=24)
    ax.set_ylabel('Peak Normalized', fontsize=24)
    #title_str = 'Polarization Efficiency {:} GHz\n {:} Cross Pol: {:.2f}%'.format(frequency, pixel, data_dict['efficiency'])
    title_str = 'Polarization Efficiency'.format(frequency)
    ax.set_title(title_str, fontsize=24)
    ax.set_ylim([-0.05, 1.05])
    ax.set_xlim([-0., 450.])
    ax.legend(loc='lower right', numpoints=1)
    save_str = './Output/Polarization_Modulation_Efficiency_{0}_{1}_GHz.pdf'.format(pixel, frequency)
    fig.subplots_adjust(top=0.93, bottom=0.13)
    fig.savefig(save_str, pad_inches=-1)
    fig.show()
    _ask_user_if_they_want_to_quit()
    return fig


## Fitting Utilities
def arbitrary_sine(amplitude, period, y_offset):
    def arb_sine(x):
        value = amplitude*np.sin(x * period) + y_offset
        return value
    return arb_sine


def test_sine(x_val, amplitude, period, phase, y_offset):
    period = float(period)
    y_offset = float(y_offset)
    value = amplitude * np.sin((2.5 * x_val / period) * 2 * np.pi + phase) + y_offset
    return value


def moments(data):
    amplitude = (np.max(data) - np.min(data)) / 2.0
    y_offset = np.min(data) + amplitude
    period = 50000
    phase = 0.0
    return amplitude, period, phase, y_offset


def fit_sine(x_data, y_data, fit_params):
    fit_params = curve_fit(test_sine, x_data, y_data, p0=fit_params)
    return fit_params[0]


## General Utilities
def _ask_user_if_they_want_to_quit():
    input_ = raw_input('Press q to (q)uit, Any other Key to Continue')
    if input_ == 'q':
        print 'Exiting'
        exit()


def run(data_path, frequency, pixel):
    data_dict = load_pol_efficiency_data(data_path)
    processed_data_dict = parse_data(data_dict)
    fig = plot_polarization_efficiency(processed_data_dict, frequency, pixel, fig=None)


if __name__ == '__main__':
    if False:
	data_path = '../Data/2015_06_03/000_350_GHz_PolModEff.dat'
	run(data_path, 350, 'HF_Triplexer')
	data_path = '../Data/2015_06_03/002_220_GHz_PolModEff.dat'
	run(data_path, 220, 'HF_Triplexer')
	data_path = '../Data/2015_06_03/005_280_GHz_PolModEff.dat'
	run(data_path, 280, 'HF_Triplexer')
        #################################3
	data_path = '../Data/2015_06_10/005_350_GHz_PolModEff.dat'
	run(data_path, 350, 'Ds Dp')
        #################################3
	data_path = '../Data/2015_06_17/010_150_PolModEff.dat'
	run(data_path, 150, 'Tetraplexer')
	data_path = '../Data/2015_06_18/007_280_PolModEff.dat'
	run(data_path, 280, 'Tetraplexer')
	data_path = '../Data/2015_06_18/006_220_PolModEff.dat'
	run(data_path, 220, 'Tetraplexer')
	data_path = '../Data/2015_07_01/280/003_PolModEff.dat'
        run(data_path, 280, 'Tetraplexer')
	data_path = '../Data/2015_07_01/150/005_PolModEff.dat' # 3.46% for 90 GHZ tetra
        run(data_path, 150, 'Tetraplexer')
	data_path = '../Data/2015_07_01/220/002_PolModEff.dat' # 2.10% for 220 GHZ tetra
        run(data_path, 220, 'Tetraplexer')
	data_path = '../Data/2015_07_01/90/015_PolModEff.dat' # 2.81% for 90 GHZ tetra
        run(data_path, 90, 'Tetraplexer')
        #################################3
	data_path = '../Data/2015_07_01/90/015_PolModEff.dat' # 2.81% for 90 GHZ tetra
        run(data_path, 90, 'Tetraplexer')
	data_path = '../Data/2015_07_01/150/018_PolModEff.dat' # 2.13% for 150 GHZ tetra
        run(data_path, 150, 'Tetraplexer')
	data_path = '../Data/2015_07_02/150/005_PolModEff.dat' # 2.50% for 150 GHZ tetra
        run(data_path, 150, 'Tetraplexer')
	data_path = '../Data/2015_07_01/280/009_PolModEff.dat' #4.10% for 280 GHz tetra
        run(data_path, 280, 'Tetraplexer')
	data_path = '../Data/2015_07_02/280/015_PolModEff.dat' #4.10% for 280 GHz tetra
        run(data_path, 280, 'Tetraplexer')
	data_path = '../Data/2015_06_17/001_150_PolModEff.dat'
	run(data_path, 150, 'Tetraplexer')
	data_path = '../Data/2015_07_01/220/002_PolModEff.dat' # 2.10% for 220 GHZ tetra
        run(data_path, 220, 'Tetraplexer')
        data_path = '../Data/2015_07_02/90/017_PolModEff.dat' # 1.51% for 90 GHZ tetra
        run(data_path, 90, 'Tetraplexer')
	data_path = '../Data/2015_07_02/220/003_PolModEff.dat' # 1.56% for 220 GHZ tetra
        run(data_path, 220, 'Tetraplexer')
	data_path = '../Data/2015_07_01/280/009_PolModEff.dat' #4.10% for 280 GHz tetra
        run(data_path, 280, 'Tetraplexer')
        # HF Triplexer 07.11.15
	data_path = '../Data/2015_07_11/280/024_PolMod.dat' # 3.15% efficiency
	data_path = '../Data/2015_07_11/280/021_PolMod.dat'
	run(data_path, 280, 'HF_Triplexer')
	data_path = '../Data/2015_07_11/350/022_PolMod.dat' # 3.56% efficiency
	run(data_path, 350, 'HF_Triplexer')
	data_path = '../Data/2015_07_11/220/005_PolMod.dat' # 2.95% efficiency
	run(data_path, 220, 'HF_Triplexer')
        # LF Triplexer 07.13.15
        #################################3
	#data_path = '../Data/2015_07_13/40/020_PolMod.dat' # 2.37% efficiency
	#run(data_path, 40, 'LF_Triplexer')
	data_path = '../Data/2015_07_13/60/009_PolMod.dat' # 2.89% efficiency
	run(data_path, 60, 'LF_Triplexer')
	data_path = '../Data/2015_07_13/90/022_PolMod.dat' # 3.57% efficiency
	run(data_path, 90, 'LF_Triplexer')
	#data_path = '../Data/2015_07_02/280/015_PolModEff.dat' #4.10% for 280 GHz tetra
        #run(data_path, 280, 'Tetraplexer')
        # HF Triplexer 07.11.15
	data_path = '../Data/2015_07_11/280/024_PolMod.dat' # 3.15% efficiency
	data_path = '../Data/2015_07_11/280/021_PolMod.dat'
	run(data_path, 280, 'HF_Triplexer')
	data_path = '../Data/2015_07_11/350/022_PolMod.dat' # 3.56% efficiency
	run(data_path, 350, 'HF_Triplexer')
	data_path = '../Data/2015_07_11/220/005_PolMod.dat' # 2.95% efficiency
	run(data_path, 220, 'HF_Triplexer')
	data_path = '../Data/2017_03_08/SQ1_Polarization3.dat' # 1.5% efficiency
	run(data_path, 150, 'PB2_Pixel')
    if True:
	data_path = '../Data/2017_03_08/SQ1_Polarization3.dat' # 1.5% efficiency
	run(data_path, 150, 'PB2_Pixel')
