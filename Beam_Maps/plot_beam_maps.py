import os
import json
import scipy.optimize as opt
import numpy as np
import pylab as pl
from scipy.signal import medfilt2d

class BeamMaps():

    def __init__(self):
        self.hi = 'hello'
        self.good_bye = 'good bye'


    ################################# 
    # Data Loading #
    ################################# 

    def load_beam_map_data(self, data_path, map_limit=2.5e6):
        '''
        This function loads the data output by labview
        Inputs
            data_path: string of the path to the data to be loaded
            map_limit: the limit of the map size in steps to load
                       used in case of loading a subset of the map
                       default (2.5e6, i.e. much bigger than will
                       be taken using the setup, loads all)
        Outputs:
            data_dict: a dictionary containg all of the data to be loaded
        '''
        data_dict = {'x_pos': [], 'y_pos': [], 'amp': [], 'error': []}
        x_grid, y_grid, x_ticks, y_ticks = self.get_grid_and_ticks(data_path)
        X_full, Y_full = np.meshgrid(x_grid, y_grid)
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            amplitude_vector = np.zeros(len(lines))
            error_vector = np.zeros(len(lines))
            for i, line in enumerate(lines):
                data_ = line.split('\t')
                amplitude_value = data_[2]
                error_ = data_[3]
                np.put(amplitude_vector, i, amplitude_value)
                np.put(error_vector, i, error_)
        if len(amplitude_vector) == X_full.size:
            Z = amplitude_vector.reshape(X_full.shape)
            E = error_vector.reshape(X_full.shape)
        else:
            print(X_full.shape)
            print(len(amplitude_vector))
            Z = np.zeros(X_full.shape)
            E = np.zeros(X_full.shape)
            k = 0
            for i in np.arange(X_full.shape[0]):
                for j in np.arange(Y_full.shape[0]):
                    if k < len(amplitude_vector):
                        Z[i][j] = amplitude_vector[k]
                        E[i][j] = error_vector[k]
                    k += 1
        return X_full, Y_full, Z.flatten(), E.flatten()

    ################################# 
    # All Plottting #
    ################################# 

    def plot_1D_beam_map(self, processed_data_dict, bolo_name='test'):
        fig = pl.figure(figsize=(6.5, 6.5))
        ax = fig.add_subplot(111)
        ax.plot(processed_data_dict['positions_in_inches'], processed_data_dict['amplitudes'], '*', label='Data')
        ax.plot(processed_data_dict['positions_in_inches'], processed_data_dict['fit_amplitudes'], label='Fit')
        ax.set_xlabel('Source Position (in)', fontsize=16)
        ax.set_ylabel('Amplitude (Au)', fontsize=16)
        ax.set_ylabel('Amplitude (Au)', fontsize=16)
        ax.set_title('1D Cut for {0}'.format(bolo_name), fontsize=16)
        ax.legend()
        fig.show()
        self._ask_user_if_they_want_to_quit()

    def get_grid_and_ticks(self, data_path):
        json_path = data_path.replace('.dat', '.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as meta_data_handle:
                meta_data = json.load(meta_data_handle)
        x_start = int(meta_data['_beam_mapper_popup_start_x_position_lineedit'])
        y_start = int(meta_data['_beam_mapper_popup_start_y_position_lineedit'])
        x_step = int(meta_data['_beam_mapper_popup_step_size_x_lineedit'])
        x_end = int(meta_data['_beam_mapper_popup_end_x_position_lineedit'])
        y_end = int(meta_data['_beam_mapper_popup_end_y_position_lineedit'])
        y_step = int(meta_data['_beam_mapper_popup_step_size_y_lineedit'])
        x_grid = np.arange(x_start, x_end + x_step, x_step)
        y_grid = np.arange(y_start, y_end + y_step, y_step)
        x_ticks = [str(int(x * 1e-3)) for x in x_grid]
        y_ticks = [str(int(x * 1e-3)) for x in y_grid]
        return x_grid, y_grid, x_ticks, y_ticks

    def set_ticks_and_labels(self, ax, x_ticks, y_ticks):
        x_tick_locs = [0.5 + x for x in range(len(x_ticks))]
        y_tick_locs = [0.5 + x for x in range(len(x_ticks))]
        ax.set_xticks(x_tick_locs)
        ax.set_yticks(y_tick_locs)
        ax.set_xticklabels(x_ticks, rotation=35, fontsize=10)
        ax.set_yticklabels(y_ticks, fontsize=10)
        ax.set_xlabel('X Position (k-steps)', fontsize=12)
        ax.set_ylabel('Y Position (k-steps)', fontsize=12)
        return ax

    def plot_beam_map_new(self, x_ticks, y_ticks, X, Y, Z, Z_fit):
        '''
        '''
        fig = pl.figure()
        ax1 = fig.add_subplot(311)
        ax2 = fig.add_subplot(312)
        ax3 = fig.add_subplot(313, projection='3d')
        # AX 2
        ax_image1 = ax1.pcolormesh(Z, label='Data')
        ax1.contour(Z_fit, color='w', lw='5', label='Fit')
        ax1.set_title('BEAM DATA WITH FIT', fontsize=12)
        ax1 = self.set_ticks_and_labels(ax1, x_ticks, y_ticks)
        color_bar = fig.colorbar(ax_image1, ax=ax1)
        ax1.legend()
        # AX 2
        ax_image2 = ax2.pcolormesh(Z - Z_fit, label='Residual')
        ax2.set_title('BEAM RESIDUAL')
        ax2 = self.set_ticks_and_labels(ax2, x_ticks, y_ticks)
        color_bar = fig.colorbar(ax_image2, ax=ax2)
        ax2.legend()
        # AX 2
        fig, ax3 = self.plot_3d(X, Y, Z, ax3, fig)
        ax3.set_title('BEAM Residual', fontsize=12)
        ax3 = self.set_ticks_and_labels(ax3, x_ticks, y_ticks)
        #ax3.legend()
        # Save and show
        fig.savefig('temp_files/temp_beam.png')
        #pl.legend()
        pl.show()

    def plot_3d(self, X, Y, Z, ax, fig):
        surface_plot = ax.plot_surface(X, Y, Z, label='3d')
        ax.set_zlabel('Normalized Amplitude')
        ax.set_title('3D Beammap')
        #color_bar = fig.colorbar(surface_plot, ax=ax)
        return fig, ax

    ################################# 
    # Math and Fitting Functions    #
    ################################# 

    def fit_data(self, X, Y, Z):
        XY = (X, Y)
        initial_guess = self.guess_fit_params_2D(Z)
        fit_params = self.fit_2D_gaussian(self.twoD_Gaussian, XY, Z, initial_guess)
        fit_amplitude = self.twoD_Gaussian(XY, *fit_params)
        return fit_amplitude

    def fit_1D_gaussian(self, function, position, amplitude, initial_guess):
        print(initial_guess)
        popt, pcov = opt.curve_fit(self.oneD_Gaussian, position, amplitude, p0=initial_guess)
        print(popt)
        return popt

    def fit_2D_gaussian(self, function, XY, Z, initial_guess):
        print(initial_guess)
        X, Y = XY[0], XY[0]
        print(X.shape, Z.size)
        popt, pcov = opt.curve_fit(self.twoD_Gaussian, XY, Z.T, p0=initial_guess)
        print(popt)
        return popt

    #Initial Guesses for Fitting
    def guess_fit_params_1D(self, positions, amplitudes):
        amplitude = amplitudes.max()
        x_0 = 0
        sigma_x = 0.5 * np.max(positions)
        return amplitude, x_0, sigma_x

    def guess_fit_params_2D(self, data):
        height = data.max()
        x = 0
        y = 0
        width_x = 25000
        width_y = 25000
        rotation = 0
        return height, x, y, width_x, width_y, rotation

    def twoD_Gaussian(self, XY, amplitude, x_0, y_0, sigma_x, sigma_y, theta):
        x = XY[0]
        y = XY[1]
        x_0 = float(x_0)
        y_0 = float(y_0)
        theta = np.deg2rad(theta)
        a = (np.cos(theta) ** 2) / (2 * sigma_x ** 2) + (np.sin(theta) ** 2) / (2 * sigma_y ** 2)
        b = -(np.sin(2 * theta)) / (4 * sigma_x ** 2) + (np.sin(2 * theta)) / (4 * sigma_y ** 2)
        c = (np.sin(theta) ** 2) / (2 * sigma_x ** 2) + (np.cos(theta) ** 2) / (2 * sigma_y ** 2)
        Z = amplitude * np.exp(- (a * ((x - x_0) **2) + 2 * b * (x - x_0) * (y - y_0) + c * ((y - y_0) ** 2)))
        return Z.ravel()

    def oneD_Gaussian(self, position, amplitude, x_0, sigma_x):
        x_0 = float(x_0)
        print(amplitude, x_0, sigma_x)
        gaussian = (amplitude / (sigma_x * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((position - x_0)/(sigma_x)) **2)
        return gaussian

    ################################# 
    # Run #
    ################################# 

    def run2(self, list_of_input_dicts):
        for input_dict in list_of_input_dicts:
            print(input_dict)
            data_path = input_dict['data_path']
            x_grid, y_grid, x_ticks, y_ticks = self.get_grid_and_ticks(data_path)
            X, Y, Z, E = self.load_beam_map_data(data_path)
            Z_fit = self.fit_data(X, Y, Z)
            self.plot_beam_map_new(x_ticks, y_ticks, X, Y, Z.reshape(X.shape), Z_fit.reshape(X.shape))

    ################################# 
    # General #
    ################################# 

    def _ask_user_if_they_want_to_quit(self):
        input_ = raw_input('Press q to (q)uit, Any other Key to Continue:\n')
        if input_ == 'q':
            print('Exiting')
            exit()

if __name__ == '__main__':
    bm = BeamMap()
