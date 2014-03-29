/*
 * SUID wrapper for Update Accelerator 2.x
 *
 * This code is distributed under the terms of the GPL
 *
 * (c) 2007 marco.s - http://www.advproxy.net/update-accelerator
 * Portions (c) 2012 by dotzball - http://www.blockouttraffic.de
 *
 * $Id: setperms,v 2.0 2012-01-19 21:22:04Z dotzball $
 *
 */

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <fcntl.h>
#include "setuid.h"

#define BUFFER_SIZE 1024

char command[BUFFER_SIZE];

int main(int argc, char *argv[])
{
  if (argc < 2)
    return(1);

  if (!(initsetuid()))
    exit(-1);

  snprintf(command, BUFFER_SIZE-1, "/bin/chown nobody:squid /home/httpd/vhost81/html/updatecache/%s", argv[1]);
  safe_system(command);

  return(0);
}
