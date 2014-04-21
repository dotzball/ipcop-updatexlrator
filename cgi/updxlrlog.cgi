#!/usr/bin/perl
#
# This code is distributed under the terms of the GPL
#
# (c) 2013,2014 umberto.miceli http://joeyramone76.altervista.org
#
# $Id: updxlrlog.cgi,v 1.0.1 2014/03/08 00:00:00 umberto.miceli Exp $
#

# Add entry in menu
# MENUENTRY logs 034 "Update Accelerator Logs" "updxlrlog log"  haveProxy
#
# Make sure translation exists $Lang::tr{'updxlrlog log'}

use strict;

# enable only the following on debugging purpose
use warnings;
use CGI::Carp 'fatalsToBrowser';
use IO::Socket;

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';
require '/usr/lib/ipcop/header.pl';

require '/var/ipcop/addons/updatexlrator/updxlrator-lib.pl';

use POSIX();

my $logdir = "/var/log/updatexlrator";



my %cgiparams    = ();
my %logsettings  = ();
my %ips          = ();
my %responsecodes = ();
my %vendors      = ();
my %selected     = ();
my %checked      = ();
my @log          = ();
my $errormessage = '';
my $hintcolour='#FFFFCC';

my $unique=time;

my @now  = localtime();
my $dow  = $now[6];          # day of week
my $doy  = $now[7];          # day of year (0..364)
my $tdoy = $now[7];
my $year = $now[5] + 1900;

my %columnsortedclass = ();

my %debug = ();

$cgiparams{'DAY'}           = $now[3];
$cgiparams{'MONTH'}         = $now[4];
$cgiparams{'SOURCE_IP'}     = 'ALL';
$cgiparams{'RESPONSE_CODE'}     = 'ALL';
$cgiparams{'VENDOR'}     = 'ALL';
$cgiparams{'FILTER'}        = "";
$cgiparams{'ENABLE_FILTER'} = 'off';
$cgiparams{'INCLUDE_FILTER'}        = "";
$cgiparams{'ENABLE_INCLUDE_FILTER'} = 'off';
$cgiparams{'SORT_BY'}     = 'DATE';
$cgiparams{'ORDER'}     = 'ASC';
$cgiparams{'ACTION'}        = '';
$cgiparams{'FULL_URL'} = 'off';
$cgiparams{'MEASURES_RAW'} = 'off';

&General::getcgihash(\%cgiparams);
$logsettings{'LOGVIEW_REVERSE'}  = 'off';
$logsettings{'LOGVIEW_VIEWSIZE'} = 150;
&General::readhash('/var/ipcop/logging/settings', \%logsettings);



if ($cgiparams{'ACTION'} eq '') {
    my %save = ();
    &General::readhash('/var/ipcop/addons/updatexlrator/viewersettings', \%save)  if (-e '/var/ipcop/addons/updatexlrator/viewersettings');
    $cgiparams{'FILTER'}        = $save{'FILTER'}        if (exists($save{'FILTER'}));
    $cgiparams{'ENABLE_FILTER'} = $save{'ENABLE_FILTER'} if (exists($save{'ENABLE_FILTER'}));

	$cgiparams{'INCLUDE_FILTER'}        = $save{'INCLUDE_FILTER'}        if (exists($save{'INCLUDE_FILTER'}));
    $cgiparams{'ENABLE_INCLUDE_FILTER'} = $save{'ENABLE_INCLUDE_FILTER'} if (exists($save{'ENABLE_INCLUDE_FILTER'}));

	$cgiparams{'SORT_BY'} = $save{'SORT_BY'} if (exists($save{'SORT_BY'}));
	$cgiparams{'ORDER'} = $save{'ORDER'} if (exists($save{'ORDER'}));

	$cgiparams{'FULL_URL'} = $save{'FULL_URL'} if (exists($save{'FULL_URL'}));
	$cgiparams{'MEASURES_RAW'} = $save{'MEASURES_RAW'} if (exists($save{'MEASURES_RAW'}));
}

