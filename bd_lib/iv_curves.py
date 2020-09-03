import os
import bisect
import numpy as np
import pylab as pl
from pprint import pprint
from copy import copy


class IVCurves():

    def __init__(self):
        self.r_n_fraction = 0.75
        self.simulated_bands_folder = 'bd_filter_bands'
        self.dewar_transmission = 0.75
