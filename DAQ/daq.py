import numpy as np
import pylab as pl
#import DAQDRIVER as daq_driver

class DAQ():

    def __init__(self):
        print 'hi'

    def get_data(self, signal_channel=0, integration_time=500, sample_rate=50, central_value=1.0,
                 simulate=True, plot=True):
        print signal_channel
        print integration_time
        print sample_rate
        n_samples = int(sample_rate) * (integration_time / 1000.)
        if simulate:
            simulated_time_stream = self.simulate_time_stream(central_value, integration_time, sample_rate)
        else:
            #self.daq_driver.get_buffer(signal_channel, integration_time, sample_rate)
            simulated_time_stream = np.random.rand(int(n_samples))
        mean = np.mean(simulated_time_stream)
        min_ = np.min(simulated_time_stream)
        max_ = np.max(simulated_time_stream)
        std_ = np.std(simulated_time_stream)
        if plot:
            fig = pl.figure(figsize=(3.5,1.5))
            ax = fig.add_subplot(111)
            fig.subplots_adjust(left=0.23, right=0.99, top=0.8, bottom=0.35)
            ax.set_xlabel('time (ms)')
            ax.set_ylabel('Signal')
            ax.set_title('Timestream Data')
            ax.plot(simulated_time_stream)
            fig.savefig('temp_ts.png')
            pl.close('all')
        return simulated_time_stream, mean, min_, max_, std_

    def read_buffer(self, signal_channel=0, integration_time=500, sample_rate=50, central_value=1.0, simulate=True):
        return raw_data

    def simulate_time_stream(self, central_value, integration_time, sample_rate, noise_factor=0.1):
        n_samples = int(sample_rate) * (integration_time / 1000.)
        simulated_time_stream = np.random.rand(int(n_samples))
        simulated_time_stream *= noise_factor
        simulated_time_stream += central_value
        return simulated_time_stream

if __name__ == '__main__':
    daq = DAQ()
    print daq.get_data(0, 500, 50)
