import os
import bisect
import numpy as np
import pylab as pl
from pprint import pprint
from copy import copy
from .settings import settings


class IVCurve():

    def __init__(self, list_of_input_dicts):
        self.list_of_input_dicts = list_of_input_dicts
        self.r_n_fraction = 0.75

    def load_data(self, data_path):
        '''
        This loads the data as two vectors of data representing the bias voltage and squid out voltage
        Inputs:
            data_path: path to the data in question
        Outputs:
            bias_voltage: a vector of the bias voltage
            squid_voltage: a vector of the squid out voltage
        '''
        bias_voltage = []
        squid_voltage = []
        with open(data_path, 'r') as file_handle:
            for line in file_handle:
                squid_voltage_val = line.split('\t')[1]
                bias_voltage_val = line.split('\t')[0]
                if float(bias_voltage_val) < 0:
                    bias_voltage.append(-1 * float(bias_voltage_val))
                else:
                    bias_voltage.append(float(bias_voltage_val))
                squid_voltage.append(float(squid_voltage_val))
        return np.asarray(bias_voltage), np.asarray(squid_voltage)

## Mathematical Operations

    def convert_IV_to_real_units(self, bias_voltage, squid_voltage, stds=None,
                                 squid_conv=30.0, v_bias_multiplier=1e-4,
                                 determine_calibration=False, calibration_resistor_val=1.0,
                                 clip=(0, 100), quick_plot=False, label=''):
        '''
        This loads the data as two vectors of data representing the bias voltage and squid out voltage
        Inputs:
            bias_voltage: a vector of the bias voltage
            squid_voltage: a vector of the squid out voltage
            squid_conv: a value of the squid transimpedance (microAmps / Volt, default is 30.0)
            v_bias_multiplier: a value of the v_bias multiplier (default is 1e-4)
            determine_calibration: a boolean asking whether or not one should get the calibration value
                                   from the data.  This requires accurate use of the calibration_resistor_val
                                   (default is False)
            calibration_resistor_val: the value (in Ohms) of the calibration resistor used to run the test.
                                      Is only used when determine_calibration is set to True
        Outputs:
            v_bias_real: a vector of the bias voltage in Volts
            i_bolo_real: a vector of the bolo current in Amps
        '''
        corrected_squid_voltage = self.fit_and_remove_offset(bias_voltage, squid_voltage, v_bias_multiplier,
                                                             clip=clip, quick_plot=quick_plot)
        v_bias_real = bias_voltage * v_bias_multiplier # in V
        v_bias_real *= 1e6  # in uV
        if determine_calibration:
            squid_conv = self.determine_squid_transimpedance(v_bias_real, corrected_squid_voltage,
                                                             calibration_resistor_val)
        i_bolo_real = corrected_squid_voltage * squid_conv # in uA
        if stds is not None:
            i_bolo_real_std = stds * squid_conv
        else:
            i_bolo_real_std = np.zeros(len(v_bias_real))
        if quick_plot:
            pl.plot(v_bias_real, i_bolo_real)
            pl.show()
        return v_bias_real, i_bolo_real, i_bolo_real_std

    def fit_and_remove_offset(self, x_vector, y_vector, v_bias_multiplier,
                              n=1, clip=None, quick_plot=True, return_fit=False):
        '''
        This function is necessary to correct the arbitrary offset and sometime negative sign
        which is naturally applied to the SQUID output.  It doesn't change the units, but ensures
        that the data go through (0, 0) and have a slope consistent with a positive resistance.
        It's worth noting that this fit is down with bias voltage as the x_axis, since that is
        what is being modulated during the measurement and doesn't need correction
        Inputs:
            data: to remvoe polynomial
            n: order of polynomial to remove (default n=1)
        Outputs:
            return_fit: Return fit values
            data_with_first_order_poly_removed
        '''
        scaled_x_vector = copy(x_vector)
        scaled_x_vector *= v_bias_multiplier
        scaled_x_vector *= 1e6 # This is now in uV
        if clip is not None:
            selector = np.logical_and(clip[0] < scaled_x_vector, scaled_x_vector < clip[1])
        if len(scaled_x_vector[selector]) > 2:
            fit_vals = np.polyfit(x_vector[selector], y_vector[selector], n)
            offset_removed = y_vector - fit_vals[1]
            if fit_vals[0] < 0:
                offset_removed = -1 * offset_removed
            if quick_plot and False:
                poly_fit = np.polyval(fit_vals, x_vector[selector])
                x_vector_2 = np.arange(-1, 3, 0.5)
                poly_fit = np.polyval(fit_vals, x_vector_2)
                pl.plot(x_vector, y_vector)
                pl.plot(x_vector, offset_removed)
                pl.plot(x_vector_2, poly_fit)
                pl.show()
        else:
            offset_removed = y_vector
        return offset_removed

    def determine_squid_transimpedance(self, v_bias_real, corrected_squid_voltage, calibration_resistor_val):
        '''
        This function fits the (offset) corrected_squid_voltage and the real voltage bias
        and compares it against the calibration_resistor_val to determine the true
        transmipedance of the squid
        Inputs:
            v_bias_real: a vector of the bias voltage in Volts
            corrected_squid_voltage: squid_voltage with the offset removed
            calibration_resistor_vale: value of the resistor that the transimpedance will be corrected to match
        Outputs:
            squid_conv: the value of the transimpedance of the SQUID based on the calibration
        '''
        fit_vals = np.polyfit(v_bias_real, corrected_squid_voltage, 1)
        slope = fit_vals[0]
        squid_conv = 1.0 / (slope * calibration_resistor_val)
        print('\n\n Transimpedance Value: {1}\n\n'.format(squid_conv))
        return squid_conv

    def find_nearest_r_bolo(self, r_bolo, r_n, fracrn):
        frac_r_n = fracrn * r_n
        nearest_r_bolo_index = np.abs(r_bolo - frac_r_n).argmin()
        nearest_r_bolo = r_bolo[nearest_r_bolo_index]
        return nearest_r_bolo, nearest_r_bolo_index

