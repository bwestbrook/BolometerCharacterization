# AlMn Only 

input_dict_1 = {'data_path': '/home/westbrook/Desktop/Pixel_Testing/Data/2015_10_28/White_GRT_200_3mV/005_AlMn_Only.dat',
                'grt_serial_number': 29268,
                'label': 'AlMn Only, 200$\Omega$ Rng (W)',
                'sample_res_factor': 1.,
                'grt_res_factor': 100.}

input_dict_2 = {'data_path': '/home/westbrook/Desktop/Pixel_Testing/Data/2015_10_28/Black_GRT_200_3mV/003_AlMn_Only.dat',
                'grt_serial_number': 29268,
                'label': 'AlMn Only, 200$\Omega$ Rng (B)',
                'sample_res_factor': 1.,
                'grt_res_factor': 100.}

input_dict_3 = {'data_path': '/users/Jamin/Repositories/Experimental_CMB_Scripts/Pixel_Testing/Data/2015_10_28/White_GRT_2000_3mV/006_AlMn_Only.dat',
                'grt_serial_number': 29268,
                'label': 'AlMn Only, 2000$\Omega$ Rng (W)',
                'sample_res_factor': 1.,
                'grt_res_factor': 1000.}

input_dict_4 = {'data_path': '/users/Jamin/Repositories/Experimental_CMB_Scripts/Pixel_Testing/Data/2017_09_01/SQ6_300C_RvT_atTc.dat',
                'grt_serial_number': 29268,
                'label': 'BT3-04 300C, UR',
                'sample_res_factor': 1.,
                'grt_res_factor': 1000.}

input_dict_5 = {'data_path': '/users/Jamin/Repositories/Experimental_CMB_Scripts/Pixel_Testing/Data/2017_09_05/SQ2_RvsT_Hi2Lo.dat',
                'grt_serial_number': 29268,
                'label': 'AlMn New Hi2Lo',
                'sample_res_factor': 1.,
                'normal_res': 23.15,
                'invert': True,
                'grt_res_factor': 100.}

input_dict_6 = {'data_path': '/users/Jamin/Repositories/Experimental_CMB_Scripts/Pixel_Testing/Data/2017_09_05/SQ2_RvsT_Lo2Hi.dat',
                'grt_serial_number': 29268,
                'label': 'AlMn Old',
                'sample_res_factor': 1.,
                'normal_res': 23.15,
                'invert': True,
                'grt_res_factor': 100.}

input_dict_7 = {'data_path': '/users/Jamin/Repositories/Experimental_CMB_Scripts/Pixel_Testing/Data/2017_09_05/SQ4_RvsT_Hi2Lo.dat',
                'grt_serial_number': 29268,
                'label': 'AlMn Old Hi2Lo',
                'sample_res_factor': 1.,
                'normal_res': 0.84,
                'invert': False,
                'grt_res_factor': 1000.}

input_dict_8 = {'data_path': '/users/Jamin/Repositories/Experimental_CMB_Scripts/Pixel_Testing/Data/2017_09_05/SQ4_RvsT_Lo2Hi.dat',
                'grt_serial_number': 29268,
                'label': 'AlMn Old Lo2Hi',
                'sample_res_factor': 1.,
                'normal_res': 0.84,
                'invert': False,
                'grt_res_factor': 1000.}

input_dict_9 = {'data_path': '/users/Jamin/Repositories/Experimental_CMB_Scripts/Pixel_Testing/Data/2017_09_05/SQ2_RvsT_Hi2Lo_3.dat',
                'grt_serial_number': 29268,
                'label': 'AlMn New Hi2Lo',
                'sample_res_factor': 1.,
                'normal_res': 23.15,
                'invert': True,
                'grt_res_factor': 1000.}

input_dict_10 = {'data_path': '/users/Jamin/Repositories/Experimental_CMB_Scripts/Pixel_Testing/Data/2017_09_06/SQ2_RvsT_Lo2Hi.dat',
                'grt_serial_number': 29268,
                'label': 'AlMn New Lo2Hi',
                'sample_res_factor': 1.,
                'normal_res': 23.15,
                'invert': True,
                'grt_res_factor': 1000.}

input_dict_11 = {'data_path': '/users/Jamin/Repositories/Experimental_CMB_Scripts/Pixel_Testing/Data/2017_09_06/SQ2_RvsT_Hi2Lo.dat',
                'grt_serial_number': 29268,
                'label': 'AlMn New Hi2Lo',
                'sample_res_factor': 1.,
                'normal_res': 23.15,
                'invert': True,
                'grt_res_factor': 1000.}

xlim = (400, 600)
list_of_input_dicts = [input_dict_1, input_dict_2, input_dict_3]
list_of_input_dicts = [input_dict_5]

list_of_input_dicts = [input_dict_7, input_dict_8] # AlMn Old
list_of_input_dicts = [input_dict_5, input_dict_9] #AlMn New
list_of_input_dicts = [input_dict_10, input_dict_11] # AlMn New
