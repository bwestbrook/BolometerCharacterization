from math import log10, cos, acos
from copy import copy
import pylab as pl
import numpy as np
import sys
from scipy.signal import medfilt2d
from scipy.optimize import leastsq, curve_fit


def resistance_to_temp(resistance, serial_number):
    '''
    #Returns calibrated resistance from GRT thermometer with Serial Number 29312/25312 (same GRT labeled 2x)
    #This is the spare for dewar 576, the main for 575, and sometimes used on the dunk probe
    '''
    if not type(resistance) is np.ndarray:
        if type(resistance) is list:
            resistance = pl.asarray(resistance)
        elif not type(resistance) is list:
            resistance = pl.asarray([float(resistance)])
        else:
            print('Please supply a single number (can be formatted as string, int, float) or a list of such values')
            exit()
    serial_number = serial_number
    temperature_array = pl.zeros(resistance.size)
    for j, resistance_value in enumerate(resistance):
        z = np.log10(float(resistance_value))
        z_lower, z_upper, a_coefficients = _return_chebychev_coefficients_and_impedance_limits(z, serial_number)
        x = ((z - z_lower) - (z_upper - z)) / (z_upper - z_lower)
        temperature = 0.
        for i, coefficient in enumerate(a_coefficients):
            temperature += coefficient * np.cos(i * pl.arccos(x))
        temperature_array[j] = copy(temperature)
    return temperature_array


def make_calibration_curve(serial_number, r_low=2.0, r_upper=2000, r_resolution=1.0, plot_type='loglog'):
    '''
    This function makes either a loglog (default) or linear plot (must be specified with plot_type)
    of the R vs T curve for a given GRT with the serial # specified by serial_number.  By default,
    the function will plot the calibration from 2 to 2000 ohms with 1 ohm resolution
    '''
    resistance_array = pl.arange(r_low, r_upper, r_resolution)
    temperature_array = resistance_to_temp(resistance_array, serial_number)
    pl.title('Calibration for GRT {0} (Serial #)'.format(serial_number), fontsize=16)
    pl.xlabel('GRT Resistance ($\Omega$)', fontsize=16)
    pl.subplots_adjust(bottom=0.14)
    if np.nanmax(temperature_array) > 1.5:
        pl.ylabel('GRT Temperature (K)', fontsize=16)
    else:
        pl.ylabel('GRT Temperature (mK)', fontsize=16)
        pl.xlim(np.nanmin(resistance_array), np.nanmax(resistance_array))
        temperature_array *= 1e3
    if plot_type == 'loglog':
        pl.loglog(resistance_array, temperature_array)
        pl.grid(which='both')
        save_string = "LogLog_Calibration_Curve_for_GRT_{0}.png".format(serial_number)
    elif plot_type == 'linear':
        pl.plot(resistance_array, temperature_array)
        pl.grid()
        save_string = "Linear_Calibration_Curve_for_GRT_{0}.png".format(serial_number)
    pl.savefig(save_string)
    pl.show()

