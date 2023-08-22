# Exposure time is graphed against median count with a linear regression,
# using the images in 'test_exposures/'.
# Same functionality as 'exposure_grapher.py' without generating new exposures.
# Before running make sure the global variables match those which generated the captures.

import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
import scipy.optimize as scpo

exp_start_time = 0.1
exp_range = 0.1
nexps = 100

def line(xs, gradient, intercept):
    return gradient*xs + intercept

# creates a matplotlib graph with a linear regression of exposure time against median count
xs = np.arange(exp_start_time, exp_start_time+exp_range, exp_range/nexps)
ys = np.zeros(nexps)
for i in range(nexps):
    with fits.open(f"test_exposures/exposure{str(i)}.fits") as image:
        image_array = image[0].data
        ys[i] = np.median(image_array)
actual_fit_parameters, covariance_matrix = scpo.curve_fit(line, xs, ys)
fit_gradient = actual_fit_parameters[0]
fit_intercept = actual_fit_parameters[1]
y_best_fits = line(xs, fit_gradient, fit_intercept)
print(f"Gradient: {str(fit_gradient)}; Intercept: {str(fit_intercept)}")
plt.figure(1)
plt.plot(xs, ys, marker='o', label="data")
plt.plot(xs, y_best_fits, linestyle='dashed', label="best fit")
plt.xlabel("exposure time")
plt.ylabel("median count")
plt.legend()
plt.show()
