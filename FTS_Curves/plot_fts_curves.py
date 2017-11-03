import pylab as pl
import numpy as np
import sys
from foreground_plotter import ForegroundPlotter


class FTSCurve():

    def __init__(self, list_of_input_dicts):
        self.list_of_input_dicts = list_of_input_dicts

    def load_simulation_data(self, data_path):
        '''
        Inputs:
            data_path:  the path to the .fft data file (string)
        Outputs:
            frequency_vector: the extracted frequency vector
            transmission_vector: the extracted frequency vector
        Returns a frequency and transmission vector from the data file
        produced by Toki's LabView software
        '''
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            frequency_vector = np.zeros(len(lines))
            transmission_vector = np.zeros(len(lines))
            for i, line in enumerate(lines):
                frequency = line.split('\t')[0]
                transmission = line.split('\t')[1].strip('\n')
                transmission = 10.0 ** (float(transmission)/10.0)
                np.put(frequency_vector, i, float(frequency))
                np.put(transmission_vector, i, float(transmission))
        normalized_transmission_vector = transmission_vector / max(transmission_vector)
        return frequency_vector, transmission_vector, normalized_transmission_vector


    def save_FFT_data(self, frequency_vector, transmission_vector, save_path):
        '''
        Inputs:
            data_vector: the data vector to write to file
            save_path: path to save the data file to
        Outputs:
            None
        Returns a frequency and transmission vector from the data file
        produced by Toki's LabView software
        '''
        with open(save_path, 'w') as file_handle:
            for i, frequency in enumerate(frequency_vector):
                transmission = transmission_vector[i]
                line = '{0} \t {1}\n'.format(frequency, transmission)
                file_handle.write(line)
        return None


    def load_FFT_data(self, data_path, smoothing_factor=0):
        '''
        Inputs:
            data_path:  the path to the .fft data file (string)
        Outputs:
            frequency_vector: the extracted frequency vector
            transmission_vector: the extracted frequency vector
        Returns a frequency and transmission vector from the data file
        produced by Toki's LabView software
        '''
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            frequency_vector = np.zeros(len(lines))
            transmission_vector = np.zeros(len(lines))
            for i, line in enumerate(lines):
                frequency = line.split('\t')[0]
                transmission = line.split('\t')[1]
                np.put(frequency_vector, i, frequency)
                np.put(transmission_vector, i, transmission)
        if smoothing_factor > 0.0:
            transmission_vector = self.running_mean(transmission_vector, smoothing_factor=smoothing_factor)
        normalized_transmission_vector = transmission_vector / max(transmission_vector)
        return frequency_vector, transmission_vector, normalized_transmission_vector

    def load_IF_data(self, data_path):
        '''
        Inputs:
            data_path:  the path to the .if data file (string)
        Outputs:
            position_vector: the extracted frequency vector
            signal_vector: the extracted frequency vector
        Returns a frequency and transmission vector from the data file
        produced by Toki's LabView software
        '''
        with open(data_path, 'r') as file_handle:
            lines = file_handle.readlines()
            signal_vector = np.zeros(len(lines))
            position_vector = np.zeros(len(lines))
            for i, line in enumerate(lines):
                position = line.split('\t')[0]
                signal = line.split('\t')[1]
                np.put(position_vector, i, position)
                np.put(signal_vector, i, signal)
        return position_vector, signal_vector

    def plot_IF_data(self, position_vector, signal_vector, color='b',
                     label='', fig=None, plot_if=False, plot_fft=False):
        if fig is None:
            fig = pl.figure()
            if plot_fft and plot_if:
                fig.add_subplot(211)
                fig.add_subplot(212)
                ax = fig.get_axes()[1]
            elif plot_fft or plot_if:
                fig.add_subplot(111)
                ax = fig.get_axes()[0]
            fig.subplots_adjust(hspace=0.26, bottom=0.12, top =0.96, left=0.16, right=0.84)
        ax.set_xlabel('Mirror Position', fontsize=14)
        ax.set_ylabel('IF Signal ', fontsize=14)
        ax.plot(position_vector, signal_vector, color, label=label, lw=2)
        return fig

    def plot_FFT_data(self, frequency_vector, transmission_vector, color='b',
                      label='', xlim=(100,400), fig=None, plot_if=False, plot_fft=False):
        '''
        This function will take the output of Load_FFT_Data
        '''
        if fig is None:
            fig = pl.figure()
            if plot_fft and plot_if:
                fig.add_subplot(211)
                fig.add_subplot(212)
                ax = fig.get_axes()[1]
            elif plot_fft or plot_if:
                fig.add_subplot(111)
                ax = fig.get_axes()[0]
            fig.subplots_adjust(hspace=0.26, bottom=0.12, top =0.96, left=0.16, right=0.84)
        ax1 = fig.get_axes()[0]
        ax1.plot(frequency_vector, transmission_vector, color, label=label, lw=2)
        ax1.tick_params(labelsize=14)
        ax1.set_xlabel('Frequency (GHz)', fontsize=14)
        ax1.set_ylabel('Normalized Transmission', fontsize=14)
        ax1.set_xlim(xlim)
        for axis in fig.get_axes():
            handles, labels = axis.get_legend_handles_labels()
            axis.legend(handles, labels, numpoints=1, loc=1)
        return fig


    def _ask_user_if_they_want_to_quit(self):
        quit_boolean = raw_input('Press q to q(uit), any other key to continue:\n')
        if quit_boolean == 'q':
            exit()

        N = int(smoothing_factor * len(vector))

    def running_mean(self, vector, smoothing_factor=0.01):
        print smoothing_factor
        print smoothing_factor
        print smoothing_factor
        N = int(smoothing_factor * len(vector))
        averaged_vector = np.zeros(len(vector))
        for i, value in enumerate(vector):
            low_index = i
            hi_index = i + N
            if hi_index > len(vector) - 1:
                hi_index = len(vector) - 1
            averaged_value = np.mean(vector[low_index:hi_index])
            np.put(averaged_vector, i, averaged_value)
        return averaged_vector

    def run(self, save_fft=False, run_open_comparison=False,
            add_atmosphric_lines=False, add_foreground=False):
        fig = None
        plot_if = False
        plot_fft = False
        for dict_ in self.list_of_input_dicts:
            if '.if' == dict_['measurements']['data_path'][-3:]:
                plot_if = True
            elif '.fft' == dict_['measurements']['data_path'][-4:]:
                plot_fft = True
        for dict_ in self.list_of_input_dicts:
            data_path = dict_['measurements']['data_path']
            label = dict_['measurements']['plot_label']
            color = dict_['measurements']['color']
            color = dict_['measurements']['color']
            xlim = dict_['measurements']['xlim']
            smoothing_factor = float(dict_['measurements']['smoothing_factor'])
            if data_path[-4:] == '.fft':
                frequency_vector, transmission_vector, normalized_transmission_vector = self.load_FFT_data(data_path, smoothing_factor=smoothing_factor)
                if run_open_comparison:
                    open_data_path = dict_['open_air']['data_path']
                    data_path = dict_['measurements']['data_path']
                    open_frequency_vector, open_transmission_vector, open_normalized_transmission_vector = self.load_FFT_data(open_data_path)
                    divided_transmission_vector = transmission_vector / open_transmission_vector
                else:
                    divided_transmission_vector = normalized_transmission_vector
                if save_fft:
                    save_path = './Output/{0}_Filter_Transmission.fft'.format(dict_['filter_name'])
                    save_path = 'out.fft'
                    self.save_FFT_data(frequency_vector, divided_transmission_vector, save_path)
                fig = self.plot_FFT_data(frequency_vector, divided_transmission_vector, color=color, label=label, xlim=xlim,
                                         fig=fig, plot_if=plot_if, plot_fft=plot_fft)
                print 'plottting FFT', data_path
            elif data_path[-3:] == '.if':
                position_vector, signal_vector = self.load_IF_data(data_path)
                fig = self.plot_IF_data(position_vector, signal_vector, color=color, label=label, fig=fig,
                                         plot_if=plot_if, plot_fft=plot_fft)
                print 'plottting IF', data_path
        fig.savefig('{0}.png'.format(label))
        pl.show()