if ($cgiparams{'ACTION'} eq $Lang::tr{'restore defaults'}) {
    $cgiparams{'SOURCE_IP'}     = 'ALL';
	$cgiparams{'RESPONSE_CODE'}     = 'ALL';
	$cgiparams{'VENDOR'}     = 'ALL';
    $cgiparams{'FILTER'}        = "[.](gif|jpeg|jpg|png|css|js)\$";
    $cgiparams{'ENABLE_FILTER'} = 'on';
	$cgiparams{'INCLUDE_FILTER'}        = "";
    $cgiparams{'ENABLE_INCLUDE_FILTER'} = 'off';
	$cgiparams{'SORT_BY'}     = 'DATE';
	$cgiparams{'ORDER'}     = 'ASC';
	$cgiparams{'FULL_URL'}     = 'off';
	$cgiparams{'MEASURES_RAW'}     = 'off';


}

if ($cgiparams{'ACTION'} eq $Lang::tr{'save'}) {
    my %save = ();
    $save{'FILTER'}        = $cgiparams{'FILTER'};
    $save{'ENABLE_FILTER'} = $cgiparams{'ENABLE_FILTER'};
	$save{'INCLUDE_FILTER'}        = $cgiparams{'INCLUDE_FILTER'};
    $save{'ENABLE_INCLUDE_FILTER'} = $cgiparams{'ENABLE_INCLUDE_FILTER'};
	$save{'SORT_BY'} = $cgiparams{'SORT_BY'};
	$save{'ORDER'} = $cgiparams{'ORDER'};
	$save{'FULL_URL'} = $cgiparams{'FULL_URL'};
	$save{'MEASURES_RAW'} = $cgiparams{'MEASURES_RAW'};;

    &General::writehash('/var/ipcop/addons/updatexlrator/viewersettings', \%save);
}

#my $start = ($cgiparams{'ORDER'} eq 'DESC') ? 0x7FFFF000 : 0;    #index of first line number to display
my $start = 0;


my @temp_then = ();
if ($ENV{'QUERY_STRING'} && $cgiparams{'ACTION'} ne $Lang::tr{'update'}) {
    @temp_then = split(',', $ENV{'QUERY_STRING'});
    $start                  = $temp_then[0];
    $cgiparams{'MONTH'}     = $temp_then[1];
    $cgiparams{'DAY'}       = $temp_then[2];
    $cgiparams{'SOURCE_IP'} = $temp_then[3];
	$cgiparams{'RESPONSE_CODE'} = $temp_then[4];
	$cgiparams{'VENDOR'} = $temp_then[5];
	$cgiparams{'SORT_BY'} = $temp_then[6];
	$cgiparams{'ORDER'} = $temp_then[7];
	$cgiparams{'FULL_URL'} = $temp_then[8];
	$cgiparams{'ENABLE_FILTER'} = $temp_then[9];
	$cgiparams{'FILTER'} = $temp_then[10];
	$cgiparams{'ENABLE_INCLUDE_FILTER'} = $temp_then[11];
	$cgiparams{'INCLUDE_FILTER'} = $temp_then[12];



}

if (!($cgiparams{'MONTH'} =~ /^(0|1|2|3|4|5|6|7|8|9|10|11)$/)
    || !($cgiparams{'DAY'} =~
        /^(0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31)$/))
{
    $cgiparams{'DAY'}   = $now[3];
    $cgiparams{'MONTH'} = $now[4];
}
elsif ($cgiparams{'ACTION'} eq '>>') {
    @temp_then = &General::calculatedate($year, $cgiparams{'MONTH'}, $cgiparams{'DAY'}, 1);
    $year               = $temp_then[5]+1900;
    $cgiparams{'MONTH'} = $temp_then[4];
    $cgiparams{'DAY'}   = $temp_then[3];
}
elsif ($cgiparams{'ACTION'} eq '<<') {
    @temp_then = &General::calculatedate($year, $cgiparams{'MONTH'}, $cgiparams{'DAY'}, -1);
    $year               = $temp_then[5]+1900;
    $cgiparams{'MONTH'} = $temp_then[4];
    $cgiparams{'DAY'}   = $temp_then[3];
}
else {
    @temp_then = &General::validatedate(0, $cgiparams{'MONTH'}, $cgiparams{'DAY'});
    $year               = $temp_then[5]+1900;
    $cgiparams{'MONTH'} = $temp_then[4];
    $cgiparams{'DAY'}   = $temp_then[3];
}

# Date to display
my $date;
$date = sprintf("%d-%02d-%02d", $year, $cgiparams{'MONTH'}+1, $cgiparams{'DAY'});

