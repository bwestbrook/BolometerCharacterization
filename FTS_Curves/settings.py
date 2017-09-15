from settings_files.hf_triplexer_settings import *
from settings_files.lf_triplexer_settings import *
from settings_files.hybrid_settings import *
from settings_files.tetraplexer_settings import *
from settings_files.dsdp_settings import *
from settings_files.one_off_settings import *

class Class(object):

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

        def __repr__(self):
            return "%s(%s)" % (self.__class__.__name__, str(self.__dict__))

settings = Class()

divide_mmf_response = True
divide_beam_splitter_response = True
simulations = False
data = False
both = False
co_plot = True
for_poster = False
plot_foreground = False

print wafers

if list(set(pixels)) == 'LF_Triplexer':
    smoothing_factor = 1
else:
    smoothing_factor = 3

#Apply all settings here
settings.frequencies = frequencies
settings.wafers = wafers
settings.dies = dies
settings.dates = dates
settings.pixels = pixels
settings.simulations = simulations
settings.data = data
settings.co_plot = co_plot
settings.both = both
settings.divide_mmf_response = divide_mmf_response
settings.divide_beam_splitter_response = divide_beam_splitter_response
settings.smoothing_factor = smoothing_factor
settings.for_poster = for_poster
settings.plot_foreground = plot_foreground

settings.pos_for_40 = pos_for_40
settings.pos_for_60 = pos_for_60
settings.pos_for_90 = pos_for_90
settings.pos_for_150 = pos_for_150
settings.pos_for_220 = pos_for_220
settings.pos_for_280 = pos_for_280
settings.pos_for_350 = pos_for_350

