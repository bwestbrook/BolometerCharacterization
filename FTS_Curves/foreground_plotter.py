import pylab as pl
import numpy as np
#Dust parameters                                                                                                                                                                                           
#angDustFact = 0.5*2*10*(10.0/1.8/8.0)*2e-6 #uK^2                                                                                                                                                          
angDustFact = 2*4e-12
dustSpecIndex = 1.5
dustEll0 = 10.0
dustNu0 = 90.0e9
dustM = -0.5

#For calculating the polarized galactic dust angular power spectrum

def dustAngPowSpec(eta, nu, ell, fact=angDustFact, beta=dustSpecIndex, ell0=dustEll0, nu0=dustNu0, m=dustM):
        return eta*((2 * np.pi * fact) / (ell * (ell + 1))) * ((nu / nu0) ** (2 * beta)) * ((ell / ell0) ** m)
        #return eta*((fact))*((nu/nu0)**(2*beta))*((ell/ell0)**m)                                                                                                                                       

#Synchrotron parameters                                                                                                                                                                                 
angSyncFact = 0.5*2*10*(0.1/1.8/9)*2e-6 #uK^2                                                                                                                                                           
angSyncFact = 2e-12
syncSpecIndex = -3.0
syncEll0 = 10.0
syncNu0 = 90.0e9
syncM = -0.6

#For calculating the polarized synchrotron radiation angular power spectrum

def syncAngPowSpec(eta, nu, ell, fact=angSyncFact, beta=syncSpecIndex, ell0=syncEll0, nu0=syncNu0, m=syncM):
        return eta*((2 * np.pi * fact) / (ell * (ell + 1))) * ((nu / nu0) ** (2 * beta)) * ((ell / ell0) ** m)
        #return eta*((fact))*((nu/nu0)**(2*beta))*((ell/ell0)**m)

def write_foreground_data_to_file(save_path, frequencies, intensities):
    with open(save_path, 'w') as file_handle:
        for i in range(frequencies.size):
            line = '{0}\t{1}\n'.format(frequencies[0], intensities[1])
            file_handle.write(line)

def run_test():
    frequencies = np.arange(10e9, 1e12, 100e6)
    sync_intensities = np.zeros(frequencies.size)
    dust_intensities = np.zeros(frequencies.size)
    for i, nu in enumerate(frequencies):
        sync_intensity = syncAngPowSpec(1, nu, 100)
        dust_intensity = dustAngPowSpec(1, nu, 100)
        np.put(sync_intensities, i, sync_intensity)
        np.put(dust_intensities, i, dust_intensity)
    save_path_sync = './Output/synchrotron_foreground.dat'
    write_foreground_data_to_file(save_path_sync, frequencies, sync_intensities)
    save_path_dust = './Output/dust_foreground.dat'
    write_foreground_data_to_file(save_path_dust, frequencies, dust_intensities)
    fig = pl.figure()
    ax1 = fig.add_subplot(111)
    ax1.loglog(frequencies / 1e9, sync_intensities, 'g', label='Synchrotron')
    ax1.loglog(frequencies / 1e9, dust_intensities, 'r', label='Dust')
    ax1.legend(loc='best')
    ax1.set_xticks([50, 150, 250, 350, 450])
    ax1.set_xticklabels([50, 150, 250, 350, 450])
    ax1.set_xlim([50, 450])
    for axis in fig.get_axes():
        handles, labels = axis.get_legend_handles_labels()
        axis.legend(handles, labels, numpoints=1, loc='best')
    fig.show()

if __name__ == '__main__':
    run_test()
