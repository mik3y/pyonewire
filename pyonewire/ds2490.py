"""
Python interface to DS2490 USB device, (c) 2005 mike wakerly
Derived from libusblinux300 package, (c) 2004 Dallas Semiconductor Corporation

This is an all-Python rewrite of the c libraries provided by Dallas for use
with DS2490-based 1-Wire adapters.

This package requires Python and libusb. As both are available for Linux,
Windows, and Mac OS X platforms, this is a truly universal library.

In this first pass of rewrite, little attempt has been made to refactor or
clarify the original Dallas code (which is mostly well written anyway.)
"""

import time

import cstruct
import usb
import libusb

### defines - from libusbds2490.c

# Request byte, Command Type Code Constants 
CONTROL_CMD = 0x00
COMM_CMD = 0x01
MODE_CMD = 0x02
TEST_CMD = 0x03

# Value field, Control commands
# Control Command Code Constants 
CTL_RESET_DEVICE = 0x0000
CTL_START_EXE = 0x0001
CTL_RESUME_EXE = 0x0002
CTL_HALT_EXE_IDLE = 0x0003
CTL_HALT_EXE_DONE = 0x0004
CTL_CANCEL_CMD = 0x0005
CTL_CANCEL_MACRO = 0x0006
CTL_FLUSH_COMM_CMDS = 0x0007
CTL_FLUSH_RCV_BUFFER = 0x0008
CTL_FLUSH_XMT_BUFFER = 0x0009
CTL_GET_COMM_CMDS = 0x000A

# Value field COMM Command options

# COMM Bits (bitwise or into COMM commands to build full value byte pairs)
# Byte 1
COMM_TYPE = 0x0008
COMM_SE = 0x0008
COMM_D = 0x0008
COMM_Z = 0x0008
COMM_CH = 0x0008
COMM_SM = 0x0008
COMM_R = 0x0008
COMM_IM = 0x0001

# Byte 2
COMM_PS = 0x4000
COMM_PST = 0x4000
COMM_CIB = 0x4000
COMM_RTS = 0x4000
COMM_DT = 0x2000
COMM_SPU = 0x1000
COMM_F = 0x0800
COMM_ICP = 0x0200
COMM_RST = 0x0100

# Read Straight command, special bits 
COMM_READ_STRAIGHT_NTF = 0x0008
COMM_READ_STRAIGHT_ICP = 0x0004
COMM_READ_STRAIGHT_RST = 0x0002
COMM_READ_STRAIGHT_IM = 0x0001

# Value field COMM Command options (0-F plus assorted bits)
COMM_ERROR_ESCAPE = 0x0601
COMM_SET_DURATION = 0x0012
COMM_BIT_IO = 0x0020
COMM_PULSE = 0x0030
COMM_1_WIRE_RESET = 0x0042
COMM_BYTE_IO = 0x0052
COMM_MATCH_ACCESS = 0x0064
COMM_BLOCK_IO = 0x0074
COMM_READ_STRAIGHT = 0x0080
COMM_DO_RELEASE = 0x6092
COMM_SET_PATH = 0x00A2
COMM_WRITE_SRAM_PAGE = 0x00B2
COMM_WRITE_EPROM = 0x00C4
COMM_READ_CRC_PROT_PAGE = 0x00D4
COMM_READ_REDIRECT_PAGE_CRC = 0x21E4
COMM_SEARCH_ACCESS = 0x00F4

# Mode Command Code Constants 
# Enable Pulse Constants
ENABLEPULSE_PRGE = 0x01  # strong pull-up
ENABLEPULSE_SPUE = 0x02  # programming pulse

# 1Wire Bus Speed Setting Constants
ONEWIREBUSSPEED_REGULAR = 0x00
ONEWIREBUSSPEED_FLEXIBLE = 0x01
ONEWIREBUSSPEED_OVERDRIVE = 0x02

# Value field Mode Commands options
MOD_PULSE_EN = 0x0000
MOD_SPEED_CHANGE_EN = 0x0001
MOD_1WIRE_SPEED = 0x0002
MOD_STRONG_PU_DURATION = 0x0003
MOD_PULLDOWN_SLEWRATE = 0x0004
MOD_PROG_PULSE_DURATION = 0x0005
MOD_WRITE1_LOWTIME = 0x0006
MOD_DSOW0_TREC = 0x0007

