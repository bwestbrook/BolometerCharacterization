import os
from copy import copy
from pprint import pprint
from bd_lib.bolo_serial import BoloSerial
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass

class FridgeCycle(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, status_bar, agilent_widget, hp_widget):
        '''
        '''
        super(FridgeCycle, self).__init__()
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.agilent_widget = agilent_widget
        self.hp_widget = hp_widget
        self.fc_setup_input()


    def fc_setup_input(self):
        '''
        '''
        self.welcome_label = QtWidgets.QLabel('Welcome to Fridge Cycle!')
        self.layout().addWidget(self.welcome_label, 0, 0, 1, 1)
        self.cycle_voltage_lineedit = self.gb_make_labeled_lineedit(label_text='Cycle Voltage (V)', lineedit_text='25')
        self.layout().addWidget(self.cycle_voltage_lineedit, 1, 0, 1, 1)
        self.set_voltage_pushbutton = QtWidgets.QPushButton('Set Voltage')
        self.set_voltage_pushbutton.clicked.connect(self.fc_set_ps_voltage)
        self.layout().addWidget(self.set_voltage_pushbutton, 1, 1, 1, 1)
        # Resistance Thresholds
        self.cycle_start_resistance_lineedit = self.gb_make_labeled_lineedit(label_text='Cycle Start Res (Ohm):', lineedit_text='500e3')
        self.layout().addWidget(self.cycle_start_resistance_lineedit, 2, 0, 1, 1)
        self.cycle_end_resistance_lineedit = self.gb_make_labeled_lineedit(label_text='Cycle End Res (Ohm):', lineedit_text='3.5e3')
        self.layout().addWidget(self.cycle_end_resistance_lineedit, 2, 1, 1, 1)
        self.current_resistance_label = self.gb_make_labeled_label(label_text='Current Resistance (Ohm):')
        self.layout().addWidget(self.current_resistance_label, 3, 0, 1, 1)
        self.get_current_resistance_pushbutton = QtWidgets.QPushButton('Get Resistance')
        self.get_current_resistance_pushbutton.clicked.connect(self.fc_get_abr_resistance)
        self.layout().addWidget(self.get_current_resistance_pushbutton, 3, 1, 1, 1)
        # Start
        self.start_cycle_pushbutton = QtWidgets.QPushButton('Start Cycle')
        self.start_cycle_pushbutton.clicked.connect(self.fc_start_cycle)
        self.layout().addWidget(self.start_cycle_pushbutton, 5, 0, 1, 2)

    def fc_get_abr_resistance(self, clicked=True, voltage=0):
        '''
        '''
        resistance = float(self.hp_widget.hp_get_resistance().strip())
        self.current_resistance_label.setText('{0:.4f}'.format(flaresistance))

    def fc_set_ps_voltage(self, clicked=True, voltage=0):
        '''
        '''
        voltage = float(self.cycle_voltage_lineedit.text())
        applied_voltage = self.agilent_widget.ae_apply_voltage(voltage)
        return applied_voltage

    def fc_start_cycle(self, clicked=True, voltage=0):
        '''
        '''
        # Wait to start
        cycle_wait = True
        cycle_start_resistance = float(self.cycle_start_resistance_lineedit.text())
        while cycle_wait:
            resistance = self.hp_widget.get_resistance()
            if resistance < cycle_start_resistance:
                wait(3)
            else:
                cycle_wait = False
        # Apply Voltage to start
        cycle_voltage = float(self.cycle_voltage.text())
        self.agilent_widget.apply_volage

    def bd_close_fridge_cycle(self):
        '''
        '''
        self.fridge_cycle_popup.close()


    def bd_get_fridge_cycle_save_path(self):
        date = datetime.now()
        date_str = datetime.strftime(date, '%Y_%m_%d_%H_%M')
        for i in range(1, 10):
            data_path = './FridgeCycles/fc_{0}_{1}.dat'.format(date_str, str(i).zfill(2))
            if not os.path.exists(data_path):
                break
        return data_path

    def bd_get_grt_temp(self, fc_params):
        grt_data, grt_data_mean, grt_data_min, grt_data_max, grt_data_std = self.daq.get_data(signal_channel=fc_params['grt_daq_channel'],
                                                                                                   integration_time=100,
                                                                                                   sample_rate=1000,
                                                                                                   active_devices=[self.active_daqs[0]])
        rtc = RTCurve([])
        voltage_factor = float(self.multimeter_voltage_factor_range_dict[fc_params['grt_range']])
        grt_serial = fc_params['grt_serial']
        print(grt_serial)
        print(grt_serial)
        print(grt_serial)
        temperature_array, is_valid = rtc.resistance_to_temp_grt(grt_data * voltage_factor, serial_number=grt_serial)
        if is_valid:
            temperature = np.mean(1e3 * temperature_array)
        else:
            self.gb_quick_message('GRT config is not correct assuming 1000 Ohms')
        if self.is_float(temperature, enforce_positive=True):
            temperature_str = '{0:.3f} mK'.format(temperature)
        else:
            temperature_str = 'NaN'
        return temperature, temperature_str


    def bd_start_fridge_cycle(self, sleep_time=1.0):
        # Config globals
        global do_cycle_fridge
        self.aborted_cycle = False
        do_cycle_fridge = True
        # Get essential FC params
        fc_params = self.get_params_from_fride_cycle()
        charcoal_start_resistance = float(fc_params['charcoal_start_resistance'])
        charcoal_end_resistance = float(fc_params['charcoal_end_resistance'])
        cycle_end_temperature = float(fc_params['cycle_end_temperature'])
        # Set Data Path
        data_path = self.get_fridge_cycle_save_path()
        self.gb_quick_message('Saving data to {0}'.format(data_path))
        fig = None
        if 'Cycle Aborted' in getattr(self, '_fridge_cycle_popup_status_label').text():
            self.fc_time_stamp_vector, self.ps_voltage_vector, self.abr_resistance_vector, self.abr_temperature_vector, self.grt_temperature_vector = [], [], [], [], []
        with open(data_path, 'w') as fc_file_handle:
            # Get new data 
            data_line = self.check_cycle_stage_and_update_data(fc_params, data_path, sleep_time)
            fc_file_handle.write(data_line)
            self.update_fridge_cycle(data_path=data_path)
            # Update status
            status = 'Cooling ABR before heating'
            getattr(self, '_fridge_cycle_popup_status_label').setText(status)
            # Check ABR Res to Start While Loop
            abr_resistance, abr_resistance_str = self.fc.get_resistance()
            while abr_resistance < charcoal_start_resistance and do_cycle_fridge:
                # Get new data 
                data_line = self.check_cycle_stage_and_update_data(fc_params, data_path, sleep_time)
                fc_file_handle.write(data_line)
                # Check ABR Res
                abr_resistance, abr_resistance_str = self.fc.get_resistance()
            if do_cycle_fridge:
                # Update Status
                status = 'Charcoal has reached {0} turning on voltage'.format(charcoal_start_resistance)
                getattr(self, '_fridge_cycle_popup_status_label').setText(status)
                # Turn on voltage in steps of 1 volt over with a sleep between
                for i in range(0, int(fc_params['cycle_voltage']) + 1, 5):
                    # Apply voltage and update gui
                    applied_voltage = self.fc.apply_voltage(i)
                    getattr(self, '_fridge_cycle_popup_ps_voltage_value_label').setText(str(applied_voltage))
                    # Get new data 
                    data_line = self.check_cycle_stage_and_update_data(fc_params, data_path, sleep_time)
                    fc_file_handle.write(data_line)
                # Update Status
                status = 'Charcoal being heated: Voltage to heater set to {0} V'.format(i)
                getattr(self, '_fridge_cycle_popup_status_label').setText(status)
            # Check ABR Res to Start While Loop
            abr_resistance, abr_resistance_str = self.fc.get_resistance()
            while abr_resistance > charcoal_end_resistance and do_cycle_fridge:
                # Get new data 
                data_line = self.check_cycle_stage_and_update_data(fc_params, data_path, sleep_time)
                fc_file_handle.write(data_line)
                # Check ABR Res
                abr_resistance, abr_resistance_str = self.fc.get_resistance()
            status = 'Charcoal reached {0} turning off voltage and cooling stage'.format(abr_resistance)
            getattr(self, '_fridge_cycle_popup_status_label').setText(status)
            self.fc.apply_voltage(0)
            getattr(self, '_fridge_cycle_popup_ps_voltage_value_label').setText('0')
            # Record the data until grt reaches base temp 
            grt_temperature, grt_temperature_str = self.get_grt_temp(fc_params)
            while grt_temperature > cycle_end_temperature and do_cycle_fridge:
                # Get new data 
                data_line = self.check_cycle_stage_and_update_data(fc_params, data_path, sleep_time)
                fc_file_handle.write(data_line)
                # Check GRT Temp 
                grt_temperature, grt_temperature_str = self.get_grt_temp(fc_params)
            if self.aborted_cycle:
                status = 'Previous Cycle Aborted, Idle'
                getattr(self, '_fridge_cycle_popup_status_label').setText(status)
            else:
                status = 'Stage has reached {0}, cycle finished'.format(grt_temperature_str)
                getattr(self, '_fridge_cycle_popup_status_label').setText(status)
            do_cycle_fridge = False
            root.update()

    def bd_check_cycle_stage_and_update_data(self, fc_params, data_path, sleep_time):
        # Update ABR resistance
        abr_resistance, abr_resistance_str = self.fc.get_resistance()
        getattr(self, '_fridge_cycle_popup_abr_resistance_value_label').setText(abr_resistance_str)
        abr_temperature, abr_temperature_str = self.fc.abr_resistance_to_kelvin(abr_resistance)
        getattr(self, '_fridge_cycle_popup_abr_temperature_value_label').setText(abr_temperature_str)
        # Update ABR temperature
        abr_resistance, abr_resistance_str = self.fc.get_resistance()
        getattr(self, '_fridge_cycle_popup_abr_resistance_value_label').setText(abr_resistance_str)
        # Update temp
        grt_temperature, grt_temperature_str = self.get_grt_temp(fc_params)
        getattr(self, '_fridge_cycle_popup_grt_temperature_value_label').setText(grt_temperature_str)
        # Update voltage
        applied_voltage, applied_voltage_str = self.fc.get_voltage()
        getattr(self, '_fridge_cycle_popup_ps_voltage_value_label').setText(applied_voltage_str)
        # Update time stamp
        time_stamp = datetime.now()
        time_stamp = datetime.strftime(time_stamp, '%Y_%m_%d_%H_%M_%S')
        # Add and plot data
        self.fc_time_stamp_vector.append(time_stamp)
        self.ps_voltage_vector.append(applied_voltage)
        self.abr_resistance_vector.append(abr_resistance)
        self.abr_temperature_vector.append(abr_temperature)
        self.grt_temperature_vector.append(grt_temperature)
        self.update_fridge_cycle(data_path=data_path)
        # Write Data 
        data_line = '{0}\t{1}\t{2}\t{3}\t{4}\n'.format(time_stamp, abr_resistance, abr_temperature, applied_voltage, grt_temperature)
        # Update Gui and Sleep
        root.update()
        self.repaint()
        time.sleep(sleep_time)
        return data_line

    def bd_stop_fridge_cycle(self):
        if hasattr(self, 'fc'):
            self.fc.apply_voltage(0)
        global do_cycle_fridge
        do_cycle_fridge = False
        self.aborted_cycle = True
        self.fc_time_stamp_vector, self.ps_voltage_vector, self.abr_resistance_vector, self.grt_temperature_vector = [], [], [], []
        root.update()

    def bd_get_params_from_fride_cycle(self):
        params = {}
        grt_daq_channel = str(getattr(self, '_fridge_cycle_popup_grt_daq_channel_combobox').currentText())
        grt_serial = str(getattr(self, '_fridge_cycle_popup_grt_serial_combobox').currentText())
        grt_range = str(getattr(self, '_fridge_cycle_popup_grt_range_combobox').currentText())
        ps_voltage = str(getattr(self, '_fridge_cycle_popup_ps_voltage_value_label').text())
        abr_resistance = str(getattr(self, '_fridge_cycle_popup_abr_resistance_value_label').text())
        grt_temperature = str(getattr(self, '_fridge_cycle_popup_grt_temperature_value_label').text())
        charcoal_start_resistance = str(getattr(self, '_fridge_cycle_popup_start_resistance_lineedit').text())
        charcoal_end_resistance = str(getattr(self, '_fridge_cycle_popup_end_resistance_lineedit').text())
        cycle_voltage = str(getattr(self, '_fridge_cycle_popup_cycle_voltage_combobox').currentText())
        cycle_end_temperature = str(getattr(self, '_fridge_cycle_popup_cycle_end_temperature_combobox').currentText())
        params.update({'grt_daq_channel': grt_daq_channel})
        params.update({'grt_serial': grt_serial})
        params.update({'grt_range': grt_range})
        params.update({'ps_voltage': ps_voltage})
        params.update({'abr_resistance': abr_resistance})
        params.update({'grt_temperature': grt_temperature})
        params.update({'charcoal_start_resistance': charcoal_start_resistance})
        params.update({'charcoal_end_resistance': charcoal_end_resistance})
        params.update({'cycle_voltage': cycle_voltage})
        params.update({'cycle_end_temperature': cycle_end_temperature})
        return params

    def bd_update_fridge_cycle(self, data_path=None):
        fc_params = self.get_params_from_fride_cycle()
        fig, ax = self.bd_create_blank_fig(frac_screen_width=0.75, frac_screen_height=0.7,
                                         left=0.08, right=0.98, top=0.9, bottom=0.1,
                                         multiple_axes=True)
        ax1 = fig.add_subplot(411)
        ax2 = fig.add_subplot(412)
        ax3 = fig.add_subplot(413)
        ax4 = fig.add_subplot(414)
        time_stamp_vector = [datetime.strptime(x, '%Y_%m_%d_%H_%M_%S') for x in self.fc_time_stamp_vector]
        ax1.plot(time_stamp_vector, self.ps_voltage_vector, color='r', label='PS Voltage (V)')
        date = datetime.strftime(datetime.now(), '%Y_%m_%d')
        ax1.set_title('576 Fridge Cycle {0}'.format(date))
        ax1.set_ylabel('PS Voltage (V)')
        ax1.set_ylim([0, 26])
        ax2.plot(time_stamp_vector, self.abr_temperature_vector, color='g', label='ABR Temp (K)')
        ax2.set_ylabel('ABR Temp (K)')
        ax2.axhline(float(self.fc.abr_resistance_to_kelvin(float(fc_params['charcoal_end_resistance']))[0]), color='b', label='ABR End')
        ax2.axhline(float(self.fc.abr_resistance_to_kelvin(float(fc_params['charcoal_start_resistance']))[0]), color='m', label='ABR Start')
        ax3.plot(time_stamp_vector, np.asarray(self.abr_resistance_vector) * 1e-3, color='k', label='GRT Temp (mK)')
        ax3.axhline(float(fc_params['charcoal_end_resistance']) * 1e-3, color='b', label='ABR End')
        ax3.axhline(float(fc_params['charcoal_start_resistance']) * 1e-3, color='m', label='ABR Start')
        ax3.set_ylabel('ABR Res (kOhms)')
        ax4.plot(time_stamp_vector, self.grt_temperature_vector, color='c', label='GRT Temp (mK)')
        ax4.axhline(float(fc_params['cycle_end_temperature']), color='b', label='Approx GRT Base')
        ax4.set_ylabel('GRT Temp (mK)')
        ax4.set_xlabel('Time Stamps')
        # Add legends
        handles, labels = ax1.get_legend_handles_labels()
        ax1.legend(handles, labels, numpoints=1)
        handles, labels = ax2.get_legend_handles_labels()
        ax2.legend(handles, labels, numpoints=1)
        handles, labels = ax3.get_legend_handles_labels()
        ax3.legend(handles, labels, numpoints=1)
        if data_path is not None:
            save_path = data_path.replace('.dat', '.png')
        else:
            save_path = 'temp_files/temp_fc.png'
        pl.legend()
        fig.savefig(save_path)
        pl.cla()
        pl.close('all')
        image_to_display = QtGui.QPixmap(save_path)
        getattr(self, '_fridge_cycle_popup_fridge_cycle_plot_label').setPixmap(image_to_display)
        self.repaint()
