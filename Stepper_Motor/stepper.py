import sys
import numpy as np

class Stepper():

    def __init__(self, com_port):
        self.hello = 'for stepper stuff'
        self.stepper_position_dict = {'COM1': 0, 'COM2': 0, 'COM3': 0, 'COM4': 0}
        self.com_port = com_port

    def connect_to_com_port(self, com_port):
        if np.random.random() > 0.5:
            return True
        else:
            return False

    def get_current_position_from_com_port(self, com_port):
        return self.stepper_position_dict[com_port]

    def move_to(self, move_to):
        print 'Im moving {0} to position {1}'.format(self.com_port, move_to)

    def test(self, com_port='COM1'):
        self.connect_to_com_port(com_port)
        self.get_current_position_from_com_port(com_port)

    def _is_stepper(self):


if __name__ == '__main__':
    print sys.argv
    com_port = sys.argv[1]
    #move_to = sys.argv[2]
    stepper = Stepper(com_port)
    #stepper.move_to(move_to)
