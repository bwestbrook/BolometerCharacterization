import os
import json
from pprint import pprint


class ToolTipExtractor():

    def __init__(self):
        '''
        '''

    def get_widgets(self, path):
        '''
        '''
        all_widgets = []
        tool_tip_dict = {}
        with open(path, 'r') as fh:
            for i, line in enumerate(fh.readlines()):
                widget_name = None
                if '_label = self.gb_m' in line or '_label = QtWi' in line:
                    widget_name = line.split(' ')[8].split('.')[1]
                    print(line.split(' '))
                    all_widgets.append(widget_name)
                elif '_lineedit = self.gb_m' in line or '_lineedit = QtWi' in line:
                    try:
                        widget_name = line.split(' ')[8].split('.')[1]
                        print(line.split(' '))
                        all_widgets.append(widget_name)
                    except IndexError:
                        pass
                elif '_combobox = self.gb_m' in line or '_combobox = QtWi' in line:
                    widget_name = line.split(' ')[8].split('.')[1]
                    print(line.split(' '))
                    all_widgets.append(widget_name)
                elif '_checkbox = QtW' in line:
                    widget_name = line.split(' ')[8].split('.')[1]
                    print(line.split(' '))
                    all_widgets.append(widget_name)
                elif '_pushbutton = QtW' in line:
                    try:
                        widget_name = line.split(' ')[8].split('.')[1]
                        print(line.split(' '))
                        all_widgets.append(widget_name)
                    except IndexError:
                        pass
                if widget_name is not None:
                    tool_tip = 'Tool Tip {0}'.format(i)
                    tool_tip_dict[widget_name] = tool_tip
        return tool_tip_dict

    def save_tool_tip_dict(self, tool_tip_dict, script):
        '''
        '''
        name = script.split('.')[0]
        full_path = os.path.join('bd_resources', '{0}_tool_tips.json'.format(name))
        with open(full_path, 'w') as fh:
            json.dump(tool_tip_dict, fh, indent=4, sort_keys=True)

if __name__ == '__main__':

    script = 'rt_collector.py'
    path = os.path.join('bd_tools', script)
    tte = ToolTipExtractor()
    tool_tip_dict = tte.get_widgets(path)
    tte.save_tool_tip_dict(tool_tip_dict, script)
