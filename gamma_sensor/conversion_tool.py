# Applies S or S^{-1} to a given image
import matplotlib.pyplot as pl
import numpy as np
from scipy.ndimage import imread  # needs pillow!
import os

from uncoverml import filtering


test_file = os.path.expanduser('~/Data/badger.jpg')

def main():

    # Make the inputs
    gain = 1.
    mass_attenuation_air = 0.09  # assume some sort of bulk property
    density_air = 1.22
    mu_air = mass_attenuation_air * density_air
    res_x = 20.0  # metres
    res_y = 20.0
    img0 = np.mean(imread(test_file), axis=2).T
    img = img0
    img_w, img_h = img.shape
    height = 100  # metres

    # Compute a sensor footprint of the same shape as the image:
    S = filtering.sensor_footprint(img_w, img_h, res_x, res_y, height, mu_air,
                                gain)
   
    # Apply and unapply the filter (mirrored boundary conditions)
    out1 = filtering.fwd_filter(img, S)
    out2 = filtering.inv_filter(out1, S)

    pl.subplot(131)
    pl.imshow(img.T, interpolation='none', cmap=pl.cm.gray)
    pl.title('Original')
    pl.subplot(132)
    pl.imshow(out1.T, interpolation='none', cmap=pl.cm.gray)
    pl.title('Forward Sensored')
    pl.subplot(133)
    pl.imshow(out2.T, interpolation='none', cmap=pl.cm.gray)
    pl.title('Inverse Sensored')
    pl.show()




if __name__=='__main__':
    main()