my $filter    = $cgiparams{'ENABLE_FILTER'} eq 'on' ? $cgiparams{'FILTER'} : '';
my $enablefilter  = $cgiparams{'ENABLE_FILTER'} eq 'on' ? 1 : 0;
my $includefilter = $cgiparams{'ENABLE_INCLUDE_FILTER'} eq 'on' ? $cgiparams{'INCLUDE_FILTER'} : '';
my $enableincludefilter  = $cgiparams{'ENABLE_INCLUDE_FILTER'} eq 'on' ? 1 : 0;
my $fullurl = $cgiparams{'FULL_URL'} eq 'on' ? 1 : 0;
my $measuresraw = $cgiparams{'MEASURES_RAW'} eq 'on' ? 1 : 0;

my $sourceip  = $cgiparams{'SOURCE_IP'};
my $sourceall = $cgiparams{'SOURCE_IP'} eq 'ALL' ? 1 : 0;

my $responsecode  = $cgiparams{'RESPONSE_CODE'};
my $responseall = $cgiparams{'RESPONSE_CODE'} eq 'ALL' ? 1 : 0;

my $vendor  = $cgiparams{'VENDOR'};
my $vendorall = $cgiparams{'VENDOR'} eq 'ALL' ? 1 : 0;

my $sortby = $cgiparams{'SORT_BY'};
my $order = $cgiparams{'ORDER'};
my $lastdatetime;    # for debug
my $lines    = 0;
my $continueflag = 1;

if(defined $filter) {
	my $temp     = "";
	my $thiscode = '$temp =~ /$filter/;';
	eval($thiscode);
	if ($@ ne '') {
		$errormessage = "$Lang::tr{'bad ignore filter'}:.$@<P>";
		$filter       = '';
		$continueflag = 0;
	}
}

if(defined $includefilter) {
	my $temp2     = "";
	my $thiscode2 = '$temp2 =~ /$includefilter/;';
	eval($thiscode2);
	if ($@ ne '') {
		$errormessage = "$Lang::tr{'bad ignore filter'}:.$@<P>";
		$includefilter       = '';
		$continueflag = 0;
	}
}
if ($continueflag)
 {
    my $loop    = 1;
    my $filestr = 0;

    my $day_extension = ($cgiparams{'DAY'} == 0 ? 1: $cgiparams{'DAY'});

    while ($loop) {

        my $gzindex;
        if (($cgiparams{'MONTH'} eq $now[4]) && ($day_extension eq $now[3])) {
            $filestr = "$logdir/cache.log";
            $loop = 0;
        }
        else {
            $filestr = sprintf("$logdir/cache.log-%d%02d%02d", $year, $cgiparams{'MONTH'}+1, $day_extension);
            $filestr = "${filestr}.gz" if -f "${filestr}.gz";
        }

        # now read file if existing
        if (open(FILE, ($filestr =~ /.gz$/ ? "gzip -dc $filestr |" : $filestr))) {

			#&General::log("reading $filestr");
            my @temp_now = localtime(time);
            $temp_now[4] = $cgiparams{'MONTH'};
            $temp_now[3] = $cgiparams{'DAY'};
            if (   ($cgiparams{'MONTH'} eq $now[4]) && ($cgiparams{'DAY'} > $now[3])
                || ($cgiparams{'MONTH'} > $now[4]))
            {
                $temp_now[5]--;    # past year
            }

            $temp_now[2] = $temp_now[1] = $temp_now[0] = 0;    # start at 00:00:00
            $temp_now[3] = 1 if ($cgiparams{'DAY'} == 0);      # All days selected, start at '1'
            my $mintime = POSIX::mktime(@temp_now);
            my $maxtime;
            if ($cgiparams{'DAY'} == 0) {                      # full month
                if ($temp_now[4]++ == 12) {
                    $temp_now[4] = 0;
                    $temp_now[5]++;
                }
                $maxtime = POSIX::mktime(@temp_now);
            }
            else {
                $maxtime = $mintime + 86400;                   # full day
            }
        READ: while (<FILE>) {
                my ($datetime, $ip, $username, $vendorname, $result, $url, $size) = split;
				$ip =~ tr/\/-//d;



                # for debug
                $lastdatetime = $datetime;
				my $testpassed = 0;
                # collect lines between date && filter
                if (   (($datetime > $mintime) && ($datetime < $maxtime))
                    && ((!$enablefilter) || (($enablefilter) && !($url =~ /$filter/)))
                    && ((($ip eq $sourceip) || $sourceall))
					&& ((($vendorname eq $vendor) || $vendorall))
					&& ((($result eq $responsecode) || $responseall))
					&& ((($url =~ /$includefilter/) || ($includefilter eq "")))
					)

                {
						$ips{$ip}++;
						$responsecodes{$result}++;
						$vendors{$vendorname}++;


						# when standart viewing, just keep in memory the correct slices
						# it starts a '$start' and size is $viewport
						# If export, then keep all lines...
						if ($cgiparams{'ACTION'} eq $Lang::tr{'export'}) {
							$log[ $lines++ ] = "$datetime $ip $vendorname $result $url $username $size";
						}
						else {
						    $lines++;
							push(@log, "$datetime $ip $vendorname $result $url $username $size");
						}

                }

                # finish loop when date of lines are past maxtime
                $loop = ($datetime < $maxtime);
            }
            close(FILE);
			#close (TMPLOG);
        }
        $day_extension++;
        if ($day_extension > 31) {
            $loop = 0;
        }
    }

}

