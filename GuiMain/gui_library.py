import sys
import os
import subprocess
import shutil
import time
import numpy as np
import datetime
import pylab as pl
from PyPDF2 import PdfFileMerger
from pprint import pprint
from copy import copy
from PyQt4 import QtCore, QtGui
from libraries.gen_class import Class
from ba_settings.all_settings import settings
from RT_Curves.plot_rt_curves import RTCurve


class GuiTemplate(QtGui.QWidget):

    def __init__(self, analysis_types):
        super(GuiTemplate, self).__init__()
        self.grid = QtGui.QGridLayout()
        self.grid.setVerticalSpacing(0)
        self.setLayout(self.grid)
        self.__apply_settings__(settings)
        self._create_main_window('main_panel_widget')
        self.main_panel_widget.show()
        self.data_folder = './data'

    def __apply_settings__(self, settings):
        for setting in dir(settings):
            if '__' not in setting:
                setattr(self, setting, getattr(settings, setting))

    def _create_main_window(self, name):
        self._create_popup_window(name)
        self._build_panel(settings.main_panel_build_dict)

    def _close_main(self):
        self.main_panel_widget.close()
        sys.exit()

    def _select_analysis_type(self):
        sender_name = str(self.sender().whatsThis())
        checkboxes = ['_main_panel_ivcurve_checkbox', '_main_panel_rtcurve_checkbox']
        for checkbox in checkboxes:
            if sender_name == checkbox:
                getattr(self, checkbox).setCheckState(True)
                self.analysis_type = checkbox.split('_')[3]
            else:
                getattr(self, checkbox).setCheckState(False)

    def _select_file(self):
        self.data_path = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.data_folder))
        getattr(self, '_main_panel_selected_file_label').setText(os.path.basename(self.data_path))

    def _run_analysis(self):
        if not hasattr(self, 'analysis_type'):
            getattr(self, '_main_panel_selected_file_label').setText('Please Select a Analysis Type')
        else:
            print self.analysis_type

    def _plot_rt_curve(self):
        rt = RtCurve()
        rt.run()
        print 'plotting RT'

    #################################################
    # WIDGET GENERATORS AND FUNCTIONS
    #################################################

    def _unpack_widget_function(self, function_text):
        if '.' in function_text:
            if len(function_text.split('.')) == 2:
                base_function, attribute_function = function_text.split('.')
                base_function = getattr(self, base_function)
                widget_function = getattr(base_function, attribute_function)
        else:
            widget_function = getattr(self, function_text)
        return widget_function

    def _build_panel(self, build_dict, parent=None):
        for unique_widget_name, widget_settings in build_dict.iteritems():
            widget_settings_copy = copy(build_dict['_common_settings'])
            if unique_widget_name != '_common_settings':
                widget_settings_copy.update(widget_settings)
                widget_settings_copy.update({'parent': parent})
                for widget_param, widget_param_value in widget_settings.iteritems():
                    if 'function' == widget_param:
                        widget_function = self._unpack_widget_function(widget_param_value)
                        widget_settings_copy.update({'function':  widget_function})

                self._create_and_place_widget(unique_widget_name, **widget_settings_copy)

    def _create_popup_window(self, name):
        popup_window = QtGui.QWidget()
        popup_window.setGeometry(100, 100, 400, 200)
        popup_window.setLayout(QtGui.QGridLayout())
        setattr(self, name, popup_window)

    def _create_and_place_widget(self,
                                 unique_widget_name,
                                 parent=None,
                                 function=None,
                                 text=None,
                                 font=None,
                                 color=None,
                                 width=None,
                                 height=None,
                                 layout=None,
                                 url=None,
                                 orientation=None,
                                 tick_interval=None,
                                 tick_range=None,
                                 check_state=None,
                                 word_wrap=None,
                                 pixmap=None,
                                 alignment=None,
                                 keep_aspect_ratio=True,
                                 image_scale=(100, 100),
                                 widget_alignment=None,
                                 position=None,
                                 place_widget=True,
                                 **widget_setttings):
        widget_type = self.widget_to_object_dict[unique_widget_name.split('_')[-1]]
        if orientation is not None and widget_type == 'QSlider':
            widget = QtGui.QSlider(getattr(QtCore.Qt, orientation))
            widget.setTracking(True)
        else:
            if parent is not None:
                widget = getattr(QtGui, widget_type)(parent)
            else:
                widget = getattr(QtGui, widget_type)()
        if function is not None:
            if widget_type == 'QSlider':
                widget.valueChanged.connect(function)
            elif widget_type in ('QPushButton', 'QCheckBox'):
                widget.clicked.connect(function)
                #button_icon = QtGui.QIcon()
                #button_icon.addFile('./resources/Bolo_Chip.jpg')
                #widget.setIcon(button_icon)
                #widget.setIconSize(QtCore.QSize(50, 50))
            elif widget_type in ('QLineEdit', 'QTextEdit'):
                widget.textChanged.connect(function)
            elif widget_type in ('QComboBox',):
                widget.activated.connect(function)
        if text is not None:
            if url is not None:
                text = '<a href=\"{0}\">{1}</a>'.format(url, text)
                widget.setOpenExternalLinks(True)
            widget.setText(text)
        if font is not None:
            widget.setFont(getattr(self, '{0}_font'.format(font)))
        if width is not None:
            widget.setFixedWidth(width)
        if height is not None:
            widget.setFixedHeight(height)
        if word_wrap is not None:
            widget.setWordWrap(word_wrap)
        if color is not None:
            widget.setStyleSheet('%s {color: %s}' % (widget_type, color))
        if pixmap is not None:
            image = QtGui.QPixmap(pixmap)
            if keep_aspect_ratio:
                image = image.scaled(image_scale[0], image_scale[1], QtCore.Qt.KeepAspectRatio)
            else:
                image = image.scaled(image_scale[0], image_scale[1])
            widget.setPixmap(image)
        if alignment is not None:
            qt_alignment = getattr(QtCore.Qt, 'Align{0}'.format(alignment))
            widget.setAlignment(qt_alignment)
        if layout is not None:
            widget.setLayout(getattr(QtGui, layout)())
        if tick_interval is not None:
            widget.setTickInterval(1)
        if tick_range is not None:
            widget.setRange(tick_range[0], tick_range[1])
        if check_state is not None:
            widget.setCheckState(check_state)
        if place_widget:
            row, col, row_span, col_span = position[0], position[1], position[2], position[3]
            if 'widget' in unique_widget_name:
                if widget_alignment is not None:
                    self.grid.addWidget(widget, row, col, row_span, col_span,
                                        getattr(QtCore.Qt, widget_alignment))
                else:
                    self.grid.addWidget(widget, row, col, row_span, col_span)
                    print widget
            else:
                if 'panel' in unique_widget_name:
                    panel = '{0}_{1}'.format(unique_widget_name.split('_panel')[0][1:], 'panel_widget')
                if 'popup' in unique_widget_name:
                    panel = '{0}_{1}'.format(unique_widget_name.split('_popup')[0][1:], 'popup')
                if 'panel' in unique_widget_name and 'popup' in unique_widget_name and widget_type != 'QWidget':
                    panel = '_{0}_{1}'.format(unique_widget_name.split('_panel')[0][1:], 'panel')
                if widget_alignment is not None:
                    getattr(self, panel).layout().addWidget(widget, row, col, row_span, col_span,
                                                            getattr(QtCore.Qt, widget_alignment))
                else:
                    getattr(self, panel).layout().addWidget(widget, row, col, row_span, col_span)
        else:
            widget.close()
        setattr(self, unique_widget_name, widget)
        widget.setWhatsThis(unique_widget_name)
        return widget
