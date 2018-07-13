import os
import cPickle
from pprint import pprint
import pylab as pl
import numpy as np
from histogram_settings import histogram_settings

class Hist():

    def __init__(self):
        self.hello = 'hello'

    def load_data(self, pkl_path):
        with open(pkl_path, 'rb') as pkl_handle:
            data = cPickle.load(pkl_handle)
        return data

    def extract_data_from_pkl(self, data,
                              tc=False,
                              psat=False,
                              pturn=False,
                              rn=False,
                              from_logan=False,
                              from_kek=False,
                              from_tucker=False,
                              from_john=False,
                              from_darcy=False):
        if from_john:
            data_array = self.extract_data_from_john_pkl(data, rn=rn, tc=tc, psat=psat, pturn=pturn)
        elif from_kek:
            data_array = self.extract_data_from_kek_pkl(data, rn=rn, tc=tc, psat=psat, pturn=pturn)
        elif from_darcy:
            data_array = self.extract_data_from_darcy_pkl(data, rn=rn, tc=tc, psat=psat, pturn=pturn)
        elif from_logan:
            data_array = self.extract_data_from_logan_pkl(data, rn=rn, tc=tc, psat=psat, pturn=pturn)
        elif from_tucker:
            data_array = self.extract_data_from_tucker_pkl(data, rn=rn, tc=tc, psat=psat, pturn=pturn)
        return data_array

    def split_power_data_into_bands(self, data):
        data_array_90 = np.asarray([])
        data_array_150 = np.asarray([])
        for value in data:
            if value < 9.0:
                data_array_90 = np.append(data_array_90, value)
            elif value >= 9.0:
                data_array_150 = np.append(data_array_150, value)
        data_array = [data_array_90, data_array_150]
        return data_array

    def extract_data_from_john_pkl(self, data, rn=False, tc=False, psat=False, pturn=False):
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
            value = data[bolo][data_type_key]
            if pturn or psat:
                value *= 1e12 # pW
            elif tc:
                value = data[bolo][data_type_key] * 1e12 # pW
                value *= 1e3 # mK
            data_array = np.append(data_array, value)
        if psat or pturn:
            data_array = self.split_power_data_into_bands(data_array)
        return data_array

    def extract_data_from_logan_pkl(self, data, rn=False, tc=False, psat=False, pturn=False):
        if type(data) == dict:
            if rn:
                return data['Rn_corrected']
            if tc:
                print data
                return data['Tc'] * 1e3
            if pturn or psat:
                data = data['Psat_corrected']
                data = self.split_power_data_into_bands(data)
                return data
        else:
            return data

    def extract_data_from_kek_pkl(self, data, rn=False, tc=False, psat=False, pturn=False):
        data_array = data
        if psat or pturn:
            data_array = np.asarray(data_array)
            data_array *= 1e12
            data_array = self.split_power_data_into_bands(data_array)
        if tc:
            print data.shape
            if len(data.shape) == 2:
                data_array = np.asarray(data_array.transpose()[0], dtype=float)
            data_array *= 1e3
        return data_array

    def extract_data_from_tucker_pkl(self, data, rn=False, tc=False, psat=False, pturn=False):
        data_array = np.asarray(data)
        if tc:
            data_array *= 1e3
        if psat or pturn:
            data_array = self.split_power_data_into_bands(data_array)
        return data_array

    def extract_data_from_darcy_pkl(self, data, rn=False, tc=False, psat=False, pturn=False):
        data_array = np.asarray([float(x) for x in data])
        if pturn:
            data_array *= 1e12
        if psat or pturn:
            data_array = self.split_power_data_into_bands(data_array)
        return data_array

    def basic(self):
        data = np.asarray([1.27, 1.29, 1.25, 1.19, 1.09, 1.21])
        data = np.asarray([465, 461, 454, 457])
        data = np.asarray([10.4, 10.0, 24.8, 20.1])
        self.make_histogram(data, xlabel='Psat (pW)', ylabel='Count', xlim=(8, 30),
                            bins=10, title='13-18 and 13-20 witness pixel Psat')

    def make_histogram(self, data, xlabel='', ylabel='', xlim=(0,2), bins=20, title='', target_ranges=[]):
        if len(data) == 2:
            median_1 = np.median(data[0])
            var_1 = np.std(data[0])
            label_1 = '90 GHz: {0:.2f} +/ {1:.2f} pW'.format(median_1, var_1)
            counts, bins, patches = pl.hist(data[0], bins, range=xlim, color='r', label=label_1)
            median_2 = np.median(data[1])
            var_2 = np.std(data[1])
            label_2 = '150 GHz: {0:.2f} +/ {1:.2f} pW'.format(median_2, var_2)
            counts, bins, patches = pl.hist(data[1], bins, range=xlim, color='b', label=label_2)
        else:
            median = np.median(data[data > 0])
            var = np.std(data[np.logical_and(0.7 < data, data < 2.0)])
            label = '{0:.2f} +/ {1:.2f} $\Omega$'.format(median, var)
            #import ipdb;ipdb.set_trace()
            counts, bins, patches = pl.hist(data, bins, range=xlim, label=label)
        pl.title(title, fontsize=20)
        pl.xlabel(xlabel, fontsize=16)
        pl.ylabel(ylabel, fontsize=16)
        for frequency, target_range_list in target_ranges.iteritems():
            if frequency == '90':
                color = 'r'
            elif frequency == '150':
                color = 'b'
            for range_type, target_list in target_range_list.iteritems():
                for i, target_range in enumerate(target_list):
                    print range_type, target_range
                    if range_type == 'Target':
                        alpha = 0.5
                    elif range_type == 'Requirement':
                        alpha = 0.2
                    pl.axvline(target_range[0], color=color)
                    pl.axvline(target_range[1], color=color)
                    if i == 0:
                        label = '{0} {1}'.format(frequency, range_type)
                        pl.axvspan(target_range[0], target_range[1], 0, 1, label=label, color=color, alpha=alpha)
                    else:
                        pl.axvspan(target_range[0], target_range[1], 0, 1, color=color, alpha=alpha)
        pl.legend()
        pl.show()

    def run(self, run_tc=False, run_rn=False, run_pturn=False, run_psat=False,
            from_john=False, from_logan=False, from_kek=False, from_tucker=False, from_darcy=False):
        for pkl_path in histogram_settings.data_paths:
            data = self.load_data(pkl_path)
            data_array = self.extract_data_from_pkl(data,
                                                    tc=run_tc,
                                                    psat=run_psat,
                                                    pturn=run_pturn,
                                                    rn=run_rn,
                                                    from_logan=from_logan,
                                                    from_kek=from_kek,
                                                    from_tucker=from_tucker,
                                                    from_john=from_john,
                                                    from_darcy=from_darcy)
        if run_tc:
            self.make_histogram(all_data, xlabel='$T_c$ (mK)', ylabel='Count',
                                xlim=histogram_settings.tc_xlim, bins=histogram_settings.tc_bins,
                                target_ranges=histogram_settings.tc_target_range,
                                title='PB20.13.15 $T_c$ Histogram')
        if run_rn:
            self.make_histogram(all_data, xlabel='$R_n$ ($\Omega$)', ylabel='Count',
                                xlim=histogram_settings.rn_xlim, bins=histogram_settings.rn_bins,
                                target_ranges=histogram_settings.rn_target_range,
                                title='Seven V11 Wafers $R_n$ Histogram')
        if run_pturn or run_psat:
            all_pturn_data = np.asarray([])
            for pkl_path in histogram_settings.data_paths:
                data = self.load_data(pkl_path)
                if from_logan:
                    pturn_vector = self.extract_data_from_logan_pkl(data, pturn=True)
                if from_darcy:
                    pturn_vector = self.extract_data_from_darcy_pkl(data, pturn=True)
                if from_kek:
                    pturn_vector = self.extract_data_from_kek_pkl(data, pturn=True)
                if from_john:
                    pturn_vector = self.extract_data_from_john_pkl(data, psat=run_psat, pturn=run_pturn)
                all_pturn_data = np.append(all_pturn_data, pturn_vector)
            print
            print 'Pturn data'
            print np.median(all_pturn_data)
            print np.std(all_pturn_data)
            self.make_histogram(all_pturn_data, xlabel='$P_{turn}$ ($pW$)', ylabel='Count',
                                xlim=self.pturn_xlim, bins=self.pturn_bins,
                                target_range=[(7.0, 9.0), (17.0, 24.0)],
                                title='PB20.13.09 $P_{turn}$ Histogram')
        if run_psat or run_pturn:
            self.make_histogram(all_data, xlabel='$P_{sat}$ ($pW$)', ylabel='Count',
                                xlim=histogram_settings.pturn_xlim, bins=histogram_settings.pturn_bins,
                                target_ranges=histogram_settings.psat_target_range,
                                title='PB20.13.11 $P_{sat}$ Histogram')

    def combine_data(self, data_combo_dict, run_tc=False, run_rn=False, run_pturn=False, run_psat=False):
        with open(histogram_settings.pturn_path_5, 'w') as write_fh:
            all_data = np.asarray([])
            all_90_data = np.asarray([])
            all_150_data = np.asarray([])
            for source, data_path in data_combo_dict.iteritems():
                loader = getattr(self, 'extract_data_from_{0}_pkl'.format(source))
                data = self.load_data(data_path)
                data_array = loader(data, tc=run_tc, rn=run_rn, psat=run_psat, pturn=run_pturn)
                if len(data_array) == 2:
                    all_90_data = np.append(all_90_data, data_array[0])
                    all_150_data = np.append(all_150_data, data_array[1])
                else:
                    all_data = np.append(all_data, data_array)
        if len(all_90_data) > 0 and len(all_150_data) > 0:
            all_data = [all_90_data, all_150_data]
        json_to_dump = {"Version13": all_data}
        return all_data

