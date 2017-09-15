import pylab as pl
import numpy as np
import sys

def CR110_trans(t, f):   #t is thickness in cm, f is freq in GHz
#
# returns transmission of a plane wave through cold (4.8K) eccosorb CR110 (castable version of MF110)
# data from "Far infrared transmission of dielectrics at ... " Halpern et al Applied Optics 1986
# Note that this ignores the dielectric reflection, material has n=1.88 cold
# Teflon (n~1.4) is a good AR coating

	nu = f / 30.
	a = 0.30
	b = 1.2
	return np.exp(-(t * a * nu**b))

if __name__ == '__main__':
	if len(sys.argv) > 1:
		transmission = CR110_trans(float(sys.argv[1]), float(sys.argv[2]))
		print transmission
	else:
		frequencies = np.arange(0, 600)
		thicknesses = [0.1, 0.4, 0.7, 1.0]
		for thickness in thicknesses:
			transmissions = CR110_trans(thickness, frequencies)
			pl.plot(frequencies, transmissions, label='{0} cm CR110'.format(thickness))
		pl.ylabel('Transmission', fontsize=16)
		pl.xlabel('Frequency (GHz)', fontsize=16)
		pl.title('CR100 Transmission', fontsize=16)
		pl.legend()
		pl.show()

