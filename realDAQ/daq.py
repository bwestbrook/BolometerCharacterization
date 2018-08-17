import nidaqmx
import time
import numpy as np
from nidaqmx.constants import AcquisitionType, Edge

class DAQ():
    def get_data(self, signal_channel=5, integration_time=500, sample_rate=50, central_value=1.0):
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev1/ai{0}".format(int(signal_channel)))
            integration_time = int(integration_time)
            sample_rate = int(sample_rate)
            num = int(integration_time * sample_rate/1000)
            task.timing.cfg_samp_clk_timing(rate= sample_rate,sample_mode=AcquisitionType.FINITE,samps_per_chan=num)
            data_time_stream = task.read(number_of_samples_per_channel=num)
        mean = np.mean(data_time_stream)
        min_ = np.min(data_time_stream)
        max_ = np.max(data_time_stream)
        std_ = np.std(data_time_stream)
        return data_time_stream, mean, min_, max_, std_

    def get_data2(self, visa_x=0, visa_y=1):
       with nidaqmx.Task() as task:
           task.ai_channels.add_ai_voltage_chan("Dev1/ai{0}, Dev1/ai{1}".format(int(visa_x),int(visa_y)))
           task.timing.cfg_samp_clk_timing(rate = 50, sample_mode=AcquisitionType.FINITE,samps_per_chan=2)
           data_time_stream = task.read(number_of_samples_per_channel=2)
       return data_time_stream[0],data_time_stream[1]


if __name__ == '__main__':
    daq = DAQ()
    daq.get_data2()
