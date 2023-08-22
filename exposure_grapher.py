# Run 'indiserver -v indi_sx_ccd' to launch the server with the needed driver.

# Takes 'nexps' exposures each with an increased exposure time on the one before.
# Exposure time is then graphed against median count with a linear regression.

import io, os, sys, time
import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
import scipy.optimize as scpo
from indi_client import IndiClient

# GraphClient inherits from Indiclient
class GraphClient(IndiClient):
    
    def __init__(self, exp_time=0.1, nexps=10, exp_range=0.1):
        super().__init__(exp_time, nexps)
        self.logger.info("instance subclass: GraphClient")
        self.exp_start_time = exp_time
        self.exp_range = exp_range
        # clear test_exposures directory
        dir = 'test_exposures'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))
        self.logger.info("test_exposures directory cleared")

    def newBLOB(self, bp):
        self.logger.info("new BLOB "+ bp.name)
        # get image data
        img = bp.getblobdata()
        # write image data to BytesIO buffer
        blobfile = io.BytesIO(img)
        # open a file and save buffer to disk
        with open(f"test_exposures/exposure{str(self.count)}.fits", "wb") as f:
            f.write(blobfile.getvalue())
        # increases the exposure time for the next capture
        self.count += 1
        self.exp_time += self.exp_range / self.nexps
        # start new exposure if count<nexps, else plot median exposure count
        if self.count < self.nexps:
            self.takeExposure()
        else:
            self.graph()

    def line(self, xs, gradient, intercept):
        return gradient*xs + intercept
    
    # creates a matplotlib graph with a linear regression of exposure time against median count
    def graph(self):
        xs = np.linspace(self.exp_start_time, self.exp_start_time+self.exp_range, self.nexps)
        ys = np.zeros(self.nexps)
        for i in range(self.nexps):
            with fits.open(f"test_exposures/exposure{str(i)}.fits") as image:
                image_array = image[0].data
                ys[i] = np.median(image_array)
        actual_fit_parameters, covariance_matrix = scpo.curve_fit(self.line, xs, ys)
        fit_gradient = actual_fit_parameters[0]
        fit_intercept = actual_fit_parameters[1]
        y_best_fits = self.line(xs, fit_gradient, fit_intercept)
        self.logger.info(f"Gradient: {str(fit_gradient)}; Intercept: {str(fit_intercept)}")
        plt.figure(1)
        plt.plot(xs, ys, marker='o', label="data")
        plt.plot(xs, y_best_fits, linestyle='dashed', label="best fit")
        plt.xlabel("exposure time")
        plt.ylabel("median count")
        plt.legend()
        plt.show()

# instantiate the client
indiclient=GraphClient(exp_range=0.05, nexps=50)
# set indi server localhost and port 7624
indiclient.setServer("localhost",7624)
# connect to indi server
print("Connecting to indiserver")
if (not(indiclient.connectServer())):
     print("No indiserver running on "+indiclient.getHost()+":"+str(indiclient.getPort()))
     sys.exit(1)
  
# start endless loop, client works asynchron in background
while True:
    time.sleep(1)
