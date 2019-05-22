import pylab as pl
from mpl_toolkits.mplot3d.axes3d import Axes3D
from scipy.signal import medfilt2d
import scipy.optimize as opt
import matplotlib
import numpy as np
import matplotlib.cm as cm
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import pylab as pl

class BeamMap():

    def __init__(self):
        self.hi = 'hello'
        self.good_bye = 'good bye'

    # Data Loading
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
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            y_position_vector = np.zeros(len(lines)) * np.nan
            x_position_vector = np.zeros(len(lines)) * np.nan
            amplitude_vector = np.zeros(len(lines)) * np.nan
            error_vector = np.zeros(len(lines)) * np.nan
            for i, line in enumerate(lines):
                data_ = line.split('\t')
                x_position = data_[0]
                y_position = data_[1]
                amplitude_value = data_[2]
                error_ = data_[3]
                reduce_ = False
                if reduce_:
                    if np.abs(float(x_position)) < map_limit and np.abs(float(y_position)) < map_limit:
                        np.put(x_position_vector, i, x_position)
                        np.put(y_position_vector, i, y_position)
                        np.put(amplitude_vector, i, amplitude_value)
                        np.put(error_vector, i, error_)
                else:
                    np.put(x_position_vector, i, x_position)
                    np.put(y_position_vector, i, y_position)
                    np.put(amplitude_vector, i, amplitude_value)
                    np.put(error_vector, i, error_)
        x_position_vector = x_position_vector[~np.isnan(x_position_vector)]
        y_position_vector = y_position_vector[~np.isnan(y_position_vector)]
        amplitude_vector = amplitude_vector[~np.isnan(amplitude_vector)]
        error_vector = error_vector[~np.isnan(x_position_vector)]
        data_dict = {'x_position': x_position_vector, 'y_position': y_position_vector,
                     'amplitude': amplitude_vector, 'error': error_vector}
        return data_dict

    # Data Parsing
    def parse_1D_beam_map_data(self, data_dict, cut='x'):
        if np.max(data_dict['y_position']) == 0.0:
            positions = data_dict['x_position']
        else:
            positions = data_dict['y_position']
        positions_in_inches = positions / 1e5
        max_amplitude = np.max(data_dict['amplitude'])
        amplitudes = data_dict['amplitude']
        normalized_amplitudes = amplitudes / max_amplitude
        initial_guess = self.guess_fit_params_1D(positions_in_inches, amplitudes)
        fit_params = self.fit_1D_gaussian(self.oneD_Gaussian, positions_in_inches, amplitudes, initial_guess)
        fit_amplitudes = self.oneD_Gaussian(positions_in_inches, *fit_params)
        max_fit_amplitude = np.max(fit_amplitudes)
        normalized_fit_amplitudes = fit_amplitudes / max_fit_amplitude
        processed_data_dict = {'positions': positions, 'positions_in_inches': positions_in_inches,
                               'amplitudes': amplitudes,'normalized_amplitudes': normalized_amplitudes,
                               'fit_amplitudes': fit_amplitudes, 'normalized_fit_amplitudes': normalized_amplitudes,
                               'fit_params': fit_params}
        return processed_data_dict

    def parse_beam_map_data(self, data_dict, source_distance=18.0, is_1D=False, cut='x'):
        '''
        This function parse the raw data loaded by load_data
        '''
        if is_1D:
            processed_data_dict = self.parse_1D_beam_map_data(data_dict, cut=cut)
        else:
            #Load the raw data
            X_Pos_Data = data_dict['x_position']
            Y_Pos_Data = data_dict['y_position']
            raw_amplitude = data_dict['amplitude']
            # Convert to angle 
            X_Pos_Angle = (180.0 / np.pi) * np.arctan((data_dict['x_position'] / 100000.) / source_distance)
            Y_Pos_Angle = (180.0 / np.pi) * np.arctan((data_dict['x_position'] / 100000.) / source_distance)
            # Find the stepping scheme and compute a few useful values
            raw_x = sorted(list(set(X_Pos_Angle)))
            raw_y = sorted(list(set(Y_Pos_Angle)))
            num_step_x = len(raw_x)
            num_step_y = len(raw_y)
            step_size_x = (max(raw_x) - np.min(raw_x)) / (num_step_x - 1)
            step_size_y = (max(raw_y) - np.min(raw_y)) / (num_step_y - 1)
            boundary_x = step_size_x * (num_step_x - 1) / 2
            boundary_y = step_size_y * (num_step_y - 1) / 2
            plot_extent = [-boundary_x, boundary_x, -boundary_y, boundary_y]
            # Create a matrix with the X, Y values
            if len(np.arange(-boundary_x, boundary_x + step_size_x / 2.0, step_size_x)) % 2 == 0:
                X, Y = np.meshgrid(np.arange(-boundary_x, boundary_x, step_size_x),
                                   np.arange(-boundary_x, boundary_x, step_size_x))
            else:
                X, Y = np.meshgrid(np.arange(-boundary_x, boundary_x + step_size_x / 2.0, step_size_x),
                                   np.arange(-boundary_x, boundary_x + step_size_x / 2.0, step_size_x))
            # Re-shape and normalize the amplitude data
            try:
                print
                print 'Basic boundary conditions extracted from data'
                print -boundary_x, -boundary_y, boundary_x, boundary_y
                print raw_amplitude.shape
                print X.shape
                amplitude = raw_amplitude.reshape(X.shape)
                print
                print
            except ValueError:
                print 'data size error padding with zeroes'
                zeros = np.zeros(Y.shape[0] ** 2 - raw_amplitude.shape[0])
                padded_amplitude = np.append(raw_amplitude, zeros)
                raw_amplitude = padded_amplitude
                amplitude = padded_amplitude.reshape(X.shape)
            normalized_amplitude = amplitude / np.max(amplitude)
            initial_guess = self.guess_fit_params_2D(raw_amplitude.reshape(X.shape))
            fit_params = self.fit_2D_gaussian(self.twoD_Gaussian, X, Y, raw_amplitude, initial_guess)
            fit_amplitude = self.twoD_Gaussian((X, Y), *fit_params)
            fit_amplitude = fit_amplitude.reshape(X.shape)
            normalized_fit_amplitude = fit_amplitude / np.max(fit_amplitude)
            residual_amplitude = normalized_amplitude - normalized_fit_amplitude
            processed_data_dict = {'X': X, 'Y': Y, 'fit_params': fit_params,
                                   'normalized_fit_amplitude': normalized_fit_amplitude, 'fit_amplitude': fit_amplitude,
                                   'amplitude': amplitude, 'normalized_amplitude': normalized_amplitude,
                                   'residual_amplitude': residual_amplitude,
                                   'extent': plot_extent}
        return processed_data_dict

    # All Plottting 
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

    def plot_beam_map(self, processed_data_dict, bolo_name='test',
                      plot_raw=True, save_raw=True,
                      plot_fits=True, save_fits=True,
                      plot_3d=True, save_3d=True,
                      clip=True, clip_value=10):
        # crete a figure if needed
        X, Y = processed_data_dict['X'], processed_data_dict['Y'],
        Z_data, Z_fit, Z_res = processed_data_dict['normalized_amplitude'], processed_data_dict['normalized_fit_amplitude'],\
                               processed_data_dict['residual_amplitude']
        if clip:
            for i in np.arange(len(X)):
                for j in np.arange(len(Y)):
                    if np.abs(X[i, j]) > clip_value or np.abs(Y[i,j]) > clip_value:
                        Z_data[i, j] = 0.0
                        Z_fit[i, j] = 0.0
                        Z_res[i, j] = 0.0
        if plot_raw or save_raw:
            self.plot_raw(X, Y, Z_data, Z_fit, label=bolo_name, contours='fit')
        if plot_fits:
            self.plot_fits(X, Y, Z_data, Z_fit, Z_res, label=bolo_name)
        if plot_3d:
            self.plot_3d(X, Y, Z_data, label=bolo_name)

    def plot_raw(self, X, Y, Z, Z_fit, label='', contours='data'):
        fig_raw = pl.figure(figsize=(6.5, 6.5))
        box_size = 0.70 #width and height
        box_start_corner = 0.19 # lower left corner
        main_box_rectangle = (box_start_corner, box_start_corner, box_size, box_size)
        cb_box_rectangle = (box_size + 0.2, box_start_corner, 0.04, box_size)
        ax_raw = fig_raw.add_axes(main_box_rectangle)
        ax_raw.tick_params(labelsize=18)
        fig_raw_cb_axis = fig_raw.add_axes(cb_box_rectangle)
        ax_raw.set_xlabel('X position ($^{\circ}$)', fontsize=24)
        ax_raw.set_ylabel('Y position ($^{\circ}$)', fontsize=24)
        ax_raw.set_title('Beam Map\n{0}'.format(label), fontsize=24)
        color_plot_data = ax_raw.pcolor(X, Y, Z, label='Data',
                                        vmin=np.nanmin(Z), vmax=np.nanmax(Z),
                                        cmap=matplotlib.cm.jet)
        if contours == 'data':
            contour_plot_data = ax_raw.contour(X, Y, Z, 8, color='w',
                                               vmin=0, vmax=np.nanmax(Z))
        elif contours == 'fit':
            contour_plot_data = ax_raw.contour(X, Y, Z_fit, 8, color='w',
                                               vmin=0, vmax=np.nanmax(Z))
        fig_raw.colorbar(color_plot_data, cax=fig_raw_cb_axis)
        save_str_raw = './Output/Python/Beam_Map_{0}_GHz.png'.format(label)
        fig_raw.savefig(save_str_raw, pad_inches=-1, axis='equal')
        fig_raw.show()
        self._ask_user_if_they_want_to_quit()

    def plot_fits(self, X, Y, Z_data, Z_fit, Z_res, label='', clip=False):
        fig_height = 10.
        fig_width = 5.
        left_align_position = 0.25
        sub_plot_width = 2.5
        sub_plot_height = sub_plot_width
        top_position = 0.72
        bot_position = 0.08
        cb_width = 0.06
        full_figure = pl.figure(figsize=(fig_width, 2.0 * fig_width))
        sub_plot_height = sub_plot_height / fig_height
        sub_plot_width = sub_plot_width / fig_width
        cb_align_position = sub_plot_width + left_align_position + 0.06
        mid_position = np.mean([top_position, bot_position])
        cb_bot_height = sub_plot_height
        cb_mid_height = sub_plot_height
        cb_top_height = sub_plot_height
        # Add the axes for the plots
        raw_data_cb_axis = full_figure.add_axes((cb_align_position, top_position, cb_width, cb_top_height))
        fit_data_cb_axis = full_figure.add_axes((cb_align_position, mid_position, cb_width, cb_mid_height))
        res_cb_axis = full_figure.add_axes((cb_align_position, bot_position, cb_width, cb_bot_height))
        # Add the axes for the plots
        ax_data = full_figure.add_axes((left_align_position, top_position, sub_plot_width, sub_plot_height))
        ax_fit = full_figure.add_axes((left_align_position, mid_position, sub_plot_width, sub_plot_height))
        ax_res = full_figure.add_axes((left_align_position, bot_position, sub_plot_width, sub_plot_height))
        # Create the color and contour maps for each of the three cases
        ### Data ###
        color_plot_data = ax_data.pcolor(X, Y, Z_data, label='Data',
                                         vmin=0, vmax=np.nanmax(Z_data),
                                         cmap=matplotlib.cm.jet)
        contour_plot_data = ax_data.contour(X, Y, Z_data, 8, label='Data', color='w', vmin=np.nanmin(Z_data), vmax=np.nanmax(Z_data))
        ### Fit ###
        color_plot_fit = ax_fit.pcolor(X, Y, Z_fit, label='Fit',
                                       vmin=np.nanmin(Z_fit), vmax=np.nanmax(Z_fit),
                                       cmap=matplotlib.cm.jet)
        contour_plot_fit = ax_fit.contour(X, Y, Z_fit, 8, label='Fit', color='w', vmin=np.nanmin(Z_fit), vmax=np.nanmax(Z_fit))
        ### Residual ###
        color_plot_res = ax_res.pcolor(X, Y, Z_res, label='Residual',
                                       vmin=np.nanmin(Z_res), vmax=np.nanmax(Z_res),
                                       cmap=matplotlib.cm.jet)
        contour_plot_res = ax_res.contour(X, Y, Z_res, 8, label='Residual', color='w', vmin=np.nanmin(Z_res), vmax=np.nanmax(Z_res))
        # Add text labels to the color map
        ax_data.text(0.05, 0.85, 'Data', color='w', fontsize=16, transform=ax_data.transAxes)
        ax_fit.text(0.05, 0.85, 'Fit', color='w', fontsize=16, transform=ax_fit.transAxes)
        ax_res.text(0.05, 0.85, 'Residual', color='k', fontsize=16, transform=ax_res.transAxes)
        if clip:
            # Data
            ax_data.set_xlim([-clip_value, clip_value])
            ax_data.set_ylim([-clip_value, clip_value])
            # Fit
            ax_fit.set_xlim([-clip_value, clip_value])
            ax_fit.set_ylim([-clip_value, clip_value])
            # Residual
            ax_res.set_xlim([-clip_value, clip_value])
            ax_res.set_ylim([-clip_value, clip_value])
        # Add the color bars
        full_figure.colorbar(color_plot_data, cax=raw_data_cb_axis)
        full_figure.colorbar(color_plot_fit, cax=fit_data_cb_axis)
        full_figure.colorbar(color_plot_res, cax=res_cb_axis)
        # Basic Plotting Options 
        ax_data.set_xlabel('X position ($^{\circ}$)', fontsize=16)
        ax_fit.set_xlabel('X position ($^{\circ}$)', fontsize=16)
        ax_res.set_xlabel('X position ($^{\circ}$)', fontsize=16)
        ax_data.set_ylabel('Y position ($^{\circ}$)', fontsize=16)
        ax_fit.set_ylabel('Y position ($^{\circ}$)', fontsize=16)
        ax_res.set_ylabel('Y position ($^{\circ}$)', fontsize=16)
        ax_data.set_title('Beam Map {0}'.format(label))
        save_str_fits = './Output/Python/Beam_Map_{0}_GHz_fits.png'.format(label)
        full_figure.savefig(save_str_fits, figsize=(6,6))
        full_figure.show()
        self._ask_user_if_they_want_to_quit()

    def plot_3d(self, X, Y, Z, label=''):
        fig_3d = pl.figure()
        ax_3d = fig_3d.add_subplot(111, projection='3d')
        surface_plot = ax_3d.plot_surface(X, Y, Z, rstride=1, cstride=1,
                                          vmin=np.nanmin(0), vmax=np.nanmax(Z_res),
                                          cmap=matplotlib.cm.jet)
        ax_3d.set_xlabel('X position ($^{\circ}$)')
        ax_3d.set_ylabel('Y position ($^{\circ}$)')
        ax_3d.set_zlabel('Normalized Amplitude')
        ax_3d.set_title('{0} GHz 3D Beammap'.format(label))
        fig_3d.colorbar(surface_plot)
        save_str_3d = './Output/Python/Beam_Map_{0}_GHz_3d.png'.format(label)
        if save_3d:
            fig_3d.savefig(save_str_3d, figsize=(6,6))
        fig_3d.show()
        self._ask_user_if_they_want_to_quit()

    #Definitions of the 1D and 2D cases
    def twoD_Gaussian(self, (x, y), amplitude, x_0, y_0, sigma_x, sigma_y, theta):
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
        print amplitude, x_0, sigma_x
        gaussian = (amplitude / (sigma_x * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((position - x_0)/(sigma_x)) **2)
        return gaussian

    #Fitting the 1D and 2D cases
    def fit_1D_gaussian(self, function, position, amplitude, initial_guess):
        print initial_guess
        popt, pcov = opt.curve_fit(self.oneD_Gaussian, position, amplitude, p0=initial_guess)
        print popt
        return popt

    def fit_2D_gaussian(self, function, X, Y, data, initial_guess):
        print initial_guess
        popt, pcov = opt.curve_fit(self.twoD_Gaussian, (X, Y), data, p0=initial_guess)
        print popt
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
        width_x = 1.0
        width_y = 1.0
        rotation = 0
        return height, x, y, width_x, width_y, rotation


## General Utilities
    def _ask_user_if_they_want_to_quit(self):
        input_ = raw_input('Press q to (q)uit, Any other Key to Continue:\n')
        if input_ == 'q':
            print 'Exiting'
            exit()


    def run(self, data_path, bolo_name, map_limit=2.5e6, test=False, is_1D=False):
        if test:
            X = np.linspace(0, 200, 201)
            Y = np.linspace(0, 200, 201)
            X, Y = np.meshgrid(X, Y)
            initial_params = (3, 100, 100, 20, 40, -45)
            data = self.twoD_Gaussian((X,Y), *initial_params)
            data_with_noise = data + 0.2 * np.random.normal(size=data.shape)
            initial_guess = (3, 100, 100, 20, 40, 0)
            fit_params = self.fit_2D_gaussian(self.twoD_Gaussian, X, Y, data_with_noise, initial_guess)
            fitted_data = self.twoD_Gaussian((X, Y), *fit_params)
            fig, ax = pl.subplots(1, 1)
            ax.hold(True)
            ax.pcolor(X, Y, fitted_data.reshape(X.shape), cmap=pl.cm.jet)
            ax.contour(X, Y, fitted_data.reshape(X.shape), 8, colors='w')
            fig.show()
            self._ask_user_if_they_want_to_quit()
        data_dict = self.load_beam_map_data(data_path, map_limit)
        processed_data_dict = self.parse_beam_map_data(data_dict, source_distance=5.3937, is_1D=is_1D)
        if is_1D:
            processed_data_dict = self.parse_beam_map_data(data_dict, source_distance=5.3937, is_1D=is_1D)
            fig = self.plot_1D_beam_map(processed_data_dict, bolo_name)
        else:
            processed_data_dict = self.parse_beam_map_data(data_dict, source_distance=5.3937, is_1D=is_1D)
            fig = self.plot_beam_map(processed_data_dict, bolo_name, clip=False, clip_value=12,
                                     plot_fits=True, plot_raw=True, plot_3d=False)


if __name__ == '__main__':
    bm = BeamMap()
# June 25 - 27th, 2018
    data_path = '../Data/2018_06_25/SQ4_2D_4by4in_0p125inStep_0p25inAp_Pix118_150T_Beammap.dat'
    data_path = '../Data/2018_06_26/SQ4_2D_2by2in_0p125inStep_0p25inAp_Pix118_150T_Beammap05.dat'
    data_path = '../Data/2018_06_26/SQ4_2D_6by6in_0p125inStep_0p25inAp_Pix118_150T_Beammap03.dat'
    data_path = '../Data/2018_06_26/SQ3_2D_6by6in_0p25inStep_0p5inAp_Pix118_00T_Beammap01.dat'
    bolo_name = 'PB201326-P1118-90T'
    data_path = '../Data/2018_06_27/SQ5_2D_6by6in_0p25inStep_0p5inAp_Pix101_90T_Beammap02.dat'
    bolo_name = 'PB201326-P101-90T'
    data_path = '../Data/2018_06_25/SQ4_2D_6by6in_0p25in_Pix118_150T_Beammap.dat'
    bolo_name = 'PB201326-P1118-150T'
    data_path = '../Data/2018_06_27/SQ2_2D_6by6in_0p25inStep_0p5inAp_Pix100_150B_Beammap03.dat'
    bolo_name = 'PB201326-P100-150B'
# July 25th - 26th, 2018
    #'PB201326-P118-150B'
    data_path = '../Data/2018_07_25/Pix118_150B_BeamMap_0inX6in_Yscan_0p5inAp_0p025inStep_SQ5.dat' #1D Y Scan
    data_path = '../Data/2018_07_25/Pix118_150B_BeamMap_6inX0in_Xscan_0p5inAp_0p025inStep_SQ5.dat' #1D X Scan
    data_path = '../Data/2018_07_25/Pix118_150B_BeamMap_6inX6in_0p5inAp_0p25inStep_SQ5.dat' #6x6 Low Res
    data_path = '../Data/2018_07_26/Pix118_150B_BeamMap_4inX4in_0p25inAp_0p125inStep_SQ5.dat' # 4x4 Hi Res
    bolo_name = 'PB201326-P118-150B'
    #'PB201326-P118-090T'
    data_path = '../Data/2018_07_25/Pix118_090T_BeamMap_6inX0in_Xscan_0p5inAp_0p025inStep_SQ6.dat' #1D X Scan
    data_path = '../Data/2018_07_25/Pix118_090T_BeamMap_0inX6in_Yscan_0p5inAp_0p025inStep_SQ6.dat' #1D Y Scan
    data_path = '../Data/2018_07_25/Pix118_090T_BeamMap_6inX6in_0p5inAp_0p25inStep_SQ6.dat' #6x6 Low Res
    data_path = '../Data/2018_07_26/Pix118_090T_BeamMap_4inX4in_0p25inAp_0p125inStep_SQ6.dat' # 4x4 Hi Res
    bolo_name = 'PB201326-P118-090T'
    #'PB201326-P101-150B'
    data_path = '../Data/2018_07_25/Pix101_150B_BeamMap_6inX0in_Xscan_0p5inAp_0p025inStep_SQ1.dat' #1D X Scan
    data_path = '../Data/2018_07_25/Pix101_150B_BeamMap_0inX6in_Yscan_0p5inAp_0p025inStep_SQ1.dat' #1D Y Scan
    data_path = '../Data/2018_07_25/Pix101_150B_BeamMap_6inX6in_0p5inAp_0p25inStep_SQ1.dat' #6x6 Low Res
    bolo_name = 'PB201326-P101-150B'
    #'PB201326-P069-150B'
    data_path = '../Data/2018_07_26/Pix069_150B_BeamMap_6inX6in_X_0p5inAp_0p25inStep_SQ3.dat' # 6x6 Low Res
    data_path = '../Data/2018_07_26/Pix069_150B_BeamMap_4inX4in_X_0p25inAp_0p125inStep_SQ3.dat' # 4x4 Hi Res
    bolo_name = 'PB201326-P069-150B'
    #'PB201326-P101-090T'
    data_path = '../Data/2018_07_26/Pix101_090T_BeamMap_6inX6in_X_0p5inAp_0p25inStep_SQ2.dat' # 6x6 Lo Res
    data_path = '../Data/2018_07_26/Pix101_090T_BeamMap_4inX4in_0p25inAp_0p125inStep_SQ2.dat' # 4x4 Hi Res
    bolo_name = 'PB201326-P101-090T'
    bm.run(data_path, test=False, is_1D=False, bolo_name=bolo_name)
