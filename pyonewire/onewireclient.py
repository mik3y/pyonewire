import xmlrpclib

s = xmlrpclib.ServerProxy('http://localhost:1820')

s.refresh()
