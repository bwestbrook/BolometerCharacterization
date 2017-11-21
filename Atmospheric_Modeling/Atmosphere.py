import subprocess
import pylab as pl

class Atmosphere():

    def __init__(self):
        self.start_freq = '0' # GHz
        self.end_freq = '400' # GHz
        self.freq_bins = '50' # MHz
        self.zenith_angle = '60' # Degs
        self.trop_h20_scale_factor = '1.0' #

    def run(self, config_file_path):
        am_command = '{0} {1} GHz {2} GHz {3} MHz {4} deg {5}'.format(config_file_path,
                                                                      self.start_freq, self.end_freq,
                                                                      self.freq_bins, self.zenith_angle,
                                                                      self.trop_h20_scale_factor)
        am_command = 'am {0} {1} GHz {2} GHz {3} MHz {4} deg {5}'.format(config_file_path,
                                                                         self.start_freq, self.end_freq,
                                                                         self.freq_bins, self.zenith_angle,
                                                                         self.trop_h20_scale_factor)

        am_command_list = ['am', config_file_path, self.start_freq, 'GHz', self.end_freq, 'GHz',
                           self.freq_bins, 'MHz', self.zenith_angle, 'deg', self.trop_h20_scale_factor]

        output = subprocess.Popen(am_command_list, stdout=subprocess.PIPE)
        frequencies, transmissions = [], []
        with open('chajnantor.dat', 'w') as atm_file_handle:
            for line in output.stdout.readlines():
                frequency = line.split(' ')[0]
                frequencies.append(frequency)
                transmission = line.split(' ')[2]
                transmissions.append(transmission)
                new_line = '{0}, {1}\n'.format(frequency, transmission)
                atm_file_handle.write(new_line)
        pl.plot(frequencies, transmissions)
        pl.show()



if __name__ == '__main__':
    am = Atmosphere()
    am.run('ACT_Annual_50.amc')
