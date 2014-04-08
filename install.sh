#!/bin/bash
# ipcop addon binary installer Ver 0.9a for IPCop 1.4.x
#
# created 01 January 2005 by Frank 'Darkmann' Koch <darkmann@black-empire.de>
# modified 02 January 2005 by Tom 'wintermute' Eichstaedt <wintermute@tom-e.de>
#
# extended 2006-02-24 by weizen_42
#

SCRIPTPATH=`dirname $0`
CMD="$1"

STEP=1
UPDATE=0

UPDXLVER=2.3.0
UPDXLURL=http://blockouttraffic.de/ua_index.php
HTDOCS="/home/httpd/html"
HTDOCSVHOST81="/home/httpd/vhost81/html"
LOGDIR="/var/log/updatexlrator"


#error handling
err()
{
    echo " "
    echo "Error : $1 "
    echo " "
    echo "Choose your option:"
    echo " "
    echo "./install -i   ---> to install"
    echo "./install -u   ---> to uninstall"
    echo " "
    exit
}

# start Proxy server
startsquid()
{
    echo "Step $STEP: Starting services"
    echo "--------------------------------------------"
    echo "Restarting Web Proxy service (if enabled)"

    sed -i -e "s+^\(ENABLED_.*\)=disabled+\1=on+g" /var/ipcop/proxy/settings

    /usr/local/bin/restartsquid
}

# stop Proxy server
stopsquid()
{
    echo "Step $STEP: Stopping services"
    echo "--------------------------------------------"
    echo "Stopping Web Proxy service (if running)"

    sed -i -e "s+^\(ENABLED_.*\)=on+\1=disabled+g" /var/ipcop/proxy/settings

    /usr/local/bin/restartsquid

    echo " "

    let STEP++
}