if ($cgiparams{'ACTION'} eq $Lang::tr{'export'}) {
    print "Content-type: text/plain\n";
    print "Content-Disposition: attachment; filename=\"ipcop-updxlrlog-$date.log\";\n";
    print "\n";
    print "IPCop Update Accelerator Log\r\n";
    print "$Lang::tr{'date'}: $date\r\n";
    print "Source IP: $cgiparams{'SOURCE_IP'}\r\n";
    if ($cgiparams{'ENABLE_FILTER'} eq 'on') {
        print "Ignore filter: $cgiparams{'FILTER'}\r\n";
    }
	if ($cgiparams{'ENABLE_INCLUDE_FILTER'} eq 'on') {
        print "Include filter: $cgiparams{'INCLUDE_FILTER'}\r\n";
    }
	print "Response Code Filter: $cgiparams{'RESPONSE_CODE'}\r\n";
	print "Sorted By: $cgiparams{'SORT_BY'}\r\n";
    print "\r\n";

    # Do not reverse log when exporting
    #if ($logsettings{'LOGVIEW_REVERSE'} eq 'on') { @log = reverse @log; }

    foreach $_ (@log) {
        my ($datetime, $ip, $vendor, $result, $url, $username) = split;
        my ($SECdt, $MINdt, $HOURdt, $DAYdt, $MONTHdt, $YEARdt) = localtime($datetime);
        $SECdt  = sprintf("%.02d", $SECdt);
        $MINdt  = sprintf("%.02d", $MINdt);
        $HOURdt = sprintf("%.02d", $HOURdt);
        if ($cgiparams{'DAY'} == 0) {    # full month
            $DAYdt = sprintf("%.02d", $DAYdt);
            print "$DAYdt/$HOURdt:$MINdt:$SECdt $ip $vendor $result $url\n";
        }
        else {
            print "$HOURdt:$MINdt:$SECdt $ip $vendor $result $url\n";
        }
    }
    exit;
}

$selected{'SOURCE_IP'}{$cgiparams{'SOURCE_IP'}} = "selected='selected'";
$selected{'RESPONSE_CODE'}{$cgiparams{'RESPONSE_CODE'}} = "selected='selected'";
$selected{'VENDOR'}{$cgiparams{'VENDOR'}} = "selected='selected'";
$checked{'ENABLE_FILTER'}{'off'}                       = '';
$checked{'ENABLE_FILTER'}{'on'}                        = '';
$checked{'ENABLE_FILTER'}{$cgiparams{'ENABLE_FILTER'}} = "checked='checked'";

$checked{'ENABLE_INCLUDE_FILTER'}{'off'}                       = '';
$checked{'ENABLE_INCLUDE_FILTER'}{'on'}                        = '';
$checked{'ENABLE_INCLUDE_FILTER'}{$cgiparams{'ENABLE_INCLUDE_FILTER'}} = "checked='checked'";

$selected{'SORT_BY'}{$cgiparams{'SORT_BY'}} = "selected='selected'";
$selected{'ORDER'}{$cgiparams{'ORDER'}} = "selected='selected'";

$checked{'FULL_URL'}{'off'}                       = '';
$checked{'FULL_URL'}{'on'}                        = '';
$checked{'FULL_URL'}{$cgiparams{'FULL_URL'}} = "checked='checked'";

