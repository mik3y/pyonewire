import sys
import string
from ConfigParser import ConfigParser

# a global table of ibutton info. TODO -- maybe there is a better way to
# represent this, perhaps a flatfile of our own chosing? 
global IbDb
IbDb = ConfigParser()
IbDb.read('ibuttons.cfg')

class ibutton:
   def __init__(self,net,ID):
      self.net = net
      self.ID = ID

      self.name, self.desc = self.getButtonInfo()
      self.filesystem = {}

   def __eq__(self,other):
      if self.ID == other.ID:   return 1
      else:  return 0

   def __ne__(self,other):
      return not self.__eq__(other)

   def read_id(self):
      return reduce(lambda x, y: y + x, [string.zfill(hex(ord(c))[2:],2) for c in self.ID]).upper()
      #return hex(reduce(lambda x, y: 256*x + ord(y), reduce(lambda x, y: y + x, self.ID, ""), 0)).upper()
   
   def readTemperature(self):
      return self.net.owReadTemperature(self.ID)

   def __str__(self):
      return "<%s on %s (net %s) with ID %s>" % (
         self.name, self.net.port, self.net.portn, self.read_id())

   def getButtonInfo(self):
      global IbDb
      code = self.read_id()[-2:]
      name = "unknown"
      desc = "unknown"
      try:
         name = IbDb.get(code,'name')
         desc = IbDb.get(code,'desc')
      except:
         pass
      return (name,desc)

   def activate(self):
      self.net.owSerialNum(self.ID)
      return self.net.owAccess()

   def activateOverdrive(self):
      self.net.owSerialNum(self.ID)
      return self.net.owOverdriveAccess()

   def verify(self):
      self.net.owSerialNum(self.ID)
      return self.net.owVerify()

   def dir(self):
      self.net.owSerialNum(self.ID)
      lst = []
      file = self.net.owFirstFile(self.ID)
      while file:
         file["Name"] = file["Name"].strip()
         lst.append(file)
         file = self.net.owNextFile(self.ID)
      return lst

   def changedir(self,dir,ref="."):
      cdbuf = {'Entries': [dir.ljust(4)], 'Ref': ref}
      self.net.owChangeDirectory(self.ID,cdbuf)            
      if self.net.owHasErrors():
         while  self.net.owHasErrors():
            self.net.owPrintErrorMsgStd()
         raise IOError, "Unable to change directory to %s" % dir

   def scanfilesystem(self):
      self.changedir(".","/")
      self.filesystem = self.__scanfilesystem()
      return self.filesystem

   def __scanfilesystem(self):
      files = {}
      for file in self.dir():
         if not file["Name"] in (".",".."):
            if (file["Ext"] == 127):
               self.changedir(file["Name"])
               files[file["Name"]] = self.__scanfilesystem()
               self.changedir("..")
            else:
               files["%s.%03d" % (file["Name"], file["Ext"])] = {
                  'Spage': file['Spage'],
                  'Attrib': file['Attrib'],
                  'NumPgs': file['NumPgs']}
      return files


   def open(self,filename,flags="r"):
      return ibuttonfile(self,filename)

   def unlink(self,filename):
      ibf = ibuttonfile(self,filename)
      ibf.unlink()
      del ibf

   def supports(self,feature):
      global IbDb
      code = self.read_id()[-2:]
      featname = "feat_" + feature
      if IbDb.has_section(code) and IbDb.has_option(code,featname):
         return IbDb.getboolean(code,featname)
      return 0

class ibuttonfile:
   def __init__(self,ib,filename):
      self.ib = ib
      self.filename = filename.upper()
      self.linebuf = None
      self.linelst = None

      fe = self.__nav_and_make_fe()
      foundself = 0
      for item in self.ib.dir():
         if item["Name"] == fe["Name"] and item["Ext"] == fe["Ext"]:
            foundself = 1
      if not foundself:
         self.create()

   def create(self,fe=None):
      if fe:
         ret = self.ib.net.owCreateFile(self.ib.ID,fe)
      else:
         ret = self.ib.net.owCreateFile(self.ib.ID,self.__nav_and_make_fe())                
      if self.ib.net.owHasErrors():
         while  self.ib.net.owHasErrors():
            self.ib.net.owPrintErrorMsgStd()
         raise IOError, "Unable to create file %s" % filename            

   def __repr__(self):
      return "<ibuttonfile \"%s\" on %s>" % (self.filename, self.ib)

   def close(self):
      None
      
   def __gh(self):
      self.handle = self.ib.net.owOpenFile(self.ib.ID,self.__nav_and_make_fe())
      if self.ib.net.owHasErrors():
         while  self.ib.net.owHasErrors():
            self.ib.net.owPrintErrorMsgStd()
         raise IOError, "Error creating file handle"
      return None

   def __dh(self):
      self.ib.net.owCloseFile(self.ib.ID,self.handle)

   def __nav_and_make_fe(self):
      dirs = self.filename.split("/")
      file = dirs[-1]
      dirs = dirs[0:-1]
      self.ib.changedir(".","/")
      for dir in dirs:  self.ib.changedir(dir,".")
      try:
         return {'Name':file[0:4],'Ext':int(file[5:8])}
      except:
         raise ValueError, "Badly specified filename %s" % self.filename

   def unlink(self):
      ret = self.ib.net.owDeleteFile(self.ib.ID,self.__nav_and_make_fe())
      if self.ib.net.owHasErrors():
         while  self.ib.net.owHasErrors():
            self.ib.net.owPrintErrorMsgStd()
         raise IOError, "Unable to delete file %s" % self.filename
      return None

   def write(self,data):
      self.__gh()
      ret = self.ib.net.owWriteFile(self.ib.ID,self.handle,data,len(data))
      if self.ib.net.owHasErrors():
         while  self.ib.net.owHasErrors():
            self.ib.net.owPrintErrorMsgStd()
         raise IOError, "Unable to write file %s" % self.filename
      #write does NOT need handle free

   def read(self):
      self.__gh()            
      contents = self.ib.net.owReadFile(self.ib.ID,self.handle)
      if self.ib.net.owHasErrors():
         while  self.ib.net.owHasErrors():
            self.ib.net.owPrintErrorMsgStd()
         raise IOError, "Error reading file %s" % self.filename
      return contents
      self.__dh()

   def readline(self):
      if not self.linebuf:
         self.linebuf = self.read()
         self.linelst = self.linebuf.split("\n")
         self.linelst.reverse()
      if not self.linelst:
         return None
      else:
         return self.linelst.pop()

class NotSupportedError(Exception):
   pass
