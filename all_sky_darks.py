# Run 'indiserver -v indi_sx_ccd' to launch the server with the needed driver.

# Takes 'nexps' exposures and median combines them to create a dark;
# this is saved as 'master_dark_{exp_time}.fits'.

import io, os, sys, time
import numpy as np
from astropy.io import fits
from indi_client import IndiClient

# DarkClient inherits from IndiClient
class DarkClient(IndiClient):

    def __init__(self, exp_time=0.1, nexps=10):
        super().__init__(exp_time, nexps)
        self.logger.info("instance subclass: DarkClient")
    
    def newBLOB(self, bp):
        self.logger.info("new BLOB "+ bp.name)
        # get image data
        img = bp.getblobdata()
        # write image data to BytesIO buffer
        blobfile = io.BytesIO(img)
        # open a file and save buffer to disk
        with open(f"dark_exposures/dark{str(self.count)}.fits", "wb") as f:
            f.write(blobfile.getvalue())
        self.count += 1
        # start new exposure if count<nexps, else combine darks
        if self.count < self.nexps:
            self.takeExposure()
        else:
            self.combineDarks()

    def combineDarks(self):
        with fits.open("dark_exposures/dark0.fits") as image0:
            image0_array = image0[0].data
        size = image0_array.shape
        cube = np.zeros((self.nexps, size[0], size[1]))
        for k in range(self.nexps):
            with fits.open(f"dark_exposures/dark{str(k)}.fits") as image:
                image_array = image[0].data
            cube[k,:,:] = image_array
        master_dark = np.median(cube,axis=0)
        master_dark = master_dark.astype("uint16")
        try:
            os.remove(f"master_dark_{self.exp_time}.fits")
        except:
            pass
        hdu = fits.PrimaryHDU(master_dark)
        hdu.writeto(f"master_dark_{self.exp_time}.fits")
        self.logger.info(f"Darks combined and saved as as master_dark_{self.exp_time}.fits")
        sys.exit()
 
# instantiate the client
indiclient = DarkClient()
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
