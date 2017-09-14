import os
import numpy as np
import pylab as pl
from settings import settings


class IVCurve():

    def __init__(self):
        self.yo = 'yo'

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


    def convert_IV_to_real_units(self, bias_voltage, squid_voltage, squid_conv=30.0, v_bias_multiplier=1e-4,
                                 determine_calibration=False, calibration_resistor_val=1.0,
                                 clip=None, quick_plot=False):
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
        corrected_squid_voltage = fit_and_remove_offset(bias_voltage, squid_voltage, clip=clip, quick_plot=quick_plot)
        v_bias_real = bias_voltage * v_bias_multiplier # in V
        v_bias_real *= 1e6  # in uV
        if determine_calibration:
            squid_conv = determine_squid_transimpedance(v_bias_real, corrected_squid_voltage, calibration_resistor_val)
        i_bolo_real = corrected_squid_voltage * squid_conv # in uA
        plot_iv_curve(v_bias_real, i_bolo_real, clip=clip)
        return v_bias_real, i_bolo_real


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
        print '\n\n Transimpedance Value: {0}\n\n'.format(squid_conv)
        return squid_conv


    def fit_and_remove_offset(self, x_vector, y_vector, n=1, clip=None, quick_plot=False, return_fit=False):
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
        if clip is not None:
            selector = np.logical_and(clip[0] < x_vector, x_vector < clip[1])
            print x_vector
        fit_vals = np.polyfit(x_vector, y_vector, n)
        poly_fit = np.polyval(fit_vals, x_vector)
        offset_removed = y_vector - fit_vals[1]
        if fit_vals[0] < 0:
            offset_removed = -1 * offset_removed
        if quick_plot:
            x_vector_2 = np.arange(-1, 3, 0.5)
            poly_fit = np.polyval(fit_vals, x_vector_2)
            pl.plot(x_vector, y_vector)
            pl.plot(x_vector_2, poly_fit)
            pl.show()
        return offset_removed


    def plot_iv_curve(self, bolo_voltage_bias, bolo_current, clip=None):
        '''
        This function creates an x-y scatter plot with V_bias on the x-axis and
        bolo curent on the y-axis.  The resistance value is reported as text annotation
        Inputs:
            bolo_votlage_bias: bolo_voltage in Volts
            bolo_current: bolo_current in Amps
        '''
        fig = pl.figure(figsize=(10, 5))
        fig.subplots_adjust(bottom=0.2)
        selector = np.logical_and(clip[0] < bolo_voltage_bias,bolo_voltage_bias < clip[1])
        fit_vals = np.polyfit(bolo_voltage_bias[selector], bolo_current[selector], 1)
        v_fit_x_vector = np.arange(0, 50, 0.2)
        selector_2 = np.logical_and(clip[0] < v_fit_x_vector, v_fit_x_vector < clip[1])
        poly_fit = np.polyval(fit_vals, v_fit_x_vector[selector_2])
        ax1 = fig.add_subplot(111)
        ax1.plot(bolo_voltage_bias, bolo_current, '.', label=settings.label)
        ax1.plot(v_fit_x_vector[selector_2], poly_fit, label='Fit: {0:.2f}$\Omega$'.format(1.0 / fit_vals[0]))
        ax1.set_xlabel("Voltage ($\mu$V)", fontsize=16)
        ax1.set_ylabel("Current ($\mu$A)", fontsize=16)
        ax1.legend(loc='best', numpoints=1)
        fig.show()
        #self._ask_user_if_they_want_to_quit()


    def _ask_user_if_they_want_to_quit(self):
        '''
        A simple method to stop the code without setting a trace with the option of quittting
        '''
        quit_boolean = raw_input('Press q to q(uit), any other key to continue:\n')
        if quit_boolean == 'q':
            exit()


    def run(self):
        bias_voltage, squid_voltage = load_data(settings.data_path)
        v_bias_real, i_bolo_real = convert_IV_to_real_units(bias_voltage, squid_voltage,
                                                            squid_conv=settings.squid_conv,
                                                            v_bias_multiplier=settings.voltage_conv,
                                                            calibration_resistor_val=settings.calibration_resistor_val,
                                                            determine_calibration=settings.determine_calibration,
                                                            clip=settings.clip)



if __name__ == '__main__':
    ivc = IVCurve()
    ivc.run()