if __name__ == '__main__':
    dict_12icm = {'filter_name': '12icm',
                  'open_air': {'data_path': "./Data/MMF/2015_03_20/003_OpenAir_High_Res.fft",
                               'label': 'Open Trans', 'color': 'r'},
                  'measurements': {'data_path': "./Data/MMF/2015_03_20/004_576_12icm_High_Res.fft",
                                   'label': 'Raw Trans', 'color': 'b'}}
    dict_14icm = {'filter_name': '14icm',
                  'open_air': {'data_path': "2015_03_20\\003_OpenAir_High_Res.fft",
                               'label': 'Open Trans', 'color': 'g'},
                  'measurements': {'data_path': "2015_03_20\\010_576_14icm_High_Res.fft",
                                   'label': 'Raw Trans', 'color': 'm'}}
    dict_18icm = {'filter_name': '18icm',
                  'open_air': {'data_path': "2015_03_20\\003_OpenAir_High_Res.fft",
                               'label': 'Open Trans', 'color': 'k'},
                  'measurements': {'data_path': "2015_03_20\\011_576_18icm_High_Res.fft",
                                   'label': 'Raw Trans', 'color': 'm'}}
    list_of_input_dicts = [dict_12icm]
    fts = FTSCurve(list_of_input_dicts)
    fts.run()
