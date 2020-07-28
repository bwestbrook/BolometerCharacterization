import socket
import argparse
import numpy as np
import logging
import time

BUFF_SIZE = 4096

voltage_excitation_key = {1: 2.0e-6,
                          2: 6.32e-6,
                          3: 20.0e-6,
                          4: 63.2e-6,
                          5: 200.0e-6,
                          6: 632.0e-6,
                          7: 2.0e-3,
                          8: 6.32e-3,
                          9: 20.0e-3,
                          10: 63.2e-3,
                          11: 200.0e-3,
                          12: 632.0e-3}

current_excitation_key = {1: 1.0e-12,
                          2: 3.16e-12,
                          3: 10.0e-12,
                          4: 31.6e-12,
                          5: 100.0e-12,
                          6: 316.0e-12,
                          7: 1.0e-9,
                          8: 3.16e-9,
                          9: 10.0e-9,
                          10: 31.6e-9,
                          11: 100.0e-9,
                          12: 316.0e-9,
                          13: 1.0e-6,
                          14: 3.16e-6,
                          15: 10.0e-6,
                          16: 31.6e-6,
                          17: 100.0e-6,
                          18: 316.0e-6,
                          19: 1.0e-3,
                          20: 3.16e-3,
                          21: 10.0-3,
                          22: 31.6-3}

