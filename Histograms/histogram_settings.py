import os
from libraries.gen_class import Class

histogram_settings = Class()

##################################################### RUN CONFIG #####################################################
histogram_settings.make_histogram = False
histogram_settings.combine_data = True

# Data Types to Run
histogram_settings.run_tc = False
histogram_settings.run_rn = True
histogram_settings.run_psat = False
histogram_settings.run_pturn = False

# Data Source 
histogram_settings.from_john = False
histogram_settings.from_logan = False
histogram_settings.from_darcy = False
histogram_settings.from_tucker = False
histogram_settings.from_kek = True


##################################################### DATA LOADING #####################################################
histogram_settings.data_dir = 'C:\Users\pb2safabrication\Repositories\BolometerCharacterization\Data'
histogram_settings.data_dir = 'C:\Users\jamin\Repositories\BolometerCharacterization\Data'

#### TC DATA ####
histogram_settings.tc_path_1 = os.path.join(histogram_settings.data_dir, 'PB201101\\20170712_raise_PB201101_res_Tc.pkl') #KEK Run38
histogram_settings.tc_path_2 = os.path.join(histogram_settings.data_dir, 'PB201102\\20170712_raise_PB201102_res_Tc.pkl') #KEK Run38
histogram_settings.tc_path_3 = os.path.join(histogram_settings.data_dir, 'PB201102\\20170712_raise_PB201102_res_Tc.pkl') #UCSD Test Tucker 
histogram_settings.tc_path_4 = os.path.join(histogram_settings.data_dir, 'PB201311\\180316_RvsT_PB201311_data.pkl') #PB2B Backend Logan
histogram_settings.tc_path_5 = os.path.join(histogram_settings.data_dir, 'PB201315\\PB201315_Tc.pkl')

#### Rn Data ####
histogram_settings.rn_path_1 = os.path.join(histogram_settings.data_dir, 'PB201311\\180316_RvsT_PB201311_data.pkl')
histogram_settings.rn_path_2 = os.path.join(histogram_settings.data_dir, 'PB201101\\Overbiased_Resistance_fromIV_Run38_20171103.pkl')
histogram_settings.rn_path_3 = os.path.join(histogram_settings.data_dir, 'PB201309\\bolometer_properties_from_IVs.pkl')

#### Psat/Pturn Data ####
histogram_settings.pturn_path_1 = os.path.join(histogram_settings.data_dir, 'PB201311\\180416_Pturn_PB201311_data.pkl')
histogram_settings.pturn_path_2 = os.path.join(histogram_settings.data_dir, 'PB201311\\180416_Psat_PB201311.pkl')
histogram_settings.pturn_path_3 = os.path.join(histogram_settings.data_dir, 'PB201108\\Pturn_1108_300k_load.pkl')
histogram_settings.pturn_path_4 = os.path.join(histogram_settings.data_dir, 'PB201309\\bolometer_properties_from_IVs.pkl')
histogram_settings.pturn_path_5 = os.path.join(histogram_settings.data_dir, 'Version13\\PB201311_PB201309_combined_psat.pkl')


#histogram_settings.data_paths = [histogram_settings.tc_path_5]
histogram_settings.data_paths = [histogram_settings.pturn_path_3]



histogram_settings.data_combo_dict = {
                                      'logan': histogram_settings.tc_path_4,
                                      }


histogram_settings.data_combo_dict = {
                                      'logan': histogram_settings.tc_path_4,
                                      #'kek': histogram_settings.tc_path_2,
                                      }

histogram_settings.data_combo_dict = {
                                      'john': histogram_settings.pturn_path_4,
                                      'logan': histogram_settings.pturn_path_2,
                                      }

histogram_settings.data_combo_dict = {
                                      'kek': histogram_settings.pturn_path_3,
                                      }

histogram_settings.data_combo_dict = {
                                       #'john': histogram_settings.rn_path_3,
                                      'logan': histogram_settings.rn_path_1,
                                      }
##################################################### PLOTTING #####################################################
# TARGET RANGES
histogram_settings.tc_target_range = {'90': {'Target': [(440.0, 460.0)], 'Requirement': [(420.0, 480.0)]},
                                      '150': {'Target': [(440.0, 460.0)], 'Requirement': [(420.0, 480.0)]}}
histogram_settings.tc_target_range = {'90': {'Target': []},
                                      '150': {'Target': []}}
histogram_settings.rn_target_range = {'90': {'Target': [(1.0, 1.2)], 'Requirement': [(0.9, 1.5)]},
                                      '150': {'Target': [(1.0, 1.2)], 'Requirement': [(0.9, 1.5)]}}
histogram_settings.rn_target_range = {'90': {'Target': []},
                                      '150': {'Target': []}}
histogram_settings.psat_target_range = {'90': {'Requirement': [(5.0, 15.0)]},
                                        '150': {'Requirement': [(16.0, 30.0)]}}
histogram_settings.psat_target_range = {'90': {'Target': [(7.0, 9.0)], 'Requirement': [(5.0, 15.0)]},
                                        '150': {'Target': [(17.0, 24.0)], 'Requirement': [(16.0, 30.0)]}}
histogram_settings.psat_target_range = {'90': {'Target': [(7.0, 9.0)]},
                                        '150': {'Target': [(17.0, 24.0)]}}
histogram_settings.psat_target_range = {'90': {'Target': []},
                                        '150': {'Target': []}}
# Plotting for Tc
histogram_settings.tc_bins = 20
histogram_settings.tc_xlim = (400, 500)
# Plotting for Rn
histogram_settings.rn_bins = 35
histogram_settings.rn_xlim = (0.5, 2.5)
# Plotting for Pturn
histogram_settings.pturn_xlim = (0, 35)
histogram_settings.pturn_bins = 35