TIMEOUT_LIBUSB = 5000

### defines - from ownet.h
WRITE_FUNCTION = 1
READ_FUNCTION = 0

# error codes
READ_ERROR = 1
INVALID_DIR = 2
NO_FILE = 3
WRITE_ERROR = 4
WRONG_TYPE = 5
FILE_TOO_BIG = 6

# mode bit flags
MODE_NORMAL = 0x00
MODE_OVERDRIVE = 0x01
MODE_STRONG5 = 0x02
MODE_PROGRAM = 0x04
MODE_BREAK = 0x08

# output flags
LV_ALWAYS = 2
LV_OPTIONAL = 1
LV_VERBOSE = 0


### defines - libusbllnk.c
FAMILY_CODE_04_ALARM_TOUCHRESET_COMPLIANCE = 1


### defines - libusbds2490.h
DS2490_EP1 = 0x81
DS2490_EP2 = 0x02
DS2490_EP3 = 0x83


def SetupPacket():
   return cstruct.cStruct(( ('C', 'RequestTypeReservedBits'),
                            ('C', 'Request'),
                            ('H', 'Value'),
                            ('H', 'Index'),
                            ('H', 'Length'),
                            ('H', 'DataOut'), # XXX SMALLINT
                            ('s', 'DataInBuffer'),
                         ))
def StatusPacket():
   return cstruct.cStruct(( ('C', 'EnableFlags'),
                            ('C', 'OneWireSpeed'),
                            ('C', 'StrongPullUpDirection'),
                            ('C', 'ProgPulseDuration'),
                            ('C', 'PullDownSlewRate'),
                            ('C', 'Write1LowTime'),
                            ('C', 'DSOW0RecoveryTime'),
                            ('C', 'Reserved1'),
                            ('C', 'StatusFlags'),
                            ('C', 'CurrentCommCmd1'),
                            ('C', 'CurrentCommCmd2'),
                            ('C', 'CommBufferStatus'),
                            ('C', 'WriteBufferStatus'),
                            ('C', 'ReadBufferStatus'),
                            ('C', 'Reserved2'),
                            ('C', 'Reserved3'),
                            ('s', 'CommResultCodes'),
                         ))


