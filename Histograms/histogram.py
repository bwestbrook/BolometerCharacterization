import cPickle
from pprint import pprint
import pylab as pl
import numpy as np

class RTHist():

    def __init__(self):
        print 'hello'
        self.pkl_path_1 = 'C:\Users\jamin\Repositories\BolometerCharacterization\Data\\2017_11_03\\20170712_raise_PB201101_res_Tc.pkl'
        self.pkl_path_2 = 'C:\Users\jamin\Repositories\BolometerCharacterization\Data\\2017_11_03\\20170712_raise_PB201102_res_Tc.pkl'
        self.pkl_path_3 = 'C:\Users\jamin\Repositories\BolometerCharacterization\Data\\2017_11_03\\Overbiased_Resistance_fromIV_Run38_20171103.pkl'
        # plotting for Tc
        self.tc_bins = 20
        self.tc_xlim = (400, 540)
        # plotting for Rn
        self.rn_bins = 35
        self.rn_xlim = (0.5, 2.5)

    def load_data(self, pkl_path=None):
        if pkl_path is None:
            pkl_path = self.pkl_path_1
        with open(pkl_path, 'r') as pkl_handle:
            data = cPickle.load(pkl_handle)
        return data

    def extract_tc_from_kek(self, data, xlim=None, bins=None):
        if xlim is None:
            xlim = self.tc_xlim
        if bins is None:
            bins = self.tc_bins
        tc_vector = 1e3 * np.asarray([float(data[x][0]) for x in range(data.shape[0])]) #mK
        tc_vector = tc_vector[tc_vector > xlim[0]]
        tc_vector = tc_vector[tc_vector < xlim[1]]
        return tc_vector

    def extract_rn_from_darcy(self, data, xlim=None, bins=None):
        if xlim is None:
            xlim = self.rn_xlim
        if bins is None:
            bins = self.rn_bins
        rn_vector = np.asarray([float(x) for x in data])
        rn_vector = rn_vector[rn_vector > xlim[0]]
        rn_vector = rn_vector[rn_vector < xlim[1]]
        return rn_vector

    def basic(self):
        data = np.asarray([1.27, 1.29, 1.25, 1.19, 1.09, 1.21])
        data = np.asarray([465, 461, 454, 457])
        data = np.asarray([10.4, 10.0, 24.8, 20.1])
        self.make_histogram(data, xlabel='Psat (pW)', ylabel='Count', xlim=(8, 30),
                            bins=10, title='13-18 and 13-20 witness pixel Psat')

    def make_histogram(self, data, xlabel='', ylabel='', xlim=(0,2), bins=20, title=''):
        counts, bins, patches = pl.hist(data, bins, range=xlim, normed=False)
        pl.title(title)
        pl.xlabel(xlabel, fontsize=16)
        pl.ylabel(ylabel, fontsize=16)
        pl.show()

    def run(self):
        all_tc_data = np.asarray([])
        for pkl_path in [self.pkl_path_1, self.pkl_path_2]:
            data = self.load_data(pkl_path)
            tc_vector = self.extract_tc_from_kek(data)
            print
            print
            print np.median(tc_vector)
            print np.std(tc_vector)
            all_tc_data = np.append(all_tc_data, tc_vector)
        print
        print
        print np.median(all_tc_data)
        print np.std(all_tc_data)
        self.make_histogram(all_tc_data, xlabel='$T_c$ (mK)', ylabel='Count',
                            xlim=self.tc_xlim, bins=self.tc_bins)
        all_rn_data = np.asarray([])
        for pkl_path in [self.pkl_path_3]:
            data = self.load_data(pkl_path)
            rn_vector = self.extract_rn_from_darcy(data)
            all_rn_data = np.append(all_rn_data, rn_vector)
        print
        print
        print np.median(all_rn_data)
        print np.std(all_rn_data)
        self.make_histogram(all_rn_data, xlabel='$R_n$ ($\Omega$)', ylabel='Count',
                            xlim=self.rn_xlim, bins=self.rn_bins)

if __name__ == '__main__':
    rt_hist = RTHist()
    #rt_hist.run()
    rt_hist.basic()
