import xmlrpclib

class onewireremote:
   def __init__(self,host,port):
      self.s = xmlrpclib.ServerProxy('http://%s:%s' % (host,port))