$checked{'MEASURES_RAW'}{'off'}                       = '';
$checked{'MEASURES_RAW'}{'on'}                        = '';
$checked{'MEASURES_RAW'}{$cgiparams{'MEASURES_RAW'}} = "checked='checked'";


&Header::showhttpheaders();

&Header::openpage($Lang::tr{'proxy log viewer'}, 1, '');

&Header::openbigbox('100%', 'left', '');

if ($errormessage) {
    &Header::openbox('100%', 'left', "$Lang::tr{'error messages'}:", 'error');
    print "<font class='base'>$errormessage&nbsp;</font>\n";
    &Header::closebox();
}


# ------------------------------------------------------------------

&Header::openbox('100%', 'left', "$Lang::tr{'settings'}:");

print <<END
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<table width='100%'>
<tr>
	<td width='50%' class='base' nowrap='nowrap'>$Lang::tr{'month'}:&nbsp;
	<select name='MONTH'>
END
    ;
for (my $month = 0; $month < 12; $month++) {
    print "\t<option ";
    if ($month == $cgiparams{'MONTH'}) {
        print "selected='selected' ";
    }
    print "value='$month'>$Lang::tr{$General::longMonths[$month]}</option>\n";
}
print <<END
	</select>
	&nbsp;&nbsp;$Lang::tr{'day'}:&nbsp;
	<select name='DAY'>
END
    ;
print "<option value='0'>$Lang::tr{'all'}</option>";
for (my $day = 1; $day <= 31; $day++) {
    print "\t<option ";
    if ($day == $cgiparams{'DAY'}) {
        print "selected='selected' ";
    }
    print "value='$day'>$day</option>\n";
}
print <<END
	</select>
	</td>
	<td width='45%'  align='center'>

	</td>
    <td class='onlinehelp'>
        <!-- <a href='${General::adminmanualurl}/logs-proxy.html' target='_blank'><img src='/images/web-support.png' alt='$Lang::tr{'online help en'}' title='$Lang::tr{'online help en'}' /></a> -->
    </td>
</tr>
</table>
<hr />
<table width='100%' border='0'>
<tr>
	<td colspan='4' class='base'><b>$Lang::tr{'updxlrlog options'}:</b></td>
</tr>
<tr>
	<td  style='width:30%;' class='base'>$Lang::tr{'source ip'}:</td>
	<td  style='width:15%;'>
	<select name='SOURCE_IP'>
	<option value='ALL' $selected{'SOURCE_IP'}{'ALL'}>$Lang::tr{'caps all'}</option>
END
    ;
if (%ips) {
	foreach my $ip (keys %ips) {
		if (defined $ip) {
			print "<option value='$ip' $selected{'SOURCE_IP'}{$ip}>$ip</option>\n";
		}
	}
}
print <<END
	</select>
	</td>
	<td style='width:30%;' class='base'>Response Code:</td>
	<td style='width:25%;'>
	<select name='RESPONSE_CODE'>
	<option value='ALL' $selected{'RESPONSE_CODE'}{'ALL'}>$Lang::tr{'caps all'}</option>
END
    ;
if (%responsecodes) {
	foreach my $responsecode (keys %responsecodes) {
		print "<option value='$responsecode' $selected{'RESPONSE_CODE'}{$responsecode}>$responsecode</option>\n";
	}
}
print <<END
	</select>
	</td>
</tr>



<tr>
	<td  style='width:30%;' class='base'>Vendor:</td>
	<td  style='width:15%;'>
	<select name='VENDOR'>
	<option value='ALL' $selected{'VENDOR'}{'ALL'}>$Lang::tr{'caps all'}</option>
END
    ;
if (%vendors) {
	foreach my $vendor (keys %vendors) {
		if ($vendor) {
			print "<option value='$vendor' $selected{'VENDOR'}{$vendor}>$vendor</option>\n";
		}
	}
}
print <<END
	</select>
	</td>
	<td style='width:30%;' class='base'></td>
	<td style='width:25%;'>
	</td>
</tr>


<tr>
	<td class='base'>$Lang::tr{'enable ignore filter'}:</td>
	<td><input type='checkbox' name='ENABLE_FILTER' value='on' $checked{'ENABLE_FILTER'}{'on'} /></td>
	<td class='base'>$Lang::tr{'ignore filter'}:</td>
	<td><input type='text' name='FILTER' value='$cgiparams{'FILTER'}' size='40' /></td>
