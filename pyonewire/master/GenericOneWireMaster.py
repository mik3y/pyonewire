#!/usr/bin/env python
"""
Generic OneWire master for the pyonewire package

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

class GenericOneWireMaster(object):
  """Base class for onewire bus masters.

  This class is derived from the linux kernel struct w1_bus_master.
  """
  def Reset(self):
    """Clear any device state"""
    raise NotImplementedError

  def StartPulse(self, delay):
    """Issue a onewire start pulse"""
    raise NotImplementedError

  def ReadBit(self):
    """Sample the line level.

    Returns
      The level read (0 or 1)
    """
    raise NotImplementedError

  def WriteBit(self, bit):
    """Set the bus line level.

    Args
      bit - level to set
    Returns
      None
    """
    raise NotImplementedError

  def TouchBit(self, bit):
    """Low-level onewire function.

    If bit is clear, causes a onewire "write 0" cycle. If set, causes a onewire
    "write 1" or read cycle.

    Args
      bit - write 0 if clear, write 1 or read if set
    Returns
      the bit read (0 or 1)
    """
    raise NotImplementedError

  def ReadByte(self):
    """Read a byte from the bus.

    Equivalent to 8 TouchBit(1) calls.

    Returns:
      the value read
    """
    raise NotImplementedError

  def WriteByte(self, byte):
    """Write an entire byte to the bus.

    Equivalent to 8 TouchBit(x) calls.

    Args
      byte - value to write
    Returns
      None
    """
    raise NotImplementedError

  def ReadBlock(self, numblocks):
    """Read a series of bytes form the bus.

    Equivalent to |numblocks| ReadByte calls.

    Args
      numblocks - number of bytes to read
    Returns
      iterable of bytes returned
    """
    raise NotImplementedError

  def WriteBlock(self, data):
    """Write several bytes to the bus.

    Equivalent to len(data) WriteByte calls.

    Args
      data - iterable of integers as bytes to write
    Returns
      None
    """
    raise NotImplementedError

  def Triplet(self, bdir):
    """Combination of two reads and smart write for ROM search.

    Args
      dbit - direction to choose if both are valid
    Returns
      tuple of (id_bit, comp_bit, dir_taken)
    """
    id_bit = self.TouchBit(1)
    comp_bit = self.TouchBit(1)

    if id_bit and comp_bit:
      return 0x03 # error

    if not id_bit and not comp_bit:
      # both bits are valid, take the direction given
      if bdir:
        retval = 0x04
      else:
        retval = 0
    else:
      # only one bit is valid, take that direction
      bdir = id_bit
      if id_bit:
        retval = 0x05
      else:
        retval = 0x02

    self.TouchBit(bdir)

    return retval

  def Search(self, search_type):
    """Generator that performs search and yields address found.

    Args
      search_type - one of SEARCH_NORMAL, SEARCH_ALARM
    Yields
      64 bit integer ids found
    """
    last_rn = 0L
    rn = 0L
    tmp64 = 0L
    i = 0L
    last_device = 0L
    last_zero = -1L

    desc_bit = 64

    ret = []

    def pick_search_bit(i, desc_bit, last_rn):
      if i == desc_bit:
        # took 0 path last time, so take 1 path
        return 1
      elif i > desc_bit:
        # take the 0 path on the next branch
        return 0
      else:
        return ((last_rn >> i) & 0x1)

    while not last_device:
      last_rn = rn
      rn = 0L

      # Reset bus
      self.Reset()

      self.WriteByte(search_type)

      for i in xrange(64):
        # Determine the direction/search bit
        search_bit = pick_search_bit(i, desc_bit, last_rn)

        # read two bits and write one bit
        triplet_ret = self.Triplet(search_bit)

        if (triplet_ret & 0x03) == 0x03:
          # quit if no devices responded
          break

        # if both directions were valid & we took the 0 path
        if triplet_ret == 0:
          last_zero = i

        # extract the direction taken & update the device number
        tmp64 = triplet_ret >> 2
        rn |= (tmp64 << i)

      if triplet_ret & 0x03 != 0x03:
        if desc_bit == last_zero or last_zero < 0:
          last_device = True
        desc_bit = last_zero
        ret.append(rn)

    return ret
