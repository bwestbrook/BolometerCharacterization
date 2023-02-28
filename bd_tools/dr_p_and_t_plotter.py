import sys
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import pylab as pl
import datetime
from pprint import pprint
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass


class DilutionRefridgeratorPressureTemperatureLogPlotter(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, status_bar, screen_resolution, monitor_dpi, data_folder):
        '''
        '''
        '''
        '''
        super(DilutionRefridgeratorPressureTemperatureLogPlotter, self).__init__()
        self.serial_number = '00848.001'
        self.temps_to_plot = {
            '50K-PTC': 'CH1 T',
            '4K-PTC': 'CH2 T',
            'Still': 'CH5 T',
            'MC': 'CH6 T',
            'CP': 'CH8 T',
            'X110595': 'CH10 T',
            }
        self.pressures_to_plot_2 = [
            'Vacuum Can',
            'DR Low',
            'DR High',
            'Trap Inlet',
            'Mixture Tank',
            'Service Manifold',
            ]
        self.pressures_to_plot = {
            'CH1': 'Vacuum Can',
            'CH2': 'DR Low',
            'CH3': 'DR High',
            'CH4': 'Trap Inlet',
            'CH5': 'Mixture Tank',
            'CH6': 'Service Manifold',
            }
        self.date_format = '%Y-%m-%d'
        self.time_format = '%H:%M:%S'
        self.today = datetime.datetime.now()
        self.yesterday = self.today - datetime.timedelta(days=1)
        self.today_str = datetime.datetime.strftime(self.today, self.date_format)
        self.yesterday_str = datetime.datetime.strftime(self.yesterday, self.date_format)
        if status_bar is not None:
            self.status_bar = status_bar
            self.screen_resolution = screen_resolution
            self.monitor_dpi = monitor_dpi
            self.data_folder = data_folder
            self.status_bar.showMessage('Ready')
            grid = QtWidgets.QGridLayout()
            self.setLayout(grid)
            grid_2 = QtWidgets.QGridLayout()
            self.serial_number = '00848.001'
            self.lp_input_data_panel()

    def lp_input_data_panel(self):
        '''
        '''
        #Range
        self.start_date_lineedit = self.gb_make_labeled_lineedit(label_text='Start Date (YY-MM-DD)', lineedit_text=self.yesterday_str)
        self.layout().addWidget(self.start_date_lineedit, 1, 0, 1, 3)
        self.end_date_lineedit = self.gb_make_labeled_lineedit(label_text='End Date (YY-MM-DD)', lineedit_text=self.today_str)
        self.layout().addWidget(self.end_date_lineedit, 1, 3, 1, 3)
        self.start_time_lineedit = self.gb_make_labeled_lineedit(label_text='Start Time (HH:MM:SS)', lineedit_text='00:00:00')
        self.layout().addWidget(self.start_time_lineedit, 2, 0, 1, 3)
        self.end_time_lineedit = self.gb_make_labeled_lineedit(label_text='End Time (HH:MM:SS)', lineedit_text='23:59:59')
        self.layout().addWidget(self.end_time_lineedit, 2, 3, 1, 3)
        #Desample
        self.desample_p_lineedit = self.gb_make_labeled_lineedit(label_text='Desample P', lineedit_text='2')
        self.layout().addWidget(self.desample_p_lineedit, 3, 0, 1, 3)
        self.desample_p_ticks_lineedit = self.gb_make_labeled_lineedit(label_text='Desample P Ticks', lineedit_text='100')
        self.layout().addWidget(self.desample_p_ticks_lineedit, 4, 0, 1, 3)
        self.desample_t_lineedit = self.gb_make_labeled_lineedit(label_text='Desample T', lineedit_text='5')
        self.layout().addWidget(self.desample_t_lineedit, 3, 3, 1, 3)
        self.desample_t_ticks_lineedit = self.gb_make_labeled_lineedit(label_text='Desample T Ticks', lineedit_text='200')
        self.layout().addWidget(self.desample_t_ticks_lineedit, 4, 3, 1, 3)
        #Plot Option
        self.plot_type_combobox = self.gb_make_labeled_combobox(label_text='Plot type')
        for item in ['log', 'linear']:
            self.plot_type_combobox.addItem(item)
        self.layout().addWidget(self.plot_type_combobox, 5, 0, 1, 1)
        for i, ch in enumerate(self.pressures_to_plot):
            checkbox = QtWidgets.QCheckBox('P {0}'.format(i + 1))
            checkbox.setChecked(True)
            setattr(self, 'p_{0}_select_checkbox'.format(ch), checkbox)
            self.layout().addWidget(checkbox, 6, i, 1, 1)

        for i, ch in enumerate(self.temps_to_plot):
            checkbox = QtWidgets.QCheckBox('{0}'.format(ch))
            checkbox.setChecked(True)
            setattr(self, 't_{0}_select_checkbox'.format(ch), checkbox)
            self.layout().addWidget(checkbox, 7, i, 1, 1)
        self.plot_flow_checkbox = QtWidgets.QCheckBox('Flow', self)
        self.layout().addWidget(self.plot_flow_checkbox, 7, i + 1, 1, 1)
        self.plot_flow_checkbox.setChecked(True)
        #Control Display
        self.plot_pushbutton = QtWidgets.QPushButton('Plot', self)
        self.layout().addWidget(self.plot_pushbutton, 8, 0, 1, 6)
        self.pressure_plot_label = QtWidgets.QLabel(self)
        self.layout().addWidget(self.pressure_plot_label, 9, 0, 1, 6)
        self.temperature_plot_label = QtWidgets.QLabel(self)
        self.layout().addWidget(self.temperature_plot_label, 9, 1, 1, 6)

        #Connect functions
        self.plot_type_combobox.activated.connect(self.lp_plot_all_dates)
        self.start_time_lineedit.returnPressed.connect(self.lp_plot_all_dates)
        self.end_time_lineedit.returnPressed.connect(self.lp_plot_all_dates)
        self.start_date_lineedit.returnPressed.connect(self.lp_plot_all_dates)
        self.end_date_lineedit.returnPressed.connect(self.lp_plot_all_dates)
        self.desample_p_lineedit.returnPressed.connect(self.lp_plot_all_dates)
        self.desample_p_ticks_lineedit.returnPressed.connect(self.lp_plot_all_dates)
        self.desample_t_lineedit.returnPressed.connect(self.lp_plot_all_dates)
        self.desample_t_ticks_lineedit.returnPressed.connect(self.lp_plot_all_dates)
        self.plot_pushbutton.clicked.connect(self.lp_plot_all_dates)

    def lp_get_dates(self):
        '''
        '''
        start_date_str = self.start_date_lineedit.text()
        start_time_str = self.start_time_lineedit.text()
        start_date = datetime.datetime.strptime(start_date_str, self.date_format)
        start_time = datetime.datetime.strptime(start_time_str, self.time_format)
        start_date = start_date + datetime.timedelta(hours=start_time.hour)
        start_date = start_date + datetime.timedelta(minutes=start_time.minute)
        start_date = start_date + datetime.timedelta(seconds=start_time.second)
        start_date_str = datetime.datetime.strftime(start_date, '{0} {1}'.format(self.date_format, self.time_format))
        end_date_str = self.end_date_lineedit.text()
        end_time_str = self.end_time_lineedit.text()
        end_date = datetime.datetime.strptime(end_date_str, self.date_format)
        end_time = datetime.datetime.strptime(end_time_str, self.time_format)
        end_date = end_date + datetime.timedelta(hours=end_time.hour)
        end_date = end_date + datetime.timedelta(minutes=end_time.minute)
        end_date = end_date + datetime.timedelta(seconds=end_time.second)
        end_date_str = datetime.datetime.strftime(end_date, '{0} {1}'.format(self.date_format, self.time_format))
        dates = (start_date, end_date)
        date_strs = (start_date_str, end_date_str)
        elapsed_days = end_date - start_date
        days = []
        for i in range(elapsed_days.days + 1):
            date = start_date + datetime.timedelta(days=i)
            day = datetime.datetime.strftime(date, '%y-%m-%d')
            date_str = datetime.datetime.strftime(date, '%y-%m-%d')
            days.append(day)
        return dates, date_strs, days

    def lp_make_blank_figures(self, date_strs):
        '''
        '''
        pl.close('all')
        pressure_fig = pl.figure()
        pressure_ax = pressure_fig.add_subplot(111)
        pressure_ax.set_ylabel('Pressure (mbar)', fontsize=14)
        pressure_ax.set_xlabel('DD-MM-YY HH:MM:SS', fontsize=14)
        title = 'Pressures in BF DR SN:{0} from {1} to {2}'.format(self.serial_number, date_strs[0], date_strs[-1])
        pressure_ax.set_title(title, fontsize=16)
        pressure_ax.axhline(1e3, color='k', alpha=0.66, lw=3, label='ATM')
        pressure_fig.subplots_adjust(left=0.05, bottom=0.17, right=0.99, top=0.96)
        temperature_fig = pl.figure()
        temperature_ax = temperature_fig.add_subplot(111)
        temperature_ax.set_ylabel('Temperature (K)', fontsize=14)
        temperature_ax.set_xlabel('DD-MM-YY HH:MM:SS', fontsize=14)
        title = 'Temperatures in BF DR SN:{0} from {1} to {2}'.format(self.serial_number, date_strs[0], date_strs[-1])
        temperature_ax.set_title(title, fontsize=16)
        temperature_fig.subplots_adjust(left=0.05, bottom=0.17, right=0.99, top=0.96)
        return pressure_fig, temperature_fig

    def lp_plot_all_dates(self, clicked=True, dates=None,
                          plot_type='log',
                          desample_p=None, desample_p_ticks=None,
                          desample_t=None, desample_t_ticks=None):
        '''
        '''
        if dates is None:
            dates, date_strs, days = self.lp_get_dates()
        else:
            date_strs = (dates[0], dates[1])
            start_date = datetime.datetime.strptime(dates[0], '%y-%m-%d')
            end_date = datetime.datetime.strptime(dates[1], '%y-%m-%d')
            elapsed_days = end_date - start_date
            days = []
            for i in range(elapsed_days.days + 1):
                date = start_date + datetime.timedelta(days=i)
                day = datetime.datetime.strftime(date, '%y-%m-%d')
                days.append(day)
            dates = (start_date, end_date)
        if desample_p is None:
            desample_p = int(self.desample_p_lineedit.text())
        if desample_p_ticks is None:
            desample_p_ticks = int(self.desample_p_ticks_lineedit.text())
        if desample_t is None:
            desample_t = int(self.desample_t_lineedit.text())
        if desample_t_ticks is None:
            desample_t_ticks = int(self.desample_t_ticks_lineedit.text())
        all_data_frames = {}
        for day in days:
            all_data_frames = self.lp_get_data(day, all_data_frames)
        pressure_fig, temperature_fig = self.lp_make_plot(all_data_frames, dates, date_strs,
                                                          plot_pressure=True,
                                                          plot_type=plot_type,
                                                          plot_temperature=True,
                                                          desample_p=desample_p,
                                                          desample_p_ticks=desample_p_ticks,
                                                          desample_t=desample_t,
                                                          desample_t_ticks=desample_t_ticks)

    def lp_make_plot_selector(self, small_data, dates):
        '''
        '''
        selector = []
        pprint(small_data)
        for time_stamp_str in small_data['Time']:
            print(time_stamp_str)
            if self.gb_is_float(time_stamp_str):
                time_stamp_str = None
            elif time_stamp_str.startswith(' '):
                time_stamp_str = time_stamp_str[1:]
            if time_stamp_str is not None:
                time_stamp = datetime.datetime.strptime(time_stamp_str, '%d-%m-%y %H:%M:%S')
            if time_stamp_str is None:
                selector.append(False)
                valid = False
            elif dates[0] < time_stamp < dates[1]:
                selector.append(True)
                valid = True
            else:
                selector.append(False)
                valid = False
        return selector



    def lp_make_plot(self, all_data_frames, dates, date_strs,
                     plot_pressure=True, plot_temperature=True,
                     plot_type = None,
                     desample_p=5, desample_p_ticks=20,
                     desample_t=5, desample_t_ticks=20):
        '''
        '''
        pressure_fig, temperature_fig = self.lp_make_blank_figures(date_strs)
        print(all_data_frames)
        if plot_type is None:
            plot_type = self.plot_type_combobox.currentText()
        if plot_pressure:
            pressure_ax = pressure_fig.axes[0]
            for ch_key, name in self.pressures_to_plot.items():
                #if getattr(self, 'p_{0}_select_checkbox'.format(ch_key)).isChecked():
                    data = all_data_frames[name]
                    small_data = data.iloc[1::desample_p, :] #take every nth
                    index = ch_key.replace('CH', '')
                    label = '{0} (P{1})'.format(name, index)
                    selector = self.lp_make_plot_selector(small_data, dates)
                    if plot_type == 'log':
                        print(small_data['Time'][selector])
                        pressure_ax.semilogy(small_data['Time'][selector], small_data['{0}_Value'.format(ch_key)][selector], label=label)
                    else:
                        print(small_data['Time'][selector])
                        pressure_ax.plot(small_data['Time'][selector], small_data['{0}_Value'.format(ch_key)][selector], label=label)
                    xticks = np.asarray(small_data['Time'])[selector][::desample_p_ticks]
                    xtick_labels = [str(x) for x in xticks]
                    pressure_ax.set_xticks(xticks)
                    pressure_ax.set_xticklabels(xtick_labels, rotation=45, fontsize=10)
            #if self.plot_flow_checkbox.isChecked():
                #data = all_data_frames['flow']
                #small_data = data.iloc[1::desample_p, :] #take every nth
                ##selector = self.lp_make_plot_selector(small_data, dates)
                #flows = [x[1] for x in small_data['Time']['Time'].values]
                ##import ipdb;ipdb.set_trace()
                #pressure_ax.plot(flows, label='Flow')
            pressure_ax.legend(loc='best')
        if plot_temperature:
            temperature_ax = temperature_fig.axes[0]
            for ch_key, name in self.temps_to_plot.items():
                try:
                    data = all_data_frames[ch_key]
                    small_data = data.iloc[1::desample_t, :] #take every nth
                    label = '{0}'.format(ch_key)
                    selector = self.lp_make_plot_selector(small_data, dates)
                    #if getattr(self, 't_{0}_select_checkbox'.format(ch_key)).isChecked():
                    if plot_type == 'log':
                        temperature_ax.semilogy(small_data['Time'][selector], small_data['Value'][selector], label=label)
                    else:
                        temperature_ax.plot(small_data['Time'][selector], small_data['Value'][selector], label=label)
                    xticks = np.asarray(small_data['Time'])[selector][::desample_t_ticks]
                    xtick_labels = [str(x) for x in xticks]
                    temperature_ax.set_xticks(xticks)
                    temperature_ax.set_xticklabels(xtick_labels, rotation=45, fontsize=10)
                    temperature_ax.legend(loc='best')
                except KeyError:
                    pass
        pressure_fig.savefig(os.path.join('temp_files', 'pressure_log.png'))
        image = QtGui.QPixmap(os.path.join('temp_files', 'pressure_log.png'))
        #self.pressure_plot_label.setPixmap(image)
        temperature_fig.savefig(os.path.join('temp_files', 'temperature_log.png'))
        image = QtGui.QPixmap(os.path.join('temp_files', 'temperature_log.png'))
        #self.temperature_plot_label.setPixmap(image)
        pl.show()
        pl.close('all')
        return pressure_fig, temperature_fig

    def lp_get_data(self, day, all_data_frames):
        '''
        '''
        path = os.path.join('C:\\', 'Users', 'BlueFors_PC', 'Desktop', 'SN00848.0010 Log Files', day)
        print(path)
        if not os.path.exists(path):
            return None
        for file_name in os.listdir(path):
            for name, text in self.temps_to_plot.items():
                if text in file_name:
                    file_path = os.path.join(path, file_name)
                    test_df = pd.read_csv(file_path, names=['Day', 'Time', 'Value'])
                    values = test_df['Value']
                    days = test_df['Day']
                    times = test_df['Time']
                    full_times = days + ' ' + times
                    df_to_add = pd.concat([full_times, values], axis=1)
                    df_to_add = df_to_add.rename(columns={0: 'Time'})
                    #Aimport ipdb;ipdb.set_trace()
                    if name not in all_data_frames:
                        all_data_frames[name] = df_to_add
                    else:
                        #import ipdb;ipdb.set_trace()
                        all_data_frames[name] = all_data_frames[name].append(df_to_add)
        maxigauge_names = ['Day', 'Time',
                          'CH1', 'CH10', 'CH1A', 'CH1_Value', 'CH1B', 'CH1C',
                          'CH2', 'CH20', 'CH2A', 'CH2_Value', 'CH2B', 'CH2C',
                          'CH3', 'CH30', 'CH3A', 'CH3_Value', 'CH3B', 'CH3C',
                          'CH4', 'CH40', 'CH4A', 'CH4_Value', 'CH4B', 'CH4C',
                          'CH5', 'CH50', 'CH5A', 'CH5_Value', 'CH5B', 'CH5C',
                          'CH6', 'CH60', 'CH6A', 'CH6_Value', 'CH6B', 'CH6C',
                          'o', 
                          ]
        maxigauge_path = os.path.join(path, 'maxigauge {0}.log'.format(day))
        maxigauge_df = pd.read_csv(maxigauge_path, names=maxigauge_names)
        #maxigauge_df = pd.read_csv(maxigauge_path)
        #print(maxigauge_df)
        for ch_name, name in self.pressures_to_plot.items():
            value_key = '{0}_Value'.format(ch_name)
            values = maxigauge_df[value_key]
            days = maxigauge_df['Day']
            times = maxigauge_df['Time']
            full_times = days + ' ' + times
            print(values)
            print(full_times)
            test_df = pd.concat([full_times, values], axis=1)
            test_df = test_df.rename(columns={0: 'Time'})
            if name not in all_data_frames:
                all_data_frames[name] = test_df
            else:
                #import ipdb;ipdb.set_trace()
                all_data_frames[name] = all_data_frames[name].append(test_df)
        #import ipdb;ipdb.set_trace()
        flowmeter_path = os.path.join(path, 'Flowmeter {0}.log'.format(day))
        flowmeter_df = pd.read_csv(flowmeter_path, names=['flow'])
        #maxigauge_df = pd.read_csv(maxigauge_path)
        #print(maxigauge_df)
        for name in ['flow']:
            values = pd.DataFrame(flowmeter_df[name].values)
            days = pd.DataFrame([x[0].strip() for x in flowmeter_df.index])
            times = pd.DataFrame([x[1].strip() for x in flowmeter_df.index])
            full_times = days + ' ' + times
            test_df = pd.concat([full_times, values], axis=1)
            test_df = test_df.rename(columns={0: 'Time'})
            if name not in all_data_frames:
                all_data_frames[name] = test_df
            else:
                #import ipdb;ipdb.set_trace()
                all_data_frames[name] = all_data_frames[name].append(test_df)
        return all_data_frames




