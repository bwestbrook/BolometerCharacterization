import numpy as np
import pylab as pl
from .grt_calibration import resistance_to_temp


class RTCurve():

    def __init__(self, list_of_input_dicts):
        self.list_of_input_dicts = list_of_input_dicts
        self.xlim = (200, 1000)
        self.ylim = (0, 2.5)
        self.grt_list = [25070, 25312, 29268]

    def run(self, plot=True):
        if plot:
            fig = None
        for input_dict in self.list_of_input_dicts:
            grt_res_vector, sample_res_vector = self.load_data(input_dict)
            grt_temperature_vector = self.resistance_to_temp_grt(grt_res_vector, input_dict['grt_serial'])
            sample_res_vector = self.normalize_squid_output(sample_res_vector, input_dict)
            fig = None
            fig = self.plot_rt_curves(grt_temperature_vector, sample_res_vector, fig=fig, input_dict=input_dict)
        if plot:
            fig.subplots_adjust(left=0.08, right=0.95)
            axis = fig.get_axes()[0]
            axis.legend()
            pl.show()

    def normalize_squid_output(self, sample_res_vector, input_dict):
        if input_dict['invert']:
            sample_res_vector = list(np.asarray(sample_res_vector) * -1)
        if 'normal_res' in input_dict:
            if np.min(sample_res_vector) < 0:
                sample_res_vector += np.abs(np.min(sample_res_vector))
            elif np.min(sample_res_vector) > 0:
                sample_res_vector -= np.min(sample_res_vector)
            sample_res_vector *= (input_dict['normal_res'] / np.max(sample_res_vector))
        return sample_res_vector

    def load_data(self, input_dict, quick_plot=False):
        data_path = input_dict['data_path']
        grt_res_vector, sample_res_vector = [], []
        point = None
        with open(data_path, 'r') as file_handle:
            for i, file_line in enumerate(file_handle.readlines()):
                grt_res = float(file_line.split('\t')[0].strip('\r\n')) * input_dict['grt_res_factor']
                if grt_res < 0:
                    grt_res *= -1
                sample_res = float(file_line.split('\t')[1].strip('\r\n')) * input_dict['sample_res_factor']
                grt_res_vector.append(grt_res)
                sample_res_vector.append(sample_res)
        if quick_plot:
            pl.plot(grt_res_vector, sample_res_vector)
            pl.show()
        return np.asarray(grt_res_vector), np.asarray(sample_res_vector)

    def resistance_to_temp_grt(self, grt_res_vector, serial_number='29268'):
        grt_temperature_vector = resistance_to_temp(grt_res_vector, serial_number)
        return grt_temperature_vector

    def plot_rt_curves(self, grt_temperature_vector, sample_res_vector, in_millikelvin=False,
                       fig=None, input_dict={}):
        if fig is None:
            fig = pl.figure(figsize=(10, 5))
            axis = fig.add_subplot(111)
        else:
            axis = fig.get_axes()[0]
        if in_millikelvin:
            axis.plot(grt_temperature_vector, sample_res_vector, label=input_dict['label'])
        else:
            axis.plot(grt_temperature_vector * 1e3, sample_res_vector, label=input_dict['label'])
        axis.set_xlabel('Temperature (mK)')
        axis.set_ylabel('Sample Resistance ($\Omega$)')
        axis.legend()
        if 'title' in input_dict:
            axis.set_title(input_dict['title'])
        else:
            axis.set_title('Res vs. Temp')
        if 'xlim' in input_dict:
            axis.set_xlim(input_dict['xlim'])
        else:
            axis.set_xlim(self.xlim)
        if 'normal_res' in input_dict:
            upper = input_dict['normal_res'] * 1.1
            ylim = (0, upper)
            axis.set_ylim(ylim)
        else:
            axis.set_ylim(self.ylim)
        return fig

    def _ask_user_if_they_want_to_quit(self):
        raw_input('Do you want to quit?\n')


if __name__ == '__main__':
    rt = RTCurve()
    rt.run()
