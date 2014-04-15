#!/usr/bin/perl
#
# This code is distributed under the terms of the GPL
#
# (c) 2006-2008 marco.s - http://update-accelerator.advproxy.net
#
# Portions (c) 2008 by dotzball - http://www.blockouttraffic.de
# Portions (c) 2012 by dotzball - http://www.blockouttraffic.de
#
# $Id: updatexlrator.cgi,v 2.3.0 2014/03/30 00:00:00 marco.s Exp $
#

# Add entry in menu
# MENUENTRY services 022 "updxlrtr update accelerator" "updxlrtr configuration"

use strict;
use IO::Socket;
use LWP::UserAgent;

# enable only the following on debugging purpose
use warnings; no warnings 'once';# 'redefine', 'uninitialized';
use CGI::Carp 'fatalsToBrowser';


require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';
require '/usr/lib/ipcop/header.pl';

require '/var/ipcop/addons/updatexlrator/updxlrator-lib.pl';


my $versionfile = "/var/ipcop/addons/updatexlrator/version";
my $updateUrl = "http://blockouttraffic.de/version/UpdateAccelerator.latest";
my $latestVersionFile = "/var/ipcop/addons/updatexlrator/latestVersion";

# enable(==1)/disable(==0) HTML Form debugging
my $debugFormparams = 0;
my %debug = ();

my %checked=();
my %selected=();
my %netsettings=();
my %mainsettings=();
my %proxysettings=();
my %xlratorsettings=();
my %dlinfo=();
my $id=0;
my @dfdata=();
my $dfstr='';
my @updatelist=();
my @sources=();
my $sourceurl='';
my $vendorid='';
my $uuid='';
my $status=0;
my $updatefile='';
my $shortname='';
my $time='';
my $filesize=0;
my $filedate='';
my $lastaccess='';
my $lastcheck='';
my $lastrawaccess='';
my $lastrawcheck='';
my $cachedtraffic=0;
my @requests=();
my $data='';
my $counts=0;
my $numfiles=0;
my $cachehits=0;
my $efficiency='0.0';
my @vendors=();
my %vendorstats=();
my $http_port='81';

my $hintcolour = '#FFFFCC';
my $colourgray = '#808080';

my $sfUnknown='0';
my $sfOk='1';
my $sfOutdated='2';
my $sfNoSource='3';

my $not_accessed_last='';

my $errormessage='';

my @repositorylist=();
my @repositoryfiles=();
my @downloadlist=();
my @downloadfiles=();

my @metadata=();

my $chk_cron_dly = "/var/ipcop/addons/updatexlrator/autocheck/cron.daily";
my $chk_cron_wly = "/var/ipcop/addons/updatexlrator/autocheck/cron.weekly";
my $chk_cron_mly = "/var/ipcop/addons/updatexlrator/autocheck/cron.monthly";

my @logfilelist		= ();
my %logsettings		= ();
my $start = 0;
my %vendors = ();
my %statuses = ();
$logsettings{'LOGVIEW_VIEWSIZE'} = 50;
&General::readhash('/var/ipcop/logging/settings', \%logsettings);

&General::readhash("/var/ipcop/ethernet/settings", \%netsettings);
&General::readhash("/var/ipcop/main/settings", \%mainsettings);
&General::readhash("/var/ipcop/proxy/settings", \%proxysettings);

$xlratorsettings{'ACTION'} = '';
$xlratorsettings{'ENABLED'}   = 'off';
$xlratorsettings{'ENABLE_LOG'} = 'off';
$xlratorsettings{'PASSIVE_MODE'} = 'off';
$xlratorsettings{'MAX_DISK_USAGE'} = '75';
$xlratorsettings{'LOW_DOWNLOAD_PRIORITY'} = 'off';
$xlratorsettings{'MAX_DOWNLOAD_RATE'} = '';
$xlratorsettings{'ENABLE_AUTOCHECK'} = 'off';
$xlratorsettings{'FULL_AUTOSYNC'} = 'off';
$xlratorsettings{'NOT_ACCESSED_LAST'} = 'month1';
$xlratorsettings{"AUTOCHECK_SCHEDULE"} = 'daily';
$xlratorsettings{'REMOVE_NOSOURCE'} = 'off';
$xlratorsettings{'REMOVE_OUTDATED'} = 'off';
$xlratorsettings{'REMOVE_OBSOLETE'} = 'off';

$xlratorsettings{'SORT_BY'} = 'LAST_ACCESS';
$xlratorsettings{'ORDER'} = 'DESC';
$xlratorsettings{'FILTER_VENDOR'} = 'ALL';
$xlratorsettings{'FILTER_STATUS'} = 'ALL';

&General::getcgihash(\%xlratorsettings);


$xlratorsettings{'EXTENDED_GUI'} = '';

if ($xlratorsettings{'ACTION'} eq "$Lang::tr{'updxlrtr statistics'} >>")
{
    $xlratorsettings{'EXTENDED_GUI'} = 'statistics';
}

if (($xlratorsettings{'ACTION'} eq "$Lang::tr{'updxlrtr maintenance'} >>") || ($xlratorsettings{'ACTION'} eq "$Lang::tr{'updxlrtr update'}"))
{
   
    $xlratorsettings{'EXTENDED_GUI'} = 'maintenance';
}

