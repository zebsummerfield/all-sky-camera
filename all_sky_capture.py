# Run 'indiserver -v indi_sx_ccd' to launch the server with the needed driver.

# Continuously requests a CCD capture and saves the current image to 'current.fits;
# then the 'master_dark_0.1.fits' is subtracted from the image and the new file is saved as 'current_minus_dark.fits'.

import os, sys, time
from astropy.io import fits
from indi_client import IndiClient

# CaptureClient inherits from IndiClient
class CaptureClient(IndiClient):

    def __init__(self, exp_time=0.1, nexps=1):
        super().__init__(exp_time, nexps)
        self.logger.info("instance subclass: CaptureClient")
 
    def newBLOB(self, bp):
        self.logger.info("new BLOB "+ bp.name)
        # get image data
        img = bp.getblobdata()
        # write image data to BytesIO buffer
        import io
        blobfile = io.BytesIO(img)
        # open a file and save buffer to disk
        with open("current.fits", "wb") as f:
            f.write(blobfile.getvalue())
            self.logger.info("image saved to 'current.fits'")
        # subtract dark from image and save to new fits file
        with fits.open("current.fits") as image:
            image_array = image[0].data.astype('int')
            with fits.open("master_dark_0.1.fits") as dark:
                dark_array = dark[0].data.astype('int')
                minus_dark = image_array - dark_array
                minus_dark[minus_dark < 0] = 0
                minus_dark = minus_dark.astype('uint16')
                try:
                    os.remove("current_minus_dark.fits")
                except:
                    pass
                hdu = fits.PrimaryHDU(minus_dark)
                hdu.writeto("current_minus_dark.fits")
                self.logger.info("image with dark subtracted saved to 'current_minus_dark.fits'")
        sys.exit()
 
# instantiate the client
indiclient = CaptureClient()
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