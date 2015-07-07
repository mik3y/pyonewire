# What is it? #

Pure Python library for accessing Dallas/Maxim OneWire (1-Wire) devices.

Pyonewire supports the DS2490 USB 1-Wire bus master, via the libusb Python wrappers. Thanks to Python and libusb, pyonewire can run on many platforms, and has been tested on Mac OS X and Linux.

# Requirements #

Pyonewire works on any system that supports:
  * [Python](http://www.python.org)
  * [libusb](http://libusb.wiki.sourceforge.net/)
  * [pyusb](http://pyusb.berlios.de/)

If you have these packages, then you do not need additional drivers to use pyonewire.

# Example #$ python
>>> from pyonewire.master import ds2490
>>> master = ds2490.DS2490Master()
>>> for ib in master.Search(master.SEARCH_NORMAL):
...   print hex(ib)
... 
0xbe00000024d5ea81L
0xfeedface00000001L
>>> 
```