if ($xlratorsettings{'ACTION'} eq $Lang::tr{'updxlrtr purge'})
{
    $xlratorsettings{'EXTENDED_GUI'} = 'maintenance';

    if (($xlratorsettings{'REMOVE_OBSOLETE'} eq 'on') || ($xlratorsettings{'REMOVE_NOSOURCE'} eq 'on') || ($xlratorsettings{'REMOVE_OUTDATED'} eq 'on'))
    {
        undef (@sources);
        undef @repositoryfiles;
        foreach (<$UPDXLT::repository/*>)
        {
            if (-d $_)
            {
                unless (/^$UPDXLT::repository\/download$/) { push(@sources,$_); }
            }
        }

        foreach (@sources)
        {
            @updatelist=<$_/*>;
            $vendorid = substr($_,rindex($_,"/")+1);
            foreach(@updatelist)
            {
                $uuid = substr($_,rindex($_,"/")+1);
                if (-e "$_/source.url")
                {
                    open (FILE,"$_/source.url");
                    $sourceurl=<FILE>;
                    close FILE;
                    chomp($sourceurl);
                    $updatefile = substr($sourceurl,rindex($sourceurl,'/')+1,length($sourceurl));
                    $updatefile = "$vendorid/$uuid/$updatefile";
                    push(@repositoryfiles,$updatefile);
                }
            }
        }

        foreach (@repositoryfiles)
        {
            ($vendorid,$uuid,$updatefile) = split('/');

            if (-e "$UPDXLT::repository/$vendorid/$uuid/status")
            {
                open (FILE,"$UPDXLT::repository/$vendorid/$uuid/status");
                @metadata = <FILE>;
                close FILE;
                chomp(@metadata);
                $status = $metadata[-1];
            }

            if (-e "$UPDXLT::repository/$vendorid/$uuid/access.log")
            {
                open (FILE,"$UPDXLT::repository/$vendorid/$uuid/access.log");
                @metadata = <FILE>;
                close FILE;
                chomp(@metadata);
                $lastaccess = $metadata[-1];
            }

            if (($xlratorsettings{'REMOVE_NOSOURCE'} eq 'on') && ($status == $sfNoSource))
            {
                if (-e "$UPDXLT::repository/$vendorid/$uuid/$updatefile") { system("rm -r $UPDXLT::repository/$vendorid/$uuid"); }
            }
            if (($xlratorsettings{'REMOVE_OUTDATED'} eq 'on') && ($status == $sfOutdated))
            {
                if (-e "$UPDXLT::repository/$vendorid/$uuid/$updatefile") { system("rm -r $UPDXLT::repository/$vendorid/$uuid"); }
            }
            if ($xlratorsettings{'REMOVE_OBSOLETE'} eq 'on')
            {
                if (($xlratorsettings{'NOT_ACCESSED_LAST'} eq 'week') && ($lastaccess < (time - 604800)))
                {
                    if (-e "$UPDXLT::repository/$vendorid/$uuid/$updatefile") { system("rm -r $UPDXLT::repository/$vendorid/$uuid"); }
                }
                if (($xlratorsettings{'NOT_ACCESSED_LAST'} eq 'month1') && ($lastaccess < (time - 2505600)))
                {
                    if (-e "$UPDXLT::repository/$vendorid/$uuid/$updatefile") { system("rm -r $UPDXLT::repository/$vendorid/$uuid"); }
                }
                if (($xlratorsettings{'NOT_ACCESSED_LAST'} eq 'month3') && ($lastaccess < (time - 7516800)))
                {
                    if (-e "$UPDXLT::repository/$vendorid/$uuid/$updatefile") { system("rm -r $UPDXLT::repository/$vendorid/$uuid"); }
                }
                if (($xlratorsettings{'NOT_ACCESSED_LAST'} eq 'month6') && ($lastaccess < (time - 15033600)))
                {
                    if (-e "$UPDXLT::repository/$vendorid/$uuid/$updatefile") { system("rm -r $UPDXLT::repository/$vendorid/$uuid"); }
                }
                if (($xlratorsettings{'NOT_ACCESSED_LAST'} eq 'year') && ($lastaccess < (time - 31536000)))
                {
                    if (-e "$UPDXLT::repository/$vendorid/$uuid/$updatefile") { system("rm -r $UPDXLT::repository/$vendorid/$uuid"); }
                }
            }
        }
    }
}

if ($xlratorsettings{'ACTION'} eq $Lang::tr{'save'})
{
    if (!($xlratorsettings{'MAX_DISK_USAGE'} =~ /^\d+$/) || ($xlratorsettings{'MAX_DISK_USAGE'} < 1) || ($xlratorsettings{'MAX_DISK_USAGE'} > 100))
    {
        $errormessage .= "$Lang::tr{'updxlrtr invalid disk usage'}<br />";
        goto ERROR;
    }

    if (($xlratorsettings{'MAX_DOWNLOAD_RATE'} ne '') && ((!($xlratorsettings{'MAX_DOWNLOAD_RATE'} =~ /^\d+$/)) || ($xlratorsettings{'MAX_DOWNLOAD_RATE'} < 1)))
    {
        $errormessage .= "$Lang::tr{'updxlrtr invalid download rate'}<br />";
        goto ERROR;
    }

    &savesettings;
}

if ($xlratorsettings{'ACTION'} eq $Lang::tr{'updxlrtr save and restart'})
{
    if (!($xlratorsettings{'MAX_DISK_USAGE'} =~ /^\d+$/) || ($xlratorsettings{'MAX_DISK_USAGE'} < 1) || ($xlratorsettings{'MAX_DISK_USAGE'} > 100))
    {
        $errormessage .= "$Lang::tr{'updxlrtr invalid disk usage'}<br />";
        goto ERROR;
    }

    if (($xlratorsettings{'MAX_DOWNLOAD_RATE'} ne '') && ((!($xlratorsettings{'MAX_DOWNLOAD_RATE'} =~ /^\d+$/)) || ($xlratorsettings{'MAX_DOWNLOAD_RATE'} < 1)))
    {
        $errormessage .= "$Lang::tr{'updxlrtr invalid download rate'}<br />";
        goto ERROR;
    }
    if ((!($proxysettings{'ENABLED_GREEN_1'} eq 'on')) && (!($proxysettings{'ENABLED_BLUE_1'} eq 'on')) && (!($proxysettings{'ENABLED_OVPN'} eq 'on')))
    {
        $errormessage .= "$Lang::tr{'updxlrtr web proxy service required'}<br />";
        goto ERROR;
    }

    if (!($proxysettings{'ENABLE_REDIRECTOR'} eq 'on'))
    {
        $errormessage .= "$Lang::tr{'redirectors are disabled'}<br />";
        goto ERROR;
    }

    &savesettings;

    system('/usr/local/bin/restartsquid');
}

if ($xlratorsettings{'ACTION'} eq $Lang::tr{'updxlrtr remove file'})
{
    $xlratorsettings{'EXTENDED_GUI'} = 'maintenance';

    $updatefile = $xlratorsettings{'ID'};

    unless ($updatefile =~ /^download\//)
    {
        ($vendorid,$uuid,$updatefile) = split('/',$updatefile);
        if (-e "$UPDXLT::repository/$vendorid/$uuid/$updatefile") { system("rm -r $UPDXLT::repository/$vendorid/$uuid"); }
    }
}

if (($xlratorsettings{'ACTION'} eq $Lang::tr{'updxlrtr cancel download'}) || ($xlratorsettings{'ACTION'} eq $Lang::tr{'updxlrtr remove file'}))
{
    $updatefile = $xlratorsettings{'ID'};
    $debug{'DEBUG-1'} = "Updatefile: $updatefile";

    if ($updatefile =~ /^download\//)
    {
        ($uuid,$vendorid,$updatefile) = split('/',$updatefile);

        if (-e "$UPDXLT::repository/download/$vendorid/$updatefile.info")
        {
            &General::readhash("$UPDXLT::repository/download/$vendorid/$updatefile.info", \%dlinfo);

            my $searchDownloadCmd = "\\s/var/ipcop/addons/updatexlrator/bin/download\\s.*\\s".quotemeta($dlinfo{'SRCURL'})."\\s+\\d\\s*\$";
            $debug{'DEBUG-2'} = "Search download: $searchDownloadCmd";
            my $downloadPid = &getPID($searchDownloadCmd);
            $debug{'DEBUG-3'} = "download PID: $downloadPid";
            if ($downloadPid) {
                $debug{'DEBUG-4'} = "/bin/kill -9 $downloadPid";
                system("/bin/kill -9 $downloadPid");
            }

            my $searchWgetCmd = "\\s/usr/bin/wget\\s.*\\s".quotemeta($dlinfo{'SRCURL'})."\$";
            $debug{'DEBUG-5'} = "Search wget: $searchWgetCmd";
            my $wgetPid = &getPID($searchWgetCmd);
            $debug{'DEBUG-6'} = "wget PID: $wgetPid";
            if ($wgetPid) {
                $debug{'DEBUG-7'} = "/bin/kill -9 $wgetPid";
                system("/bin/kill -9 $wgetPid");
            }

            $debug{'DEBUG-8'} = "rm $UPDXLT::repository/download/$vendorid/$updatefile.info";
            system("rm $UPDXLT::repository/download/$vendorid/$updatefile.info");
        }

        if (-e "$UPDXLT::repository/download/$vendorid/$updatefile")
        {
            $debug{'DEBUG-9'} = "rm $UPDXLT::repository/download/$vendorid/$updatefile";

            system("rm $UPDXLT::repository/download/$vendorid/$updatefile");
        }
    }

}

# 2014 - pagination parameter (TODO)
# my @temp_then = ();
#if ($ENV{'QUERY_STRING'} && $xlratorsettings{'EXTENDED_GUI'} eq 'maintenance') {
 #   @temp_then = split(',', $ENV{'QUERY_STRING'});
  #  #$start                  = $temp_then[0];
	#$xlratorsettings{'SORT_BY'} = $temp_then[0];
	#$xlratorsettings{'ORDER'} = $temp_then[1];
	#$xlratorsettings{'FILTER_VENDOR'} = $temp_then[2];
	#$xlratorsettings{'ACTION'} = $temp_then[3];	
#}

my $statusfilter  = $xlratorsettings{'FILTER_STATUS'};
my $vendorfilter  = $xlratorsettings{'FILTER_VENDOR'};
my $statusfilterall = $xlratorsettings{'FILTER_STATUS'} eq 'ALL' ? 1 : 0;
my $vendorfilterall = $xlratorsettings{'FILTER_VENDOR'} eq 'ALL' ? 1 : 0;
my $sortby = $xlratorsettings{'SORT_BY'};
my $order = $xlratorsettings{'ORDER'};

$not_accessed_last =  $xlratorsettings{'NOT_ACCESSED_LAST'};
undef($xlratorsettings{'NOT_ACCESSED_LAST'});

if (-e "/var/ipcop/addons/updatexlrator/settings")
{
    &General::readhash("/var/ipcop/addons/updatexlrator/settings", \%xlratorsettings);
}

unless (defined($xlratorsettings{'NOT_ACCESSED_LAST'}))
{
    $xlratorsettings{'NOT_ACCESSED_LAST'} = $not_accessed_last;
}

ERROR:

$checked{'ENABLED'}{'off'}                                          = '';
$checked{'ENABLED'}{'on'}                                           = '';
$checked{'ENABLED'}{$xlratorsettings{'ENABLED'}}     = "checked='checked'";
$checked{'ENABLE_LOG'}{'off'} = '';
$checked{'ENABLE_LOG'}{'on'} = '';
$checked{'ENABLE_LOG'}{$xlratorsettings{'ENABLE_LOG'}} = "checked='checked'";
$checked{'PASSIVE_MODE'}{'off'} = '';
$checked{'PASSIVE_MODE'}{'on'} = '';
$checked{'PASSIVE_MODE'}{$xlratorsettings{'PASSIVE_MODE'}} = "checked='checked'";
$checked{'LOW_DOWNLOAD_PRIORITY'}{'off'} = '';
$checked{'LOW_DOWNLOAD_PRIORITY'}{'on'} = '';
$checked{'LOW_DOWNLOAD_PRIORITY'}{$xlratorsettings{'LOW_DOWNLOAD_PRIORITY'}} = "checked='checked'";
$checked{'ENABLE_AUTOCHECK'}{'off'} = '';
$checked{'ENABLE_AUTOCHECK'}{'on'} = '';
$checked{'ENABLE_AUTOCHECK'}{$xlratorsettings{'ENABLE_AUTOCHECK'}} = "checked='checked'";
$checked{'FULL_AUTOSYNC'}{'off'} = '';
$checked{'FULL_AUTOSYNC'}{'on'} = '';
$checked{'FULL_AUTOSYNC'}{$xlratorsettings{'FULL_AUTOSYNC'}} = "checked='checked'";
$checked{'REMOVE_NOSOURCE'}{'off'} = '';
$checked{'REMOVE_NOSOURCE'}{'on'} = '';
$checked{'REMOVE_NOSOURCE'}{$xlratorsettings{'REMOVE_NOSOURCE'}} = "checked='checked'";
$checked{'REMOVE_OUTDATED'}{'off'} = '';
$checked{'REMOVE_OUTDATED'}{'on'} = '';
$checked{'REMOVE_OUTDATED'}{$xlratorsettings{'REMOVE_OUTDATED'}} = "checked='checked'";
$checked{'REMOVE_OBSOLETE'}{'off'} = '';
$checked{'REMOVE_OBSOLETE'}{'on'} = '';
$checked{'REMOVE_OBSOLETE'}{$xlratorsettings{'REMOVE_OBSOLETE'}} = "checked='checked'";


$selected{'AUTOCHECK_SCHEDULE'}{'daily'} = '';
$selected{'AUTOCHECK_SCHEDULE'}{'weekly'} = '';
$selected{'AUTOCHECK_SCHEDULE'}{'monthly'} = '';
$selected{'AUTOCHECK_SCHEDULE'}{$xlratorsettings{'AUTOCHECK_SCHEDULE'}} = "selected='selected'";

$selected{'NOT_ACCESSED_LAST'}{'week'} = '';
$selected{'NOT_ACCESSED_LAST'}{'month1'} = '';
$selected{'NOT_ACCESSED_LAST'}{'month3'} = '';
$selected{'NOT_ACCESSED_LAST'}{'month6'} = '';
$selected{'NOT_ACCESSED_LAST'}{'year'} = '';
$selected{'NOT_ACCESSED_LAST'}{$xlratorsettings{'NOT_ACCESSED_LAST'}} = "selected='selected'";

$selected{'SORT_BY'}{'LAST_ACCESS'} = '';
$selected{'SORT_BY'}{'LAST_CHECK'} = '';
$selected{'SORT_BY'}{'VENDOR'} = '';
$selected{'SORT_BY'}{'DATE'} = '';
$selected{'SORT_BY'}{'SIZE'} = '';
$selected{'SORT_BY'}{'STATUS'} = '';
$selected{'SORT_BY'}{'NAME'} = '';
$selected{'SORT_BY'}{$sortby} = "selected='selected'";

$selected{'ORDER'}{'ASC'} = '';
$selected{'ORDER'}{'DESC'} = '';
$selected{'ORDER'}{$order} = "selected='selected'";

$selected{'FILTER_VENDOR'}{$vendorfilter} = "selected='selected'";
$selected{'FILTER_STATUS'}{$statusfilter} = "selected='selected'";


# ----------------------------------------------------
#    Settings dialog
# ----------------------------------------------------

&Header::showhttpheaders();

&Header::openpage($Lang::tr{'updxlrtr configuration'}, 1, '');


###############
# DEBUG DEBUG
if ($debugFormparams == 1) {
    &Header::openbox('100%', 'left', 'DEBUG');
    my $debugCount = 0;
    foreach my $line (sort keys %xlratorsettings) {
        print "$line = $xlratorsettings{$line}<br />\n";
        $debugCount++;
    }
    foreach my $line (sort keys %debug) {
        print "$line = $debug{$line}<br />\n";
        $debugCount++;
    }
    print "&nbsp;Count: $debugCount\n";
    &Header::closebox();
}

&Header::openbigbox('100%', 'left', '', $errormessage);

if ($errormessage) {
    &Header::openbox('100%', 'left', $Lang::tr{'error messages'});
    print "<font class='base'>$errormessage&nbsp;</font>\n";
    &Header::closebox();
}


# check for new version
&checkForNewVersion();


print "<form method='post' action='$ENV{'SCRIPT_NAME'}' enctype='multipart/form-data'>\n";

&Header::openbox('100%', 'left', "$Lang::tr{'updxlrtr update accelerator'}");

print <<END
<table width='100%'>
<tr>
        <td colspan='4'><b>$Lang::tr{'updxlrtr common settings'}</b></td>
</tr>
<tr>
    <td class='base' width='25%'>$Lang::tr{'enabled'}:</td>
    <td class='base' width='20%'><input type='checkbox' name='ENABLED' $checked{'ENABLED'}{'on'} /></td>
    <td class='base' width='25%'>$Lang::tr{'updxlrtr enable log'}:</td>
    <td class='base' width='30%'><input type='checkbox' name='ENABLE_LOG' $checked{'ENABLE_LOG'}{'on'} /></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'updxlrtr passive mode'}:</td>
    <td class='base'><input type='checkbox' name='PASSIVE_MODE' $checked{'PASSIVE_MODE'}{'on'} /></td>
    <td class='base'>$Lang::tr{'updxlrtr max disk usage'}:</td>
    <td class='base'><input type='text' name='MAX_DISK_USAGE' value='$xlratorsettings{'MAX_DISK_USAGE'}' size='1' /> %</td>
</tr>
</table>
<hr size='1' />
<table width='100%'>
<tr>
        <td colspan='4'><b>$Lang::tr{'updxlrtr performance options'}</b></td>
</tr>
<tr>
    <td class='base' width='25%'>$Lang::tr{'updxlrtr low download priority'}:</td>
    <td class='base' width='20%'><input type='checkbox' name='LOW_DOWNLOAD_PRIORITY' $checked{'LOW_DOWNLOAD_PRIORITY'}{'on'} /></td>
    <td class='base' width='25%'>$Lang::tr{'updxlrtr max download rate'}:&nbsp;<img src='/blob.gif' alt='*' /></td>
    <td class='base' width='30%'><input type='text' name='MAX_DOWNLOAD_RATE' value='$xlratorsettings{'MAX_DOWNLOAD_RATE'}' size='5' /></td>
</tr>
</table>
<hr size='1' />
<table width='100%'>
<tr>
        <td colspan='4'><b>$Lang::tr{'updxlrtr source checkup'}</b></td>
</tr>
<tr>
    <td class='base' width='25%'>$Lang::tr{'updxlrtr enable autocheck'}:</td>
    <td class='base' width='20%'><input type='checkbox' name='ENABLE_AUTOCHECK' $checked{'ENABLE_AUTOCHECK'}{'on'} /></td>
    <td class='base' width='25%'>$Lang::tr{'updxlrtr source checkup schedule'}:</td>
    <td class='base' width='30%'>
    <select name='AUTOCHECK_SCHEDULE'>
    <option value='daily' $selected{'AUTOCHECK_SCHEDULE'}{'daily'}>$Lang::tr{'updxlrtr daily'}</option>
    <option value='weekly' $selected{'AUTOCHECK_SCHEDULE'}{'weekly'}>$Lang::tr{'updxlrtr weekly'}</option>
    <option value='monthly' $selected{'AUTOCHECK_SCHEDULE'}{'monthly'}>$Lang::tr{'updxlrtr monthly'}</option>
    </select>
    </td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'updxlrtr full autosync'}:</td>
    <td class='base'><input type='checkbox' name='FULL_AUTOSYNC' $checked{'FULL_AUTOSYNC'}{'on'} /></td>
    <td>&nbsp;</td>
    <td>&nbsp;</td>
</tr>
</table>
<hr size='1' />
<table width='100%'>
<tr>
    <td align='center' width='20%'><input type='submit' name='ACTION' value='$Lang::tr{'save'}' /></td>
    <td align='center' width='20%'><input type='submit' name='ACTION' value='$Lang::tr{'updxlrtr save and restart'}' /></td>
    <td>&nbsp;</td>
END
;

print"	<td align='center' width='20%'><input type='submit' name='ACTION' value='$Lang::tr{'updxlrtr statistics'}";
if ($xlratorsettings{'EXTENDED_GUI'} eq 'statistics') { print " <<' "; } else { print " >>' "; }
print "/></td>\n";

print" 	<td align='center' width='20%'><input type='submit' name='ACTION' value='$Lang::tr{'updxlrtr maintenance'}";
if ($xlratorsettings{'EXTENDED_GUI'} eq 'maintenance') { print " <<' "; } else { print " >>' "; }
print "/></td>\n";


my %versionSettings = ();

&General::readhash($versionfile, \%versionSettings);

print <<END
</tr>
</table>
<table width='100%'>
<tr>
    <td align='right'>
    <sup><small><a href='$versionSettings{'URL'}' target='_blank'>Update Accelerator $versionSettings{'VERSION_INSTALLED'}</a></small></sup>
    </td>
</tr>
</table>
END
;

&Header::closebox();

print "</form>\n";

# ----------------------------------------------------
#   List pending downloads - if any
# ----------------------------------------------------

if (($xlratorsettings{'EXTENDED_GUI'} ne 'statistics') && ($xlratorsettings{'EXTENDED_GUI'} ne 'maintenance'))
{
    @downloadlist = <$UPDXLT::repository/download/*>;

    undef(@downloadfiles);
    foreach (@downloadlist)
    {
        if (-d)
        {
            my @filelist = <$_/*>;
            $vendorid = substr($_,rindex($_,"/")+1);
            foreach(@filelist)
            {
                next if(/\.info$/);
                $updatefile = substr($_,rindex($_,"/")+1);
                $updatefile .= ":download/$vendorid/$updatefile";
                $updatefile = " ".$updatefile;
                push(@downloadfiles, $updatefile);
            }
        }
    }

    if (@downloadfiles)
    {
        &Header::openbox('100%', 'left', "$Lang::tr{'updxlrtr pending downloads'}");

        print <<END
<table>
    <tr><td class='boldbase'><b>$Lang::tr{'updxlrtr current downloads'}</b></td></tr>
</table>
<table width='100%'>
<colgroup span='3' width='2%'></colgroup>
<colgroup span='1' width='0*'></colgroup>
<colgroup span='3' width='5%'></colgroup>
<colgroup span='1' width='2%'></colgroup>
<tr>
    <td class='base' align='center'>&nbsp;</td>
    <td class='base' align='left' colspan='2'><i>$Lang::tr{'updxlrtr source'}</i></td>
    <td class='base' align='center'><i>$Lang::tr{'updxlrtr filename'}</i></td>
    <td class='base' align='center'><i>$Lang::tr{'updxlrtr filesize'}</i></td>
    <td class='base' align='center'><i>$Lang::tr{'date'}</i></td>
    <td class='base' align='center'><i>$Lang::tr{'updxlrtr progress'}</i></td>
    <td class='base' align='center'>&nbsp;</td>
</tr>
END
;
        $id = 0;
        foreach $updatefile (@downloadfiles)
        {
            $updatefile =~ s/.*://;
            my $size_updatefile = 0;
            my $mtime = 0;
            if(-e "$UPDXLT::repository/$updatefile") {
                $size_updatefile = (-s "$UPDXLT::repository/$updatefile");
                $mtime = &getmtime("$UPDXLT::repository/$updatefile");
            }
            if (-e "$UPDXLT::repository/$updatefile.info") {
                &General::readhash("$UPDXLT::repository/$updatefile.info", \%dlinfo);
            } else {
                undef(%dlinfo);
            }

            $id++;
            if ($id % 2) {
                print "<tr class='table1colour'>\n"; }
            else {
                print "<tr class='table2colour'>\n"; }

            $filesize = $size_updatefile;
            1 while $filesize =~ s/^(-?\d+)(\d{3})/$1.$2/;

            my ($SECdt,$MINdt,$HOURdt,$DAYdt,$MONTHdt,$YEARdt) = localtime($mtime);
            $DAYdt   = sprintf ("%.02d",$DAYdt);
            $MONTHdt = sprintf ("%.02d",$MONTHdt+1);
            $YEARdt  = sprintf ("%.04d",$YEARdt+1900);
            $filedate = $YEARdt."-".$MONTHdt."-".$DAYdt;

            ($uuid,$vendorid,$shortname) = split('/',$updatefile);

        print "\t\t<td align='center' nowrap='nowrap'>&nbsp;";
        if (&getPID("\\s/usr/bin/wget\\s.*\\s".quotemeta($dlinfo{'SRCURL'})."\$"))
        {
            print "<img src='/images/updxl-led-blue.gif' alt='$Lang::tr{'updxlrtr condition download'}' />&nbsp;</td>\n";
        } else {
            print "<img src='/images/updxl-led-gray.gif' alt='$Lang::tr{'updxlrtr condition suspended'}' />&nbsp;</td>\n";
        }

            print "\t\t<td align='center' nowrap='nowrap'>&nbsp;";
            if ($vendorid =~ /^Adobe$/i)
            {
                print "<img src='/images/updxl-src-adobe.gif' alt='Adobe'}' />&nbsp;</td>\n";
            } elsif ($vendorid =~ /^Microsoft$/i)
            {
                print "<img src='/images/updxl-src-windows.gif' alt='Microsoft'}' />&nbsp;</td>\n";
            } elsif ($vendorid =~ /^Symantec$/i)
            {
                print "<img src='/images/updxl-src-symantec.gif' alt='Symantec'}' />&nbsp;</td>\n";
            } elsif ($vendorid =~ /^Linux$/i)
            {
                print "<img src='/images/updxl-src-linux.gif' alt='Linux'}' />&nbsp;</td>\n";
            } elsif ($vendorid =~ /^TrendMicro$/i)
            {
                print "<img src='/images/updxl-src-trendmicro.gif' alt='Trend Micro'}' />&nbsp;</td>\n";
            } elsif ($vendorid =~ /^Apple$/i)
            {
                print "<img src='/images/updxl-src-apple.gif' alt='Apple'}' />&nbsp;</td>\n";
            } elsif ($vendorid =~ /^Avast$/i)
            {
                print "<img src='/images/updxl-src-avast.gif' alt='Avast'}' />&nbsp;</td>\n";
            } else
            {
                if (-e "/home/httpd/html/images/updxl-src-" . $vendorid . ".gif")
                {
                    print "<img src='/images/updxl-src-" . $vendorid . ".gif' alt='" . ucfirst $vendorid . "' />&nbsp;</td>\n";
                } else {
                    print "<img src='/images/updxl-src-unknown.gif' alt='" . ucfirst $vendorid . "' />&nbsp;</td>\n";
                }
            }

            $shortname = substr($updatefile,rindex($updatefile,"/")+1);
            $shortname =~ s/(.*)_[\da-f]*(\.(exe|cab|psf)$)/$1_*$2/i;

            $filesize = $dlinfo{'REMOTESIZE'};
            1 while $filesize =~ s/^(-?\d+)(\d{3})/$1.$2/;
            $dlinfo{'VENDORID'}=ucfirst $vendorid;

            print <<END
        <td class='base' align='center'>&nbsp;$dlinfo{'VENDORID'}&nbsp;</td>
        <td class='base' align='left' title='cache:/$updatefile'>$shortname</td>
        <td class='base' align='right'  nowrap='nowrap'>&nbsp;$filesize&nbsp;</td>
        <td class='base' align='center' nowrap='nowrap'>&nbsp;$filedate&nbsp;</td>
        <td class='base' align='center' nowrap='nowrap'>
END
;
            my $percent="0%";
            if ($dlinfo{'REMOTESIZE'} && $size_updatefile)
            {
                $percent=int(100 / ($dlinfo{'REMOTESIZE'} / $size_updatefile))."%";
            }
            print $percent; &percentbar($percent);
            print <<END
        </td>
        <td align='center'>
        <form method='post' name='frma$id' action='$ENV{'SCRIPT_NAME'}'>
        <input type='image' name='$Lang::tr{'updxlrtr cancel download'}' src='/images/delete.gif' title='$Lang::tr{'updxlrtr cancel download'}' alt='$Lang::tr{'updxlrtr cancel download'}' />
        <input type='hidden' name='ID' value='$updatefile' />
        <input type='hidden' name='ACTION' value='$Lang::tr{'updxlrtr cancel download'}' />
        </form>
        </td>
    </tr>
END
;
        }

        print "</table>\n<br>\n<table>\n";
        &printlegenddownload();
        print "</table>\n";

        &Header::closebox();
    }
}

# =====================================================================================
#  CACHE STATISTICS
# =====================================================================================

if ($xlratorsettings{'EXTENDED_GUI'} eq 'statistics')
{

# ----------------------------------------------------
#    Get statistics
# ----------------------------------------------------

@sources=();
foreach (<$UPDXLT::repository/*>)
{
    if (-d $_)
    {
        unless ((/^$UPDXLT::repository\/download$/) || (/^$UPDXLT::repository\/lost\+found$/)) { push(@sources,$_); }
    }
}

@vendors=();
foreach (@sources)
{
    $vendorid=substr($_,rindex($_,'/')+1,length($_));
    push(@vendors,$vendorid);
    $vendorstats{$vendorid."_filesize"} = 0;
    $vendorstats{$vendorid."_requests"} = 0;
    $vendorstats{$vendorid."_files"} = 0;
    $vendorstats{$vendorid."_cachehits"} = 0;
    $vendorstats{$vendorid."_0"} = 0;
    $vendorstats{$vendorid."_1"} = 0;
    $vendorstats{$vendorid."_2"} = 0;
    $vendorstats{$vendorid."_3"} = 0;

    @updatelist=<$_/*>;
    foreach $data (@updatelist)
    {
        if (-e "$data/source.url")
        {
            open (FILE,"$data/source.url");
            $sourceurl=<FILE>;
            close FILE;
            chomp($sourceurl);
            $updatefile = substr($sourceurl,rindex($sourceurl,'/')+1,length($sourceurl));

            my $size_updatefile = 0;
            if(-e "$data/$updatefile") {
                $size_updatefile = (-s "$data/$updatefile");
            }
            else
            {
                # DEBUG
                #die "file not found: $data/$updatefile\n";
            }
        #
        # Total file size
        #
            $filesize += $size_updatefile;
        #
        # File size for this source
        #
            $vendorstats{$vendorid."_filesize"} += $size_updatefile;
        #
        # Number of requests from cache for this source
        #
            open (FILE,"$data/access.log");
            @requests=<FILE>;
            close FILE;
            chomp(@requests);
            $counts = @requests;
            $counts--;
            $vendorstats{$vendorid."_requests"} += $counts;
            $cachehits += $counts;
        #
        # Total number of files in cache
        #
            $numfiles++;
        #
        # Number of files for this source
        #
            $vendorstats{$vendorid."_files"}++;
        #
        # Count cache status occurences
        #
            open (FILE,"$data/status");
            $_=<FILE>;
            close FILE;
            chomp;
            $vendorstats{$vendorid."_".$_}++;
        #
        # Calculate cached traffic for this source
        #
            $vendorstats{$vendorid."_cachehits"} += $counts * $size_updatefile;
        #
        # Calculate total cached traffic
        #
            $cachedtraffic += $counts * $size_updatefile;

        }
    }
}

if ($numfiles) { $efficiency = sprintf("%.1f", $cachehits / $numfiles); }

1 while $filesize =~ s/^(-?\d+)(\d{3})/$1.$2/;
1 while $cachedtraffic =~ s/^(-?\d+)(\d{3})/$1.$2/;

# ----------------------------------------------------
#    Show statistics
# ----------------------------------------------------

&Header::openbox('100%', 'left', "$Lang::tr{'updxlrtr cache statistics'}");

unless ($numfiles) { print "<i>$Lang::tr{'updxlrtr empty repository'}</i>\n<hr size='1' />\n"; }

print <<END
<table>
<tr><td class='boldbase'><b>$Lang::tr{'updxlrtr disk usage'}</b></td></tr>
</table>
<table cellpadding='3'>
<tr>
<td align='left' class='base'><i>$Lang::tr{'updxlrtr cache dir'}</i></td>
<td align='center' class='base'><i>$Lang::tr{'size'}</i></td>
<td align='center' class='base'><i>$Lang::tr{'used'}</i></td>
<td align='center' class='base'><i>$Lang::tr{'free'}</i></td>
<td align='left' class='base' colspan='2'><i>$Lang::tr{'percentage'}</i></td>
</tr>
END
;

open(DF,"/bin/df -h $UPDXLT::repository|");
@dfdata = <DF>;
close DF;
shift(@dfdata);
chomp(@dfdata);
$dfstr = join(' ',@dfdata);
my ($device,$size,$used,$free,$percent,$mount) = split(' ',$dfstr);

print <<END
<tr>
<td>[$UPDXLT::repository]</td>
<td align='right'>$size</td>
<td align='right'>$used</td>
<td align='right'>$free</td>
<td>
END
;
&percentbar($percent);
print <<END
</td>
<td align='right'>$percent</td>
</tr>
</table>
END
;

if ($numfiles)
{
    print <<END
<hr size='1' />
<table width='100%'>
<tr>
        <td colspan='5'><b>$Lang::tr{'updxlrtr summary'}</b></td>
</tr>
<tr>
    <td class='base' width='25%'>$Lang::tr{'updxlrtr total files'}:</td>
    <td class='base' width='20%'><font color='$colourgray'>$numfiles</font></td>
    <td class='base' width='25%'>$Lang::tr{'updxlrtr total cache size'}:</td>
    <td class='base' width='15%' align='right'><font color='$colourgray'>$filesize</font></td>
    <td class='base'></td>
</tr>
<tr>
    <td class='base'>$Lang::tr{'updxlrtr efficiency index'}:</td>
    <td class='base'><font color='$colourgray'>$efficiency</font></td>
    <td class='base'>$Lang::tr{'updxlrtr total data from cache'}:</td>
    <td class='base' align='right'><font color='$colourgray'>$cachedtraffic</font></td>
    <td class='base'></td>
</tr>
</table>
<hr size='1' />
<table>
<tr>
        <td colspan='17'><b>$Lang::tr{'updxlrtr statistics by source'}</b></td>
</tr>
<tr>
    <td class='base' colspan='2'><i>$Lang::tr{'updxlrtr source'}</i></td>
    <td class='base' width='7%'>&nbsp;</td>
    <td class='base' align='right'><i>$Lang::tr{'updxlrtr files'}</i></td>
    <td class='base' width='7%'>&nbsp;</td>
    <td class='base' align='right'><nobr><i>$Lang::tr{'updxlrtr cache size'}</i></nobr></td>
    <td class='base' width='7%'>&nbsp;</td>
    <td class='base' align='right'><nobr><i>$Lang::tr{'updxlrtr data from cache'}</i></nobr></td>
    <td class='base' width='15%'>&nbsp;</td>
    <td class='base'><img src="/images/updxl-led-green.gif" /></td>
    <td class='base' width='15%'>&nbsp;</td>
    <td class='base'><img src="/images/updxl-led-yellow.gif" /></td>
    <td class='base' width='15%'>&nbsp;</td>
    <td class='base'><img src="/images/updxl-led-red.gif" /></td>
    <td class='base' width='15%'>&nbsp;</td>
    <td class='base'><img src="/images/updxl-led-gray.gif" /></td>
    <td class='base' width='90%'>&nbsp;</td>
</tr>
END
;

$id = 0;

foreach (@vendors)
{
    $vendorid = $_;

    unless ($vendorstats{$vendorid . "_files"}) { next; }

    $id++;
    if ($id % 2) {
        print "<tr class='table1colour'>\n"; }
    else {
        print "<tr class='table2colour'>\n"; }

    print "<td class='base' align='center'><nobr>&nbsp;";

    if ($vendorid =~ /^Adobe$/i)
    {
        print "<img src='/images/updxl-src-adobe.gif' alt='Adobe'}' />&nbsp;</nobr></td>\n";
        print "<td class='base'>&nbsp;Adobe&nbsp;</td>\n";
    } elsif ($vendorid =~ /^Microsoft$/i)
    {
        print "<img src='/images/updxl-src-windows.gif' alt='Microsoft'}' />&nbsp;</nobr></td>\n";
        print "<td class='base'>&nbsp;Microsoft&nbsp;</td>\n";
    } elsif ($vendorid =~ /^Symantec$/i)
    {
        print "<img src='/images/updxl-src-symantec.gif' alt='Symantec'}' />&nbsp;</nobr></td>\n";
        print "<td class='base'>&nbsp;Symantec&nbsp;</td>\n";
    } elsif ($vendorid =~ /^Linux$/i)
    {
        print "<img src='/images/updxl-src-linux.gif' alt='Linux'}' />&nbsp;</nobr></td>\n";
        print "<td class='base'>&nbsp;Linux&nbsp;</td>\n";
    } elsif ($vendorid =~ /^TrendMicro$/i)
    {
        print "<img src='/images/updxl-src-trendmicro.gif' alt='Trend Micro'}' />&nbsp;</nobr></td>\n";
        print "<td class='base'>&nbsp;Trend&nbsp;Micro&nbsp;</td>\n";
    } elsif ($vendorid =~ /^Apple$/i)
    {
        print "<img src='/images/updxl-src-apple.gif' alt='Apple'}' />&nbsp;</nobr></td>\n";
        print "<td class='base'>&nbsp;Apple&nbsp;</td>\n";
    } elsif ($vendorid =~ /^Avast$/i)
    {
        print "<img src='/images/updxl-src-avast.gif' alt='Avast'}' />&nbsp;</nobr></td>\n";
        print "<td class='base'>&nbsp;Avast&nbsp;</td>\n";
    } else
    {
        if (-e "/home/httpd/html/images/updxl-src-" . $vendorid . ".gif")
        {
            print "<img src='/images/updxl-src-" . $vendorid . ".gif' alt='" . ucfirst $vendorid . "' />&nbsp;</nobr></td>\n";
        } else {
            print "<img src='/images/updxl-src-unknown.gif' alt='" . ucfirst $vendorid . "' />&nbsp;</nobr></td>\n";
        }
        print "<td class='base'>&nbsp;" . ucfirst $vendorid . "&nbsp;</td>\n";
    }

    print "<td class='base' colspan=2 align='right'>";
    printf "%5d", $vendorstats{$vendorid."_files"};
    print "&nbsp;</td>\n";

    unless ($vendorstats{$vendorid."_filesize"}) { $vendorstats{$vendorid."_filesize"} = '0'; }
    1 while $vendorstats{$vendorid."_filesize"} =~ s/^(-?\d+)(\d{3})/$1.$2/;
    print "<td class='base' colspan=2 align='right'>";
    printf "%15s", $vendorstats{$vendorid."_filesize"};
    print "&nbsp;</td>\n";

    unless ($vendorstats{$vendorid."_cachehits"}) { $vendorstats{$vendorid."_cachehits"} = '0'; }
    1 while $vendorstats{$vendorid."_cachehits"} =~ s/^(-?\d+)(\d{3})/$1.$2/;
    print "<td class='base' colspan=2 align='right'>";
    printf "%15s", $vendorstats{$vendorid."_cachehits"};
    print "&nbsp;</td>\n";

    print "<td class='base' colspan=2 align='right'>";
    printf "%5d", $vendorstats{$vendorid."_1"};
    print "&nbsp;&nbsp;</td>\n";

    print "<td class='base' colspan=2 align='right'>";
    printf "%5d", $vendorstats{$vendorid."_3"};
    print "&nbsp;&nbsp;</td>\n";

    print "<td class='base' colspan=2 align='right'>";
    printf "%5d", $vendorstats{$vendorid."_2"};
    print "&nbsp;&nbsp;</td>\n";

    print "<td class='base' colspan=2 align='right'>";
    printf "%5d", $vendorstats{$vendorid."_0"};
    print "&nbsp;&nbsp;</td>\n";

    print "<td class='base'>&nbsp;</td>\n";
    print "</tr>\n";
}

print "</table>\n";

print <<END
<br>
<table>
    <tr>
        <td class='boldbase'>&nbsp; <b>$Lang::tr{'legend'}:</b></td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-led-green.gif' alt='$Lang::tr{'updxlrtr condition ok'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr condition ok'}</td>
        <td class='base'>&nbsp;&nbsp;&nbsp;</td>
        <td align='center'><img src='/images/updxl-led-yellow.gif' alt='$Lang::tr{'updxlrtr condition nosource'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr condition nosource'}</td>
        <td class='base'>&nbsp;&nbsp;&nbsp;</td>
        <td align='center'><img src='/images/updxl-led-red.gif' alt='$Lang::tr{'updxlrtr condition outdated'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr condition outdated'}</td>
        <td class='base'>&nbsp;&nbsp;&nbsp;</td>
        <td align='center'><img src='/images/updxl-led-gray.gif' alt='$Lang::tr{'updxlrtr condition unknown'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr condition unknown'}</td>
        <td class='base'>&nbsp;&nbsp;&nbsp;</td>
    </tr>
</table>
END
;

}

&Header::closebox();

}

# =====================================================================================
#  CACHE MAINTENANCE
# =====================================================================================

if ($xlratorsettings{'EXTENDED_GUI'} eq 'maintenance')
{

# ----------------------------------------------------
#    File list dialog
# ----------------------------------------------------

&Header::openbox('100%', 'left', "$Lang::tr{'updxlrtr cache maintenance'}");

@sources= <$UPDXLT::repository/download/*>;

undef @repositoryfiles;
foreach (@sources)
{
    if (-d)
    {
        @updatelist = <$_/*>;
        $vendorid = substr($_,rindex($_,"/")+1);
		$vendors{$vendorid}++;
		# 2014 verify filter condition 
		if (
			   ((($vendorid eq $vendorfilter) || $vendorfilterall))
		)	
		
        { 
			
			foreach(@updatelist)
			{
				next if(/\.info$/);
				$updatefile = substr($_,rindex($_,"/")+1);
				$updatefile .= ":download/$vendorid/$updatefile";
				$updatefile = " ".$updatefile;
				push(@repositoryfiles,$updatefile);
			}
		}	
    }
}

undef (@sources);
foreach (<$UPDXLT::repository/*>)
{
    if (-d $_)
    {
        unless (/^$UPDXLT::repository\/download$/) { push(@sources,$_); }
    }
}

foreach (@sources)
{
    @updatelist=<$_/*>;
    $vendorid = substr($_,rindex($_,"/")+1);
	$vendors{$vendorid}++;
	# 2014 - verify only vendor condition - at this point we don't have the status yet 
	if ((($vendorid eq $vendorfilter) || $vendorfilterall))	
	{
	    
		foreach(@updatelist)
		{
			$uuid = substr($_,rindex($_,"/")+1);
			if (-e "$_/source.url")
			{
				open (FILE,"$_/source.url");
				$sourceurl=<FILE>;
				close FILE;
				chomp($sourceurl);
				$updatefile = substr($sourceurl,rindex($sourceurl,'/')+1,length($sourceurl));
				$_ = $updatefile; tr/[A-Z]/[a-z]/;
				$updatefile = "$_:$vendorid/$uuid/$updatefile";
				push(@repositoryfiles,$updatefile);
			}
		}
	}	
}

@repositoryfiles = sort(@repositoryfiles);

unless (@repositoryfiles) { print "<i>$Lang::tr{'updxlrtr empty repository'}</i>\n<hr size='1' />\n"; }

print <<END
<table>
<tr><td class='boldbase'><b>$Lang::tr{'updxlrtr disk usage'}</b></td></tr>
</table>
<table cellpadding='3'>
<tr>
<td align='left' class='base'><i>$Lang::tr{'updxlrtr cache dir'}</i></td>
<td align='center' class='base'><i>$Lang::tr{'size'}</i></td>
<td align='center' class='base'><i>$Lang::tr{'used'}</i></td>
<td align='center' class='base'><i>$Lang::tr{'free'}</i></td>
<td align='left' class='base' colspan='2'><i>$Lang::tr{'percentage'}</i></td>
</tr>
END
;

open(DF,"/bin/df -h $UPDXLT::repository|");
@dfdata = <DF>;
close DF;
shift(@dfdata);
chomp(@dfdata);
$dfstr = join(' ',@dfdata);
my ($device,$size,$used,$free,$percent,$mount) = split(' ',$dfstr);

print <<END
<tr>
<td>[$UPDXLT::repository]</td>
<td align='right'>$size</td>
<td align='right'>$used</td>
<td align='right'>$free</td>
<td>
END
;
&percentbar($percent);
print <<END
</td>
<td align='right'>$percent</td>
</tr>
</table>
END
;

if (@repositoryfiles)
{
print <<END
<hr size='1' />
<form method='post' action='$ENV{'SCRIPT_NAME'}' enctype='multipart/form-data'>
<table width='100%'>
<tr>
    <td class='base' colspan='3'><input type='submit' name='ACTION' value='$Lang::tr{'updxlrtr purge'}' /> &nbsp;$Lang::tr{'updxlrtr all files'}</td>
    <td class='base' width='25%'>
        <input type='checkbox' name='REMOVE_OBSOLETE' $checked{'REMOVE_OBSOLETE'}{'on'} />&nbsp;$Lang::tr{'updxlrtr not accessed'}
    </td>
    <td class='base' colspan='3'>
        <select name='NOT_ACCESSED_LAST'>
            <option value='week'   $selected{'NOT_ACCESSED_LAST'}{'week'}>$Lang::tr{'updxlrtr week'}</option>
            <option value='month1' $selected{'NOT_ACCESSED_LAST'}{'month1'}>$Lang::tr{'updxlrtr month'}</option>
            <option value='month3' $selected{'NOT_ACCESSED_LAST'}{'month3'}>$Lang::tr{'updxlrtr 3 months'}</option>
            <option value='month6' $selected{'NOT_ACCESSED_LAST'}{'month6'}>$Lang::tr{'updxlrtr 6 months'}</option>
            <option value='year'   $selected{'NOT_ACCESSED_LAST'}{'year'}>$Lang::tr{'updxlrtr year'}</option>
        </select>
    </td>
</tr>
<tr>
</tr>
<tr>
    <td class='base' width='25%'>
        <input type='checkbox' name='REMOVE_NOSOURCE' $checked{'REMOVE_NOSOURCE'}{'on'} />&nbsp;$Lang::tr{'updxlrtr marked as'}
    </td>
    <td class='base' width='3%'><img src='/images/updxl-led-yellow.gif' alt='$Lang::tr{'updxlrtr condition nosource'}' /></td>
    <td class='base' width='17%'>[<i>$Lang::tr{'updxlrtr condition nosource'}</i>]</td>
    <td class='base' width='25%'>
        <input type='checkbox' name='REMOVE_OUTDATED' $checked{'REMOVE_OUTDATED'}{'on'} />&nbsp;$Lang::tr{'updxlrtr marked as'}
    </td>
    <td class='base' width='3%'><img src='/images/updxl-led-red.gif' alt='$Lang::tr{'updxlrtr condition outdated'}' /></td>
    <td class='base' width='27%'>[<i>$Lang::tr{'updxlrtr condition outdated'}</i>]</td>
</tr>
</table>
</form>
END
;

&Header::closebox();
&Header::openbox('100%', 'left', "$Lang::tr{'updxlrtr current files'} - $Lang::tr{'updxlrtr sort by'} $sortby");

print <<END
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<table width='100%' border='0'>

<tr>
	<td  style='width:30%;' class='base'>$Lang::tr{'updxlrtr sort by'}:</td>
	<td  style='width:15%;'>
	
	 <select name='SORT_BY'>
		<option value='LAST_ACCESS' $selected{'SORT_BY'}{'LAST_ACCESS'}>$Lang::tr{'updxlrtr sort by last access'}</option>
		<option value='LAST_CHECK' $selected{'SORT_BY'}{'LAST_CHECK'}>$Lang::tr{'updxlrtr sort by last check'}</option>
		<option value='VENDOR' $selected{'SORT_BY'}{'VENDOR'}>$Lang::tr{'updxlrtr sort by vendor'}</option>
		<option value='DATE' $selected{'SORT_BY'}{'DATE'}>$Lang::tr{'updxlrtr sort by date'}</option>
		<option value='SIZE' $selected{'SORT_BY'}{'SIZE'}>$Lang::tr{'updxlrtr sort by size'}</option>
		<option value='STATUS' $selected{'SORT_BY'}{'STATUS'}>$Lang::tr{'updxlrtr sort by status'}</option>
		<option value='NAME' $selected{'SORT_BY'}{'NAME'}>$Lang::tr{'updxlrtr sort by name'}</option>
	 </select>	
	<td>	
	<td style='width:30%;' class='base'>$Lang::tr{'updxlrtr order'}:</td>
	<td style='width:25%;'>
		<select name='ORDER'>
		<option value='ASC' $selected{'ORDER'}{'ASC'}>$Lang::tr{'updxlrtr order asc'}</option>
		<option value='DESC' $selected{'ORDER'}{'DESC'}>$Lang::tr{'updxlrtr order desc'}</option>
	 </select>	
	</td>
</tr>
<tr>
    <td  style='width:30%;' class='base'>$Lang::tr{'updxlrtr sort by vendor'}:</td>
	<td  style='width:15%;'>
	<select name='FILTER_VENDOR'>
	<option value='ALL' $selected{'FILTER_VENDOR'}{'ALL'}>$Lang::tr{'caps all'}</option>
END
    ;
foreach my $vendor (keys %vendors) {
    if ($vendor) {
	    if (!$selected{'FILTER_VENDOR'}{$vendor}) {
		 $selected{'FILTER_VENDOR'}{$vendor} = '';
		}
		print "<option value='$vendor' $selected{'FILTER_VENDOR'}{$vendor}>$vendor</option>\n";
	}
}
print <<END
	</select>
	</td>
	<td style='width:30%;' class='base'></td>
	<td style='width:25%;'></td>
</tr>
<tr>
 <td colspan="4">
	<input type='submit' name='ACTION' value='$Lang::tr{'updxlrtr update'}'>
 </td>
</table>

<hr />
</form>

END
;
	
    &printcurrentfiles("$sortby", "$order", @repositoryfiles);
    print "<br>\n<table>\n";
    &printlegendicons();
    &printlegendspacer();
    &printlegendstatus();
    &printlegendspacer();
    &printlegendsource();
    print "</table>\n";
}

&Header::closebox();

}

# =====================================================================================

&Header::closebigbox();

&Header::closepage();

# -------------------------------------------------------------------

sub printcurrentfiles
{
    #my $title = shift;
	my $sortby = shift;
	my $order = shift;
    my @files = @_;
	#my $sortby = $xlratorsettings{'SORT_BY'};
	#my $order = $xlratorsettings{'ORDER'};
	
    print <<END

<table width='100%'>
<colgroup span='2' width='2%'></colgroup>
<colgroup span='1' width='0*'></colgroup>
<colgroup span='4' width='5%'></colgroup>
<colgroup span='1' width='2%'></colgroup>
<tr>
    <td class='base' align='center'>&nbsp;</td>
    <td class='base' align='center'>&nbsp;</td>
    <td class='base' align='center'><b>$Lang::tr{'updxlrtr filename'}</b></td>
    <td class='base' align='center'><b>$Lang::tr{'updxlrtr filesize'}</b></td>
    <td class='base' align='center'><b>$Lang::tr{'date'}</b></td>
    <td class='base' align='center'><img src='/images/reload.gif' alt='$Lang::tr{'updxlrtr last access'}' /></td>
    <td class='base' align='center'><img src='/images/updxl-globe.gif' alt='$Lang::tr{'updxlrtr last checkup'}' /></td>
    <td class='base' align='center'>&nbsp;</td>
</tr>
END
;
    $id = 0;
    foreach $updatefile (@files)
    {
        $updatefile =~ s/.*://;
        my $size_updatefile = 0;
        my $mtime = 0;
        if(-e "$UPDXLT::repository/$updatefile") {
            $size_updatefile = (-s "$UPDXLT::repository/$updatefile");
            $mtime = &getmtime("$UPDXLT::repository/$updatefile");
        }

       

        $filesize = $size_updatefile;
        1 while $filesize =~ s/^(-?\d+)(\d{3})/$1.$2/;

        my ($SECdt,$MINdt,$HOURdt,$DAYdt,$MONTHdt,$YEARdt) = localtime($mtime);
        $DAYdt   = sprintf ("%.02d",$DAYdt);
        $MONTHdt = sprintf ("%.02d",$MONTHdt+1);
        $YEARdt  = sprintf ("%.04d",$YEARdt+1900);
        $filedate = $YEARdt."-".$MONTHdt."-".$DAYdt;

        $lastaccess = "n/a";
        $lastcheck  = "n/a";
		$lastrawaccess = 0;
        $lastrawcheck  = 0;

        $status = $sfUnknown;

        unless ($updatefile =~ /^download\//)
        {
            ($vendorid,$uuid,$shortname) = split('/',$updatefile);

            if (-e "$UPDXLT::repository/$vendorid/$uuid/access.log")
            {
                open (FILE,"$UPDXLT::repository/$vendorid/$uuid/access.log");
                @metadata = <FILE>;
                close(FILE);
                chomp @metadata;

                ($SECdt,$MINdt,$HOURdt,$DAYdt,$MONTHdt,$YEARdt) = localtime($metadata[-1]);
                $DAYdt   = sprintf ("%.02d",$DAYdt);
                $MONTHdt = sprintf ("%.02d",$MONTHdt+1);
                $YEARdt  = sprintf ("%.04d",$YEARdt+1900);
                if (($metadata[-1] =~ /^\d+/) && ($metadata[-1] >= 1)) { $lastaccess = $YEARdt."-".$MONTHdt."-".$DAYdt; $lastrawaccess = $metadata[-1];}
            }
            if (-e "$UPDXLT::repository/$vendorid/$uuid/checkup.log")
            {
                open (FILE,"$UPDXLT::repository/$vendorid/$uuid/checkup.log");
                @metadata = <FILE>;
                close(FILE);
                chomp @metadata;

                ($SECdt,$MINdt,$HOURdt,$DAYdt,$MONTHdt,$YEARdt) = localtime($metadata[-1]);
                $DAYdt   = sprintf ("%.02d",$DAYdt);
                $MONTHdt = sprintf ("%.02d",$MONTHdt+1);
                $YEARdt  = sprintf ("%.04d",$YEARdt+1900);
                if (($metadata[-1] =~ /^\d+/) && ($metadata[-1] >= 1)) { $lastcheck = $YEARdt."-".$MONTHdt."-".$DAYdt; $lastrawcheck = $metadata[-1]; }
            }
            if (-e "$UPDXLT::repository/$vendorid/$uuid/status")
            {
                open (FILE,"$UPDXLT::repository/$vendorid/$uuid/status");
                @metadata = <FILE>;
                close(FILE);
                chomp @metadata;
                $status = $metadata[-1];
            }
        } else {
            ($uuid,$vendorid,$shortname) = split('/',$updatefile);
            $status = $sfOutdated;
        }
		
		push(@logfilelist, "$status $vendorid $updatefile $filesize $filedate $lastaccess $lastcheck $lastrawaccess $lastrawcheck $size_updatefile");
	}
	
	# 2014 - sort entry by user preferences
	if ($sortby eq 'LAST_ACCESS') {
	  @logfilelist = sort { (split ' ', $a)[7] <=> (split ' ', $b)[7] } @logfilelist;	
	} 
	elsif ($sortby eq 'LAST_CHECK') {
	  @logfilelist = sort { (split ' ', $a)[8] <=> (split ' ', $b)[8] } @logfilelist;	
	} 
	elsif ($sortby eq 'SIZE') {
	  @logfilelist = sort { (split ' ', $a)[9] <=> (split ' ', $b)[9] } @logfilelist;	
	}
	elsif ($sortby eq 'DATE') {
	  @logfilelist = sort { (split ' ', $a)[4] cmp (split ' ', $b)[4] } @logfilelist;	
	}
	elsif ($sortby eq 'VENDOR') {
	  @logfilelist = sort { (split ' ', $a)[1] cmp (split ' ', $b)[1] } @logfilelist;	
	}
	elsif ($sortby eq 'NAME') {
	  @logfilelist = sort { (split ' ', $a)[2] cmp (split ' ', $b)[2] } @logfilelist;	
	}
	elsif ($sortby eq 'STATUS') {
	  @logfilelist = sort { (split ' ', $a)[0] cmp (split ' ', $b)[0] } @logfilelist;	
	}
	
	if ($order eq 'DESC') { @logfilelist = reverse @logfilelist; }
	
	foreach $_ (@logfilelist) {
        my ($status, $vendorid, $updatefile, $filesize, $filedate, $lastaccess, $lastcheck) = split;
		 $id++;
        if ($id % 2) {
            print "<tr class='table1colour'>\n"; }
        else {
            print "<tr class='table2colour'>\n"; }
        print "\t\t<td align='center' nowrap='nowrap'>&nbsp;";
        if ($status == $sfUnknown)
        {
            print "<img src='/images/updxl-led-gray.gif' alt='$Lang::tr{'updxlrtr condition unknown'}' />&nbsp;</td>\n";
        }
        if ($status == $sfOk)
        {
            print "<img src='/images/updxl-led-green.gif' alt='$Lang::tr{'updxlrtr condition ok'}' />&nbsp;</td>\n";
        }
        if ($status == $sfNoSource)
        {
            print "<img src='/images/updxl-led-yellow.gif' alt='$Lang::tr{'updxlrtr condition nosource'}' />&nbsp;</td>\n";
        }
        if (($status == $sfOutdated) && (!($updatefile =~ /^download\//i)))
        {
            print "<img src='/images/updxl-led-red.gif' alt='$Lang::tr{'updxlrtr condition outdated'}' />&nbsp;</td>\n";
        }
        if (($status == $sfOutdated) && ($updatefile =~ /^download\//i))
        {
            print "<img src='/images/updxl-led-blue.gif' alt='$Lang::tr{'updxlrtr condition download'}' />&nbsp;</td>\n";
        }

        print "\t\t<td align='center' nowrap='nowrap'>&nbsp;";
        if ($vendorid =~ /^Adobe$/i)
        {
            print "<img src='/images/updxl-src-adobe.gif' alt='Adobe'}' />&nbsp;</td>\n";
        } elsif ($vendorid =~ /^Microsoft$/i)
        {
            print "<img src='/images/updxl-src-windows.gif' alt='Microsoft'}' />&nbsp;</td>\n";
        } elsif ($vendorid =~ /^Symantec$/i)
        {
            print "<img src='/images/updxl-src-symantec.gif' alt='Symantec'}' />&nbsp;</td>\n";
        } elsif ($vendorid =~ /^Linux$/i)
        {
            print "<img src='/images/updxl-src-linux.gif' alt='Linux'}' />&nbsp;</td>\n";
        } elsif ($vendorid =~ /^TrendMicro$/i)
        {
            print "<img src='/images/updxl-src-trendmicro.gif' alt='Trend Micro'}' />&nbsp;</td>\n";
        } elsif ($vendorid =~ /^Apple$/i)
        {
            print "<img src='/images/updxl-src-apple.gif' alt='Apple'}' />&nbsp;</td>\n";
        } elsif ($vendorid =~ /^Avast$/i)
        {
            print "<img src='/images/updxl-src-avast.gif' alt='Avast'}' />&nbsp;</td>\n";
        } else
        {
            if (-e "/home/httpd/html/images/updxl-src-" . $vendorid . ".gif")
            {
                print "<img src='/images/updxl-src-" . $vendorid . ".gif' alt='" . ucfirst $vendorid . "' />&nbsp;</td>\n";
            } else {
                print "<img src='/images/updxl-src-unknown.gif' alt='" . ucfirst $vendorid . "' />&nbsp;</td>\n";
            }
        }

        $shortname = substr($updatefile,rindex($updatefile,"/")+1);
        $shortname =~ s/(.*)_[\da-f]*(\.(exe|cab|psf)$)/$1_*$2/i;

        my $urlLocation =  "http://$ENV{'SERVER_ADDR'}:$http_port";

print <<END
        <td class='base' align='left' title='cache:/$updatefile'><a href="$urlLocation/updatecache/$updatefile">$shortname</a></td>
        <td class='base' align='right'  nowrap='nowrap'>&nbsp;$filesize&nbsp;</td>
        <td class='base' align='center' nowrap='nowrap'>&nbsp;$filedate&nbsp;</td>
        <td class='base' align='center' nowrap='nowrap'>&nbsp;$lastaccess&nbsp;</td>
        <td class='base' align='center' nowrap='nowrap'>&nbsp;$lastcheck&nbsp;</td>
        <td align='center'>
        <form method='post' name='frma$id' action='$ENV{'SCRIPT_NAME'}'>
        <input type='image' name='$Lang::tr{'updxlrtr remove file'}' src='/images/delete.gif' title='$Lang::tr{'updxlrtr remove file'}' alt='$Lang::tr{'updxlrtr remove file'}' />
        <input type='hidden' name='ID' value='$updatefile' />
        <input type='hidden' name='ACTION' value='$Lang::tr{'updxlrtr remove file'}' />
        </form>
        </td>
    </tr>
END
;
    }

    print "</table>\n";

}

# -------------------------------------------------------------------

sub printlegenddownload
{
    print <<END
    <tr>
        <td class='boldbase'>&nbsp; <b>$Lang::tr{'legend'}:</b></td>
        <td class='base'>&nbsp;</td>
        <td><img src='/images/updxl-led-blue.gif' alt='$Lang::tr{'updxlrtr condition download'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr condition download'}</td>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
        <td><img src='/images/updxl-led-gray.gif' alt='$Lang::tr{'updxlrtr condition suspended'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr condition suspended'}</td>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
        <td><img src='/images/delete.gif' alt='$Lang::tr{'updxlrtr cancel download'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr cancel download'}</td>
    </tr>
END
;
}

# -------------------------------------------------------------------

sub printlegendicons
{
    print <<END
    <tr>
        <td class='boldbase'>&nbsp; <b>$Lang::tr{'legend'}:</b></td>
        <td class='base'>&nbsp;</td>
        <td><img src='/images/reload.gif' alt='$Lang::tr{'updxlrtr last access'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr last access'}</td>
        <td class='base'>&nbsp;</td>
        <td><img src='/images/updxl-globe.gif' alt='$Lang::tr{'updxlrtr last checkup'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr last checkup'}</td>
        <td class='base'>&nbsp;</td>
        <td><img src='/images/delete.gif' alt='$Lang::tr{'updxlrtr remove file'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr remove file'}</td>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
    </tr>
END
;
}

# -------------------------------------------------------------------

sub printlegendstatus
{
    print <<END
    <tr>
        <td class='base'>&nbsp; $Lang::tr{'status'}:</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-led-green.gif' alt='$Lang::tr{'updxlrtr condition ok'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr condition ok'}</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-led-yellow.gif' alt='$Lang::tr{'updxlrtr condition nosource'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr condition nosource'}</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-led-red.gif' alt='$Lang::tr{'updxlrtr condition outdated'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr condition outdated'}</td>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
    </tr>
    <tr>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-led-blue.gif' alt='$Lang::tr{'updxlrtr condition download'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr condition download'}</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-led-gray.gif' alt='$Lang::tr{'updxlrtr condition unknown'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr condition unknown'}</td>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
    </tr>
END
;
}

# -------------------------------------------------------------------

sub printlegendsource
{
    print <<END
    <tr>
        <td class='base'>&nbsp; $Lang::tr{'updxlrtr source'}:</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-src-adobe.gif' alt='Adobe' /></td>
        <td class='base'>Adobe</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-src-apple.gif' alt='Apple' /></td>
        <td class='base'>Apple</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-src-avast.gif' alt='Avast' /></td>
        <td class='base'>Avast</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-src-linux.gif' alt='Linux' /></td>
        <td class='base'>Linux</td>
    </tr>
    <tr>
        <td colspan='13'></td>
    </tr>
    <tr>
        <td class='base'>&nbsp;</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-src-windows.gif' alt='Microsoft' /></td>
        <td class='base'>Microsoft</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-src-symantec.gif' alt='Symantec' /></td>
        <td class='base'>Symantec</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-src-trendmicro.gif' alt='Trend Micro' /></td>
        <td class='base'>Trend Micro</td>
        <td class='base'>&nbsp;</td>
        <td align='center'><img src='/images/updxl-src-unknown.gif' alt='$Lang::tr{'updxlrtr other'}' /></td>
        <td class='base'>$Lang::tr{'updxlrtr other'}</td>
    </tr>
END
;
}

# -------------------------------------------------------------------

sub printlegendspacer
{
    print <<END
    <tr>
        <td colspan='13'>&nbsp;<br></td>
    </tr>
END
;
}

# -------------------------------------------------------------------

sub checkForNewVersion
{
	# download latest version
	&downloadLatestVersionInfo();

	if(-e $latestVersionFile)
	{
		my %versionSettings = ();
		&General::readhash($versionfile, \%versionSettings);

		my %latestVersion = ();
		&General::readhash($latestVersionFile, \%latestVersion);

		if($versionSettings{'VERSION_INSTALLED'} lt $latestVersion{'VERSION_AVAILABLE'})
		{
			&Header::openbox('100%', 'left', $Lang::tr{'info'});
            my $msg = $Lang::tr{'updxlrtr update information'};
            $msg =~ s@__URL_UPDATE__@$latestVersion{'URL_UPDATE'}@g;

			print <<END;
				<table width="100%">
				<tr>
					<td>
						$msg
					</td>
				</tr>
				</table>
END

			&Header::closebox();
		}
	}
}


# -------------------------------------------------------------------

sub downloadLatestVersionInfo
{
    # only check if we are online
	if (! -e '/var/ipcop/red/active')
	{
		return;
	}

	# download latest version file if it is not existing or outdated (i.e. 5 days old)
	if((! -e $latestVersionFile) || (int(-M $latestVersionFile) > 5))
	{
		my %versionSettings = ();
		&General::readhash($versionfile, \%versionSettings);

		my $ua = LWP::UserAgent->new;
		$ua->timeout(120);
		$ua->agent("Mozilla/4.0 (compatible; IPCop $General::version; Update Accelerator $versionSettings{'VERSION_INSTALLED'})");
		my $content = $ua->get($updateUrl);

		if ( $content->is_success )
		{
			my %latestVersion = ();

			# latest versions, format is: MOD_VERSION="2.2.1"
			$content->content =~ /MOD_VERSION="(.+?)"/;
			$latestVersion{'VERSION_AVAILABLE'} = $1;

			# URL format is: MOD_URL="http://blockouttraffic.de/..."
			$content->content =~ /MOD_URL="(.+?)"/;
			$latestVersion{'URL_UPDATE'} = $1;

			&General::writehash($latestVersionFile, \%latestVersion);
		}
	}
}

# -------------------------------------------------------------------

sub savesettings
{
    if($xlratorsettings{'ENABLED'} ne 'on') {
        $xlratorsettings{'ENABLED'} = 'off';
    }

    if (-e $chk_cron_dly) { unlink($chk_cron_dly); }
    if (-e $chk_cron_wly) { unlink($chk_cron_wly); }
    if (-e $chk_cron_mly) { unlink($chk_cron_mly); }

    if (($xlratorsettings{'ENABLE_AUTOCHECK'} eq 'on') && ($xlratorsettings{'AUTOCHECK_SCHEDULE'} eq 'daily'))
    {
        symlink("../bin/checkup",$chk_cron_dly)
    } else {
        symlink("/bin/false",$chk_cron_dly)
    }
        if (($xlratorsettings{'ENABLE_AUTOCHECK'} eq 'on') && ($xlratorsettings{'AUTOCHECK_SCHEDULE'} eq 'weekly'))
    {
        symlink("../bin/checkup",$chk_cron_wly)
    } else {
        symlink("/bin/false",$chk_cron_wly)
    }
        if (($xlratorsettings{'ENABLE_AUTOCHECK'} eq 'on') && ($xlratorsettings{'AUTOCHECK_SCHEDULE'} eq 'monthly'))
    {
        symlink("../bin/checkup",$chk_cron_mly)
    } else {
        symlink("/bin/false",$chk_cron_mly)
    }

    # don't save those variable to the settings file,
    # but we wan't to have them in the hash again after saving to file
    my $obsolete = $xlratorsettings{'REMOVE_OBSOLETE'};
    my $nosource = $xlratorsettings{'REMOVE_NOSOURCE'};
    my $outdated = $xlratorsettings{'REMOVE_OUTDATED'};
    my $gui = $xlratorsettings{'EXTENDED_GUI'};

    delete($xlratorsettings{'REMOVE_OBSOLETE'});
    delete($xlratorsettings{'REMOVE_NOSOURCE'});
    delete($xlratorsettings{'REMOVE_OUTDATED'});

    delete($xlratorsettings{'EXTENDED_GUI'});

    &General::writehash("/var/ipcop/addons/updatexlrator/settings", \%xlratorsettings);

    # put temp variables back into the hash
    $xlratorsettings{'REMOVE_OBSOLETE'} = $obsolete;
    $xlratorsettings{'REMOVE_NOSOURCE'} = $nosource;
    $xlratorsettings{'REMOVE_OUTDATED'} = $outdated;
    $xlratorsettings{'EXTENDED_GUI'} = $gui;


    # write redirector config
    my %redirectorconf=();
    $redirectorconf{'NAME'} = "$Lang::tr{'updxlrtr update accelerator'}";
    $redirectorconf{'ORDER'} = 20;
    $redirectorconf{'CMD'} = '/usr/sbin/updxlrator';
    $redirectorconf{'ENABLED'} = $xlratorsettings{'ENABLED'};

    &General::writehash("/var/ipcop/proxy/redirector/updatexlrator", \%redirectorconf);

    system('/usr/local/bin/restartsquid --config');
}

# -------------------------------------------------------------------

sub percentbar
{
  my $percent = $_[0];
  my $fg = '#a0a0a0';
  my $bg = '#e2e2e2';

  if ($percent =~ m/^(\d+)%$/ )
  {
    print <<END
<table width='100' border='1' cellspacing='0' cellpadding='0' style='border-width:1px;border-style:solid;border-color:$fg;width:100px;height:10px;'>
<tr>
END
;
    if ($percent eq "100%") {
      print "<td width='100%' bgcolor='$fg' style='background-color:$fg;border-style:solid;border-width:1px;border-color:$bg'>"
    } elsif ($percent eq "0%") {
      print "<td width='100%' bgcolor='$bg' style='background-color:$bg;border-style:solid;border-width:1px;border-color:$bg'>"
    } else {
      print "<td width='$percent' bgcolor='$fg' style='background-color:$fg;border-style:solid;border-width:1px;border-color:$bg'></td><td width='" . (100-$1) . "%' bgcolor='$bg' style='background-color:$bg;border-style:solid;border-width:1px;border-color:$bg'>"
    }
    print <<END
<img src='/images/null.gif' width='1' height='1' alt='' /></td></tr></table>
END
;
  }
}

# -------------------------------------------------------------------

sub getmtime
{
    my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($_[0]);

    return $mtime;
}

# -------------------------------------------------------------------

sub getPID
{
    my $pid='';
    my @psdata=`ps ax --no-heading`;

    foreach (@psdata){
        if (/$_[0]/) {
            ($pid)=/^\s*(\d+)/;
        }
    }

    return $pid;
}

# -------------------------------------------------------------------
