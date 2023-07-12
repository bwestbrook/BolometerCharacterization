from bd_lib.bolo_daq import BoloDAQ
from PyQt5 import QtCore, QtGui, QtWidgets
from GuiBuilder.gui_builder import GuiBuilder, GenericClass
from bd_lib.bolo_pyvisa import BoloPyVisa

class PyVisaUtility(QtWidgets.QWidget, GuiBuilder):

    def __init__(self, status_bar, screen_resolution, monitor_dpi):
        '''
        '''
        super(PyVisaUtility, self).__init__()
        self.status_bar = status_bar
        self.screen_resolution = screen_resolution
        self.monitor_dpi = monitor_dpi
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.bvp = BoloPyVisa()
        self.pvu_gui_panel()

    def pvu_gui_panel(self):
        '''
        '''
        welcome_header_label = QtWidgets.QLabel('Welcome to PyVisa Utility', self)
        self.layout().addWidget(welcome_header_label, 0, 0, 1, 2)
        self.com_port_combobox = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.com_port_combobox, 1, 0, 1, 1)
        for resource in self.bvp.resources:
            if not 'ASRL' in resource:
                self.com_port_combobox.addItem(resource)
        self.test_command_lineedit = QtWidgets.QLineEdit('*IDN?', self)
        self.layout().addWidget(self.test_command_lineedit, 1, 1, 1, 2)
        send_command_and_read_pushbutton = QtWidgets.QPushButton('Send Command and Read', self)
        self.layout().addWidget(send_command_and_read_pushbutton, 2, 0, 1, 1)
        send_command_pushbutton = QtWidgets.QPushButton('Send Command', self)
        self.layout().addWidget(send_command_pushbutton, 2, 1, 1, 1)
        read_port_pushbutton = QtWidgets.QPushButton('Read Instrument Report', self)
        self.layout().addWidget(read_port_pushbutton, 2, 2, 1, 1)
        self.status_string_label = QtWidgets.QLabel('SERIAL READ', self)
        self.layout().addWidget(self.status_string_label, 3, 0, 1, 3)
        read_port_pushbutton.clicked.connect(self.pvu_read_command)
        send_command_pushbutton.clicked.connect(self.pvu_send_command)
        send_command_and_read_pushbutton.clicked.connect(self.pvu_send_command_and_read)

    def pvu_send_command(self):
        '''
        '''
        if not hasattr(self.bvp, 'inst'):
            return None

    def pvu_read_command(self):
        '''
        '''
        if not hasattr(self.bvp, 'inst'):
            return None

    def pvu_send_command_and_read(self):
        '''
        '''
        if not hasattr(self.bvp, 'inst'):
            return None
        command = self.test_command_lineedit.text()
        command_str = "{0}".format(command)
        self.status_bar.showMessage('Sending {0}'.format(command_str))
        response = self.bvp.inst.query(command_str)
        self.status_string_label.setText(response)