# installation
ai()
{
    echo ""
    echo "===================================================="
    echo "  IPCop 2.0 Update Accelerator add-on installation"
    echo "===================================================="
    echo ""

    ## verify already installed and uninstall
    if [ -e /var/ipcop/addons/updatexlrator/version ]; then
        UPDATE=1
    fi

    if [ "$UPDATE" == 1 ]; then
        stopsquid
    fi


    echo "Step $STEP: Creating directories"
    echo "--------------------------------------------"

    for DIR in /var/ipcop/addons/updatexlrator /var/ipcop/addons/updatexlrator/bin /var/ipcop/addons/updatexlrator/autocheck $HTDOCSVHOST81/updatecache $HTDOCSVHOST81/updatecache/download $LOGDIR
    do
        echo "$DIR"
        if [ ! -d $DIR ]; then
            mkdir $DIR
        fi
    done


    if [ -e /var/ipcop/updatexlrator/settings ]; then
        echo "Moving config files"
        mv /var/ipcop/updatexlrator/* /var/ipcop/addons/updatexlrator/
        rm -rf /var/ipcop/updatexlrator
    fi

    if [ -e /home/httpd/html/updatecache ]; then
        echo "Moving existing updatecache"
        mv $HTDOCS/updatecache/* $HTDOCSVHOST81/updatecache/
        rm -rf /home/httpd/html/updatecache
    fi

    echo " "
    let STEP++



    echo "Step $STEP: Patching system files"
    echo "--------------------------------------------"

    echo -n "Extending cron table"

    if [ $(grep -c UpdateAccelerator /var/spool/cron/root.orig) == 0 ]; then
        addtofiletail UpdateAccelerator $SCRIPTPATH/setup/cron.add /var/spool/cron/root.orig
        /usr/bin/fcrontab -z &> /dev/null
        echo ""
    else
        echo "... nothing to do"
    fi

    echo "Patching language files"
    addtolanguage UpdateAccelerator bz,de,en,es,fr,it,nl,pl,pt,ru $SCRIPTPATH/langs

    echo " "
    let STEP++



    echo "Step $STEP: Copying Update Accelerator files"
    echo "--------------------------------------------"

    echo "/usr/sbin/updxlrator"
    cp $SCRIPTPATH/bin/updxlrator /usr/sbin/updxlrator
    chmod 755 /usr/sbin/updxlrator

    echo "/home/httpd/cgi-bin/updatexlrator.cgi"
    addcgi $SCRIPTPATH/cgi/updatexlrator.cgi

    for BIN in checkdeaddl checkup download lscache setperms
    do
        echo "/var/ipcop/addons/updatexlrator/bin/$BIN"
        cp $SCRIPTPATH/bin/$BIN /var/ipcop/addons/updatexlrator/bin/$BIN
    chmod 755 /var/ipcop/addons/updatexlrator/bin/$BIN
    done

    echo "/usr/bin/lscache"
    cp $SCRIPTPATH/bin/lscache /usr/bin/lscache
    chmod 755 /usr/bin/lscache

    echo "/var/ipcop/addons/updatexlrator/updxlrator-lib.pl"
    cp $SCRIPTPATH/cgi/updxlrator-lib.pl /var/ipcop/addons/updatexlrator/updxlrator-lib.pl

    for CRONSCRIPT in daily weekly monthly
    do
        if [ ! -e "/var/ipcop/addons/updatexlrator/autocheck/cron.$CRONSCRIPT" ]; then
            echo "/var/ipcop/addons/updatexlrator/autocheck/cron.$CRONSCRIPT"
            ln -s /bin/false /var/ipcop/addons/updatexlrator/autocheck/cron.$CRONSCRIPT
        fi
    done

    echo "All icons in $HTDOCS/images"
    cp $SCRIPTPATH/images/updxl-*.gif $HTDOCS/images/

    echo "/var/ipcop/addons/updatexlrator/version"
    echo "VERSION_INSTALLED=$UPDXLVER" > /var/ipcop/addons/updatexlrator/version
    echo "URL=$UPDXLURL" >> /var/ipcop/addons/updatexlrator/version

    rm -rf /var/ipcop/addons/updatexlrator/latestVersion

    if [ ! -e /var/ipcop/proxy/redirector/updatexlrator ]; then
        echo "/var/ipcop/proxy/redirector/updatexlrator"
        echo "ENABLED=off" > /var/ipcop/proxy/redirector/updatexlrator
        echo "ORDER=20" >> /var/ipcop/proxy/redirector/updatexlrator
        echo "NAME='Update Accelerator'" >> /var/ipcop/proxy/redirector/updatexlrator
        echo "CMD=/usr/sbin/updxlrator" >> /var/ipcop/proxy/redirector/updatexlrator
        chown nobody.nobody /var/ipcop/proxy/redirector/updatexlrator
    elif [ $(/bin/grep -c OPTION_CHAIN /var/ipcop/proxy/redirector/updatexlrator) == 0 ]; then
        echo "/var/ipcop/proxy/redirector/updatexlrator"
        echo "OPTION_CHAIN=-f" >> /var/ipcop/proxy/redirector/updatexlrator
    fi

    echo " "
    let STEP++


    echo "Step $STEP: Configuring logfile rotation"
    echo "--------------------------------------------"

    echo -n "/etc/logrotate.d/UpdateAccelerator"
    if [ ! -e /etc/logrotate.d/UpdateAccelerator ]; then
        cp $SCRIPTPATH/setup/logrotate.add /etc/logrotate.d/UpdateAccelerator
        echo ""
    else
        echo "... keep existing file"
    fi

    echo " "
    let STEP++


    echo "Step $STEP: Setting ownerships and permissions"
    echo "--------------------------------------------"

    echo "Setting ownership and permissions (updxlrtr)"
    chown -R nobody:nobody /var/ipcop/addons/updatexlrator
    chown root:root /var/ipcop/addons/updatexlrator/bin/setperms
    chown squid:squid $LOGDIR
    chmod 4755 /var/ipcop/addons/updatexlrator/bin/setperms
    chmod 755 $LOGDIR

    echo "Setting ownership and permissions (updcache)"
    chown nobody:squid $HTDOCSVHOST81/updatecache
    chmod 775 $HTDOCSVHOST81/updatecache

    find $HTDOCSVHOST81/updatecache/ -type d -exec chown -R nobody:squid {} \; -exec chmod 775 {} \;
    find $HTDOCSVHOST81/updatecache/ -type f -exec chown -R nobody:squid {} \; -exec chmod 664 {} \;
    find $HTDOCSVHOST81/updatecache/ -type d -name 'lost+found' -exec chown -R 0:0 {} \; -exec chmod -R og-rwx {} \;
    echo " "
    let STEP++


    if [ "$UPDATE" == 1 ]; then
        if [ -d $HTDOCSVHOST81/updatecache/metadata ]; then
            echo "Step $STEP: Converting update cache directory"
            echo "--------------------------------------------"
            echo "Found an existing version 1.0 cache."
            echo "Running cache conversion:"
           $SCRIPTPATH/bin/convert -nv
            echo "************************************************"
            echo "* Source checkup required for cache integrity! *"
            echo "************************************************"
            echo "Please run /var/ipcop/addons/updatexlrator/bin/checkup"
            let STEP++
        fi

        startsquid

        echo " "
    fi

    echo " "
}

# deinstallation
au()
{

    echo "===================================================="
    echo "  IPCop 2.0 Update Accelerator add-on uninstall"
    echo "===================================================="
    echo ""

    if [ ! -e "/home/httpd/cgi-bin/updatexlrator.cgi" ] && [ ! -d "/var/ipcop/addons/updatexlrator" ]; then
        echo "ERROR: Update Accelerator add-on is not installed."
        exit
    fi

   stopsquid

    echo "Step $STEP: Removing directories"
    echo "--------------------------------------------"

    for DIR in /var/ipcop/addons/updatexlrator $HTDOCSVHOST81/updatecache $LOGDIR
    do
        echo "$DIR"
        if [ -d "$DIR" ]; then
            rm -rf $DIR
        fi
    done

    echo ""
    let STEP++


    echo "Step $STEP: Deleting Update Accelerator files"
    echo "--------------------------------------------"

    for FILE in /etc/logrotate.d/UpdateAccelerator /usr/bin/lscache /usr/sbin/updxlrator
    do
        echo "$FILE"
        if [ -f "$FILE" ]; then
            rm -rf $FILE
        elif [ -d "$FILE" ]; then
            rm -rf $FILE
        fi
    done

    echo "/home/httpd/cgi-bin/updatexlrator.cgi"
    removecgi updatexlrator.cgi

    echo "all icons in $HTDOCS/images"
    rm -f $HTDOCS/images/updxl-*.gif

    if [ -e /var/ipcop/proxy/redirector/updatexlrator ]; then
        echo "/var/ipcop/proxy/redirector/updatexlrator"
        rm -f /var/ipcop/proxy/redirector/updatexlrator
    fi

    echo ""
    let STEP++


    echo "Step $STEP: Restoring system files"
    echo "--------------------------------------------"

    echo "Restoring cron table"

    removefromfile UpdateAccelerator /var/spool/cron/root.orig

    /usr/bin/fcrontab -z &> /dev/null

    echo ""


    echo "Removing language texts"
    removefromlanguage UpdateAccelerator

    echo ""
    let STEP++



    echo "Step $STEP: Cleaning up Web Proxy configuration"
    echo "--------------------------------------------"

    echo "Rebuilding squid.conf"
    /usr/local/bin/restartsquid --config

    echo ""

    startsquid

}


if [ ! -e /usr/lib/ipcop/library.sh ]; then
    echo "Upgrade your IPCop, library.sh is missing"
    exit 1
fi

. /usr/lib/ipcop/library.sh

# check IPCop version
VERSIONOK=1
if [ 0$LIBVERSION -ge 2 ]; then
    isversion 2.1.5 newer
    VERSIONOK=$?
fi
#DEBUG:
#echo "VERSIONOK: $VERSIONOK"
if [ $VERSIONOK -ne 0 ]; then
    echo "Upgrade your IPCop, this Addon requires at least IPCop 2.1.5"
    exit 1
fi


case $CMD in
    -i|i|install)
        echo " "
        ai
        echo " "
        ;;

    -u|u|uninstall)
        echo " "
        au
        echo " "
        ;;

    *)
        err "Invalid Option"
        ;;
esac
sync

#end of file
