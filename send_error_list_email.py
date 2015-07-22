#!/usr/bin/env /proj/sot/ska/bin/python

#############################################################################################################
#                                                                                                           #
#      send_error_list_email.py: read the current error lists and send out email                            #
#                                                                                                           #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                                       #
#                                                                                                           #
#           Last Update: Jul 16, 2015                                                                       #
#                                                                                                           #
#############################################################################################################

import sys
import os
import string
import re
import getpass
import socket
import random
import time
import datetime

#
#--- reading directory list
#
comp_test = 'live'
if comp_test == 'test':
    path = '/data/mta/Script/Cron_check/house_keeping/dir_list_py_test'
else:
    path = '/data/mta/Script/Cron_check/house_keeping/dir_list_py'

f= open(path, 'r')
data = [line.strip() for line in f.readlines()]
f.close()
for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec "%s = %s" %(var, line)
#
#--- append  pathes to private folders to a python directory
#
sys.path.append(bin_dir)
sys.path.append(mta_dir)
#
#--- import several functions
#
import convertTimeFormat          as tcnv       #---- contains MTA time conversion routines
import mta_common_functions       as mcf        #---- contains other functions commonly used in MTA scripts
#
#--- check whose account, and set a path to temp location
#
user = getpass.getuser()
user = user.strip()
#
#---- find host machine name
#
machine = socket.gethostname()
machine = machine.strip()
#
#--- possible machine names and user name lists
#
cpu_list     = ['colossus', 'colossus-v', 'rhodes', 'c3po-v', 'r2d2-v']
usr_list     = ['mta', 'cus']
cpu_usr_list = ['colossus_mta', 'rhodes', 'colossus-v_mta', 'r2d2-v_mta', 'r2d2-v_cus', 'c3po-v_mta', 'c3po-v_cus']
#
#--- temp writing file name
#
rtail  = int(10000 * random.random())       #---- put a romdom # tail so that it won't mix up with other scripts space
zspace = '/tmp/zspace' + str(rtail)

email_list = 'tisobe@cfa.harvard.edu,swolk@head.cfa.harvard.edu,brad@head.cfa.harvard.edu'
#email_list = 'tisobe@cfa.harvard.edu'

#--------------------------------------------------------------------------------------------------------------------------
#-- report_error: read errors from <cup_usr_list>_error_list, sort it out, clean, and send out email                    ---
#--------------------------------------------------------------------------------------------------------------------------

def report_error():

    """
    read errors from <cup_usr_list>_error_list, sort it out, clean, and send out email
    Input:  none but read from <cup_usr_list>_error_list
    Output: email sent out
    """

#
#--- find the current time
#
    [year, mon, day, hours, min, sec, weekday, yday, dst] = tcnv.currentTime("Local")
#
#--- create surfix for files which will be saved in Past_errors directory
#
    smon = str(mon)
    if mon < 10:
        smon = '0' + smon
    sday = str(day)
    if day < 10:
        sday = '0' + sday
    tail = str(year) + smon + sday

    for tag in cpu_usr_list:

        efile = house_keeping + 'Records/' + tag + '_error_list'
        pfile = house_keeping + 'Records/Past_errors/' + tag + '_error_list_' + tail
        prev_line = ''

        chk   =  mcf.chkFile(efile)
        if chk > 0:
#
#--- read error messages from the file
#
            f    = open(efile, 'r')
            data = [line.strip() for line in f.readlines()]
            f.close()
#
#--- sort the data so that we can correct messages to each cron job together
#
            data.sort()

            task_list = []
            time_list = []
            mssg_list = []
            for ent in data:
                atemp = re.split(' : ' , ent)
                task_list.append(atemp[0])

                stime = int(atemp[1])
                dtime = tcnv.axTimeMTA(stime)
                time_list.append(dtime)

                mssg_list.append(atemp[2])
#
#--- write out cron job name
#
            fo    = open(zspace, 'w')
            cname = task_list[0]
            line  = '\n\n' + cname + '\n____________________\n\n'
            fo.write(line)

            for i in range(0, len(mssg_list)):
                if task_list[i] != cname:
                    cname = task_list[i]
                    line  = '\n\n' + cname + '\n____________________\n\n'
                    fo.write(line)
#
#--- create each line. if it is exactly same as one line before, skip it
#
                line = time_list[i] + ' : ' + mssg_list[i] + '\n'

                if line != prev_line:
                    fo.write(line)
                prev_line = line

            fo.close()
#
#--- send email out
#
#            cmd = 'cp  ' + zspace + ' ' + '/data/mta/Script/Cron_check/Scripts/' + tag
#            os.system(cmd)
            send_mail(tag, email_list)
#
#--- move the error list to Past_errors directory
#
            cmd = 'mv ' + efile + ' ' + pfile
            os.system(cmd)
#            cmd = 'chmod 755 ' + pfile
#            os.system(cmd)


#--------------------------------------------------------------------------------------------------------------------------
#-- send_mail: sending email out                                                                                        ---
#--------------------------------------------------------------------------------------------------------------------------

def send_mail(tag, email_list):

    """
    sending email out
    Input:  tag     --- user and machine name in the form of c3po-v_mat
            email_list  --- a string of name in the from of 'tisobecfa.harvard.edu,swolk@cfa.harvard.edu'
    Output: email sent out
    """

    chk   = mcf.isFileEmpty(zspace)
    if chk > 0:
        atemp = re.split('_', tag)

        cmd = 'cat ' + zspace + ' | mailx -s "Subject: Cron Error : ' + atemp[1] + ' on ' + atemp[0] + '"  ' + email_list
        os.system(cmd)

    mcf.rm_file(zspace)

#--------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    report_error()