</tr>
<tr>
	<td class='base'>$Lang::tr{'updxlrlog enable match criteria'}:</td>
	<td><input type='checkbox' name='ENABLE_INCLUDE_FILTER' value='on' $checked{'ENABLE_INCLUDE_FILTER'}{'on'} /></td>
	<td class='base'>$Lang::tr{'updxlrlog match criteria'}:</td>
	<td><input type='text' name='INCLUDE_FILTER' value='$cgiparams{'INCLUDE_FILTER'}' size='40' /></td>
</tr>

<tr>
	<td class='base'>$Lang::tr{'updxlrlog full url'}:</td>
	<td><input type='checkbox' name='FULL_URL' value='on' $checked{'FULL_URL'}{'on'} /></td>
	<td class='base'>$Lang::tr{'updxlrlog measures raw'}:</td>
	<td><input type='checkbox' name='MEASURES_RAW' value='on' $checked{'MEASURES_RAW'}{'on'} /></td>
</tr>

</table>

<hr />
<table width='100%' border='0'>
<tr>
	<td colspan='4' class='base'><b>$Lang::tr{'updxlrlog sorting options'}</b></td>
</tr>
<tr>
	<td  style='width:30%;' class='base'>$Lang::tr{'updxlrlog sort by'}:</td>
	<td  style='width:15%;'>
	 <select name='SORT_BY'>
		<option value='DATE' $selected{'SORT_BY'}{'DATE'}>$Lang::tr{'updxlrlog sort by date'}</option>
		<option value='RESULT' $selected{'SORT_BY'}{'RESULT'}>$Lang::tr{'updxlrlog sort by result code'}</option>
		<option value='VENDOR' $selected{'SORT_BY'}{'VENDOR'}>Vendor</option>
		<option value='SIZE' $selected{'SORT_BY'}{'SIZE'}>$Lang::tr{'updxlrlog sort by size'}</option>
		<option value='URL' $selected{'SORT_BY'}{'URL'}>$Lang::tr{'updxlrlog sort by url'}</option>
	 </select>
	<td>
	<td style='width:30%;' class='base'>$Lang::tr{'updxlrlog order'}:</td>
	<td style='width:25%;'>
		<select name='ORDER'>
		<option value='ASC' $selected{'ORDER'}{'ASC'}>$Lang::tr{'updxlrlog order asc'}</option>
		<option value='DESC' $selected{'ORDER'}{'DESC'}>$Lang::tr{'updxlrlog order desc'}</option>
	 </select>
	</td>
</tr>
</table>

<hr />
<table width='100%' border='0'>
<tr>
	<td width='45%'  align='center'>
		<input type='submit' name='ACTION' title='$Lang::tr{'day before'}' value='&lt;&lt;' />
		<input type='submit' name='ACTION' title='$Lang::tr{'day after'}' value='&gt;&gt;' />
		<input type='submit' name='ACTION' value='$Lang::tr{'update'}' />
		<input type='submit' name='ACTION' value='$Lang::tr{'export'}' />
	</td>
	<td width='55%' align='right'>
		<input type='submit' name='ACTION' value='$Lang::tr{'restore defaults'}' />&nbsp;
		<input type='submit' name='ACTION' value='$Lang::tr{'save'}' />
	</td>
	<td width='5%' align='right'>&nbsp;</td>
</tr>
<tr>
 <td colspan="2" align='right'><sup><small>Updxlrlog</small></sup></td>
 <td width='5%' align='right'>&nbsp;</td>
</tr>
</table>
</form>
END
    ;

%columnsortedclass = ("DATE"   => "boldbase",
					 "RESULT" => "boldbase",
					 "VENDOR" => "boldbase",
					 "DURATION_SIZE" => "boldbase",
					 "SIZE" => "boldbase",
					 "URL" => "boldbase"
);

$columnsortedclass{$sortby} = "ipcop_StatusBigRed";

# sort the @log based on user choices - select the column text color for ordered item

# sort by date?	Do nothing!

# sort by vendor?
if ($sortby eq 'VENDOR')
{
	@log = sort { (split ' ', $a)[2] <=> (split ' ', $b)[2] } @log ;
}
# sort by size?
elsif ($sortby eq 'SIZE') {
	@log = sort { (split ' ', $a)[6] <=> (split ' ', $b)[6] } @log ;
}
# sort by result?
elsif ($sortby eq 'RESULT')
{
	@log = sort { (split ' ', $a)[3] cmp (split ' ', $b)[3] } @log;
}

