import threading
import thread
import SimpleXMLRPCServer
import time
import sys
from socket import *

from onewirenet import *
from ibutton import *

class ReusableServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
   def server_bind(self):
      self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
      try:
         self.socket.bind(self.server_address)
      except: pass

#class request_handler(threading.Thread):
class RequestHandler:
   def __init__(self,host,port,ow_net):
      #threading.Thread.__init__(self)

      #self.KILL_EVENT = threading.Event()
      self.ow_net = ow_net
      self.server = ReusableServer((host,port), logRequests = 1)
      self.server.register_instance(self.ow_net)
      self.quit = 0

      print "server up..."

      self.run()  # no threading atm..
      #self.start()

   def run(self):
      while 1:
         if self.quit == 1:
            break
         try:
            self.server.handle_request() # blocks; only way to get out is to call the quit function!
         except:
            print 'remote request handler got exception'
            raise
      self.server.server_close()
      time.sleep(0.1)

def usage():
   print "Usage: %s <device> <host> [port]" % sys.argv[0]
   print ""
   print "device: the local device which contains a ds9097-driven onewire network"
   print "        (eg, /dev/ttyS0)"
   print ""
   print "  host: the hostname or ip to which the server will be bound. use 127.0.0.1"
   print "        (or localhost) for local-only access."
   print ""
   print "  port: the port number to use; optional (default is 1820)"
   print ""
   print ""

def main():
   if len(sys.argv) < 3:
      return usage()
   
   device = sys.argv[1]
   host = sys.argv[2]
   if len(sys.argv) > 3:
      port = int(sys.argv[3])
   else:
      port = 1820

   # create the onewire network, or die trying
   ow_net = onewirenet(device)

   # now, try to serve stuff for it
   server = RequestHandler(host, port, ow_net) # ..runs forever!

if __name__ == '__main__':
   main()
