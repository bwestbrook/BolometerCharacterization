import pylab as pl
import numpy as np
#Dust parameters                                                                                                                                                                                           
#angDustFact = 0.5*2*10*(10.0/1.8/8.0)*2e-6 #uK^2                                                                                                                                                          
class ForegroundPlotter():

    def __init__(self):
        self.angDustFact = 2*4e-12
        self.dustSpecIndex = 1.5
        self.dustEll0 = 10.0
        self.dustNu0 = 90.0e9
        self.dustM = -0.5
        #Synchrotron parameters
        self.angSyncFact = 0.5*2*10*(0.1/1.8/9)*2e-6 #uK^2                                                           
        self.angSyncFact = 2e-12
        self.syncSpecIndex = -3.0
        self.syncEll0 = 10.0
        self.syncNu0 = 90.0e9
        self.syncM = -0.6

    #For calculating the polarized galactic dust angular power spectrum
    def dustAngPowSpec(self, eta, nu, ell, fact=None, beta=None, ell0=None, nu0=None, m=None):
        if fact is None:
            fact = self.angDustFact
        if beta is None:
            beta = self.dustSpecIndex
        if ell0 is None:
            ell0 = self.dustEll0
        if nu0 is None:
            nu0 = self.dustNu0
        if m is None:
            m = self.dustM
        return eta*((2 * np.pi * fact) / (ell * (ell + 1))) * ((nu / nu0) ** (2 * beta)) * ((ell / ell0) ** m)

    #For calculating the polarized synchrotron radiation angular power spectrum
    def syncAngPowSpec(self, eta, nu, ell, fact=None, beta=None, ell0=None, nu0=None, m=None):
        if fact is None:
            fact = self.angSyncFact
        if beta is None:
            beta = self.syncSpecIndex
        if ell0 is None:
            ell0 = self.syncEll0
        if nu0 is None:
            nu0 = self.syncNu0
        if m is None:
            m = self.syncM
        return eta*((2 * np.pi * fact) / (ell * (ell + 1))) * ((nu / nu0) ** (2 * beta)) * ((ell / ell0) ** m)

    def write_foreground_data_to_file(self, save_path, frequencies, intensities):
        with open(save_path, 'w') as file_handle:
            for i in range(frequencies.size):
                line = '{0}\t{1}\n'.format(frequencies[0], intensities[1])
                file_handle.write(line)

    def running_mean(self, vector, bin_size=0.1):
        N = int(bin_size * len(vector))
        cumsum = numpy.cumsum(numpy.insert(x, 0, 0)) 
        return (cumsum[N:] - cumsum[:-N]) / N

    def add_foreground(self, fig=None):
        frequencies = np.arange(10e9, 1e12, 100e6)
        sync_intensities = np.zeros(frequencies.size)
        dust_intensities = np.zeros(frequencies.size)
        for i, nu in enumerate(frequencies):
            sync_intensity = self.syncAngPowSpec(1, nu, 100)
            dust_intensity = self.dustAngPowSpec(1, nu, 100)
            np.put(sync_intensities, i, sync_intensity)
            np.put(dust_intensities, i, dust_intensity)
        save_path_sync = './Output/synchrotron_foreground.dat'
        self.write_foreground_data_to_file(save_path_sync, frequencies, sync_intensities)
        save_path_dust = './Output/dust_foreground.dat'
        self.write_foreground_data_to_file(save_path_dust, frequencies, dust_intensities)
        if fig is None:
            fig = pl.figure()
            ax = fig.add_subplot(111)
        else:
            ax = fig.get_axes()[0]
        ax.loglog(frequencies / 1e9, sync_intensities, 'g', label='Synchrotron')
        ax.loglog(frequencies / 1e9, dust_intensities, 'r', label='Dust')
        ax.legend(loc='best')
        ax.set_xticks([50, 150, 250, 350, 450])
        ax.set_xticklabels([50, 150, 250, 350, 450])
        ax.set_xlim([50, 450])
        for axis in fig.get_axes():
            handles, labels = axis.get_legend_handles_labels()
            axis.legend(handles, labels, numpoints=1, loc='best')
        pl.show()



    def run(self):
        self.add_foreground()

if __name__ == '__main__':
    fgplotter = ForegroundPlotter()
    fgplotter.run()