# sort by url?
elsif ($sortby eq 'URL') {
	@log = sort { (split ' ', $a)[4] cmp (split ' ', $b)[4] } @log ;
} else {
	$columnsortedclass{'DATE'} = "ipcop_StatusBigRed";
}

if ($order eq 'DESC') { @log = reverse @log; }

    #$errormessage="$errormessage$Lang::tr{'date not in logs'}: $filestr $Lang::tr{'could not be opened'}";
    if (0) {           # print last date record read
        my ($SECdt, $MINdt, $HOURdt, $DAYdt, $MONTHdt, $YEARdt) = localtime($lastdatetime);
        $SECdt   = sprintf("%.02d", $SECdt);
        $MINdt   = sprintf("%.02d", $MINdt);
        $HOURdt  = sprintf("%.02d", $HOURdt);
        $DAYdt   = sprintf("%.02d", $DAYdt);
        $MONTHdt = sprintf("%.02d", $MONTHdt + 1);
        $YEARdt  = sprintf("%.04d", $YEARdt + 1900);
        &General::log("$HOURdt:$MINdt:$SECdt, $DAYdt/$MONTHdt/$YEARdt--");
    }

# my $durationcoldes = $Lang::tr{'updxlrlog duration'};
# $durationcoldes = $Lang::tr{'updxlrlog duration in ms'} if ( $measuresraw );

my $sizecoldes = $Lang::tr{'updxlrlog size in hr'};
$sizecoldes = $Lang::tr{'updxlrlog size in bytes'} if ( $measuresraw );

my $end = $start + $logsettings{'LOGVIEW_VIEWSIZE'};
$end = $#log if ($#log < $start + $logsettings{'LOGVIEW_VIEWSIZE'});
@log =  @log [$start .. $end];

&Header::closebox();
&Header::openbox('100%', 'left', "$Lang::tr{'log'}: start->$start end->$end step->$logsettings{'LOGVIEW_VIEWSIZE'}  total lines-> $lines");

$start = $lines - $logsettings{'LOGVIEW_VIEWSIZE'} if ($start >= $lines - $logsettings{'LOGVIEW_VIEWSIZE'});
$start = 0 if ($start < 0);
my $prev;
if ($start == 0) {
    $prev = -1;
}
else {
    $prev = $start - $logsettings{'LOGVIEW_VIEWSIZE'};
    $prev = 0 if ($prev < 0);
}

my $next;
if ($start == $lines - $logsettings{'LOGVIEW_VIEWSIZE'}) {
    $next = -1;
}
else {
    $next = $start + $logsettings{'LOGVIEW_VIEWSIZE'};
    $next = $lines - $logsettings{'LOGVIEW_VIEWSIZE'} if ($next >= $lines - $logsettings{'LOGVIEW_VIEWSIZE'});
}

# if ($logsettings{'LOGVIEW_REVERSE'} eq 'on') { @log = reverse @log; }

print "<p><b>$Lang::tr{'web hits'} $date: $lines - $Lang::tr{'updxlrlog sort by'} $sortby</b></p>";
if ($lines != 0) { &oldernewer(); }





print <<END
<table width='100%'>
<tr>
<td width='10%' align='center' class='$columnsortedclass{"DATE"}'><b>$Lang::tr{'time'}</b></td>
<td width='10%' align='center' class='boldbase'><b>$Lang::tr{'source ip'}</b></td>
<td width='5%' align='center' class='boldbase'><b>$sizecoldes</b></td>
<td width='5%' align='center' class='$columnsortedclass{"RESULT"}'><b>$Lang::tr{'updxlrlog sort by result code'}</b></td>
<td width='5%' align='center' class='$columnsortedclass{"VENDOR"}'><b>Vendor</b></td>
<td width='40%' align='center' class='$columnsortedclass{"URL"}'><b>$Lang::tr{'website'}</b></td>
</tr>
END
    ;


