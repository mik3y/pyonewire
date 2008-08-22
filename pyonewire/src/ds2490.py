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

import logging
import struct
import sys
import time

import cstruct
import usb
import usb

### defines - from libusbds2490.c

# status flags
STATUSFLAGS_SPUA = 0x01  # if set Strong Pull-up is active
STATUSFLAGS_PRGA = 0x02  # if set a 12V programming pulse is being generated
STATUSFLAGS_12VP = 0x04  # if set the external 12V programming voltage is present
STATUSFLAGS_PMOD = 0x08  # if set the DS2490 powered from USB and external sources
STATUSFLAGS_HALT = 0x10  # if set the DS2490 is currently halted
STATUSFLAGS_IDLE = 0x20  # if set the DS2490 is currently idle


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
# Result Registers
ONEWIREDEVICEDETECT = 0xA5  # 1-Wire device detected on bus
COMMCMDERRORRESULT_NRS = 0x01  # if set 1-WIRE RESET did not reveal a Presence Pulse or SET PATH did not get a Presence Pulse from the branch to be connected
COMMCMDERRORRESULT_SH  = 0x02  # if set 1-WIRE RESET revealed a short on the 1-Wire bus or the SET PATH couln not connect a branch due to short
COMMCMDERRORRESULT_APP = 0x04  # if set a 1-WIRE RESET revealed an Alarming Presence Pulse
COMMCMDERRORRESULT_VPP =          0x08  # if set during a PULSE with TYPE=1 or WRITE EPROM command the 12V programming pulse not seen on 1-Wire bus
COMMCMDERRORRESULT_CMP =          0x10  # if set there was an error reading confirmation byte of SET PATH or WRITE EPROM was unsuccessful
COMMCMDERRORRESULT_CRC =          0x20  # if set a CRC occurred for one of the commands: WRITE SRAM PAGE, WRITE EPROM, READ EPROM, READ CRC PROT PAGE, or READ REDIRECT PAGE W/CRC
COMMCMDERRORRESULT_RDP =          0x40  # if set READ REDIRECT PAGE WITH CRC encountered a redirected page
COMMCMDERRORRESULT_EOS =          0x80  # if set SEARCH ACCESS with SM=1 ended sooner than expected with too few ROM IDs




def SetupPacket():
   return cstruct.cStruct(( ('B', 'RequestTypeReservedBits'),
                            ('B', 'Request'),
                            ('H', 'Value'),
                            ('H', 'Index'),
                            ('H', 'Length'),
                            ('H', 'DataOut'), # XXX SMALLINT
                            ('s', 'DataInBuffer'),
                         ))
def StatusPacket():
   return cstruct.cStruct(( ('B', 'EnableFlags'),
                            ('B', 'OneWireSpeed'),
                            ('B', 'StrongPullUpDirection'),
                            ('B', 'ProgPulseDuration'),
                            ('B', 'PullDownSlewRate'),
                            ('B', 'Write1LowTime'),
                            ('B', 'DSOW0RecoveryTime'),
                            ('B', 'Reserved1'),
                            ('B', 'StatusFlags'),
                            ('B', 'CurrentCommCmd1'),
                            ('B', 'CurrentCommCmd2'),
                            ('B', 'CommBufferStatus'),
                            ('B', 'WriteBufferStatus'),
                            ('B', 'ReadBufferStatus'),
                            ('B', 'Reserved2'),
                            ('B', 'Reserved3'),
                            ('s', 'CommResultCodes', ''),
                         ))


class iButton:
   def __init__(self, longid):
      self.longid = longid

   def __str__(self):
      return ''.join(['%02x' % ((self.longid >> (8*i)) & 0xff) for i in reversed(range(8))])

   def __repr__(self):
      return self.__str__()

def GetDevice(vendor_id, product_id):
  buses = usb.busses()
  for bus in buses:
    for device in bus.devices:
      if (device.idVendor, device.idProduct) == (vendor_id, product_id):
        return device
  return None

