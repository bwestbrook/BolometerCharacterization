import numpy as np
import pylab as pl
from DAQ.daq import DAQ

class BeamMapDAQ():

    def __init__(self):
        self.hi = 'hi'
        self.daq = DAQ()

    def twoD_Gaussian(self, (x, y), amplitude, x_0, y_0, sigma_x, sigma_y, theta):
        x_0 = float(x_0)
        y_0 = float(y_0)
        theta = np.deg2rad(theta)
        a = (np.cos(theta) ** 2) / (2 * sigma_x ** 2) + (np.sin(theta) ** 2) / (2 * sigma_y ** 2)
        b = -(np.sin(2 * theta)) / (4 * sigma_x ** 2) + (np.sin(2 * theta)) / (4 * sigma_y ** 2)
        c = (np.sin(theta) ** 2) / (2 * sigma_x ** 2) + (np.cos(theta) ** 2) / (2 * sigma_y ** 2)
        Z = amplitude * np.exp(- (a * ((x - x_0) **2) + 2 * b * (x - x_0) * (y - y_0) + c * ((y - y_0) ** 2)))
        return Z.ravel()

    def fit_function(self, function, X, Y, data, initial_guess):
        popt, pcov = opt.curve_fit(twoD_Gaussian, (X, Y), data, p0=initial_guess)
        return popt

    def simulate_beam(self, scan_params):
        x_grid = np.linspace(scan_params['start_x_position'], scan_params['end_x_position'],  scan_params['n_points_x'])
        y_grid = np.linspace(scan_params['start_y_position'], scan_params['end_y_position'],  scan_params['n_points_y'])
        X, Y = np.meshgrid(x_grid, y_grid)
        fit_params = {'amplitude': 100, 'x_0': 0, 'y_0': 0, 'sigma_x': 15, 'sigma_y': 15, 'theta': 1}
        Z = self.twoD_Gaussian((X, Y), **fit_params)
        Z = Z.reshape(X.shape)
        fig = pl.figure()
        ax = fig.add_subplot(111)
        ax.pcolor(X, Y, Z)
        fig.savefig('temp_beam.png')
        pl.close('all')
        return X, Y, Z

    def get_map_value(self, x_pos, y_pos, scan_params, simulate=True):
        X, Y, Z_sim = self.simulate_beam(scan_params)
        self.daq.get_data(integration_time)

    def take_beam_map(self, scan_params):
        print Z_sim
        Z_data = np.zeros(shape=X.shape)
        x_grid = np.linspace(scan_params['start_x_position'], scan_params['end_x_position'],  scan_params['n_points_x'])
        y_grid = np.linspace(scan_params['start_y_position'], scan_params['end_y_position'],  scan_params['n_points_y'])
        with open('file.dat', 'wr') as fh:

        for i, x_pos in enumerate(x_grid):
            for j, y_pos in enumerate(y_grid):
                print x_pos, y_pos
                line = '{0}, {1}, {2} {3}\n'.format(x_pos, y_pos, data, std_)
                fh.write(line)
                Z_data[i][j] = Z_sim[i][j]
                fig = pl.figure()
                ax = fig.add_subplot(111)
                ax.pcolor(X, Y, Z)
                fig.savefig('temp_beam.png')
                pl.close('all')
                import ipdb;ipdb.set_trace()

    def test(self):
        print 'beam map DAQ'

if __name__ == '__main__':
    beam_map_daq = BeamMapDAQ()
    beam_map_daq.test()
