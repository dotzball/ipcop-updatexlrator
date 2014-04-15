#!/usr/bin/perl
#
# This code is distributed under the terms of the GPL
#
# (c) 2013-2014 umberto.m - http://joeyramone76.altervista.org/advproxylog
#
# $Id: advproxylog-lib.pl,v 1.0 2014/02/10 00:00:00 umberto.m Exp $
#

package UPDXLRL;

use strict;

$|=1; # line buffering

$UPDXLRL::apphome="/var/ipcop/addons/updxlrlog";

# -------------------------------------------------------------------

###
### return the size of a file in a human readable format
### added by joeyramone76 2014
sub get_filesize_str
{
    my $size = shift();

    if ($size > 1099511627776)  #   TiB: 1024 GiB
    {
        return sprintf("%.2f TiB", $size / 1099511627776);
    }
    elsif ($size > 1073741824)  #   GiB: 1024 MiB
    {
        return sprintf("%.2f GiB", $size / 1073741824);
    }
    elsif ($size > 1048576)     #   MiB: 1024 KiB
    {
        return sprintf("%.2f MiB", $size / 1048576);
    }
    elsif ($size > 1024)        #   KiB: 1024 B
    {
        return sprintf("%.2f KiB", $size / 1024);
    }
    else                          #   bytes
    {
        return sprintf("%.2f B", $size );
    }
}


###
### return the transfer rate per sec in a human readable format
### added by joeyramone76 2014
sub get_rate_str
{
    my $size = shift();

    if ($size > 1099511627776)  #   TiB: 1024 GiB
    {
        return sprintf("%.2f TiB/s", $size / 1099511627776);
    }
    elsif ($size > 1073741824)  #   GiB: 1024 MiB
    {
        return sprintf("%.2f GiB/s", $size / 1073741824);
    }
    elsif ($size > 1048576)     #   MiB: 1024 KiB
    {
        return sprintf("%.2f MiB/s", $size / 1048576);
    }
    elsif ($size > 1024)        #   KiB: 1024 B
    {
        return sprintf("%.2f KiB/s", $size / 1024);
    }
    else                          #   bytes
    {
        return sprintf("%.2f B/s", $size );
    }
}


###
### return the transfer rate per sec in bytes
### added by joeyramone76 2014
sub get_rate_str_bytes
{
    my $size = shift();
    return sprintf("%.2f B/s", $size );
}

sub truncate_ms_to_sec  { 
 my $ms = shift();
 my	$sec = ($ms * 0.001);
    if ($sec > 60) { #   Minutes : 60 sec    {
        return sprintf("%.2f min", $sec / 60);
    }
    else 
    {
        return sprintf("%.2f sec", $sec);
    }


# return sprintf("%.2f", 0.001 * shift)
}



sub diskfree
{
    open(DF,"/bin/df --block-size=1 $_[0]|");
    my @dfdata = <DF>;
    close DF;
    shift(@dfdata);
    chomp(@dfdata);
    my $dfstr = join(' ',@dfdata);
    my ($device,$size,$used,$free,$percent,$mount) = split(' ',$dfstr);
    if ($free =~ m/^(\d+)$/)
    {
            return $free;
    }
}

# -------------------------------------------------------------------

sub diskusage
{
    open(DF,"/bin/df $_[0]|");
    my @dfdata = <DF>;
    close DF;
    shift(@dfdata);
    chomp(@dfdata);
    my $dfstr = join(' ',@dfdata);
    my ($device,$size,$used,$free,$percent,$mount) = split(' ',$dfstr);
    if ($percent =~ m/^(\d+)%$/)
    {
            $percent =~ s/%$//;
            return $percent;
    }
}

# -------------------------------------------------------------------