logging.basicConfig(level=logging.DEBUG)
class DS2490:
   VENDORID    = 0x04fa
   PRODUCTID   = 0x2490
   INTERFACEID = 0x0

   def __init__(self):
      self.devfile = None
      self.logger = logging.getLogger("ds2490")
      self.logger.setLevel(logging.DEBUG)

      self.USBLevel = 0 # TODO - fix to proper init values (?)
      self.USBSpeed = 0
      self._SerialNumber = 0L # XXX
      self.owAcquire()
      self._ResetSearch()

   def _ResetSearch(self):
      self._LastDiscrep = 0
      self._LastDevice = 0
      self._LastFamilyDiscrep = 0

   def GetIDs(self):
      self._ResetSearch()
      ret = []
      while self.owNext():
         ret.append(iButton(self._SerialNumber))
      return ret

   def owAcquire(self):
      """
      Attempt to acquire a 1-wire net using a USB port and a DS2490 based
      adapter.

      Returns:
         True - success, USB port opened
         False - failure
      """

      self._device = GetDevice(DS2490.VENDORID, DS2490.PRODUCTID)
      if not self._device:
        return False
      self.logger.debug('got device: %s' % self._device)

      self._handle = self._device.open()

      self._handle.reset()

      self._handle.claimInterface(DS2490.INTERFACEID)
      self.logger.debug('claimed interface')

      self._handle.setAltInterface(3)
      self.logger.debug('set alt interface')

      self.logger.debug('clearing endpoints')
      for ep in (DS2490_EP3, DS2490_EP2, DS2490_EP1):
        self._handle.clearHalt(ep)

      # verify adapter is working
      self.logger.debug('adapter recover..')
      ret = self.AdapterRecover()

      self.logger.debug('done (ret=%i)' % ret)
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
         # call the libusb driver
         ret = self.DoControlMessage(setup)

         if ret < 0:
            # failure
            self.AdapterRecover()
            return self.USBLevel

         # start the pulse
         setup.RequestTypeReservedBits = 0x40
         setup.Request = COMM_CMD
         setup.Value = COMM_PULSE | COMM_IM
         setup.Index = 0

         ret = self.DoControlMessage(setup)

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
      self.logger.debug('owTouchReset')
      # make sure strong pullup is not on
      if self.USBLevel == MODE_STRONG5:
         self.owLevel(MODE_NORMAL)

      # construct command
      setup = SetupPacket()
      setup.RequestTypeReservedBits = 0x40
      setup.Request = COMM_CMD
      setup.Value = COMM_1_WIRE_RESET | COMM_F | COMM_IM | COMM_SE
      setup.Index = ONEWIREBUSSPEED_FLEXIBLE #XXX OVERDRIVE
      ret = self.DoControlMessage(setup)

      if ret < 0:
         # failure
         self.AdapterRecover()
         return False
      else:
         # extra delay for alarming ds1994/ds2404 compliance
         if FAMILY_CODE_04_ALARM_TOUCHRESET_COMPLIANCE and self.USBSpeed != MODE_OVERDRIVE:
            time.sleep(0.005)

         # success, check for shorts
         status, vpp = self.DS2490ShortCheck()
         if status:
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
      self.logger.debug('AdapterRecover')
      if self.DS2490Detect():
         self.USBSpeed = MODE_NORMAL
         self.USBLevel = MODE_NORMAL
         return True
      else:
         return False

   def DoControlMessage(self, setup):
      return self._handle.controlMsg(setup.RequestTypeReservedBits,
                                     setup.Request, setup.Value, setup.Index,
                                     timeout=TIMEOUT_LIBUSB)

   def DS2490Detect(self):
      setup = SetupPacket()

      # reset the DS2490
      self.DS2490Reset()

      self.logger.debug('DS2490Detect')

      # set the stron pullup duration to infinite
      setup.RequestTypeReservedBits = 0x40
      setup.Request = COMM_CMD
      setup.Value = COMM_SET_DURATION | COMM_IM
      setup.Index = 0

      #ret = self.DoControlMessage(setup)

      # set the 12V pullup duration to 512us
      setup.RequestTypeReservedBits = 0x40
      setup.Request = COMM_CMD
      setup.Value = COMM_SET_DURATION | COMM_IM | COMM_TYPE
      setup.Index = 0x40

      #ret = self.DoControlMessage(setup)

      # disable strong pullup, but leave progrm pulse enabled (faster)
      setup.RequestTypeReservedBits = 0x40
      setup.Request = MODE_CMD
      setup.Value = MOD_PULSE_EN
      setup.Index = ENABLEPULSE_PRGE

      #ret = self.DoControlMessage(setup)

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
      self.logger.debug( 'DS2490Reset')
      setup = SetupPacket()

      # setup for reset
      setup.RequestTypeReservedBits = 0x40
      setup.Request = CONTROL_CMD
      setup.Value = CTL_RESET_DEVICE
      setup.Index = 0x00

      ret = self.DoControlMessage(setup)

      if ret < 0 :
         return False
      return True

   def DS2490GetStatus(self):
      buf = self._handle.bulkRead(1, 32, TIMEOUT_LIBUSB)
      print 'got status: %s' % (repr(buf),)
      if len(buf) < 16:
         return None
      status = StatusPacket()
      b2 = struct.pack('16B', *buf)
      status.unpack(b2) # TODO: make sure CommResultCodes (string) handling is correct
      #print str(status)
      return status

   def DS2490Write(self, buf):
      # XXX 10/12 check endpoints
      nbytes = self.devfile.write(buf)
      return True

   def DS2490Read(self, buf_len):
      #return self.devfile.read(buf_len)
      howmuch = buf_len
      data=""
      while howmuch > 0:
         #print "usb_bulk_read(%s,%d,%d,%d)" % (self.devfile.iface.device.handle, DS2490_EP3, buf_len, TIMEOUT_LIBUSB)
         res,outstr=libusb.usb_bulk_read_wrapped(self.devfile.iface.device.handle, DS2490_EP3, buf_len, TIMEOUT_LIBUSB)
         #print "usb_bulk_read(%s,%d,%d,%d)=%d,%s" % (self.devfile.iface.device.handle, DS2490_EP3, buf_len, TIMEOUT_LIBUSB, res, `outstr`)
         if res<0:
             if len(data)>0:
                 return data
             e=USBException()
             raise e
         if res==0:
             return data
         data+=outstr
         howmuch-=len(outstr)
         if howmuch and len(outstr)!=buf_len:
             # short read, no more data
             break

      return data


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
      status = self.DS2490GetStatus()
      if status is None:
         return False

      # get vpp present flag
      vpp = (status.StatusFlags & STATUSFLAGS_12VP) != 0

      # check for short
      if status.CommBufferStatus != 0:
         return (False, 0)
      else:
         # check for short
         for i in range(len(status.CommResultCodes)):
            # check for SH bit (0x02), ignore 0xA5
            if ord(status.CommResultCodes[i]) & COMMCMDERRORRESULT_SH:
               # short detected
               #print '!!! short detected'
               return (False, 0)

      present = True

      # loop through result registers
      for i in range(len(status.CommResultCodes)):
         # only check for error conditions when the condition is not a ONEWIRE
         # DEVICEDETECT
         if status.CommResultCodes[i] != ONEWIREDEVICEDETECT:
            # check for NRS bit
            if ord(status.CommResultCodes[i]) & COMMCMDERRORRESULT_NRS:
               #print '!!! empty bus detected'
               # empty bus detected
               present = False
      return (True, vpp)

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
      return self.owNext(alarm_only)

   def owNext(self, alarm_only=False, do_reset=True):
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
      self.logger.debug('owNext')
      ResetSearch = False
      rt = False

      if self._LastDevice:
         self.logger.debug('Last Device!')
         self._ResetSearch()
         return False

      search_cmd = (0xF0, 0xEC)[alarm_only == 1]

      # check if reset is first requested
      if do_reset:
         # extra reset if last part was a ds1994/ds2404 (due to alarm)
         if self._SerialNumber & 0x7f == 0x04:
            self.owTouchReset()
         # if there are no parts on the 1-wire, return false
         if not self.owTouchReset():
            self._ResetSearch()
            return False

      # build the rom number to pass to the USB chip
      rom_buf = self._SerialNumber

      # take into account LastDiscrep
      if self._LastDiscrep != 0xFF:
         if self._LastDiscrep > 0:
            # bitacc stuff here - TODO
            rom_buf |= (1 << (self._LastDiscrep - 1))
         for i in range(self._LastDiscrep, 64):
            rom_buf &= ~(1 << i) # TODO - single OR much more efficient here, silly dallas

      # put the ROM ID in EP2
      self.logger.debug('_'*20 + 'rombuf:' + mkserial(rom_buf))
      rom_buf = struct.pack('Q', rom_buf) ## XXX endianness
      if not self.DS2490Write(rom_buf): # XXX libusb doesnt return len
         self.AdapterRecover()
         return False

      # setup for search command call
      setup = SetupPacket()
      setup.RequestTypeReservedBits = 0x40
      setup.Request = COMM_CMD
      setup.Value = COMM_SEARCH_ACCESS | COMM_IM | COMM_SM | COMM_F | COMM_RTS
      # the number of devices to read (1) with the search command
      setup.Index = 0x0100 | (search_cmd & 0x00ff)

      ret = self.DoControlMessage(setup)

      if ret < 0:
         # failure
         self.AdapterRecover()
         return False

      # set a time limit
      limit = time.time() + 0.200

      # do...while{}
      do_while = 0
      while not do_while or (status.StatusFlags & STATUSFLAGS_IDLE == 0 and time.time() < limit):
         do_while = 1
         status = self.DS2490GetStatus()
         if status is None:
            break
         else:
            # look for any fail conditions
            for i in range(len(status.CommResultCodes)):
               # only check for error conditions when the condition is not a
               # ONEWIREDEVICEDETECT
               if status.CommResultCodes[i] != ONEWIREDEVICEDETECT:
                  # failure
                  #print '*'*20, 'failure in owNext!'
                  break

      # check the results of the wait for idle
      if status is None or status.StatusFlags & STATUSFLAGS_IDLE == 0:
         #print '*'*20, 'owNext search failed!'
         self.AdapterRecover()
         return False

      # check for data
      if status.ReadBufferStatus > 0:
         self.logger.debug('_'*20 + 'buffer status looks good!')
         # read the load
         buf_len = 16
         ret_buf = self.DS2490Read(buf_len)
         if not ret_buf:
            #print '*'*20, 'buffer empty, wtf!!'
            self.AdapterRecover()
            return False

         self.logger.debug('___________ ret buf: %s' % repr(ret_buf))
         # success, get rom and discrepancy
         self._LastDevice = (len(ret_buf) == 8)

         # extract the ROM and check crc
         #self.setcrc8(0)
         self._SerialNumber = struct.unpack('Q', ret_buf[:8])[0]
         other_number = 0L
         if len(ret_buf) > 8:
            other_number = struct.unpack('Q', ret_buf[8:])[0]

         lastcrc8 = None

         # crc OK and family code is not 8
         if not lastcrc8 and self._SerialNumber & 0xff != 0:
            # loop through the discrepancy to get the pointers
            for i in range(64):
               # if discrepancy
               if ((other_number >> i) & 0x1) != 0 and ((self._SerialNumber >> i) & 0x1) == 0:
                  self._LastDiscrep = i + 1
            rt = True

      else:
         ResetSearch = True
         rt = False

      # check if need to reset search
      if ResetSearch:
         self._LastDiscrep = 0xFF
         self._LastDevice = False
         self._SerialNumber = 0L # TODO define this field

      return rt


def mkserial(num):
   return ' '.join(['%02x' % ((num >> (8*i)) & 0xff) for i in range(8)])


if __name__ == '__main__':
   dev = DS2490()
