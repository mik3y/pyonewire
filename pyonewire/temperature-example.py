#!/usr/bin/python
from onewirenet import *

own = onewirenet("/dev/ttyS0")

# print any temperature-reading devices we can find, along with their measured
# temperatures! note that the ReadTemperature call should be incorporated into
# a temperature-capable ibutton class - a hack for now
for ib in own:
   if ib.supports('temp'):
      print "[%s:%s] %s" % (ib.name,ib.read_id(),own.ReadTemperature(own[0].ID))
