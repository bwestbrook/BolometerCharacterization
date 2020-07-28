from math import log10, cos, acos
from copy import copy
import pylab as pl
import numpy as np
import sys
from scipy.signal import medfilt2d
from scipy.optimize import leastsq, curve_fit


class getGRTCal():
    def __init__(self):
        self.zU = 1.64330953313
        self.zL = 0.90471010057
        self.zL = 1.9
        self.zU = 10.5
        # Low R Fit > 1K X36942
        self.zL_lo = 1.41354860
        self.zU_lo = 4.11348851
        self.coefficients_lo = [4.38899368e+01, -6.14493328e+01, 6.81014731e+01, -2.35350808e+01, 3.22051536e+01,
                                -6.28008435e-03, 7.40976930e+00, 1.59323247e+00]
        # Low R Fit > 1K X36942
        self.zL = 1.41354860
        self.zU = 4.11348851
        self.coefficients = [4.38899368e+01, -6.14493328e+01, 6.81014731e+01, -2.35350808e+01, 3.22051536e+01,
                             -6.28008435e-03, 7.40976930e+00, 1.59323247e+00]

        # High R Fit < 1K X36942
        self.zL_hi = 1.820655
        self.zU_hi = 4.990586
        self.coefficients_hi = [-2.142769756245977, -16.76549838322048, -3.9888362053545374, -9.80309633188344,
                                -2.111168648643484, -3.3413753227753795, -0.46723334643183967, -0.5152785101659354]

        self.zU = 5.013378734664989
        self.zL = 1.8018480099633725
        self.coefficients = [-0.5234685959969033, -13.678124605376624, -1.4818353896784546, -7.864843469586991,
                             -1.0047821527037664, -2.6414990543941963, -0.24695301103448455, -0.4048453282392341]
    def fit_arb_temp_function(self, x_data, y_data, fit_guess):
        fit_params = curve_fit(self.arb_temp_functionX, x_data, y_data, p0=fit_guess)
        return fit_params

    def arb_temp_functionX(self, resistance, zU, zL, a0, a1, a2, a3, a4, a5, a6, a7):
        temperature = 0.0
        coefficients = [a0, a1, a2, a3, a4, a5, a6, a7]
        for i, coefficient in enumerate(coefficients):
            Z = np.log10(resistance)
            X = ((Z - zL ) - (zU - Z)) / (zU - zL)
            temperature += coefficient * np.cos(i * np.arccos(X))
            #print i
            #print temperature, coefficient
            #print
        return temperature

    def test(self, resistance):
        temp = self.arb_temp_functionX(resistance, self.zU, self.zL, *self.coefficients)
        #print resistance, temp

    def plot_arb_temp_function_2(self, zUs=None, zLs=None, coefficients_list=None, calibration_curve_data_path=None):
        if zUs is None:
            zUs = [self.zU_lo, self.zU_hi]
        if zLs is None:
            zLs = [self.zL_lo, self.zL_hi]
        if coefficients_list is None:
            coefficients_list = [self.coefficients_lo, self.coefficients_hi]
        x_ranges =[(22, 204), (203, 10000)]
        fig = None
        for i, zU in enumerate(zUs):
            zL = zLs[i]
            coefficients = coefficients_list[i]
            x_range = x_ranges[i]
            fig =self.plot_arb_temp_function(zU=zU, zL=zL, coefficients=coefficients,
                                             calibration_curve_data_path=calibration_curve_data_path, fig=fig,
                                             x_range=x_range)
        pl.show()

    def plot_arb_temp_function(self, zU=None, zL=None, coefficients=None,
                               calibration_curve_data_path=None, fig=None,
                               x_range=None):
        if zU is None:
            zU = self.zU
        if zL is None:
            zL = self.zL
        if coefficients is None:
            coefficients = self.coefficients
        temps = []
        if x_range is not None:
            resistances = np.linspace(x_range[0], x_range[1], 51)
        else:
            resistances = np.linspace(13, 15000, 1000)
        if fig is None:
            fig = pl.figure()
            fig.add_subplot(111)
        ax = fig.get_axes()[0]
        #print resistance
        for resistance in resistances:
            temp = self.arb_temp_functionX(resistance, zU, zL, *coefficients)
            temps.append(temp)
        ax.loglog(resistances, temps)
        if calibration_curve_data_path is not None:
            x_data, y_data = self.load_calibration_data(calibration_curve_data_path)
            ax.loglog(x_data, y_data, 'o', color='r', ms='2.5', alpha=0.5)
            #ax.set_xlim((48, 102))
        return fig

    def get_cal(self, calibration_curve_data_path):
        x_data, y_data = self.load_calibration_data(calibration_curve_data_path)
        fit_guess =  [self.zU, self.zL] + self.coefficients
        first_data_point = 78
        last_data_point = -1
        fit_params = self.fit_arb_temp_function(x_data[first_data_point:last_data_point], y_data[first_data_point:last_data_point], fit_guess)
        print
        print 'FIT OVERRRRRRRRRRRRRRRRRRRRRRRRRR'
        print 'GUESS'
        print fit_guess
        print 'FIT'
        print [x for x in fit_params[0]]
        print
        print
        fig = self.plot_arb_temp_function(zU=fit_params[0][0], zL=fit_params[0][1], coefficients=fit_params[0][2:])
        ax = fig.get_axes()[0]
        #ax.loglog(x_data[:last_data_point], y_data[:last_data_point], '*', color='r')
        ax.loglog(x_data[first_data_point:last_data_point], y_data[first_data_point:last_data_point], '*', color='r')
        pl.show()

    def load_calibration_data(self, calibration_curve_data_path):
        with open(calibration_curve_data_path, 'r') as file_handle:
            lines = file_handle.readlines()[1:]
            temperature_vector = np.zeros(len(lines))
            resistance_vector = np.zeros(len(lines))
            for i, line in enumerate(reversed(lines)):
                temp, resistance = line.split('\t')
                np.put(temperature_vector, i, float(temp))
                np.put(resistance_vector, i, float(resistance.replace('\n','')))
        #return temperature_vector, resistance_vector
        return resistance_vector, temperature_vector

if __name__ == '__main__':
    get_grt_cal = getGRTCal()
    calibration_curve_data_path = './X36942.dat'
    get_grt_cal.plot_arb_temp_function_2(calibration_curve_data_path=calibration_curve_data_path)
    #get_grt_cal.plot_arb_temp_function(calibration_curve_data_path=calibration_curve_data_path, x_range=(50, 100))
    #get_grt_cal.test(50)
    #pl.show()
    #get_grt_cal.get_cal(calibration_curve_data_path)
