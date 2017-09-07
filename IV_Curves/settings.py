class Class(object):

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

        def __repr__(self):
            return "%s(%s)" % (self.__class__.__name__, str(self.__dict__))

settings = Class()


# 350 Bolo from Double Slot Dipole 
data_path = '../Data/2015_06_09/002_Squid_06_Chan_06_4k_IV_Curve.dat'
settings.determine_calibration = False
squid_conv = 28.7

# 220 Bolo from HF Triplexe
data_path = '../Data/2015_06_09/001_Squid_01_Chan_01_4k_IV_Curve.dat'
settings.determine_calibration = False
squid_conv = 37.1

# Calibration Resistor IV
data_path = '../Data/2015_06_09/001_Squid_04_Chan_04_4k_IV_Curve.dat'
settings.determine_calibration = True
settings.calibration_resistor_val = 0.5

# Calibration Resistor IV
data_path = '../Data/2015_07_10/Calib_R/4K_IV_Curve.dat'
settings.determine_calibration = True
settings.calibration_resistor_val = 0.5

# ASTE SQUID 4, 10/13/2015
data_path = '../Data/2015_10_13/011_Chan4_IV_1p2K.dat'
label='Chan 4 @ 1.2K'
data_path = '../Data/2015_10_13/009_Chan4_IV_4K.dat'
label='Chan 4 @ 4K'
data_path = '../Data/2015_10_13/018_Chan4_IV_275mK.dat'
label='Chan 4 @ 250mK'
settings.determine_calibration = False
settings.calibration_resistor_val = 0.5
squid_conv = 30.0

# ASTE SQUID 2, 10/13/2015
data_path = '../Data/2015_10_13/019_Chan2_IV_275mK.dat'
label='Chan 2 @ 250mK'
data_path = '../Data/2015_10_13/008_Chan2_IV_4K.dat'
label='Chan 2 @ 4K'
data_path = '../Data/2015_10_13/012_Chan2_IV_1p2K.dat'
label='Chan 2 @ 1.2K'
settings.determine_calibration = False
settings.calibration_resistor_val = 0.5
squid_conv = 32.5

# ASTE SQUID 5, 10/13/2015
settings.determine_calibration = False
data_path = '../Data/2015_10_13/014_Chan5_IV_1p2K.dat'
label='Chan 5 @ 1.2K'
data_path = '../Data/2015_10_13/005_Chan5_IV_4K.dat'
label='Chan 5 @ 4K'
data_path = '../Data/2015_10_13/017_Chan5_IV_275mK.dat'
label='Chan 5 @ 250mK'
settings.calibration_resistor_val = 0.5
squid_conv = 26.8

# ASTE SQUID 6, 10/13/2015
settings.determine_calibration = False
data_path = '../Data/2015_10_13/016_Chan6_IV_275mK.dat'
label='Chan 6 @ 250mK'
data_path = '../Data/2015_10_13/006_Chan6_IV_4K.dat'
label='Chan 6 @ 4K'
data_path = '../Data/2015_10_13/015_Chan6_IV_1p2K.dat'
label='Chan 6 @ 1.2K'
settings.calibration_resistor_val = 0.5

# ASTE SQUID 6, 10/19/2015 and 10/20/2015
settings.determine_calibration = False
data_path = '../Data/2015_10_20/003_SQ6_IV_Curve_4K.dat'
label='Chan 6 @ 4K'
data_path = '../Data/2015_10_20/004_SQ6_IV_Curve_1p2K.dat'
label='Chan 6 @ 1.2K'
data_path = '../Data/2015_10_19/005_SQ6_IV_Curve_275mK.dat'
label='Chan 6 @ 310mK'
settings.calibration_resistor_val = 0.5
squid_conv = 28.7

# ASTE SQUID 5, 10/19/2015 and 10/20/2015
settings.determine_calibration = False
data_path = '../Data/2015_10_19/007_SQ5_IV_Curve_275mK.dat'
label='Chan 5 @ 310mK'
data_path = '../Data/2015_10_20/006_SQ5_IV_Curve_1p2K.dat'
label='Chan 5 @ 1.2K'
data_path = '../Data/2015_10_20/002_SQ5_IV_Curve_4K.dat'
label='Chan 5 @ 4K'
settings.calibration_resistor_val = 0.5
squid_conv = 26.8

# ASTE SQUID 6, 10/22/2015
settings.determine_calibration = False
data_path = ''
label='Chan 6 @ 4K'
settings.calibration_resistor_val = 0.5
squid_conv = 28.7