def _return_chebychev_coefficients_and_impedance_limits(z, serial_number):
    '''
    From the Lakeshore calibration, we compute the Chebychev polynomial coefficients
    and impedance limits for calculating the temperature from GRT resistance
    '''
    if serial_number == 25312: #Spare, 576, 575, Dunk P         
        indexLowZ = z < 1.847
        indexHighZ = z >= 1.847
        if indexLowZ:
            z_lower = 1.29703119134
            z_upper = 1.92926561825
            a_coefficients = [3.009515, -2.890878, 0.893721, -0.171457, 0.008545, 0.003623, -0.001133, -0.000844, 0.002041]
        elif indexHighZ:
            z_lower = 1.7971289878
            z_upper = 4.12178956886
            a_coefficients = [0.367386, -0.433782, 0.222165, -0.103141, 0.043246, -0.017709, 0.007038, -0.002538, 0.001405]
    elif serial_number == 29268: #576 Main
        indexLowZ = z < 1.5
        indexHighZ = z >= 1.5
        if indexLowZ:
            z_lower = 0.90471010057
            z_upper = 1.64330953313
            a_coefficients = [3.406517, -3.316534, 1.111962, -0.244558, 0.021691, 0.004550, 0.000699, -0.003230, 0.001288]
        elif indexHighZ:
            z_lower = 1.49694344573
            z_upper = 4.58887537671
            a_coefficients = [0.402365, -0.480368, 0.235846, -0.107966, 0.047552, -0.020961, 0.008959, -0.003042, 0.001272]
    elif serial_number == 25070: #SPOTC 
        indexLowZ = z < 2.45
        indexHighZ = z >= 2.45
        if indexLowZ:
            z_lower = 1.63942202014
            z_upper = 2.50611566116
            a_coefficients = [3.375220, -2.687447, 0.738616, -0.140089, 0.012422, 0.001577, -0.000108, -0.000692]
        elif indexHighZ:
            z_lower = 2.22559714466
            z_upper = 4.41995574849
            a_coefficients = [0.804488,-0.757791,0.288953,-0.100625,0.033134,-0.009878,0.002836,-0.001155]
    elif serial_number == 26399: #Trevor/Roger/SPT Gold
        indexLowZ = z < 2.34
        indexHighZ = z >= 2.34
        if indexLowZ:
            z_lower = 1.41705446024
            z_upper = 2.50611843916
            a_coefficients = [3.754597, -3.234422, 0.960543, -0.196365, 0.018874, 0.000535, 0.001509, -0.000836]
        elif indexHighZ:
            z_lower = 2.18102749783
            z_upper = 4.73415951324
            a_coefficients = [0.805553,-0.756980,0.283894,-0.097728,0.031736,-0.009586,0.003079,-0.000504]
    elif serial_number == 'X36942': #Old APEX-SZ UC Stage
        indexLowZ = z < 2.31 # R of 204 Ohms, 2.7K
        indexHighZ = z >= 2.31 # R of 204 Ohms, 2.7K
        if indexLowZ:
            z_lower = 1.41354860
            z_upper = 4.11348851
            a_coefficients = [4.38899368e+01, -6.14493328e+01, 6.81014731e+01, -2.35350808e+01, 3.22051536e+01,
                              -6.28008435e-03, 7.40976930e+00, 1.59323247e+00]
        elif indexHighZ:
            z_upper = 5.013378734664989
            z_lower = 1.8018480099633725
            a_coefficients = [-0.5234685959969033, -13.678124605376624, -1.4818353896784546, -7.864843469586991,
                              -1.0047821527037664, -2.6414990543941963, -0.24695301103448455, -0.4048453282392341]
    else:
        print('grt serial number not recognised')
        exit()
    return z_lower, z_upper, a_coefficients

def test(resistance_value):
    print('GRT')
    z_lower = 1.41354860
    z_upper = 4.11348851
    a_coefficients = [4.38899368e+01, -6.14493328e+01, 6.81014731e+01, -2.35350808e+01, 3.22051536e+01,
                      -6.28008435e-03, 6.99000000e-04, 7.40976930e+00, 1.59323247e+00]
    z = np.log10(float(resistance_value))
    x = ((z - z_lower) - (z_upper - z)) / (z_upper - z_lower)
    temperature = 0.
    for i, coefficient in enumerate(a_coefficients):
        temperature += coefficient * np.cos(i * pl.arccos(x))
        print(i)
        print(temperature, coefficient)
        print()
    print(resistance_value, temperature)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        serial_number = sys.argv[1]
        resistance_array = sys.argv[2]
        make_plot = False
        compute_temp = True
    elif len(sys.argv) == 2:
        serial_number = sys.argv[1]
        resistance_array = [50.0, '75.3', 1000]
        make_plot = True
        compute_temp = False
    elif len(sys.argv) == 1:
        serial_number = 29268
        serial_number = 'X36942'
        resistance_array = [300.0, 310, 320]
        resistance_array = [100, 1000, 10000]
        make_plot = True
        compute_temp = False
    else:
        print('\nPlease call the function as:')
        print()
        print('python {0} <serial_number> (for plots and test calls on 29268 for 50, 75.3, and 100 Ohms)'.format(sys.argv[0]))
        print('python {0} <serial_number> [for plots only]'.format(sys.argv[0]))
        print('python {0} <serial_number> <resistance> [for single temp computation]'.format(sys.argv[0]))
        print()
        exit()
    if compute_temp:
        temperature_array = resistance_to_temp(resistance_array, serial_number)
        print()
        print("GRT Serial Number", serial_number)
        print("Resistance Values", resistance_array, 'Ohms')
        print("Temperature Values", temperature_array, 'Kelvin')
        print()
    if make_plot:
        #test(50.0)
        make_calibration_curve(serial_number, r_low=20.0, r_upper=10000, r_resolution=1.0, plot_type='loglog')
        #make_calibration_curve(serial_number, r_low=2.0, r_upper=2000, r_resolution=1.0, plot_type='linear')
