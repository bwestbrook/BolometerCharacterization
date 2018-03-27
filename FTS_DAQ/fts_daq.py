import numpy as np
import pylab as pl
from pprint import pprint

class FTSDAQ():

    def __init__(self):
        self.hi = 'hi'

    def simulate_inteferogram(self, starting_position=-10000, ending_position=300000, step_size=500, test=False):
        dummy_int_x = np.arange(starting_position, ending_position, step_size)
        print dummy_int_x
        dummy_int_y = np.zeros(0)
        for i, x_pos in enumerate(dummy_int_x):
            noisy_sync = self.noisy_sync(x_pos)
            dummy_int_y = np.insert(dummy_int_y, i, noisy_sync)
        if test:
            pl.plot(dummy_int_x, dummy_int_y)
            pl.xlim(-10, 10)
            pl.show()
        return dummy_int_x, dummy_int_y

    def noisy_sync(self, x_pos, noise_amp=0.2):
        pure_sync = np.sinc(x_pos * 100)
        noise = pure_sync * noise_amp * (np.random.random() - 0.5)
        noisy_sync = pure_sync + noise
        return noisy_sync

    def get_data(self, x_position, scan_params):
        integration_time = scan_params['integration_time']
        sample_rate = scan_params['sample_rate']
        index = np.where(self.sim_int_x==x_position)
        central_value = self.sim_int_y[index]
        simulated_time_stream = self.simulate_time_stream(central_value, integration_time, sample_rate)
        mean = np.mean(simulated_time_stream)
        min_ = np.min(simulated_time_stream)
        max_ = np.max(simulated_time_stream)
        std = np.std(simulated_time_stream)
        return simulated_time_stream, mean, min_, max_, std

    def run_fts(self, scan_params):
        self.sim_int_x, self.sim_int_y = self.simulate_inteferogram(scan_params['starting_position'], scan_params['ending_position'],
                                                                    scan_params['step_size'])

    def test(self, test=False):
        self.simulate_inteferogram(starting_position=-2*np.pi, ending_position=2*np.pi, step_size=0.1, test=test)

if __name__ == '__main__':
    fts_daq = FTSDAQ()
    fts_daq.test(test=True)
