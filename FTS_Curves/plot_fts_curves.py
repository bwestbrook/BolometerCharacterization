import pylab as pl
import numpy as np
import sys


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


    def load_FFT_data(self, data_path):
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
        normalized_transmission_vector = transmission_vector / max(transmission_vector)
        return frequency_vector, transmission_vector, normalized_transmission_vector


    def plot_FFT_data(self, frequency_vector, transmission_vector, color='b', label=''):
        '''
        This function will take the output of Load_FFT_Data
        '''
        fig = pl.figure()
        ax1 = fig.add_subplot(111)
        ax1.plot(frequency_vector, transmission_vector, color, label=label, lw=2)
        fig.subplots_adjust(bottom=0.12, top =0.96, left=0.16, right=0.84)
        ax1.tick_params(labelsize=20)
        ax1.set_xlabel('Frequency (GHz)', fontsize=28)
        ax1.set_ylabel('Normalized Transmission', fontsize=28)
        ax1.set_xlim([0, 450])
        ax1.set_ylim([-0.05, 1.05])
        for axis in fig.get_axes():
            handles, labels = axis.get_legend_handles_labels()
            #axis.legend(handles, labels, numpoints=1, loc=2, bbox_to_anchor=(1.01, 1.0))
            axis.legend(handles, labels, numpoints=1, loc=1)
        pl.show()
        fig.savefig('{0}.png'.format(label))
        return fig


    def _ask_user_if_they_want_to_quit(self):
        quit_boolean = raw_input('Press q to q(uit), any other key to continue:\n')
        if quit_boolean == 'q':
            exit()


    def run(self, save_fft=False, run_open_comparison=False):
        for dict_ in self.list_of_input_dicts:
            data_path = dict_['measurements']['data_path']
            label = dict_['measurements']['plot_label']
            color = dict_['measurements']['color']
            frequency_vector, transmission_vector, normalized_transmission_vector = self.load_FFT_data(data_path)
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
            fig = self.plot_FFT_data(frequency_vector, divided_transmission_vector, color=color, label=label)


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
    #list_of_input_dicts = [dict_12icm, dict_14icm]
    fts = FTSCurve(list_of_input_dicts)
    fts.run()