# ASTE SQUID 4, 10/22/2015
settings.determine_calibration = False
data_path = ''
label='Chan 4 @ 4K'
settings.calibration_resistor_val = 0.5
squid_conv = 30.0

# ASTE SQUID 3, 10/22/2015
settings.determine_calibration = False
data_path = '../Data/2015_10_22/016_SQ3_IV_Curve_275mK.dat'
label='Chan 3 @ 275mK'
settings.calibration_resistor_val = 0.5
settings.clip = (5, 520)
squid_conv = 30.0


# ASTE SQUID 4, 01/20/2016
settings.determine_calibration = False
data_path = '../Data/2016_01_18/012_SQUID4_IV_base_temp.dat'
label='Chan 4 @ 275mK'
settings.calibration_resistor_val = 0.5
settings.clip = (5, 20)
squid_conv = 30.0

# ASTE SQUID 5, 01/20/2016
settings.determine_calibration = False
data_path = '../Data/2016_01_20/012_SQUID5_IV_Data.dat'
label='Chan 5 @ 275mK'
settings.calibration_resistor_val = 0.5
settings.clip = (5, 520)
squid_conv = 30
squid_conv = 30.0


# ASTE SQUID 4, 01/21/2016
settings.determine_calibration = False
data_path = '../Data/2016_01_21/SQUID_4_IV_Base_Temp_2.dat'
label='Chan 4 @ 275mK'
settings.calibration_resistor_val = 0.5
settings.clip = (5, 1000)
squid_conv = 30
squid_conv = 30.0

# ASTE SQUID 5, 01/21/2016
settings.determine_calibration = False
data_path = '../Data/2016_01_21/SQUID_5_IV_Base_Temp.dat'
label='Chan 5 @ 275 mK'
settings.calibration_resistor_val = 0.5
settings.clip = (5, 1000)
squid_conv = 30
squid_conv = 30.0



# BT3 SQUID 5, 08/31/2017
settings.determine_calibration = False
data_path = '../Data/2017_09_01/SQ5_350C_350mK_IVCurve.dat'
label='Chan 4 @ 350 mK'
settings.calibration_resistor_val = 0.5
settings.clip = (0, 1000)
squid_conv = 30
squid_conv = 25.9




# BT3 SQUID 6, 08/31/2017
settings.determine_calibration = False
data_path = '../Data/2017_09_01/SQ6_300C_350mK_IVCurve.dat'
label='Chan 6 @ 350 mK'
settings.calibration_resistor_val = 0.5
settings.clip = (5, 1000)
squid_conv = 30
squid_conv = 25.0

# BT3 SQUID 6, 08/31/2017
settings.determine_calibration = False
data_path = '../Data/2017_09_01/SQ6_300C_1.1K_IVCurve.dat'
label='Chan 6 @ 1.1 K'
settings.calibration_resistor_val = 0.5
settings.clip = (5, 1000)
squid_conv = 30
squid_conv = 25.0



# BT3 SQUID 5, 08/31/2017
settings.determine_calibration = False
data_path = '../Data/2017_09_05/SQ5_1.1K_IVCurve.dat'
label='Chan 5 @ 1.1 K'
settings.calibration_resistor_val = 0.5
settings.clip = (5, 1000)
squid_conv = 25.9

# BT3 SQUID 4, 08/31/2017
settings.determine_calibration = False
data_path = '../Data/2017_09_05/SQ4_1.1K_IVCurve.dat'
label='Chan 4 @ 1.1 K'
settings.calibration_resistor_val = 0.5
settings.clip = (5, 1000)
squid_conv = 30.1

# BT3 SQUID 6, 08/31/2017
settings.determine_calibration = False
data_path = '../Data/2017_09_05/SQ6_1.1K_IVCurve.dat'
label='Chan 6 @ 1.1 K'
settings.calibration_resistor_val = 0.5
settings.clip = (5, 1000)
squid_conv = 25.0
voltage_conv = 1e-4

# BT3 SQUID 2, 08/31/2017
settings.determine_calibration = False
data_path = '../Data/2017_09_05/SQ2_1.1K_IVCurve.dat'
data_path = '../Data/2017_09_06/SQ2_1.1K_IVCurve.dat'
label='Chan 2 @ 1.1 K'
settings.calibration_resistor_val = 0.5
settings.clip = (0.01, 10)
squid_conv = 27.3
voltage_conv = 1e-4

settings.data_path = data_path
settings.label = label
settings.voltage_conv = voltage_conv
settings.squid_conv = squid_conv