## Plotting

    def plot_differenced_ivs(self, v_biases, i_bolos, fracrns, colors, labels, spectra_paths):
        '''
        This code takes to sets of IV curves and takes a differenc in power at the same fracrn
        '''
        fig = pl.figure(figsize=(10, 5))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(right=0.8, left=0.10, bottom=0.15)
        ax.set_xlabel('Resistance ($\Omega$)', fontsize=16)
        ax.set_xlabel('Normalized Resistance ($\Omega$)', fontsize=16)
        ax.set_ylabel('Power ($\mu$V)', fontsize=16)
        p_at_same_rfracs = []
        for i, v_bias in enumerate(v_biases):
            print(i, v_bias)
            fracrn = fracrns[i]
            i_bolo = i_bolos[i]
            r_bolo = v_bias / i_bolo
            r_bolo_norm = r_bolo / np.max(r_bolo)
            p_bolo = v_bias * i_bolo
            #ax.plot(r_bolo, p_bolo, color=colors[i], label=labels[i])
            ax.plot(r_bolo_norm, p_bolo, color=colors[i], label=labels[i])
            #r_n = r_bolo[10] # some value near the start
            r_n = r_bolo_norm[10] # some value near the start
            nearest_r_bolo, nearest_r_bolo_index = self.find_nearest_r_bolo(r_bolo_norm, r_n, fracrn)
            p_at_same_rfrac = p_bolo[nearest_r_bolo_index]
            p_at_same_rfracs.append(p_at_same_rfrac)
            #ax.axvline(r_bolo[nearest_r_bolo_index], color=colors[i], label=labels[i])
            ax.axvline(r_bolo_norm[nearest_r_bolo_index], color=colors[i])
            spectra_path = spectra_paths[i]
        p_window = self.compute_delta_power_at_window(spectra_path)
        p_sensed = np.abs(p_at_same_rfracs[1] - p_at_same_rfracs[0])
        efficiency = 100.0 * p_sensed / p_window
        print()
        title =  'Power diff {0:.2f} / {1:.2f} (sensed / window) pW'.format(p_sensed, p_window)
        title += '\nEffiency is {0:.2f}%'.format(efficiency)
        print(title)
        print()
        ax.set_title(title)
        ax.legend(numpoints=1)
        #, loc=2, bbox_to_anchor=(1.01, 1), borderaxespad=0.0)
        pl.show()


    def plot_all_curves(self, bolo_voltage_bias, bolo_current, stds=None, label='', fit_clip=None, plot_clip=None,
                        show_plot=False, title='', pturn=False):
        '''
        This function creates an x-y scatter plot with V_bias on the x-axis and
        bolo curent on the y-axis.  The resistance value is reported as text annotation
        Inputs:
            bolo_votlage_bias: bolo_voltage in Volts
            bolo_current: bolo_current in Amps
        '''
        fig = pl.figure(figsize=(10, 5))
        fig.subplots_adjust(left=0.1, right=0.97, bottom=0.11, hspace=0.66)
        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(223)
        ax4 = fig.add_subplot(224)
        ax2.set_axis_off()
        fit_selector = np.logical_and(fit_clip[0] < bolo_voltage_bias, bolo_voltage_bias < fit_clip[1])
        plot_selector = np.logical_and(plot_clip[0] < bolo_voltage_bias, bolo_voltage_bias < plot_clip[1])
        add_fit = False
        if len(bolo_voltage_bias[fit_selector]) > 2:
            fit_vals = np.polyfit(bolo_voltage_bias[fit_selector], bolo_current[fit_selector], 1)
            v_fit_x_vector = np.arange(fit_clip[0], fit_clip[1], 0.2)
            selector_2 = np.logical_and(fit_clip[0] < v_fit_x_vector, v_fit_x_vector < fit_clip[1])
            poly_fit = np.polyval(fit_vals, v_fit_x_vector[selector_2])
            add_fit = True
        resistance_vector = bolo_voltage_bias / bolo_current
        power_vector = bolo_voltage_bias * bolo_current
        ax1.plot(bolo_voltage_bias[plot_selector], bolo_current[plot_selector], '.', label=label)
        if stds is not None:
            ax1.errorbar(bolo_voltage_bias[plot_selector], bolo_current[plot_selector], yerr=stds[plot_selector],
                         label='error', marker='.', linestyle='None', alpha=0.25)
        if pturn:
            pt_idx = np.where(bolo_current[plot_selector] == min(bolo_current[plot_selector]))[0][0]
            pl_idx = np.where(bolo_voltage_bias[plot_selector] == min(bolo_voltage_bias[plot_selector]))[0][0]
            pturn_pw = bolo_current[plot_selector][pt_idx] * bolo_voltage_bias[plot_selector][pt_idx]
            plast_pw = bolo_current[plot_selector][pl_idx] * bolo_voltage_bias[plot_selector][pl_idx]
            ax1.plot(bolo_voltage_bias[plot_selector][pt_idx], bolo_current[plot_selector][pt_idx],
                     '*', markersize=10.0, color='g', label='Pturn = {0:.2f} pW'.format(pturn_pw))
            ax1.plot(bolo_voltage_bias[plot_selector][pl_idx], bolo_current[plot_selector][pl_idx],
                     '*', markersize=10.0, color='m', label='Plast = {0:.2f} pW'.format(plast_pw))
        ax3.plot(bolo_voltage_bias[plot_selector], resistance_vector[plot_selector], 'b', label='Res ($\Omega$)')
        #ax4.plot(bolo_voltage_bias[power_selector], power_vector[power_selector], resitance_vector[plot_selector], 'r', label='Power (pW)')
        power_selector = np.logical_and(0 < power_vector, power_vector < 0.25 * np.max(power_vector))
        ax4.plot(resistance_vector[plot_selector], power_vector[plot_selector], 'r', label='Power (pW)')
        if add_fit:
            ax1.plot(v_fit_x_vector[selector_2], poly_fit, label='Fit: {0:.2f}$\Omega$'.format(1.0 / fit_vals[0]))
        # Label the axis
        ax1.set_xlabel("Voltage ($\mu$V)", fontsize=12)
        ax1.set_ylabel("Current ($\mu$A)", fontsize=12)
        ax3.set_xlabel("Voltage ($\mu$V)", fontsize=12)
        ax3.set_ylabel("Res ($\Omega$)", fontsize=12)
        ax4.set_xlabel("Res ($\Omega$)", fontsize=12)
        ax4.set_ylabel("Power ($pW$)", fontsize=12)
        # Set the titles
        ax1.set_title('IV of {0}'.format(title))
        ax3.set_title('RV of {0}'.format(title))
        ax4.set_title('PR of {0}'.format(title))
        # Grab all the labels and combine them 
        handles, labels = ax1.get_legend_handles_labels()
        handles += ax3.get_legend_handles_labels()[0]
        labels += ax3.get_legend_handles_labels()[1]
        handles += ax4.get_legend_handles_labels()[0]
        labels += ax4.get_legend_handles_labels()[1]
        ax2.legend(handles, labels, numpoints=1, mode="expand", bbox_to_anchor=(0, 0.1, 1, 1))
        #ax4.set_ylim(0, 0.5 * max(power_vector[plot_selector]))
        #ax4.set_xlim(0, 1.1 * max(power_vector[plot_selector]))
        #(max(power_vector[plot_selector]) - 0.8 * max(power_vector[plot_selector]),
        xlim_range = max(plot_clip) - min(plot_clip)
        ax1.set_xlim((plot_clip[0] - 0.1 * xlim_range, plot_clip[1] + 0.1 * xlim_range))
        ax3.set_xlim((plot_clip[0] - 0.1 * xlim_range, plot_clip[1] + 0.1 * xlim_range))
        #ax4.set_xlim((plot_clip[0], plot_clip[1]))
        if show_plot:
            pl.show()
        return fig

    def _ask_user_if_they_want_to_quit(self):
        '''
        A simple method to stop the code without setting a trace with the option of quittting
        '''
        quit_boolean = raw_input('Press q to q(uit), any other key to continue:\n')
        if quit_boolean == 'q':
            exit()

    def load_FFT_data(self, data_path):
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


    def compute_delta_power_at_window(self, spectra_path, t_source_low=77, t_source_high=300, show_spectra=False):
        boltzmann_constant = 1.38e-23
        fft_data = self.load_FFT_data(spectra_path)
        frequency_vector = fft_data[0]
        normalized_transmission_vector = fft_data[2]
        integrated_bandwidth = np.trapz(normalized_transmission_vector, frequency_vector) * 1e9
        delta_power = boltzmann_constant * (t_source_high - t_source_low) * integrated_bandwidth  # in W
        delta_power *= 1e12 # pW
        if show_spectra:
            pl.plot(frequency_vector, normalized_transmission_vector)
            pl.plot(normalized_transmission_vector)
            pl.show()
        return delta_power

    def run(self):
        '''
        Cycles through the input dicts and plots them
        '''
        for input_dict in self.list_of_input_dicts:
            difference = input_dict['difference']
            if difference:
                break
        v_biases, i_bolos, colors, label_strs, fracrns, spectra_paths = [], [], [], [], [], []
        for input_dict in self.list_of_input_dicts:
            data_path = input_dict['data_path']
            label = input_dict['label']
            color = input_dict['color']
            fracrn = input_dict['fracrn']
            spectra_path = input_dict['loaded_spectra']
            bias_voltage, squid_voltage = self.load_data(data_path)
            fit_clip = (input_dict['v_fit_lo'], input_dict['v_fit_hi'])
            plot_clip = (input_dict['v_plot_lo'], input_dict['v_plot_hi'])
            if len(input_dict['label']) == 0:
                labels = os.path.basename(data_path)
            v_bias_real, i_bolo_real, i_bolo_std = self.convert_IV_to_real_units(bias_voltage, squid_voltage,
                                                                                 squid_conv=input_dict['squid_conversion'],
                                                                                 v_bias_multiplier=input_dict['voltage_conversion'],
                                                                                 calibration_resistor_val=input_dict['calibration_resistance'],
                                                                                 determine_calibration=input_dict['calibrate'],
                                                                                 clip=fit_clip, label=label)
            v_biases.append(v_bias_real)
            i_bolos.append(i_bolo_real)
            label_strs.append(label)
            colors.append(color)
            fracrns.append(fracrn)
            spectra_paths.append(spectra_path)
            if not difference:
                 self.plot_all_curves(v_bias_real, i_bolo_real, label=label,
                                      fit_clip=fit_clip, plot_clip=plot_clip,
                                      show_plot=True)

        if difference:
            self.plot_differenced_ivs(v_biases, i_bolos, fracrns, colors, label_strs, spectra_paths)

if __name__ == '__main__':
    ivc = IVCurve()
    ivc.run()
