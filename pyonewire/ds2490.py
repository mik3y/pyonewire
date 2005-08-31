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

def SetupPacket():
   return cstruct.cStruct(( ('C', 'RequestTypeReservedBits'),
                            ('C', 'Request'),
                            ('H', 'Value'),
                            ('H', 'Index'),
                            ('H', 'Length'),
                            ('H', 'DataOut'), # XXX SMALLINT
                            ('s', 'DataInBuffer'),
                         ))


class DS2490:
   VENDORID    = 0x04fa
   PRODUCTID   = 0x2490
   INTERFACEID = 0x0
   def __init__(self):
      self.dev = None
      self.owAcquire()

   def _ResetSearch(self):
      self._LastDiscrep = 0
      self._LastDevice = 0
      self._LastFamilyDiscrep = 0

   def owAcquire(self):
      self.devfile= usb.OpenDevice(DS2490.VENDORID, DS2490.PRODUCTID, DS2490.INTERFACEID)
      self.owTouchReset()

   def owTouchReset(self):
      print 'owTouchReset'
      setup = SetupPacket()
      setup.RequestTypeReservedBits = 0x40
      setup.Request = COMM_CMD
      setup.Value = COMM_1_WIRE_RESET | COMM_F | COMM_IM | COMM_SE
      setup.Index = ONEWIREBUSSPEED_FLEXIBLE #XXX OVERDRIVE
      setup.Length = 0
      setup.DataOut = 0
      libusb.usb_control_msg( self.devfile.iface.device.handle,
                              setup.RequestTypeReservedBits,
                              setup.Request,
                              setup.Value,
                              setup.Index,
                              '',
                              setup.Length)

   # owFirst, from libusbnet.c
   def owFirst(self):
      self._ResetSearch()
      return self.owNext()

   def owNext(self):
      if self._LastDevice:
         self._ResetSearch()
         return 0

      # if do_reset: owTouchReset()

      if self._LastDiscrep != 0xFF:
         pass # XXX stop here


if __name__ == '__main__':
   print 'getting new devices...'
   usb.UpdateLists()
   dev = DS2490()
   dev.devfile.close()

