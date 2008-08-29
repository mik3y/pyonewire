#!/usr/bin/env python
"""
DS2490 OneWire master for the pyonewire package

  Copyright 2008 mike wakerly <opensource@hoho.com>

Portions of this file have been derived from the Linux kernel files w1.h, w1.c,
and ds2490.c, which have the following copyright notices:

  Copyright (c) 2004 Evgeniy Polyakov <johnpol@2ka.mipt.ru>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
"""

import logging
import time
import usb

from pyonewire.core import cstruct
from pyonewire.core import util
from pyonewire.master import GenericOneWireMaster

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

EP_CONTROL = 0
EP_STATUS = 1
EP_DATA_OUT = 2
EP_DATA_IN = 3

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

# duration of strong pullup, in ms
PULLUP_PULSE_DURATION = 750

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

TRACE = False
TRACE_LEVEL = 0
def trace(fn):
  def wrapped(*args, **kwargs):
    global TRACE
    global TRACE_LEVEL
    if not TRACE:
      return fn(*args, **kwargs)
    pad = '  ' * TRACE_LEVEL
    TRACE_LEVEL += 1
    print '%s> %s' % (pad, fn.__name__)
    ret = fn(*args, **kwargs)
    print '%s< %s' % (pad, fn.__name__)
    TRACE_LEVEL -= 1
    return ret
  return wrapped


class UsbError(Exception):
  """Raised when a libusb operation returns an error"""

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
                         ))


def GetDevice(vendor_id, product_id):
  buses = usb.busses()
  for bus in buses:
    for device in bus.devices:
      if (device.idVendor, device.idProduct) == (vendor_id, product_id):
        return device
  return None

logging.basicConfig(level=logging.DEBUG)

