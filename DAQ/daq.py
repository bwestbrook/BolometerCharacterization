import numpy as np
import pylab as pl

class DAQ():
    def __init__(self):
        print 'hi'

    def get_data(self, signal_channel, integration_time, sample_rate):
        return np.random.random()


if __name__ == '__main__':
    daq = DAQ()
    print daq.get_data(0, 500, 50)
