import nidaqmx
import os
import sys
import glob
#import serial
import time
import numpy as np
from nidaqmx.constants import AcquisitionType, Edge, WAIT_INFINITELY

class DAQ():
    
    def __init__(self):
        self.active_daqs = self.get_active_daqs()


    def get_data(self, signal_channel=3, integration_time=50, sample_rate=500, daq=None):
        with nidaqmx.Task() as task:
            if daq is None:
                daq = self.active_daqs[0]
            voltage_chan_str = '{0}/ai{1}'.format(daq, signal_channel)
            task.ai_channels.add_ai_voltage_chan(voltage_chan_str)
            integration_time = int(integration_time)
            sample_rate = int(sample_rate)
            num = int(integration_time * sample_rate / 1000)
            task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode=AcquisitionType.FINITE,
                                            samps_per_chan=num)
            data_time_stream = np.asarray(task.read(number_of_samples_per_channel=num, timeout=60*20))
        mean = np.mean(data_time_stream)
        min_ = np.min(data_time_stream)
        max_ = np.max(data_time_stream)
        std_ = np.std(data_time_stream)
        return data_time_stream, mean, min_, max_, std_

    def get_active_daqs(self):
        active_daqs = []
        with nidaqmx.Task() as task:
            for i in range(16):
                device = 'Dev{0}'.format(i)
                try:
                    task.ai_channels.add_ai_voltage_chan("{0}/ai0".format(device))
                    active_daqs.append(device)
                    print('Found an active DAQ at {0}'.format(device))
                except nidaqmx.DaqError:
                    pass
        return active_daqs

if __name__ == '__main__':
    daq = DAQ()
    daq.get_data()
