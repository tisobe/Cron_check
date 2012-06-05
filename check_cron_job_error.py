#!/usr/local/bin/python2.6

#########################################################################################################################
#                                                                                                                       #
#       check_cron_job_error.py: find new error messages from cron log files for a given machine and a given user       #
#                                                                                                                       #
#                                                                                                                       #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                                               #
#                                                                                                                       #
#               last update: Jun 5, 2012                                                                                #
#                                                                                                                       #
#########################################################################################################################

import sys
import os
import string
import re
import getpass
import socket

#
#--- set bin_dir where all related python scripts are kept
#
bin_dir = '/data/mta/Script/Cron_check/Cron_check/'
sys.path.append(bin_dir)

import convertTimeFormat as tcnv

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

tempdir = '/tmp/' + user + '/'

tempout = tempdir + 'ztemp'                             #--- temporary file to put data

#--------------------------------------------------------------------------------------------------------------------------
#-- check_cron: find new error messages from cron log files for a given machine and a given user                        ---
#--------------------------------------------------------------------------------------------------------------------------

def check_cron():

    """
    find new error messages from cron log files for a given machine and a given user.
    this script send out email if it finds new error message. The log files are clean up 1 of every month
    and the same message could be send out if there are still the same error messages occur.
    """
#
#--- error_log name
#
    error_logs = '/data/mta/Script/Cron_check/Error_logs/error_list_' + machine + '_' + user

#
#--- find cron file names for this machine for this user
#
    cron_file_name = extract_cron_file_name()

#
#--- check today's date. if it is 1st of the month, move the old error_list to archive form.
#

    [year, mon, day, hours, min, sec, weekday, yday, dst] = tcnv.currentTime('Local')

    if day == 1:
        lyear = year
        lmon  = mon - 1
        if lmon < 1:
            lmon = 12
            lyear -= 1

        error_logs_old = error_logs + '_' + str(lmon) + '_' + str(lyear)
        cmd = 'mv ' + error_logs + ' ' + error_logs_old
        os.system(cmd)

        error_dict = {}
    else:
#
#--- read existing error list
#
        error_dict = {}
        try:
            f    = open(error_logs, 'r')
            data = [line.strip() for line in f.readlines()]
            f.close()
            for ent in data:
                atemp = re.split('\<:\>', ent)
                content = []
                for i in range(1, len(atemp)):
                    content.append(atemp[i])
    
                error_dict[atemp[0]] = content
        except:
            pass

#
#--- set which Log location to check (depends on user.)
#
    dir_loc = '/home/' + user + '/Logs/'


#
#--- find names of files and directories in the Logs directory
#
    cmd = 'ls -lrtd ' + dir_loc + '/* >' + tempout
    os.system(cmd)
    f    = open(tempout, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()
    cmd = 'rm ' + tempout
    os.system(cmd)

    cron_list =[]
    for ent in data:
        atemp = re.split('\s+|\t+', ent)
        m1    = re.search('d',   atemp[0])
        m2    = re.search('Past_logs', ent)
#
#--- if it is a directory other than Past_logs, find file names in that directory
#
        if (m1 is not None) and (m2 is None):
            cmd = 'ls ' + atemp[8] + '/* > ' + tempout
            os.system(cmd)
            f    = open(tempout, 'r')
            data2 = [line.strip() for line in f.readlines()]
            f.close()
            cmd = 'rm ' + tempout
            os.system(cmd)

            for ent2 in data2:
                cron_list.append(ent2)
#
#--- files in Logs directory level
#
        elif m2 is None:
            cron_list.append(atemp[8])

    new_error_dict = {}
    for file in cron_list:
#
#--- check whether this error message blongs to this machine (and the user)
#

        mchk = 0
        for comp in cron_file_name:
            m = re.search(comp, file)

            if m is not None:
                mchk = 1
                break

        if mchk > 0:
#
#--- check whether the file has any error messages 
#
            error_list = find_error(file)
            if len(error_list) > 0:
#
#--- if there are error messages, compare them to the previous record, and if it is new append to the record.
#
                try:
                    prev_list = error_dict[file]
                    new_error = []
                    for ent in error_list:
                        chk = 0
                        for comp in prev_list:
                            if ent == comp:
                                chk = 1
    
                        if chk ==  0:
                            prev_list.append(ent)
                            new_error.append(ent)
    
                    if len(new_error) > 0:
                        error_dict[file] = prev_list
                        new_error_dict[file] = new_error 
                except:
#
#--- there is no previous error_list entry: so all error messages are new and log them
#
                    error_dict[file]     = error_list
                    new_error_dict[file] = error_list


#
#--- update error logs
#
    f = open(error_logs, 'w')
    for key in error_dict:
        line = key
        for e_ent in error_dict[key]:
            line = line + '<:>' + e_ent
        line  = line + '\n'
        f.write(line)

    f.close()

#
#---if new error messages are found; notify to a list of users
#
    chk = 0
    f = open(tempout, 'w')
    for key in new_error_dict:
        chk += 1
        line = key + '\n'
        f.write(line)
        for ent in new_error_dict[key]:
            line = '\t' + ent + '\n'
            f.write(line)

        f.write('\n')

    f.close()

    if chk > 0:
        cmd = 'cat ' + tempout + ' | mailx -s "Subject: Cron Error : ' + user + ' on ' + machine + '"  isobe@head.cfa.harvard.edu'
        os.system(cmd)
    else:
#
#--- if there is no error, notify that fact to admin
#
        f = open(tempout, 'w')
        line = '\nNo error is found today on ' + machine + ' by a user ' + user + '.\n'
        f.write(line)
        f.close()
        cmd = 'cat ' + tempout + ' | mailx -s "Subject: No Cron Error : ' + user + ' on ' + machine + '"  isobe@head.cfa.harvard.edu'
        os.system(cmd)


    cmd = 'rm ' + tempout
    os.system(cmd)


#--------------------------------------------------------------------------------------------------------------------------
#--- fine_error: extract lines contain error messages from a file                                                        --
#--------------------------------------------------------------------------------------------------------------------------

def find_error(file):

    """
    extract lines containing error messages. input: file name
                                             output: error list in a list form

    """

    f    = open(file, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    error_list = []
    for ent in data:
        m1  = re.search('Error', ent)
        m2  = re.search('Can',   ent)
        chk = 0

        if (m1 is not None) or (m2 is not None):
            for comp in error_list:
                if ent == comp:
                    chk = 1

            if chk == 0:
                error_list.append(ent)

    return error_list

#--------------------------------------------------------------------------------------------------------------------------
#--- extract_cron_file_name: extract cron error message file names for the current user/machine                         ---
#--------------------------------------------------------------------------------------------------------------------------

def extract_cron_file_name():

    """
    extract cron error message file names for the current user/machine
    output: cron_file_name:   a list of cron file names (file names only no directory path)
    """

    cmd = 'crontab -l >' +  tempout
    os.system(cmd)

    f    = open(tempout, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()
    cmd = 'rm ' + tempout
    os.system(cmd)

    cron_file_name = []
    for ent in data:
        m = re.search('Logs', ent)
        if m is not None:
            atemp = re.split('Logs/', ent)
            btemp = re.split('2>&1',  atemp[1])
            cron  = btemp[0]
#
#--- for the case the files are kept in a sub directory, remove the sub directory name
#
            m2 = re.search('\/', cron)
            if m2 is not None:
                ctemp = re.split('\/', cron)
                cron  = ctemp[1]

            cron = cron.strip()
            cron_file_name.append(cron)

    return cron_file_name


#-----------------------------------------------------------------

if __name__ == '__main__':

    check_cron()