if __name__ == '__main__':
    hist = Hist()
    if histogram_settings.make_histogram:
        hist.run(run_tc=histogram_settings.run_tc,
                 run_rn=histogram_settings.run_rn,
                 run_pturn=histogram_settings.run_pturn,
                 run_psat=histogram_settings.run_psat,
                 from_logan=histogram_settings.from_logan,
                 from_john=histogram_settings.from_john,
                 from_tucker=histogram_settings.from_tucker,
                 from_kek=histogram_settings.from_kek,
                 from_darcy=histogram_settings.from_darcy)
    elif histogram_settings.combine_data:
        all_data = hist.combine_data(histogram_settings.data_combo_dict,
                                     run_tc=histogram_settings.run_tc,
                                     run_rn=histogram_settings.run_rn,
                                     run_pturn=histogram_settings.run_pturn,
                                     run_psat=histogram_settings.run_psat)

        if histogram_settings.run_psat:
            hist.make_histogram(all_data, xlabel='$P_{sat}$ ($pW$)', ylabel='Count',
                                xlim=histogram_settings.pturn_xlim, bins=histogram_settings.pturn_bins,
                                target_ranges=histogram_settings.psat_target_range,
                                title='$P_{sat}$ Histogram PB20.11.08')

        if histogram_settings.run_rn:
            hist.make_histogram(all_data, xlabel='$R_{n}$ ($\Omega$)', ylabel='Count',
                                xlim=histogram_settings.rn_xlim, bins=histogram_settings.rn_bins,
                                target_ranges=histogram_settings.rn_target_range,
                                title='$R_{n}$ Histogram PB20.13.11')

        if histogram_settings.run_tc:
            hist.make_histogram(all_data, xlabel='$T_{c}$ ($mK$)', ylabel='Count',
                                xlim=histogram_settings.tc_xlim, bins=histogram_settings.tc_bins,
                                target_ranges=histogram_settings.tc_target_range,
                                title='$T_{c}$ Histogram PB20.13.11')