my $ll = 0;
foreach $_ (@log) {

    my ($datetime, $ip, $vendor, $result, $url, $username, $size) = split;
    my ($SECdt, $MINdt, $HOURdt, $DAYdt, $MONTHdt, $YEARdt) = localtime($datetime);
    $SECdt  = sprintf("%.02d", $SECdt);
    $MINdt  = sprintf("%.02d", $MINdt);
    $HOURdt = sprintf("%.02d", $HOURdt);
    #my $fullurl = $url;

	#my $rate = 0;

	#if ($duration > 0)
	#{
	#  $rate = $size / ($duration * 0.001);
	#} else {
	# $rate = $size * 2;
	#}
	#$rate = &ADVPXL::get_rate_str($rate) if (! $measuresraw);
	#$rate = &ADVPXL::get_rate_str_bytes($rate) if ($measuresraw);

	$size = &UPDXLT::get_filesize_str($size) if (! $measuresraw);
	#$duration = &ADVPXL::truncate_ms_to_sec($duration) if (! $measuresraw);
	# sprintf("%.01d", ($me + 1023)/1024);

	my $urlsize = 50;
	$urlsize = 190 if ($fullurl);

    $url =~ /(^.{0,$urlsize})/;
    my $part = $1;
    unless (length($part) < $urlsize) { $part = "${part}..."; }
    $url  = &Header::cleanhtml($url,  "y");
    $part = &Header::cleanhtml($part, "y");
    if ($cgiparams{'DAY'} == 0) {    # full month
        $DAYdt = sprintf("%.02d/", $DAYdt);
    }
    else {
        $DAYdt = '';
    }

	#TODO: move inline style in stylesheet
	my $resultstyle='';
	if ($result eq 'UPDCACHE') {
		$resultstyle='style="color:#558107; font-weight: bold;" ';
	}
	 print "<tr $resultstyle class='table".int(($ll % 2) + 1)."colour'>";
    print <<END
	<td align='center'>$DAYdt$HOURdt:$MINdt:$SECdt</td>
	<td align='center'>$ip</td>
	<td align='right'>$size</td>
	<td align='left'>$result</td>
	<td align='left'>$vendor</td>
	<td align='left'><a href='$url' title='$url' target='_new'>$part</a></td>
</tr>
END
        ;
    $ll++;
}

print "</table>";

&oldernewer();

&Header::closebox();

 #enable following only for debug
 # &Header::openbox('100%', 'left', 'DEBUG');
 #   my $debugCount = 0;
 #   foreach my $line (sort keys %debug) {
 #       print "$line = $debug{$line}<br />\n";
 #       $debugCount++;
 #   }
 #   print "&nbsp;Count: $debugCount\n";
 #   &Header::closebox();

&Header::closebigbox();

&Header::closepage();




# -------------------------------------------------------------------


sub oldernewer {
    print <<END
<table width='100%'>
<tr>
END
        ;

    print "<td align='center' width='50%'>";
    if ($prev != -1) {
        print
"<a href='/cgi-bin/updxlrlog.cgi?$prev,$cgiparams{'MONTH'},$cgiparams{'DAY'},$cgiparams{'SOURCE_IP'},$cgiparams{'RESPONSE_CODE'},$cgiparams{'VENDOR'},$cgiparams{'SORT_BY'},$cgiparams{'ORDER'},$cgiparams{'FULL_URL'},$cgiparams{'ENABLE_FILTER'},$cgiparams{'FILTER'},$cgiparams{'ENABLE_INCLUDE_FILTER'},$cgiparams{'INCLUDE_FILTER'}'>$Lang::tr{'updxlrlog prev'}</a>";
    }
    else {
        print "$Lang::tr{'updxlrlog prev'}";
    }
    print "</td>\n";

    print "<td align='center' width='50%'>";
    if ($next >= 0) {
        print
"<a href='/cgi-bin/updxlrlog.cgi?$next,$cgiparams{'MONTH'},$cgiparams{'DAY'},$cgiparams{'SOURCE_IP'},$cgiparams{'RESPONSE_CODE'},$cgiparams{'VENDOR'},$cgiparams{'SORT_BY'},$cgiparams{'ORDER'},$cgiparams{'FULL_URL'},$cgiparams{'ENABLE_FILTER'},$cgiparams{'FILTER'},$cgiparams{'ENABLE_INCLUDE_FILTER'},$cgiparams{'INCLUDE_FILTER'}'>$Lang::tr{'updxlrlog next'}</a>";
    }
    else {
        print "$Lang::tr{'updxlrlog next'}";
    }
    print "</td>\n";

    print <<END
</tr>
</table>
END
        ;
}