class DS2490:
   VENDORID    = 0x04fa
   PRODUCTID   = 0x2490
   INTERFACEID = 0x0

   def __init__(self):
      self.devfile = None

      self.USBLevel = 0 # TODO - fix to proper init values (?)
      self.USBSpeed = 0
      self.owAcquire()

   def _ResetSearch(self):
      self._LastDiscrep = 0
      self._LastDevice = 0
      self._LastFamilyDiscrep = 0

   def owAcquire(self):
      """
      Attempt to acquire a 1-wire net using a USB port and a DS2490 based
      adapter.

      Returns:
         True - success, USB port opened
         False - failure
      """

      self.devfile= usb.OpenDevice(DS2490.VENDORID, DS2490.PRODUCTID, DS2490.INTERFACEID)
      print 'setting alt interface...',
      ret = libusb.usb_set_altinterface(self.devfile.iface.device.handle, 3)
      print 'done (ret=%i)' % ret
      print 'cleaing endpoints'
      libusb.usb_clear_halt(self.devfile.iface.device.handle, DS2490_EP3)
      libusb.usb_clear_halt(self.devfile.iface.device.handle, DS2490_EP2)
      libusb.usb_clear_halt(self.devfile.iface.device.handle, DS2490_EP1)
      #self.devfile.resetep()

      # verify adapter is working
      print 'adapter recover..'
      ret = self.AdapterRecover()
      print 'done (ret=%i)' % ret
      return self.owTouchReset()

   def owLevel(self, new_level):
      """
      Set the 1-Wire net line level.

      The values for new_level are as follows:
      
      Input:
         new_level - new level defined as
            MODE_NORMAL    0x00
            MODE_STRONG5   0x02
            MODE_PROGRAM   0x04 (not supported in this version)
            MODE_BREAK     0x08 (not supported in this chip)

      Returns:
         Current 1-Wire Net level
      """
      setup = SetupPacket()
      # turn off infinite strong pullup?
      if new_level == MODE_NORMAL and self.USBLevel == MODE_STRONG5:
         if self.DS2490HaltPulse():
            self.USBLevel = MODE_NORMAL
      elif new_level == MODE_STRONG5 and self.USBLevel == MODE_NORMAL: # turn on infinite strong5 pullup?
         # assume duration set to infinite during setup of device
         # enable the pulse
         setup.RequestTypeReservedBits = 0x40
         setup.Request = MODE_CMD
         setup.Value = MOD_PULSE_EN
         setup.Index = ENABLEPULSE_SPUE
         setup.Length = 0x00
         setup.DataOut = False
         # call the libusb driver
         ret = libusb.usb_control_msg( self.devfile.iface.device.handle,
                                       setup.RequestTypeReservedBits,
                                       setup.Request,
                                       setup.Value,
                                       setup.Index,
                                       '',
                                       TIMEOUT_LIBUSB)
         if ret < 0:
            # failure
            self.AdapterRecover()
            return self.USBLevel

         # start the pulse
         setup.RequestTypeReservedBits = 0x40
         setup.Request = COMM_CMD
         setup.Value = COMM_PULSE | COMM_IM
         setup.Index = 0
         setup.Length = 0
         setup.DataOut = False
         # call the libusb driver
         ret = libusb.usb_control_msg( self.devfile.iface.device.handle,
                                       setup.RequestTypeReservedBits,
                                       setup.Request,
                                       setup.Value,
                                       setup.Index,
                                       '',
                                       TIMEOUT_LIBUSB)
         if ret < 0:
            # failure
            self.AdapterRecover()
            return self.USBLevel
         else:
            # success, read the result
            self.USBLevel = new_level
            return new_level

      elif new_level != self.USBLevel: # unsupported
         return self.USBLevel

      # success, return the current level
      # XXX - is this path even valid, or just for completeness, in dallas source..?
      return self.USBLevel

   def owTouchReset(self):
      """
      Reset all of the devices on the 1-Wire net and return the result.

      Returns:
         True - presence pulse(s) detected, device(s) reset
         False - no presence pulses detected

      Source:
         libusbllnk.c
      """
      print 'owTouchReset'
      # make sure strong pullup is not on
      if self.USBLevel == MODE_STRONG5:
         self.owLevel(MODE_NORMAL)

      # construct command
      setup = SetupPacket()
      setup.RequestTypeReservedBits = 0x40
      setup.Request = COMM_CMD
      setup.Value = COMM_1_WIRE_RESET | COMM_F | COMM_IM | COMM_SE
      setup.Index = ONEWIREBUSSPEED_FLEXIBLE #XXX OVERDRIVE
      setup.Length = 0
      setup.DataOut = False
      ret = libusb.usb_control_msg( self.devfile.iface.device.handle,
                                    setup.RequestTypeReservedBits,
                                    setup.Request,
                                    setup.Value,
                                    setup.Index,
                                    '',
                                    TIMEOUT_LIBUSB)
      if ret < 0:
         # failure
         self.AdapterRecover()
         return False
      else:
         # extra delay for alarming ds1994/ds2404 compliance
         if FAMILY_CODE_04_ALARM_TOUCHRESET_COMPLIANCE and self.USBSpeed != MODE_OVERDRIVE:
            time.sleep(0.005)

         # success, check for shorts
         if self.DS2490ShortCheck():
            self.USBVpp = vpp
            return True # 'present'
         else:
            # short occuring
            time.sleep(0.300)
            self.AdapterRecover()
            return False

   def AdapterRecover(self):
      """
      Attempt to recover communication with the DS2490

      Returns:
         True - DS2490 recover successful
         False - failed to recover

      Source:
         libusbllnk.c
      """
      print 'AdapterRecover'
      if self.DS2490Detect():
         self.USBSpeed = MODE_NORMAL
         self.USBLevel = MODE_NORMAL
         return True
      else:
         return False

   def DS2490Detect(self):
      print 'DS2490Detect'
      setup = SetupPacket()

      # reset the DS2490
      self.DS2490Reset()

      # set the stron pullup duration to infinite
      setup.RequestTypeReservedBits = 0x40
      setup.Request = COMM_CMD
      setup.Value = COMM_SET_DURATION | COMM_IM
      setup.Index = 0x0000
      setup.Length = 0
      setup.DataOut = False

      # call the libusb driver
      ret = libusb.usb_control_msg( self.devfile.iface.device.handle,
                                    setup.RequestTypeReservedBits,
                                    setup.Request,
                                    setup.Value,
                                    setup.Index,
                                    '',
                                    TIMEOUT_LIBUSB)

      # set the 12V pullup duration to 512us
      setup.RequestTypeReservedBits = 0x40
      setup.Request = COMM_CMD
      setup.Value = COMM_SET_DURATION | COMM_IM | COMM_TYPE
      setup.Index = 0x0040
      setup.Length = 0
      setup.DataOut = False

      # call the libusb driver
      ret = libusb.usb_control_msg( self.devfile.iface.device.handle,
                                    setup.RequestTypeReservedBits,
                                    setup.Request,
                                    setup.Value,
                                    setup.Index,
                                    '',
                                    TIMEOUT_LIBUSB)

      # disable strong pullup, but leave progrm pulse enabled (faster)
      setup.RequestTypeReservedBits = 0x40
      setup.Request = MODE_CMD
      setup.Value = MOD_PULSE_EN
      setup.Index = ENABLEPULSE_PRGE
      setup.Length = 0x00
      setup.DataOut = False

      # call the libusb driver
      ret = libusb.usb_control_msg( self.devfile.iface.device.handle,
                                    setup.RequestTypeReservedBits,
                                    setup.Request,
                                    setup.Value,
                                    setup.Index,
                                    '',
                                    TIMEOUT_LIBUSB)

      # return result of short check (XXX - return value correct?)
      return self.DS2490ShortCheck()

   def DS2490Reset(self):
      """
      Performs a hardware reset of the DS2490 equivalent to a power-on reset.

      Returns:
         True - success
         False - failure

      Source:
         libusbds2490.c
      """
      print 'DS2490Reset'
      setup = SetupPacket()

      # setup for reset
      setup.RequestTypeReservedBits = 0x40
      setup.Request = CONTROL_CMD
      setup.Value = CTL_RESET_DEVICE
      setup.Index = 0x00
      setup.Length = 0x0
      setup.DataOut = False

      # call the libusb driver
      ret = libusb.usb_control_msg( self.devfile.iface.device.handle,
                                    setup.RequestTypeReservedBits,
                                    setup.Request,
                                    setup.Value,
                                    setup.Index,
                                    '',
                                    TIMEOUT_LIBUSB)

      if ret < 0 :
         return False
      return True

   def DS2490GetStatus(self):
      print 'DS2490GetStatus'
      buf = self.devfile.read(32, TIMEOUT_LIBUSB)
      print 'got status: %s' % (repr(buf),)
      if len(buf) < 16:
         return None
      status = StatusPacket()
      status.unpack(buf) # TODO: make sure CommResultCodes (string) handling is correct
      return status

   def DS2490ShortCheck(self):
      """
      Check to see if there is a short on the 1-Write bus.

      Used to stop communication with the DS2490 while the short is in effect
      to not overrun the buffers.

      Returns:
         True - DS2490 1-Wire is NOT shorted
         False - Could not detect DS2490 or 1-Wire shorted
      """
      # get the result registers (if any)
      print 'DS2490ShortCheck'
      status = self.DS2490GetStatus()
      if status is None:
         return False

      # get vpp present flag
      vpp = (status.StatusFlags & STATUSFLAGS_12VP) != 0

      # check for short
      if status.CommBufferStatus != 0:
         return False
      else:
         # check for short
         for i in range(len(status.CommResultCodes)):
            # check for SH bit (0x02), ignore 0xA5
            if status.CommResultCodes[i] & COMMCMDERRORRESULT_SH:
               # short detected
               return False

      present = True

      # loop through result registers
      for i in range(len(status.CommResultCodes)):
         # only check for error conditions when the condition is not a ONEWIRE
         # DEVICEDETECT
         if status.CommResultCodes[i] != ONEWIREDEVICEDETECT:
            # check for NRS bit
            if status.CommResultCodes[i] & COMMCMDERRORRESULT_NRS:
               # empty bus detected
               present = False
      return True

   # owFirst, from libusbnet.c
   def owFirst(self, alarm_only = False):
      """
      Find the first device on the 1-Wire net

      This function contains only one parameter, 'alarm_only'. When 'alarm_only'
      is True, the find alarm command 0xEC is sent instead of the normal search
      command 0xF0.

      Using the find alarm command will limit the search to only 1-Wire devices
      that are in an 'alarm' state.

      Returns:
         String serialnumber - a device was found and its serial number is
         returned
         None - There are no devices on the 1-Wire Net
      """
      self._ResetSearch()
      return self.owNext()

   def owNext(self):
      """
      The owNext function does a general search.

      This function continues from the previous search state. The search state
      can be reset by using the owFirst function.

      This function contains only one parameter, 'alarm_only' (default False).
      When 'alarm_only' is True, the find alarm command 0xEC is sent instead of
      the normal search command 0xF0.

      Using the find alarm command will limit the search to only 1-Wire devices
      that are in an 'alarm' state.

      Returns:
         String serialnumber - a device was found and its serial number is
         returned
         False - no new device was found. Either the last search was the last
         device or there are no devices on the 1-Wire Net
      """

      if self._LastDevice:
         self._ResetSearch()
         return False

      if self._LastDiscrep != 0xFF:
         pass # XXX stop here

      search_command = (0xF0, 0xEC)[alarm_only == 1]

      # if do_reset - not impl. in python (yet?)

      # build the rom number to pass to the USB chip

      # take into account LastDiscrep
      if self._LastDiscrep != 0xFF:
         if self._LastDiscrep > 0:
            # bitacc stuff here - TODO
            pass

      # put the ROM ID in EP2
      if not self.DS2490Write(rom_buf):
         self.AdapterRecover()
         return False

      # setup for search command call
      setup.RequestTypeReservedBits = 0x40
      setup.Request = COMM_CMD
      setup.Value = COMM_SEARCH_ACCESS | COMM_IM | COMM_SM | COMM_F | COMM_RTS
      # the number of devices to read (1) with the search command
      setup.Index = 0x0100 | (search_cmd & 0x00ff)
      setup.Length = 0
      setup.DataOut = False
      # call the libusb driver
      ret = libusb.usb_control_msg( self.devfile.iface.device.handle,
                                    setup.RequestTypeReservedBits,
                                    setup.Request,
                                    setup.Value,
                                    setup.Index,
                                    '',
                                    TIMEOUT_LIBUSB)

      if ret < 0:
         # failure
         self.AdapterRecover()
         return False

      # set a time limit
      limit = time.time() + .200

      def loop_body():
         status = self.DS2490GetStatus()
         if not status:
            return 0 # ie, break
         else:
            # look for any fail conditions
            for i in range(len(status.CommResultCodes)):
               # only check for error conditions when the condition is not a
               # ONEWIREDEVICEDETECT
               if status.CommResultCodes[i] != ONEWIREDEVICEDETECT:
                  # failure
                  return 0 # ie break
         return status

      # do...while{}
      status = loop_body()
      while status != 0 and (status.StatusFlags & STATUSFLAGS_IDLE) == 0 and time.time() < limit:
         status = loop_body()

      # check the results of the wait for idle
      if status.StatusFlags & STATUSFLAGS_IDLE == 0:
         self.AdapterRecover()
         return False

      # check for data
      if status.ReadBufferStatus > 0:
         # read the load
         buf_len = 16
         if not self.DS2490Read():
            self.AdapterRecover()
            return False

         # success, get rom and discrepancy
         self._LastDevice = (buf_len == 8)

         # extract the ROM and check crc
         self.setcrc8(0)
         for i in range(8):
            self.SerialNum[i] = ret_buf[i]

      # crc OK and family code is not 8
      if not lastcrc8 and self.SerialNum[0] != 0:
         # loop through the discrepancy to get the pointers
         for i in range(64):
            # if discrepancy
            if self.testbit(i, ret_buf[8]) and not self.testbit(i, ret_buf[0]):
               self._LastDiscrep = i + 1
         rt = True
      else:
         ResetSearch = True
         rt = False

      # check if need to reset search
      if ResetSearch:
         self._LastDiscrep = 0xFF
         self._LastDevice = False
         self.SerialNum = 0 # TODO define this field

      return rt




if __name__ == '__main__':
   print 'getting new devices...'
   usb.UpdateLists()
   dev = DS2490()
   print 'dev acquited, now trying to get status...'
   dev.DS2490GetStatus()
   dev.devfile.close()

