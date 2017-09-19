

class TcThermalTune():

    def __init__(self):
        print 'yo'

    def load_data(self, data_path):
        thermal_tune_temps, tc = [], []
        with open(data_path, 'r') as file_handle:
            for line in file_handle.readlines():
                thermal_tune_temp = line.split(', ')[0]
                thermal_tune_temps.append(thermal_tune_temp)
                tc = line.split(', ')[0]
                tcs.append(tc)
        return thermal_tune_temps, tcs

    def plot_data(self, thermal_tune_temps, tcs):
        fig = pl.figure(
        ax1 = fig.add_subplot(111)
        ax1.set_xlabel('Thermal Tune Temp $\circ{C}$', fontsize=16)
        ax1.set_ylabel('$T_c$ ($mK$)', fontsize=16)
        ax1.plot(thermal_tune_temps, tcs)
        pl.show()

    def run(self, data_path):
        thermal_tune_temps, tcs = self.load_data(data_path)
        self.plot_data(thermal_tune_temps, tcs)


if __name__ == '__main__':
    data_path = './tc_thermal_tune.dat'
    tctt = TcThermalTune()
    tctt.run(data_path)
