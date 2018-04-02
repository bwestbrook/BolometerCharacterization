import numpy as np
import pylab as pl

def compute_delta_power_sensed(v_bias, delta_v_squid, squid_conversion):
    delta_current = delta_v_squid * squid_conversion * 1e-6
    delta_power = v_bias * delta_current # in Watts
    return delta_power


def load_FFT_data(data_path):
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
                    transmission = line.split('\t')[1]
                    np.put(frequency_vector, i, frequency)
                    np.put(transmission_vector, i, transmission)
    normalized_transmission_vector = transmission_vector / max(transmission_vector)
    return frequency_vector, transmission_vector, normalized_transmission_vector


def compute_delta_power_at_window(frequency, spectra_path, t_source_low=77, t_source_high=300, show_spectra=False):
    boltzmann_constant = 1.38e-23
    fft_data = load_FFT_data(spectra_path)
    frequency_vector = fft_data[0]
    normalized_transmission_vector = fft_data[2]
    integrated_bandwidth = np.trapz(normalized_transmission_vector, frequency_vector) * 1e9
    pl.plot(frequency_vector, normalized_transmission_vector)
    pl.show()
    delta_power = boltzmann_constant * (t_source_high - t_source_low) * integrated_bandwidth
    if show_spectra:
            pl.plot(normalized_transmission_vector)
            pl.show()
    return delta_power


def run(input_dict):
    frequency = input_dict.keys()[0]
    v_bias = input_dict[frequency]['v_bias']
    delta_v_squid = input_dict[frequency]['delta_v_squid']
    squid_conversion = input_dict[frequency]['squid_conversion']
    spectra_path = input_dict[frequency]['spectra_path']
    delta_power_sensed = compute_delta_power_sensed(v_bias, delta_v_squid, squid_conversion)
    delta_power_at_window = compute_delta_power_at_window(frequency, spectra_path)
    end_to_end_efficiency = delta_power_sensed / delta_power_at_window
    print
    print
    print 'Analysis for {0} GHz Bolo'.format(frequency)
    print 'Delta_Power_Sensed: {0} W'.format(delta_power_sensed)
    print 'Delta_Power_at_Window: {0} W'.format(delta_power_at_window)
    print 'Efficiency: {:.3f}%'.format(100.0 * end_to_end_efficiency)
    print
    print

if __name__ == '__main__':
    # HF Triplexer
    input_dict_220 = {'220': {'v_bias': 0.878e-4, 'delta_v_squid': 0.0104, 'squid_conversion': 30.0,
                              'spectra_path': '../Data/2015_05_27/002_220_Spectra_Scan.fft'}}
    input_dict_280 = {'280': {'v_bias': 0.526e-4, 'delta_v_squid': 0.0033, 'squid_conversion': 30.0,
                              'spectra_path': '../Data/2015_05_27/004_280_Spectra_Scan.fft'}}
    input_dict_350 = {'350': {'v_bias': 0.508e-4, 'delta_v_squid': 0.0025, 'squid_conversion': 28.5,
                              'spectra_path': '../Data/2015_05_27/003_350_Spectra_Scan.fft'}}


    # HF Triplexer Proper Mounting
    input_dict_220 = {'220': {'v_bias': 0.487e-4, 'delta_v_squid': 0.020, 'squid_conversion': 37.1,
                              'spectra_path': '../Data/2015_07_10/220/004_Spectra.fft'}}
    input_dict_280 = {'280': {'v_bias': 0.530e-4, 'delta_v_squid': 0.0058, 'squid_conversion': 32.5,
                              'spectra_path': '../Data/2015_07_10/280/002_Spectra.fft'}}
    input_dict_350 = {'350': {'v_bias': 0.418e-4, 'delta_v_squid': 0.0173, 'squid_conversion': 28.5,
                              'spectra_path': '../Data/2015_07_10/350/026_Spectra.fft'}}
    # Tetraplexer
    input_dict_90 = {'90': {'v_bias': 0.352e-4, 'delta_v_squid': 0.004, 'squid_conversion': 37.1,
                            'spectra_path': '../FTS_Transmission_Tests/Data/Tetraplexer/2015_06_30/Wafer_BW1_8_Die_2_5/90/003_Spectra_1p7GHz_Res.fft'}}
    input_dict_150 = {'150': {'v_bias': 0.406e-4, 'delta_v_squid': 0.002, 'squid_conversion': 32.5,
                              'spectra_path': '../FTS_Transmission_Tests/Data/Tetraplexer/2015_06_30/Wafer_BW1_8_Die_2_5/220/002_Spectra_1p7GHz_Res.fft'}}
    input_dict_220 = {'220': {'v_bias': 0.455e-4, 'delta_v_squid': 0.0035, 'squid_conversion': 28.5,
                              'spectra_path': '../FTS_Transmission_Tests/Data/Tetraplexer/2015_06_30/Wafer_BW1_8_Die_2_5/220/002_Spectra_1p7GHz_Res.fft'}}
    input_dict_280 = {'280': {'v_bias': 0.400e-4, 'delta_v_squid': 0.0033, 'squid_conversion': 30.0,
                              'spectra_path': '../FTS_Transmission_Tests/Data/Tetraplexer/2015_06_30/Wafer_BW1_8_Die_2_5/220/002_Spectra_1p7GHz_Res.fft'}}

    # LF Triplexer
    input_dict_60 = {'60': {'v_bias': 0.526e-4, 'delta_v_squid': 0.0033, 'squid_conversion': 32.5,
                            'spectra_path': '../Data/2015_05_27/004_280_Spectra_Scan.fft'}}
    input_dict_40 = {'30': {'v_bias': 0.226e-4, 'delta_v_squid': 0.0025, 'squid_conversion': 37.1,
                            'spectra_path': '../Data/2015_05_27/003_350_Spectra_Scan.fft'}}
    input_dict_90 = {'90': {'v_bias': 0.351e-4, 'delta_v_squid': 0.0114, 'squid_conversion': 28.5,
                            'spectra_path': '../FTS_Transmission_Tests/Data/Tetraplexer/2015_06_30/Wafer_BW1_8_Die_2_5/90/003_Spectra_1p7GHz_Res.fft'}}
    #for input_dict in [input_dict_90, input_dict_150, input_dict_220, input_dict_280]:
    # Double Slot Diploe
    input_dict_350_double_slot = {'350': {'v_bias': 0.514e-4, 'delta_v_squid': 0.0039, 'squid_conversion': 28.5,
                                  'spectra_path': '../Data/2015_07_10/350/026_Spectra.fft'}}
    #for input_dict in [input_dict_220, input_dict_280, input_dict_350]:
    #for input_dict in [input_dict_350_double_slot]:
    #for input_dict in [input_dict_40, input_dict_60, input_dict_90]:

    # PB2 Cl2 Etched Compressive Die Test 
    input_dict_150 = {'150': {'v_bias': 0.095e-4, 'delta_v_squid': 0.030, 'squid_conversion': 37.1,
                              'spectra_path': '../FTS_Transmission_Tests/Data/PB2/2016_03_25/Wafer_AS7-20_Die_Corner/150/009_SQ1_High_Res_MedHF_Spectra.fft'}}
    #for input_dict in [input_dict_220, input_dict_280, input_dict_350, input_dict_350_double_slot]:

    for input_dict in [input_dict_150]:
        #, input_dict_280, input_dict_350, input_dict_350_double_slot]:
        run(input_dict)