class Lakeshore372_Simulator:

    def __init__(self, port, num_channels=16, sn="LSSIM"):
        self.log = logging.getLogger()

        self.port = port
        self.sn = sn

        self.num_channels = num_channels
        self.channels = []
        for i in range(self.num_channels + 1):
            if i == 0:
                c = ChannelSim('A', "Channel A")
            else:
                c = ChannelSim(i, "Channel {}".format(i))
            self.channels.append(c)

        for i in range(self.num_channels + 1):
            print(self.channels[i].name)

        self.scanner = 1  # 0 = autoscan off; 1 = autoscan on
        self.active_channel = 1  # start on channel 1

        self.heaters = []
        for i in range(3):
            h = Heater(i)
            self.heaters.append(h)

        self.curves = []
        for i in range(60):
            v = Curve(i)
            self.curves.append(v)

        self.cmds = {
            # Lakeshore and channel commands
            "*IDN?": self.get_idn,
            "RDGK?": lambda x: self.get_reading(chan=x, unit='1'),
            "RDGR?": lambda x: self.get_reading(chan=x, unit='2'),
            "SRDG?": lambda x: self.get_reading(chan=x, unit='2'),
            "KRDG?": lambda x: self.get_reading(chan=x, unit='1'),
            "RDGST?": self.get_reading_status,
            "INNAME": self.set_channel_name,
            "INNAME?": self.get_channel_name,
            "INTYPE": self.set_channel_intype,
            "INTYPE?": self.get_channel_intype,
            "SET_VALUE": self.set_channel_value,
            "SCAN": self.set_scanner,
            "SCAN?": self.get_scanner,
            "INSET": self.set_input_parameters,
            "INSET?": self.get_input_parameters,
            "TLIMIT": self.set_tlimit,
            "TLIMIT?": self.get_tlimit,
            "RDGPWR?": self.get_rdgpwr,
            # Heater commands
            "OUTMODE?": self.get_outmode,
            "OUTMODE": self.set_outmode,
            "HTRSET?": self.get_htrset,
            "HTRSET": self.set_htrset,
            "MOUT?": self.get_mout,
            "MOUT": self.set_mout,
            "RAMP?": self.get_ramp,
            "RAMP": self.set_ramp,
            "RAMPST": self.get_ramp_status,
            "RANGE?": self.get_heater_range,
            "RANGE": self.set_heater_range,
            "SETP?": self.get_setpoint,
            "SETP": self.set_setpoint,
            "STILL?": self.get_still,
            "STILL": self.set_still,
            "PID?": self.get_pid,
            "PID": self.set_pid,
            # Curve commands
            "CRVHDR?": self.get_curve_header,
            "CRVHDR": self.set_curve_header,
            "CRVPT?": self.get_curve_data,
            "CRVPT": self.set_curve_data,
            "CRVDEL": self.delete_curve,
        }

    def set_channel_value(self, chan, value):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        self.channels[chan_index].set_value(value)

    def get_channel_intype(self, chan):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        return self.channels[chan_index].get_intype()

    def set_channel_intype(self, chan, *args):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        args = map(int, args)
        self.channels[chan_index].set_intype(*args)

    def get_channel_name(self, chan):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        return self.channels[chan_index].name

    def set_channel_name(self, chan, name):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        self.channels[chan_index].name = name

    def run(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Checks self.port plus the next ten to see if they're open
        for p in range(self.port, self.port + 10):
            try:
                self.log.info(f"Trying to listen on port {p}")
                sock.bind(('localhost', p))
                break
            except OSError as e:
                if e.errno == 48:
                    self.log.warning(f"Address {p} is already in use")
                else:
                    raise (e)
        else:
            print(f"Could not connect to ports in {range(self.port, self.port + 5)}")

        sock.listen(1)

        while True:
            self.log.info('waiting for a connection....')
            conn, client_address = sock.accept()
            self.log.info(f"Made connection with {client_address}")
            with conn:

                # Main data loop
                while True:
                    data = conn.recv(BUFF_SIZE)
                    elapsed_time = time.time() - start_time
                    print(elapsed_time)  # timestamp printed every time a command is received

                    if not data:
                        self.log.info("Connection closed by client")
                        break

                    self.log.debug("Command: {}".format(data))
                    # Only takes first command in case multiple commands are s
                    cmds = data.decode().split(';')

                    if int(self.scanner) == 1:  # useful only if all channels have the same dwell and pause settings
                        channel_change = int(elapsed_time // (self.channels[int(self.active_channel)].dwell +
                                                              self.channels[int(self.active_channel)].pause))
                        # print(channel_change)
                        if 0 < channel_change < 16:
                            self.active_channel = 1 + channel_change
                        elif channel_change >= 16:
                            new_channel_change = int(channel_change % 16)
                            self.active_channel = 1 + new_channel_change

                        print(self.active_channel)

                    elif int(self.scanner) == 0:
                        pass

                    for c in cmds:
                        if c.strip() == '':
                            continue

                        cmd_list = c.strip().split(' ')

                        if len(cmd_list) == 1:
                            cmd, args = cmd_list[0], []
                        else:
                            cmd, args = cmd_list[0], cmd_list[1].split(',')
                        self.log.debug(f"{cmd} {args}")

                        try:
                            cmd_fn = self.cmds.get(cmd)
                            if cmd_fn is None:
                                self.log.warning(f"Command {cmd} is not registered")
                                continue

                            resp = cmd_fn(*args)

                        except TypeError as e:
                            self.log.error(f"Command error: {e}")
                            continue

                        if resp is not None:
                            conn.send(resp.encode())

    def get_idn(self):
        return ','.join([
            "Lakeshore",
            "LSSIM_{}P".format(self.num_channels),
            self.sn,
            'v0.0.0'
        ])

    def get_reading(self, chan, unit='S'):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        return self.channels[chan_index].get_reading(unit=unit)

    def get_reading_status(self, chan):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        bit_string = "000"
        return bit_string

    def get_scanner(self):
        msg_string = '{:02d},{} '.format(int(self.active_channel), str(self.scanner))
        print(msg_string)
        return msg_string

    def set_scanner(self, chan, auto):
        if not 0 <= int(chan) <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        self.active_channel = int(chan)
        self.scanner = int(auto)

    def get_input_parameters(self, chan):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        return self.channels[chan_index].get_inset()

    def set_input_parameters(self, chan, *args):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        args = map(int, args)
        self.channels[chan_index].set_inset(*args)

    def get_tlimit(self, chan):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        temp = str(self.channels[chan_index].temp_limit)
        return temp

    def set_tlimit(self, chan, limit):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        self.channels[chan_index].temp_limit = float(limit)

    def get_rdgpwr(self, chan):
        if chan == 'A':
            chan_index = 0
        else:
            chan_index = int(chan)
        if not 0 <= chan_index <= self.num_channels:
            self.log.warning(f"chan num must be A or between 1 and {self.num_channels}")
            return

        return self.channels[chan_index].get_excitation_power()

    def get_outmode(self, heater_output):
        if not 0 <= int(heater_output) <= 2:
            self.log.warning("heater output must be between 0 and 2")
            return

        return self.heaters[int(heater_output)].get_output_mode()

    def set_outmode(self, heater_output, *args):
        if not 0 <= int(heater_output) <= 2:
            self.log.warning("heater output must be between 0 and 2")
            return

        args = map(str, args)
        self.heaters[int(heater_output)].set_output_mode(*args)

    def get_htrset(self, heater_output):
        if not 0 <= int(heater_output) <= 2:
            self.log.warning("heater output must be 0 or 1")
            return

        return self.heaters[int(heater_output)].get_heater_setup()

    def set_htrset(self, heater_output, *args):
        if not 0 <= int(heater_output) <= 2:
            self.log.warning("heater output must be 0 or 1")
            return

        args = map(int, args)
        self.heaters[int(heater_output)].set_heater_setup(*args)

    def get_mout(self, heater_output):
        if not 0 <= int(heater_output) <= 2:
            self.log.warning("heater output must be between 0 and 2")
            return

        return str(self.heaters[int(heater_output)].output_value)

    def set_mout(self, heater_output, value):
        if not 0 <= int(heater_output) <= 2:
            self.log.warning("heater output must be between 0 and 2")
            return

        self.heaters[int(heater_output)].output_value = float(value)

    def get_ramp(self, heater_output):
        if not 0 <= int(heater_output) <= 2:
            self.log.warning("heater output must be between 0 and 2")
            return

        ramp_string = '{},{}'.format(str(self.heaters[int(heater_output)].ramp),
                                     str(self.heaters[int(heater_output)].rate))
        return ramp_string

    def set_ramp(self, heater_output, enabled, value):
        if not 0 <= int(heater_output) <= 2:
            self.log.warning("heater output must be between 0 and 2")
            return

        if int(enabled) in [0,1]:
            self.heaters[int(heater_output)].ramp = int(enabled)
        else:
            self.log.warning("0 = ramping off, 1 = ramping on")
            return

        if 0.001 <= float(value) <= 100:
            self.heaters[int(heater_output)].rate = float(value)
        else:
            self.log.warning("setpoint ramp rate must be between 0.001 and 100 k/min")
            return

    def get_ramp_status(self, heater_output):
        if not 0 <= int(heater_output) <= 2:
            self.log.warning("heater output must be between 0 and 2")
            return

        return str(self.heaters[int(heater_output)].status)

    def get_heater_range(self, heater_output):
        if not 0 <= int(heater_output) <= 2:
            self.log.warning("heater output must be between 0 and 2")
            return

        return str(self.heaters[int(heater_output)].rng)

    def set_heater_range(self, heater_output, heater_range):
        if not 0 <= int(heater_output) <= 2:
            self.log.warning("heater output must be between 0 and 2")
            return

        self.heaters[int(heater_output)].rng = int(heater_range)

    def get_setpoint(self, heater_output):
        if not 0 <= int(heater_output) < 2:
            self.log.warning("heater output must be 0 or 1")
            return

        return str(self.heaters[int(heater_output)].setpoint)

    def set_setpoint(self, heater_output, setp):
        if not 0 <= int(heater_output) < 2:
            self.log.warning("heater output must be 0 or 1")
            return

        self.heaters[int(heater_output)].setpoint = setp

    def get_still(self):
        return str(self.heaters[2].output_value)

    def set_still(self, output):
        self.heaters[2].output_value = float(output)

    def get_pid(self):
        return ','.join([str(self.heaters[0].P), str(self.heaters[0].I), str(self.heaters[0].D)])

    def set_pid(self, heater_output, p, i, d):
        if not 0 <= int(heater_output) < 2:
            self.log.warning("heater output must be 0 or 1")
            return

        if 0.0 <= float(p) <= 1000:
            self.heaters[int(heater_output)].P = float(p)
        else:
            self.log.warning("P value must be between 0.0 and 1000")
            return

        if 0 <= float(i) <= 10000:
            self.heaters[int(heater_output)].I = float(i)
        else:
            self.log.warning("I value must be between 0 and 10000")
            return

        if 0 <= float(d) <= 2500:
            self.heaters[int(heater_output)].D = float(d)
        else:
            self.log.warning("D value must be between 0 and 2500")
            return

    def get_curve_header(self, curve):
        curve_index = int(curve)
        if not 1 <= curve_index <= 59:
            self.log.warning(f"curve num must be between 1 and 59")
            return

        return self.curves[curve_index].get_header()

    def set_curve_header(self, curve, *args):
        curve_index = int(curve)
        if not 21 <= curve_index <= 59:
            self.log.warning(f"curve num must be between 21 and 59")
            return

        args = map(str, args)
        self.curves[curve_index].set_header(*args)

    def get_curve_data(self, curve, index):
        curve_index = int(curve)
        if not 1 <= curve_index <= 59:
            self.log.warning(f"curve num must be between 1 and 59")
            return

        return '{},{},{}'.format(str(self.curves[curve_index].data[int(index)][0]),
                                 str(self.curves[curve_index].data[int(index)][1]),
                                 str(self.curves[curve_index].data[int(index)][2]))

    def set_curve_data(self, curve, index, units, kelvin, curvature=0):
        curve_index = int(curve)
        if not 21 <= curve_index <= 59:
            self.log.warning(f"curve num must be between 21 and 59")
            return

        self.curves[curve_index].data[int(index)][0] = float(units)
        self.curves[curve_index].data[int(index)][1] = float(kelvin)
        self.curves[curve_index].data[int(index)][2] = float(curvature)

    def delete_curve(self, curve):
        curve_index = int(curve)
        if not 21 <= curve_index <= 59:
            self.log.warning(f"curve num must be between 21 and 59")
            return

        for i in range(1, 201):
            self.curves[curve_index].data[i][0] = 0
            self.curves[curve_index].data[i][1] = 0
            self.curves[curve_index].data[i][2] = 0
