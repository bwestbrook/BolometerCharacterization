import cPickle
from pprint import pprint

class RTHist():

    def __init__(self):
        print 'hello'
        self.pkl_path_1 = 'C:\Users\jamin\Repositories\BolometerCharacterization\Data\\2017_11_03\\20170712_raise_PB201101_res_Tc.pkl'
        self.pkl_path_2 = 'C:\Users\jamin\Repositories\BolometerCharacterization\Data\\2017_11_03\\20170712_raise_PB201102_res_Tc.pkl'

    def load_data(self, pkl_path=None):
        if pkl_path is None:
            pkl_path = self.pkl_path_1
        with open(pkl_path, 'r') as pkl_handle:
            data = cPickle.load(pkl_handle)
        pprint(data)

    def run(self):
        self.load_data()

if __name__ == '__main__':
    rt_hist = RTHist()
    rt_hist.run()
