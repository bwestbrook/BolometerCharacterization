import os
import cPickle
from pprint import pprint
import pylab as pl
import numpy as np

class RTHist():

    def __init__(self):
        print 'hello'
        self.data_dir = 'C:\Users\jamin\Repositories\BolometerCharacterization\Data'
        #self.tc_path_1 = os.path.join(self.data_dir, 'PB201311\\180316_RvsT_PB201311_data.pkl')
        self.tc_path_1 = os.path.join(self.data_dir, 'PB201101\\20170712_raise_PB201101_res_Tc.pkl')
        self.tc_path_2 = os.path.join(self.data_dir, 'PB201102\\20170712_raise_PB201102_res_Tc.pkl')
        self.tc_paths = [self.tc_path_1]
        self.tc_paths = [self.tc_path_1, self.tc_path_2]
        #self.rn_path_1 = os.path.join(self.data_dir, 'PB201311\\180316_RvsT_PB201311_data.pkl')
        self.rn_path_1 = os.path.join(self.data_dir, 'PB201101\\Overbiased_Resistance_fromIV_Run38_20171103.pkl')
        self.rn_paths = [self.rn_path_1]
        #self.pturn_path_1 = os.path.join(self.data_dir, 'PB201311\\180416_Pturn_PB201311_data.pkl')
        #self.pturn_path_1 = os.path.join(self.data_dir, 'PB201108\\Pturn_1108_300k_load.pkl')
        self.pturn_path_1 = os.path.join(self.data_dir, 'PB201309\\bolometer_properties_from_IVs.pkl')
        self.pturn_paths = [self.pturn_path_1]
        # plotting for Tc
        self.tc_bins = 20
        self.tc_xlim = (400, 540)
        # plotting for Rn
        self.rn_bins = 35
        self.rn_xlim = (0.5, 2.5)
        # plotting for Pturn
        self.pturn_bins = 35
        self.pturn_xlim = (0, 35)

    def load_data(self, pkl_path=None):
        if pkl_path is None:
            pkl_path = self.pkl_path_1
        with open(pkl_path, 'r') as pkl_handle:
            data = cPickle.load(pkl_handle)
        return data

    def extract_data_from_john_pkl(self, data, rn=False, tc=False,
                                   psat=False, pturn=False):
        print data
        if rn:
            data_type_key = 'R_normal'
        elif tc:
            data_type_key = 'T_c'
        elif psat:
            data_type_key = 'P_sat'
        elif pturn:
            data_type_key = 'P_turn'
        elif rlatch:
            data_type_key = 'R_latch'
        data_array = np.asarray([])
        for bolo, bolo_data in data.iteritems():
            value = data[bolo][data_type_key] * 1e12 # pW
            data_array = np.append(data_array, value)
            print bolo, data_type_key, value, len(data_array)
        return data_array
        #exit()

    def extract_data_from_logan_pkl(self, data, rn=False, tc=False, pturn=False):
        if type(data) == dict:
            print data.keys()
            if return_rn:
                return data['Rn_corrected']
            if return_tc:
                return data['Tc']
            if return_pturn:
                return data['Psat_correct']
        else:
            print data
            return data

    def extract_data_from_kek_pkl(self, data, xlim=None, bins=None, tc=False, rn=False, pturn=False):
        if xlim is None:
            xlim = self.tc_xlim
        if bins is None:
            bins = self.tc_bins
        tc_vector = 1e3 * np.asarray([float(data[x][0]) for x in range(data.shape[0])]) #mK
        tc_vector = tc_vector[tc_vector > xlim[0]]
        tc_vector = tc_vector[tc_vector < xlim[1]]
        return tc_vector

    def extract_data_from_darcy_pkl(self, data, xlim=None, bins=None, pturn=False):
        data_vector = np.asarray([float(x) for x in data])
        if pturn:
            data_vector *= 1e12
        return data_vector

    def basic(self):
        data = np.asarray([1.27, 1.29, 1.25, 1.19, 1.09, 1.21])
        data = np.asarray([465, 461, 454, 457])
        data = np.asarray([10.4, 10.0, 24.8, 20.1])
        self.make_histogram(data, xlabel='Psat (pW)', ylabel='Count', xlim=(8, 30),
                            bins=10, title='13-18 and 13-20 witness pixel Psat')

    def make_histogram(self, data, xlabel='', ylabel='', xlim=(0,2), bins=20, title='', target_range=[]):
        counts, bins, patches = pl.hist(data, bins, range=xlim, normed=False)
        pl.title(title, fontsize=20)
        pl.xlabel(xlabel, fontsize=16)
        pl.ylabel(ylabel, fontsize=16)
        if len(target_range) == 2:
            print target_range
            if type(target_range[0]) == float:
                pl.axvline(target_range[0], color='r')
                pl.axvline(target_range[1], color='r')
                pl.axvspan(target_range[0], target_range[1], 0, 1, color='r', alpha=0.5)
            elif len(target_range[0]) == 2:
                print target_range
                print target_range
                pl.axvline(target_range[0][0], color='r')
                pl.axvline(target_range[0][1], color='r')
                pl.axvspan(target_range[0][0], target_range[0][1], 0, 1, color='r', alpha=0.5)
                pl.axvline(target_range[1][0], color='b')
                pl.axvline(target_range[1][1], color='b')
                pl.axvspan(target_range[1][0], target_range[1][1], 0, 1, color='b', alpha=0.5)
        pl.show()

    def run(self, run_tc=False, run_rn=False, run_pturn=False, run_psat=False,
            from_john=False, from_logan=False, from_kek=False, from_darcy=False):
        if run_tc:
            all_tc_data = np.asarray([])
            for pkl_path in self.tc_paths:
                data = self.load_data(pkl_path)
                if from_logan:
                    tc_vector = self.extract_data_from_logan_pkl(data, tc=True) * 1e3
                if from_darcy:
                    tc_vector = self.extract_data_from_darcy_pkl(data, tc=True)
                if from_kek:
                    tc_vector = self.extract_data_from_kek_pkl(data, tc=True)
                if from_john:
                    tc_vector = self.extract_data_from_john_pkl(data, tc=True)
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
                                xlim=self.tc_xlim, bins=self.tc_bins,
                                target_range=(430.0, 480.0), title='PB20.13.11 $T_c$ Histogram')

        if run_rn:
            all_rn_data = np.asarray([])
            for pkl_path in self.rn_paths:
                data = self.load_data(pkl_path)
                if from_logan:
                    rn_vector = self.extract_data_from_logan_pkl(data, rn=True)
                if from_darcy:
                    rn_vector = self.extract_data_from_darcy_pkl(data, rn=True)
                if from_kek:
                    rn_vector = self.extract_data_from_kek_pkl(data, rn=True)
                if from_john:
                    rn_vector = self.extract_data_from_john_pkl(data, rn=True)
                all_rn_data = np.append(all_rn_data, rn_vector)
            print
            print 'Rn data'
            print np.median(all_rn_data)
            print np.std(all_rn_data)
            self.make_histogram(all_rn_data, xlabel='$R_n$ ($\Omega$)', ylabel='Count',
                                xlim=self.rn_xlim, bins=self.rn_bins, target_range=(1.0, 1.5),
                                title='Seven V11 Wafers $R_n$ Histogram')
        if run_pturn or run_psat:
            all_pturn_data = np.asarray([])
            for pkl_path in self.pturn_paths:
                data = self.load_data(pkl_path)
                if from_logan:
                    pturn_vector = self.extract_data_from_logan_pkl(data, pturn=True)
                if from_darcy:
                    pturn_vector = self.extract_data_from_darcy_pkl(data, pturn=True)
                if from_kek:
                    pturn_vector = self.extract_data_from_kek_pkl(data, pturn=True)
                if from_john:
                    pturn_vector = self.extract_data_from_john_pkl(data, psat=True)
                all_pturn_data = np.append(all_pturn_data, pturn_vector)
            print
            print 'Pturn data'
            print np.median(all_pturn_data)
            print np.std(all_pturn_data)
            self.make_histogram(all_pturn_data, xlabel='$P_turn$ ($pW$)', ylabel='Count',
                                xlim=self.pturn_xlim, bins=self.pturn_bins,
                                target_range=[(7.0, 9.0), (17.0, 24.0)],
                                title='PB20.13.09 $P_{sat}$ Histogram')


if __name__ == '__main__':
    rt_hist = RTHist()
    rt_hist.run(run_tc=False, run_rn=False, run_pturn=False, run_psat=True,
                from_logan=False, from_john=True, from_kek=False, from_darcy=False)
    #rt_hist.basic()
