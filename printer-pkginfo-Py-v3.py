#!/usr/bin/python

#   Based on work by Graham Gilbert, 2014-2016
#   Modified by Hilary Brenum, 2018
#
#   Copyright 2020 LuX - (LifeUnexpected)
#   https://github.com/lifeunexpected
#
#   This script has been updated to ONLY support the new IPP - Internet Printing Protocol
#   since Apple deprecated ppd files and drivers. PPD files and printer drivers are
#   deprecated and will not be supported in a future version of CUPS.
#
#   The original script supports PPD files, printer drivers, lpd, smb and socket but since these are being deprecated this updated script removes support for them.
#   Removed #!/bin/sh since its being deprecated from macOS 10.16 and updated to use #!/bin/zsh
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import plistlib
import argparse
import tempfile
import os
import subprocess
import sys
from arguments import ScriptArguments

makepkginfo = '/usr/local/munki/makepkginfo'


def fail(errmsg=''):
    '''Print any error message to stderr,
    clean up install data, and exit'''
    if errmsg:
        print((errmsg, sys.stderr))
    # exit
    exit(1)

def yesNo(question):
    question = question+'[default: y]'
    reply = str(eval("input(question+' (y/n): ')")).lower().strip()
    if(reply == ""):
        return True
    if reply[0] == 'y':
        return True
    else:
        return False

def plistInput(plist):
    arguments = ScriptArguments()
    try:
        with open(plist, 'rb') as f:
            plist_opts = plistlib.load(f)
    except:
        fail('Could not read %s' % (plist))

    # Make sure makepkginfo is available
    if not os.path.isfile(makepkginfo) or not os.access(makepkginfo, os.X_OK):
        fail("A required exeuctable, '%s', could not be found "
             "or is not executable!" % makepkginfo)

    if not plist_opts['name'] or not plist_opts['queue_name'] or not plist_opts['display_name'] or not plist_opts['ipp'] or not plist_opts['address']:
        fail("One or more of the required options are missing from %s" %
             plist)

    arguments = arguments.fromDictionary(plist_opts)
    return arguments

def interactiveInput():
    arguments = ScriptArguments()
    address = eval("input('Printer Address: ')")
    arguments.setAddress(address)
    queueName = eval("input('Server Queue Name: ')")
    arguments.setQueueName(queueName)
    displayName = eval("input('Display Name: ')")
    arguments.setDisplayName(displayName)
    if (arguments.getQueueName()):
        arguments.setName(arguments.getQueueName())
    else:
        arguments.setName(str(arguments.getDisplayName()).strip().replace(' ',''))
    print(("Package name for Munki manifests is: ", arguments.getName()))
    arguments.setLocation(input('Location (optional): '))
    if (yesNo("Use ipp everywhere for printing?") == False):
        arguments.setIpp(eval("input('ipp (driver) path: '))"))
    if yesNo("Duplex printing?"):
       arguments.appendOption('sides=two-sided-long-edge')

    return arguments

