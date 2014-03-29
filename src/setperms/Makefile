#
# $Id: Makefile 2012-01-19 21:22:04Z dotzball $
#

COMPILE=$(CC) $(CFLAGS) -D_GNU_SOURCE
OBJLIBS=setuid.o


######

% : %.c setuid.o
	$(COMPILE) $< $(OBJLIBS) -o $@

setuid.o: setuid.c setuid.h
	$(COMPILE) $< -c -o $@

setperms: setuid.o