class DS2490Master(GenericOneWireMaster.GenericOneWireMaster):
   VENDORID    = 0x04fa
   PRODUCTID   = 0x2490
   INTERFACEID = 0
   SEARCH_NORMAL = 0xf0
   SEARCH_ALARM = 0xec
   def __init__(self):
      GenericOneWireMaster.GenericOneWireMaster.__init__(self)
      self._logger = logging.getLogger("ds2490")
      self._device = None
      self._handle = None

      self._device = GetDevice(self.VENDORID, self.PRODUCTID)

      if not self._device:
        self._logger.fatal('Could not acquire device')
        raise RuntimeError, "no device"

      self._handle = self._device.open()
      self._handle.reset()

      self._conf = self._device.configurations[0]
      self._intf = self._conf.interfaces[0][0]
      self._handle.setConfiguration(self._conf)
      self._handle.claimInterface(self._intf)
      self._handle.setAltInterface(2)

      # por reset
      self.SendControlCommand(value=CTL_RESET_DEVICE, index=0)

      # set the strong pullup duration to infinite
      self.SendControl(value=(COMM_SET_DURATION | COMM_IM), index=0)

      # set the 12V pullup duration to 512us
      self.SendControl(value=(COMM_SET_DURATION | COMM_IM | COMM_TYPE), index=0x40)

      # disable strong pullup, but leave progrm pulse enabled (faster)
      self.SendControlMode(value=MOD_PULSE_EN, index=ENABLEPULSE_PRGE)

      if 0:
        self._logger.debug('clearing endpoints')
        for ep in (DS2490_EP1, DS2490_EP2, DS2490_EP3):
          self._handle.clearHalt(ep)

      self._logger.debug('completed init')

   def _SendMessage(self, command, value, index, timeout=TIMEOUT_LIBUSB):
      ret = self._handle.controlMsg(requestType=0x40, request=command, buffer='', value=value,
                                    index=index, timeout=timeout)
      if ret:
        raise UsbError, "Error while sending control message: %s" % (ret,)

   @trace
   def SendControlCommand(self, value, index, timeout=TIMEOUT_LIBUSB):
      self._SendMessage(CONTROL_CMD, value, index, timeout)

   @trace
   def SendControlMode(self, value, index, timeout=TIMEOUT_LIBUSB):
      self._SendMessage(MODE_CMD, value, index, timeout)

   @trace
   def SendControl(self, value, index, timeout=TIMEOUT_LIBUSB):
      self._SendMessage(COMM_CMD, value, index, timeout)

   @trace
   def GetStatus(self):
     buf_len = 64
     raw = self._handle.bulkRead(EP_STATUS, buf_len, TIMEOUT_LIBUSB)
     status = StatusPacket()
     status.UnpackFromTuple(raw[:16])
     ST_EPOF = 0x80
     if status.StatusFlags & ST_EPOF:
       self._logger.info('Resetting device after ST_EPOF')
       self.SendControlCommand(CTL_RESET_DEVICE, 0)
     return status

   @trace
   def RecvData(self, size):
     raw = self._handle.bulkRead(EP_DATA_IN, size, TIMEOUT_LIBUSB)
     return raw

   @trace
   def SendData(self, buf):
     return self._handle.bulkWrite(EP_DATA_OUT, buf, TIMEOUT_LIBUSB)

   @trace
   def WaitStatus(self):
     count = 0
     status = None
     while True:
       status = self.GetStatus()
       count += 1
       time.sleep(0.01)
       if status.StatusFlags & 0x20:
         break
       if count >= 100:
         raise RuntimeError, "took too long to get status"
     return status

   @trace
   def Reset(self):
     SPEED_NORMAL = 0x00
     self.SendControl(0x43, SPEED_NORMAL)
     return self.WaitStatus()

   @trace
   def StartPulse(self, delay):
     outdelay = 1 + (delay >> 4)
     self.SendControlMode(MOD_PULSE_EN, ENABLEPULSE_SPUE)
     self.SendControl(COMM_SET_DURATION | COMM_IM, outdelay)
     self.SendControl(COMM_PULSE | COMM_IM | COMM_F, 0)
     time.sleep(delay/1000.0) # mdelay
     return self.WaitStatus()

   @trace
   def TouchBit(self, bit):
     val = COMM_BIT_IO | COMM_IM
     if bit:
       val |= COMM_D

     self.SendControl(val, 0)
     count = 0
     while True:
       count += 1
       status = self.WaitStatus()
       cmd = status.CurrentCommCmd1 | (status.CurrentCommCmd2 << 8)
       if (cmd == val) or count >= 10:
         break
     if count >= 10:
       raise ValueError, "Too many tries"

     ret = self.RecvData(1)
     return ret[0] 

   @trace
   def WriteBit(self, bit):
     val = COMM_BIT_IO | COMM_IM
     if bit:
       val |= COMM_D
     self.SendControl(val)

     return self.WaitStatus()

   @trace
   def WriteByte(self, byte):
     self.SendControl(COMM_BYTE_IO | COMM_IM | COMM_SPU, byte)
     st = self.WaitStatus()
     rbyte = self.RecvData(1)
     self.StartPulse(PULLUP_PULSE_DURATION)
     if len(rbyte) == 1:
       return byte != rbyte[0]
     else:
       return False

   @trace
   def ReadByte(self):
     self.SendControl(COMM_BYTE_IO | COMM_IM, 0xff)
     self.WaitStatus()
     ret = self.RecvData(1)
     return ret[0]

   @trace
   def ReadBlock(self, blocklen):
     if blocklen > (64*1024):
       raise ValueError, "Len too long"

     buf = [0xff]*blocklen
     self.SendData(buf)
     self.SendControl(COMM_BLOCK_IO | COMM_IM | COMM_SPU, blocklen)
     self.WaitStatus()

     return self.RecvData(blocklen)

   @trace
   def WriteBlock(self, buf):
     self.SendData(buf)
     self.WaitStatus()
     self.SendControl(COMM_BLOCK_IO | COMM_IM | COMM_SPU, len(buf))
     self.WaitStatus()
     b2 = self.RecvData(len(buf))
     self.StartPulse(PULLUP_PULSE_DURATION)

     return len(b2) != len(buf)

   @trace
   def Search(self, search_type=SEARCH_NORMAL, start=0, max=8):
     self.Reset()
     self.SendData('\x00'*8)
     self.WaitStatus()

     self._handle.clearHalt(EP_DATA_OUT)
     val = COMM_SEARCH_ACCESS | COMM_IM | COMM_SM | COMM_F | COMM_RTS
     index = (max << 8) | search_type
     self.SendControl(val, index)

     ret = []
     count = 0
     last = False

     # The read data endpoint has a maximum size of 16 bytes. To support reads
     # of 2 or more ibuttons, we need to pull from it while the search command
     # is underway.
     while True:
       buf = self.RecvData(8)
       ret += list(buf)
       if len(ret) >= 8:
         yield util.IdTupleToLong(ret[:8])
         ret = ret[8:]
       if last:
         break
       status = self.GetStatus()
       if status.StatusFlags & 0x20:
         last = True
       time.sleep(0.01)
       count += 1
       if count >= 100:
         raise RuntimeError, "took too long to get status"


def mkserial(num):
   return ' '.join(['%02x' % ((num >> (8*i)) & 0xff) for i in range(8)])


if __name__ == '__main__':
   dev = DS2490Master()
   for d in dev.Search(dev.SEARCH_NORMAL):
     print hex(d)