if __name__ == '__main__':
    status_bar = None
    monitor_dpi = None
    data_folder = None
    qt_app = QtWidgets.QApplication(sys.argv)
    qt_app.setFont(QtGui.QFont('SansSerif', 10))
    screen_resolution = qt_app.desktop().screenGeometry()
    #gui = BoloDAQGui(screen_resolution, qt_app)
    #gui.show()
    lp = DilutionRefridgeratorPressureTemperatureLogPlotter(status_bar, screen_resolution, monitor_dpi, data_folder)
    lp.show()
    #file_names = ['samples_20200814_log.csv']
    dates = ['20-07-25']
    dates = ['20-07-24', '20-07-26']
    dates = ['20-07-26']
    dates = ['20-08-14']
    dates = ['20-08-04']
    dates = ['22-02-08','22-02-10']
    dates = ['22-02-08']
    dates = ['22-02-07', '22-02-10']
    desample_p = 3
    desample_p_ticks = 100
    desample_t = 5
    desample_t_ticks = 200
    lp.lp_plot_all_dates(
        dates=dates,
        plot_type='log',
        desample_p=desample_p,
        desample_p_ticks=desample_p_ticks,
        desample_t=desample_t,
        desample_t_ticks=desample_t_ticks)
    #exit(qt_app.exec_())

