import nidaqmx
import os
import sys
import glob
#import serial
import time
import numpy as np
from pprint import pprint
from nidaqmx.constants import AcquisitionType, Edge, WAIT_INFINITELY

class BoloDAQ():

    def __init__(self):
        self.active_daqs = self.initialize_daqs()

    def get_data(self, signal_channels=[3,], int_time=50, sample_rate=500, device=None):
        with nidaqmx.Task() as task:
            if device is None:
                device = self.active_daqs[0]
            data_dict = {}
            for signal_channel in signal_channels:
                voltage_chan_str = '{0}/ai{1}'.format(device, signal_channel)
                print(signal_channels)
                print(signal_channel)
                print(voltage_chan_str)
                task.ai_channels.add_ai_voltage_chan(voltage_chan_str)
                data_dict[signal_channel] = {}
            int_time = int(int_time)
            sample_rate = int(sample_rate)
            num = int(int_time * sample_rate / 1000)
            task.timing.cfg_samp_clk_timing(rate=sample_rate, sample_mode=AcquisitionType.FINITE,
                                            samps_per_chan=num)
            data_time_stream = np.asarray(task.read(number_of_samples_per_channel=num, timeout=60*20))
            if type(data_time_stream[0]) == np.ndarray:
                for i, signal_channel in enumerate(signal_channels):
                    data_dict[signal_channel].update({'ts': data_time_stream[i]})
            else:
                data_dict[signal_channel].update({'ts': data_time_stream})
        for signal_channel in data_dict:
            data_time_stream = data_dict[signal_channel]['ts']
            mean = np.mean(data_time_stream)
            data_dict[signal_channel].update({'mean': mean})
            min_ = np.min(data_time_stream)
            data_dict[signal_channel].update({'min': min_})
            max_ = np.max(data_time_stream)
            data_dict[signal_channel].update({'max': max_})
            std_ = np.std(data_time_stream)
            data_dict[signal_channel].update({'std': std_})
        #import ipdb;ipdb.set_trace()
        return data_dict

    def initialize_daqs(self):
        daq_settings = {}
        with nidaqmx.Task() as task:
            for i in range(16): # Typically no more than a few here
                device = 'Dev{0}'.format(i)
                try:
                    task.ai_channels.add_ai_voltage_chan("{0}/ai0".format(device))
                    daq_settings[device] = {}
                    for j in range(16):
                        daq_settings[device].update({str(j): {'sample_rate': 5000, 'int_time': 100}})
                except nidaqmx.DaqError:
                    pass
        return daq_settings

if __name__ == '__main__':
    daq = DAQ()
    daq.get_data()
