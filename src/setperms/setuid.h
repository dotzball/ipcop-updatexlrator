/* SmoothWall helper program - header file
 *
 * This program is distributed under the terms of the GNU General Public
 * Licence.  See the file COPYING for details.
 * Simple header file for all setuid progs.
 * 
 * $Id: setuid.h 1501 2008-06-10 20:25:20Z owes $
 * 
 */

#ifndef SETUID_H
#define SETUID_H 1

#include <stdlib.h>
#include <sys/types.h>

/* As nothing in setuid.c uses STRING_SIZE specifically there's no real reason
 * to redefine it if it already is set */
#ifndef STRING_SIZE
#define STRING_SIZE 256
#endif
extern char * trusted_env[4];

int system_core(char* command, uid_t uid, gid_t gid, char *error);
int safe_system(char* command);
int unpriv_system(char* command, uid_t uid, gid_t gid);
size_t strlcat(char *dst, const char *src, size_t len);
int initsetuid(void);

#endif
