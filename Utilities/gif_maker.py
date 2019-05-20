import imageio
import sys
import os


class GifMaker():

    def __init__(self):
        print('Welcome to Gif Maker')

    def _make_if_fft_gif(self, folder_path):
        gif_basename = os.path.basename(folder_path)
        gif_path = os.path.join(folder_path, gif_basename + '.gif')
        images = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            #tiled_filename = './temp_files/IF_GIF/tiled_{0}.png'.format(str(i).zfill(3))
            #montage_command = 'montage {0} {1} -geometry 1600x3200+0+0 -tile 1x2 {2}'.format(if_filename, fft_filename, tiled_filename)
            #subprocess.call(montage_command, shell=True)
            images.append(imageio.imread(file_path))
        imageio.mimsave(gif_path, images, duration=0.1)
        print('Saved gif to {0}'.format(gif_path))

if __name__ == '__main__':
    gf = GifMaker()
    if len(sys.argv) == 2:
        folder_name = sys.argv[1]
    else:
        folder_name = 'SQ1_BT5-05-CR-No-Mitigation_FTS_Scan_Max_Freq_299.33_GHz_Resolution_59.91_GHz_Raw_01'
        folder_name = 'SQ1__FTS_Scan_Max_Freq_299.33_GHz_Resolution_29.95_GHz_Raw_01'
    folder_path = os.path.join('./temp_files', folder_name)
    gf._make_if_fft_gif(folder_path)