def main():
    description = "A python script to create nopkg-style files for installing printers onto client systems using Munki (https://github.com/munki/munki).  Printers can be imported from a pre-existing XML plist file or can be created interactively.  Unless a file path is specified with -o, the pkg file will be written to STDOUT. This script has been updated to ONLY support the new IPP - Internet Printing Protocol since Apple deprecated ppd files and drivers. PPD files and printer drivers are deprecated and will not be supported in a future version of CUPS."
    epilog = "To import printers into Munki, copy the output file to the pkgsinfo/ directory of your Munki repo and then re-run makecatalogs"

    o = argparse.ArgumentParser(description = description,epilog = epilog)

    o.add_argument("-p","--plist",
                 help = "Path to an XML plist file containing key/value pairs for version, display_name, queue_name, ipp, location, and other options. See example-printer.plist for an example.")

    o.add_argument('-i','--interactive',help = "Create pkginfo file in interactive mode rather than with a .plist file",action = "store_true")

    o.add_argument('-o','--outfile',help = "Write pkginfo to plist file rather than STDOUT")

    o.add_argument('-c','--catalog',default = 'testing',help = "Set Munki catalog (default without -c is \"testing\")")

    o.add_argument('-v','--version',default = 0.1,help = "Set package version if creating an updated pkginfo file for an existing printer (default without -v is 0.1)",type = float)

    o.add_argument('--prefix',help = "With -i, set prefix for printer name as it appears in Munki manifests")

    args = o.parse_args()

    if args.interactive and args.outfile is None:
        o.error("Interactive mode (-i) requires output file to be specified with -o")

    if args.plist:
        plist_opts = plistInput(args.plist)
    elif args.interactive:
        plist_opts = interactiveInput()
    else:
        plist_opts = interactiveInput()

    
    try:
        if args['version']:
            version = args['version']
        else:
            version = plist_opts.getVersion()
    except:
        version = '0.1'


    options = plist_opts.getOptions()

    try:
        if args.catalog:
            catalog = args.catalog
        else:
            catalog = plist_opts.getDefaultCatalog()
    except:
        catalog = 'testing'

    developer = plist_opts.getDefaultDeveloper()
    
    category = plist_opts.getDefaultCategory()
   
    protocol = plist_opts.getProtocol()

    formatted_options = ""
    if options:
        for option in options:
            built = "-o " + option + " "
            formatted_options = formatted_options + built

    queue_name = plist_opts.getQueueName()
    name = plist_opts.getName()
    if args.prefix:
        name = args.prefix + name
        
    if len(queue_name) > 24:
        fail("Queue name is too long")

    display_name = plist_opts.getDisplayName()
    ipp = plist_opts.getIpp()
    
    location = plist_opts.getLocation()

    if queue_name:
        address = plist_opts.getAddress() + "/" + queue_name
    else:
        address = plist_opts.getAddress()

        # build the install check script

        install_check_content = """#!/bin/zsh

    # Based on 2010 Walter Meyer SUNY Purchase College (c)
    # Modified by Nick McSpadden, 2013

    # Script to install and setup printers on a Mac OS X system in a "Munki-Friendly" way.
    # Make sure to install the required drivers first!

    # Variables. Edit these.
    printername="%s"
    location="%s"
    gui_display_name="%s"
    address="%s"
    driver_ipp="%s"
    # Populate these options if you want to set specific options for the printer. E.g. duplexing installed, etc.
    option_1=""
    option_2=""
    option_3=""
    currentVersion="%s"

    function exitWithStatus () {
    	if [ $1 -eq 0 ]; then
    		echo "INSTALL REQUIRED"
    	else
    		echo "NO INSTALL REQUIRED"
    	fi
    	echo "-------------------"
    	echo ""
    	exit $1
    }

    echo "--------------------------------"
    echo "Checking $printername Printer... "
    echo "--------------------------------"


    ### Determine if receipt is installed ###
    printf "Receipt: "
    if [ -e "/private/etc/cups/deployment/receipts/$printername.plist" ]; then
        storedVersion=$(/usr/libexec/PlistBuddy -c "Print :version" "/private/etc/cups/deployment/receipts/$printername.plist")
        echo $storedVersion
    else
    	echo "not stored."
        storedVersion="0"
    fi

    versionComparison=$(echo "$storedVersion < $currentVersion" | bc -l)
    # This will be 0 if the current receipt is greater than or equal to current version of the script

    printf "State: "

    ### Printer Install ###
    # If the queue already exists (returns 0), we don't need to reinstall it.
    LPSTATOUTPUT=$(/usr/bin/lpstat -p "$printername" 2>&1)
    if [ $? -eq 0 ]; then
        if [ "$versionComparison" -eq 0 ]; then
            # We are at the current or greater version
            echo "Configured."
            exitWithStatus 1
        fi
        # We are of lesser version, and therefore we should delete the printer and reinstall.
        echo "Configured, but receipt version $storedVersion doesn't match $currentVersion."
        exitWithStatus 0
    else
    	# Not configured. For verbosity, say unconfigured and exit with status 0"
    	echo "Unconfigured. $LPSTATOUTPUT"
    	exitWithStatus 0
    fi
    """ % (queue_name, location, display_name, address, ipp, version)

        postinstall_content = """#!/bin/zsh

    # Based on 2010 Walter Meyer SUNY Purchase College (c)
    # Modified by Nick McSpadden, 2013

    # Script to install and setup printers on a Mac OS X system in a "Munki-Friendly" way.
    # Make sure to install the required drivers first!

    # Variables. Edit these.
    printername="%s"
    location="%s"
    gui_display_name="%s"
    address="%s"
    driver_ipp="%s"
    # Populate these options if you want to set specific options for the printer. E.g. duplexing installed, etc.
    option_1=""
    option_2=""
    option_3=""
    currentVersion="%s"
    protocol="%s"

    function exitWithStatus () {
    	if [ $1 -eq 0 ]; then
    		echo "INSTALL SUCCESSFUL"
    		echo
    		exit 0
    	fi
    	echo "ERROR WITH INSTALL"
    	echo
    	exit 1
    }

    ### Determine if receipt is installed ###
    if [ -e "/private/etc/cups/deployment/receipts/$printername.plist" ]; then
        storedVersion=$(/usr/libexec/PlistBuddy -c "Print :version" "/private/etc/cups/deployment/receipts/$printername.plist")
    else
        storedVersion="0"
    fi

    versionComparison=$(echo "$storedVersion < $currentVersion" | bc -l)
    # This will be 0 if the current receipt is greater than or equal to current version of the script

    ### Printer Install ###
    # If the queue already exists (returns 0), we don't need to reinstall it.
    LPSTATOUTPUT=$(/usr/bin/lpstat -p "$printername" 2>&1)
    if [ $? -eq 0 ]; then
        if [ "$versionComparison" -eq 0 ]; then
            # We are at the current or greater version
            exitWithStatus 0
        fi
        # We are of lesser version, and therefore we should delete the printer and reinstall.
        printf "Newer install (${currentVersion})... removing existing printer ($printername)... "
        /usr/sbin/lpadmin -x "$printername"
    fi

    # Now we can install the printer.
    printf "Adding $printername... "
    /usr/sbin/lpadmin \
        -p "$printername" \
        -L "$location" \
        -D "$gui_display_name" \
        -v "${protocol}"://"${address}" \
        -m "$driver_ipp" \
        %s \
        -o printer-is-shared=false \
        -o printer-error-policy=abort-job \
        -E


    if [ $? -ne 0 ]; then
    	echo "Failed adding printer... Removing... "
    	/usr/sbin/lpadmin -x "$printername"
    	exitWithStatus 1
    fi

    # Get list of configured printers
    CONFIGUREDPRINTERS=$(lpstat -p | grep -w "printer" | awk '{print$2}' | tr '\n' ' ')

    # Check if configured.
    if [ $(echo "$CONFIGUREDPRINTERS" | grep -w "$printername" | wc -l | tr -d ' ') -eq 0 ]; then
    	echo "ERROR"
    	echo "$printername not in lpstat list after being configured. Currently configured printers are: $CONFIGUREDPRINTERS"
    	exitWithStatus 1
    fi

    # Enable and start the printers on the system (after adding the printer initially it is paused).
    printf "Enabling... "
    /usr/sbin/cupsenable $CONFIGUREDPRINTERS

    # Create a receipt for the printer
    printf "Creating v${currentVersion} receipt... "
    mkdir -p /private/etc/cups/deployment/receipts
    PLISTBUDDYOUTPUT=$(/usr/libexec/PlistBuddy -c "Add :version string" "/private/etc/cups/deployment/receipts/$printername.plist" 2>&1)
    PLISTBUDDYOUTPUT+=$(/usr/libexec/PlistBuddy -c "Set :version $currentVersion" "/private/etc/cups/deployment/receipts/$printername.plist" 2>&1)

    # If problem setting version in receipt (above command), we tell user
    if [ $? -ne 0 ]; then
    	echo "ERROR with receipt creation: $PLISTBUDDYOUTPUT"
    fi

    # Permission the directories properly.
    chown -R root:_lp /private/etc/cups/deployment
    chmod -R 700 /private/etc/cups/deployment

    echo "Complete!"
    echo "Current printers: $CONFIGUREDPRINTERS"

    exitWithStatus 0
        """ % (queue_name, location, display_name, address, ipp, version, protocol, formatted_options)

        uninstall_content = """#!/bin/zsh
    printerName="%s"

    printf "Removing $printername... "
    /usr/sbin/lpadmin -x $printerName

    printf "Removing receipt... "
    rm -f /private/etc/cups/deployment/receipts/$printerName.plist

    echo "Uninstall complete."
        """ % (queue_name)

        # write the scripts to temp files
        tempdir = tempfile.mkdtemp()

        installcheck = os.path.join(tempdir, 'installcheck')
        f = open(installcheck, "w")
        f.write(install_check_content)
        f.close()
        installcheck_option = "--installcheck_script=%s" % installcheck

        postinstall = os.path.join(tempdir, 'postinstall')
        f = open(postinstall, "w")
        f.write(postinstall_content)
        f.close()
        postinstall_option = "--postinstall_script=%s" % postinstall

        uninstall = os.path.join(tempdir, 'uninstall')
        f = open(uninstall, "w")
        f.write(uninstall_content)
        f.close()
        uninstall_option = "--uninstall_script=%s" % uninstall

        catalog_opt = str('-c' + catalog)
        name_opt = '--name=%s' % name
        version_opt = '--pkgvers=%s' % version
        developer_opt = '--developer=%s' % developer
        category_opt = '--category=%s' % category
        displayname_opt = '--displayname=%s' % display_name
        # make pkg info
        cmd = [makepkginfo, installcheck_option, postinstall_option, uninstall_option, name_opt, version_opt, catalog_opt,
               developer_opt, category_opt, displayname_opt, '--unattended_install', '--uninstall_method=uninstall_script', '--nopkg']

        task = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = task.communicate()

        pkginfo = plistlib.readPlistFromString(stdout)

        # read it back so we can add in the requires (if required, sic)
#        if args.plist and plist_opts['requires']:
#            requires = plist_opts.get('requires')
#            pkginfo['requires'] = requires

        # Add Uninstallable flag
        uninstallable = True
        pkginfo['uninstallable'] = uninstallable

        if args.outfile:
            plistlib.writePlist(pkginfo,args.outfile)
        else:
            print((plistlib.writePlistToString(pkginfo)))

        # print and clean up
if __name__ == '__main__':
    main()

