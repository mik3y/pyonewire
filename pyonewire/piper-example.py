#!/usr/local/bin/python

import onewirenet
import sys
import struct
import string
import os
            
own = onewirenet.onewirenet("/dev/ttyS0")
print own

for ib in own:
    print ib

    while 0:
        if not ib.verify():
            os.system("play /usr/lib/xemacs-20.4/etc/sounds/monkey.au")

    away = 0
    while 0:
        if not ib.verify() and not away:
            print "Button has gone missing!"
            away = 1
        elif away and ib.verify():
            print "Button has come back, I've missed you button!"
            away = 0
            
    print ib.read_id()

    if not ib.supports('fs'):
       print "%s does not support a filesystem; skipping" % ib.name
    else:
       file = ib.open("test.011")
       file.write("this is the contents of my file")
       file.close()
       
       ib.scanfilesystem()
       print ib.filesystem
       for f in ib.filesystem.keys():
           print f

       file = ib.open("test.011")
       print file.read()
       file.close()

       ib.unlink("test.011")

#for i in own.refresh():
#    print i
    
    
own.close()
