# This file defines the IndiClient which is used as the base class for all the other client classes.
# When connected to a server, the new... methods are called when the server
# registers a new instance of the corresponding object.
# For example, when the server informs the client of a new BLOB object (image),
# the newBLOB method is called which saves the image to a file
# and either tells the server to take a new capture or close the program.

import io, logging, sys
import PyIndi

class IndiClient(PyIndi.BaseClient):
 
    device = None
    count = 0

    def __init__(self, exp_time=0.1, nexps=1):
        super(IndiClient, self).__init__()
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
        self.logger = logging.getLogger('PyQtIndi.IndiClient')
        self.logger.info('creating an instance of PyQtIndi.IndiClient')
        self.exp_time = exp_time
        self.nexps = nexps

    def newDevice(self, d):
        self.logger.info("new device " + d.getDeviceName())
        # try to catch the all sky camera device "SX CCD UltraStar"
        if d.getDeviceName() == "SX CCD UltraStar":
            self.logger.info("Set new device SX CCD UltraStar")
            # save reference to the device in member variable
            self.device = d
    def newProperty(self, p):
        self.logger.info("new property "+ p.getName() + " for device "+ p.getDeviceName())
        if self.device is not None and p.getName() == "CONNECTION" and p.getDeviceName() == self.device.getDeviceName():
            self.logger.info("Got property CONNECTION for SX CCD UltraStar")
            # connect to device
            self.connectDevice(self.device.getDeviceName())
            # set BLOB mode to BLOB_ALSO
            self.setBLOBMode(1, self.device.getDeviceName(), None)
        if p.getName() == "CCD_EXPOSURE":
            # take first exposure
            self.takeExposure()
    def removeProperty(self, p):
        self.logger.info("remove property "+ p.getName() + " for device "+ p.getDeviceName())
    def newBLOB(self, bp):
        self.logger.info("new BLOB "+ bp.name)
        # get image data
        img = bp.getblobdata()
        # write image data to BytesIO buffer
        blobfile = io.BytesIO(img)
        # open a file and save buffer to disk
        with open("current.fits", "wb") as f:
            f.write(blobfile.getvalue())
            self.logger.info("image saved to 'current.fits'")
        self.count += 1
        # start new exposure if count<ndarks, else combine darks
        if self.count < self.nexps:
            self.takeExposure()
        else:
            sys.exit()
    def newSwitch(self, svp):
        self.logger.info ("new Switch "+ svp.name + " for device "+ svp.device)
    def newNumber(self, nvp):
        self.logger.info("new Number "+ nvp.name + " for device "+ nvp.device)
    def newText(self, tvp):
        self.logger.info("new Text "+ tvp.name + " for device "+ tvp.device)
    def newLight(self, lvp):
        self.logger.info("new Light "+ lvp.name + " for device "+ lvp.device)
    def newMessage(self, d, m):
        # self.logger.info("new Message "+ d.messageQueue(m))
        pass
    def serverConnected(self):
        self.logger.info("Server connected ("+self.getHost()+":"+str(self.getPort())+")")
    def serverDisconnected(self, code):
        self.logger.info("Server disconnected (exit code = "+str(code)+","+str(self.getHost())+":"+str(self.getPort())+")")
    
    def takeExposure(self):
        self.logger.info(">>>>>>>>")
        # get current exposure time
        exp = self.device.getNumber("CCD_EXPOSURE")
        # set exposure time to exp_time in seconds
        exp[0].value = self.exp_time
        # send new exposure time to server/device
        self.sendNewNumber(exp)
