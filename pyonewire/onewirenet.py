import _onewire
import sys
import struct
import string
import os
from ibutton import *

class onewirenet:
   def __init__(self,port):
      self.port  = port
      self.portn = 1
      if not _onewire.owAcquire(self.portn,port):
         while _onewire.owHasErrors():
            _onewire.owPrintErrorMsgStd()
         raise IOError, "Unable to attach to one wire network"
      print "setting overdrive"
      self.setOverdrive(0)
      print "refresh.."
      self.ibuttons = self.refresh()

   def setOverdrive(self,od=1):
      self.overdrive = _onewire.owSpeed(self.portn, od)
      if (not self.overdrive) and od:
         raise IOError, "Unable to go to Overdrive"

   def close(self):
      _onewire.owRelease(self.portn)

   def __call__(self):
      return self.ibuttons

   def __getitem__(self,item):
      return self.ibuttons[item]

   def __str__(self):
      return "<onewirenet on %s (net %s)>" % (self.port, self.portn)

   def refresh(self):

      ibs = []
      rlst =  _onewire.myOwFirst(self.portn,1,0)
      while rlst:
         ibs.append(ibutton(self,_onewire.owSerialNum(self.portn,"",1)))
         rlst = _onewire.myOwNext(self.portn,1,0)

      return ibs

   # utility functions
   # these functions are to be called by an ibutton; every ibutton must have a
   # parent network
   
   # utility functions: network management

   def owAcquire(self):
      return _onewire.owAcquire(self.port)
   
   def owRelease(self):
      return _onewire.owRelease(self.portn)

   def owSpeed(self,speed):
      return _onewire.owSpeed(newspeed)

   #
   # utility functions: button management
   #

   def owFirst(self, do_reset = 1, alarm_only = 0):
      #return _onewire.owFirst(self.portn,do_reset,alarm_only)
      return _onewire.myOwFirst(self.portn,do_reset,alarm_only)

   def owNext(self, do_reset = 1, alarm_only = 0):
      #return _onewire.owNext(self.portn,do_reset,alarm_only)
      return _onewire.myOwNext(self.portn,do_reset,alarm_only)

   def owSerialNum(self,ID,do_read = 0):
      return _onewire.owSerialNum(self.portn,ID,do_read)

   def PrintSerialNum(self,ID):
      return _onewire.PrintSerialNum(ID) # XXX - who cares about this one?

   def owAccess(self):
      return _onewire.owAccess(self.portn)

   def owOverdriveAccess(self):
      return _onewire.owOverdriveAccess(self.portn)

   def owVerify(self,alarm_only = 0):
      return _onewire.owVerify(self.portn,alarm_only)
   
   #
   # utility functions: file management
   #

   def owGetCurrentDir(self):
      return _onewire.owGetCurrentDir(self.portn)

   def owChangeDirectory(self,ID,cdbuf):
      return _onewire.owChangeDirectory(self.portn,ID,cdbuf)

   def owFirstFile(self,ID):
      return _onewire.owFirstFile(self.portn,ID,None) # XXX - remove None in typemap

   def owNextFile(self,ID):
      return _onewire.owNextFile(self.portn,ID,None)  # XXX - remove None in typemap


   def owOpenFile(self,ID,fe):
      return _onewire.owOpenFile(self.portn,ID,fe)

   def owReadFile(self,ID,handle):
      return _onewire.owMyReadFile(self.portn,ID,handle)

   def owCloseFile(self,ID,handle):
      return _onewire.owCloseFile(self.portn,ID,handle)

   def owCreateFile(self,ID,fe):
      return _onewire.owCreateFile(self.portn,ID,fe)

   def owDeleteFile(self,ID,fe):
      return _onewire.owDeleteFile(self.portn,ID,fe)

   def owWriteFile(self,ID,handle,data,datalen):
      return _onewire.owWriteFile(self.portn,ID,handle,data,datalen)

   #
   # utility functions: extra features
   #

   def ReadTemperature(self,ID):
      return _onewire.my_ReadTemperature(self.portn,ID)

   #
   # utility functions: error functions
   #

   def owGetErrorNum(self):
      return _onewire.owGetErrorNum()

   def owClearError(self):
      return _onewire.owClearError()

   def owHasErrors(self):
      return _onewire.owHasErrors()

   def owRaiseError(self):
      return _onewire.owRaiseError()

   def owPrintErrorMsgStd(self):
      return _onewire.owPrintErrorMsgStd()

   def owGetErrorMsg(self,errornum):
      return _onewire.owGetErrorMsg(errornum)



