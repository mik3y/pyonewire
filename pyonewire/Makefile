PYINC = /usr/include/python2.2
PYLIB = /usr/lib/python2.2/config/libpython2.2.a 
PYSITEPACKAGES = /usr/lib/python2.2/site-packages



LINKFILE = dallas/linuxlnk.o
ONEWIREOBJS = $(LINKFILE) dallas/ds2480ut.o dallas/ownetu.o dallas/owllu.o dallas/owsesu.o dallas/owtrnu.o \
	dallas/owerr.o dallas/ioutil.o dallas/crcutil.o
MEMOBJS = dallas/mbappreg.o dallas/mbeprom.o dallas/mbnvcrc.o dallas/mbscrcrc.o dallas/mbscrex.o dallas/mbshaee.o \
	dallas/mbee.o dallas/mbnv.o dallas/mbscr.o dallas/mbscree.o dallas/mbsha.o dallas/rawmem.o $(ONEWIREOBJS)
FILEOBJS = dallas/owfile.o dallas/owpgrw.o dallas/owprgm.o dallas/owcache.o $(MEMOBJS)
MISCOBJS = dallas/temp10.o

all: _onewiremodule.so

install: _onewiremodule.so
	cp _onewiremodule.so onewire.py $(PYSITEPACKAGES)

onewire_wrap.c: onewire.i
	swig -python onewire.i

_onewiremodule.so: onewire_wrap.c $(FILEOBJS) $(MISCOBJS)
	gcc -g -shared -I$(PYINC) $(FILEOBJS) $(MISCOBJS) $(PYLIB) onewire_wrap.c -o _onewiremodule.so

%.o: %.c
	$(CC) -g -c -Iinclude $< -o $*.o

clean:
	rm -f dallas/*.o *.o *.so *.pyc

veryclean: clean
	rm -f onewire_wrap.c *^ *.pyc *~ \#*\#

