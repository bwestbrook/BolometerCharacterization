import numpy as np

class Stepper():

    def __init__(self):
        self.hello = 'for stepper stuff'
        self.stepper_position_dict = {'COM1': 0, 'COM2': 0, 'COM3': 0, 'COM4': 0}

    def connect_to_com_port(self, com_port):
        print 'will connect to com port {0} here'.format(com_port)
        if np.random.random() > 0.5:
            return True
        else:
            return False

    def get_current_position_from_com_port(self, com_port):
        print 'Actual code will connect to driver and get position of {0}'.format(com_port)
        print 'for now it just pull for the dict'
        return self.stepper_position_dict[com_port]
