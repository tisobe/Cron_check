#!/usr/bin/env /usr/local/bin/python2.6

#############################################################################################################
#                                                                                                           #
#     check_cron_records_linux.py:reads cron job file and find newly recorded error message of each job     #
#                   this is Linux  version                                                                  #
#                                                                                                           #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                                       #
#                                                                                                           #
#           Last Update: Feb 06, 2014                                                                       #
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
#--- for linux machines, we need an older python script
#
mta_dir = '/data/mta/Script/Python_script/'
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
cpu_list     = ['colossus', 'rhodes']
usr_list     = ['mta']
cpu_usr_list = ['colossus_mta', 'rhodes_mta']

#
#--- temp writing file name
#
rtail  = int(10000 * random.random())       #---- put a romdom # tail so that it won't mix up with other scripts space
zspace = '/tmp/zspace' + str(rtail)


#--------------------------------------------------------------------------------------------------------------------------
#-- check_cron_errors: driving script: reads cron job file and find newly recorded error message of each job            ---
#--------------------------------------------------------------------------------------------------------------------------

def check_cron_records():

    """
    driving script: reads cron job file and find newly recorded error message of each job
    Input:      none but use cronjob listing for the <user> on <manchine>
                it also reads <house_keeping>/Records/<machine>_<user> for the past record
                the errors are read from /home/<user>/Logs/xxx.cron files
    Output: <house_keeping>/Records/<machine>_<user>            --- updated
            <house_keeping>/Records/<machine>_<user>_error_list --- a list of the errors
    """
#
#--- setup a record file name depending on the user and the machine
#
    cfile = house_keeping + 'Records/' + machine + '_' + user

    chk   = mcf.chkFile(cfile)
#
#--- if this is the first time, just create a record file 
#
    if chk == 0:
#
#--- crate a list of cron jobs
#
        lname          = extract_cron_file_name()
#
#--- find the last update time and the file size of the files in the list
#
        [cname, ctime, csize] = update_record_file(cfile, lname)

    else:
#
#--- if there is the past record, read it
#
        [pname, ptime, psize] = get_prev_data(cfile)
#
#--- move the previous record 
#
        cmd = 'mv ' + cfile + ' ' + cfile + '~'
        os.system(cmd)
    
        lname          = extract_cron_file_name()

        [cname, ctime, csize] = update_record_file(cfile, lname)
#
#--- find error messages and create error list
#
        compare_and_find(cname, ctime, csize, pname, ptime, psize)

#--------------------------------------------------------------------------------------------------------------------------
#-- update_record_file: for each cron job, find the last updated time and the current file length                       ---
#--------------------------------------------------------------------------------------------------------------------------

def update_record_file(cfile, lname):

    """
    for each cron job, find the last updated time and the current file length (in line #)
    Input:  cfile   --- output file name <house_keeping>/Records/<machine>_<user>
            lname   --- a list of cron jobs
    Output: cfile   --- an updated recorded file in <house_keeping>/Records/
            cname   --- a list of current file names
            ctime   --- a list of the last updated time of each cron job
            csize   --- a list of the current file length in line # of each cron record file
    """
    cname = []
    ctime = []
    csize = []
    fo    = open(cfile, 'w')
    for ent in lname:
        file  =  '/home/' + user + '/Logs/' + ent
        chk   = mcf.chkFile(file)

        if chk > 0:
            time  = modification_date(file)
            fsize = file_length(file)

            cname.append(ent)
            ctime.append(time)
            csize.append(fsize)
    
            line = file + ' : '+ str(time) + ' : ' + str(fsize) + '\n'
            fo.write(line)

    fo.close()

    return [cname, ctime, csize]

#--------------------------------------------------------------------------------------------------------------------------
#-- get_prev_data: read the last recorded data from <hosue_keeping>/<machine>_<user>                                    ---
#--------------------------------------------------------------------------------------------------------------------------

def get_prev_data(cfile):

    """
    read the last recorded data from <hosue_keeping>/<machine>_<user>
    Input:  cfile   --- the input file name: <hosue_keeping>/<machine>_<user>
    Output: jname   --- a list of the cron job names
            jtime   --- a list of the last updated time of each cron job
            jsize   --- a list of the file size of each cron job
    """
    f     = open(cfile, 'r')
    prev  = [line.strip() for line in f.readlines()]
    f.close()

    jname = []
    jtime = []
    jsize = []
    for ent in prev:
        atemp = re.split(' : ', ent)
        jname.append(atemp[0])
        jtime.append(int(atemp[1]))
        jsize.append(atemp[2])

    return [jname, jtime, jsize]

#--------------------------------------------------------------------------------------------------------------------------
#--- extract_cron_file_name: extract cron error message file names for the current user/machine                         ---
#--------------------------------------------------------------------------------------------------------------------------

def extract_cron_file_name():

    """
    extract cron error message file names for the current user/machine
    output: cron_file_name:   a list of cron file names (file names only no directory path)
    """

    cmd = 'crontab -l >' + zspace 
    os.system(cmd)

    f    = open(zspace, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()
    mcf.rm_file(zspace)

    cron_file_name = []
    for ent in data:
        m = re.search('Logs', ent)
        if m is not None and ent[0] != '#':
            atemp = re.split('Logs/', ent)
            btemp = re.split('2>&1',  atemp[1])
            cron  = btemp[0]
            cron  = cron.strip()
            cron_file_name.append(cron)
#
#--- removing duplicated lines
#
    cron_file_name = list(set(cron_file_name))

    return cron_file_name

#--------------------------------------------------------------------------------------------------------------------------
#-- modification_date: find the time of the file modified                                                               ---
#--------------------------------------------------------------------------------------------------------------------------

def modification_date(filename):

    """
    find the time of the file modified
    http://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python
    Input:  filename    --- file name
    Output: time        --- time in seconds from 1998.1.1.
    """
    t     = os.path.getmtime(filename)
    ltime = datetime.datetime.fromtimestamp(t)

    return convert_time_format(ltime)

#--------------------------------------------------------------------------------------------------------------------------
#-- convert_time_format: convert time format from datetime format to seconds from 1998.1.1                              ---
#--------------------------------------------------------------------------------------------------------------------------

def convert_time_format(ltime):

    """
    convert time format from datetime format to seconds from 1998.1.1
    Input:  ltime   --- time from datetime.datetime function
    Output: time    --- time in seconds from 1998.1.1
    """

    line = ltime.strftime("%Y%m%d%H%M%S")

    year = line[0]  + line[1] + line[2] + line[3]
    year = int(year)
    mon  = line[4]  + line[5]
    mon  = int(mon)
    day  = line[6]  + line[7]
    day  = int(day)
    hrs  = line[8]  + line[9]
    hrs  = int(hrs)
    mins = line[10] + line[11]
    mins = int(mins)
    secs = line[12] + line[13]
    secs = int(secs)

    return  tcnv.convertDateToCTime(year, mon, day, hrs, mins, secs)

#--------------------------------------------------------------------------------------------------------------------------
#-- file_length: find a file length in line number                                                                       --
#--------------------------------------------------------------------------------------------------------------------------

def file_length(filename):

    """
    find a file length in line number
    Input:  filename    --- inputfile name
    Output: length      --- the file length in line number
    """

    f    = open(filename, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()
    return len(data)

#--------------------------------------------------------------------------------------------------------------------------
#-- compare_and_find: compare the current cron job output to that of the past and find new error messages               ---
#--------------------------------------------------------------------------------------------------------------------------

def compare_and_find(cname, ctime, csize, pname, ptime, psize):

    """
    compare the current cron job output to that of the past and find new error messages
    (we assume that the cron files are accumulate so that any new potion indicated by line # is the new record)
    Input:  cname   --- a list of the cron job record output file names
            ctime   --- a list of the latest update time of each cron job
            csize   --- a list of the lattest size of the cron job record output file
            pname   --- a list of the cron job record output file names in the last recorded file
            ptime   --- a list of the last update time of each cron job
            psize   --- a list of the last size of the cron job record output file
    Output: a file <house_keeping>/Records/<machine>_<user>_error_list

    """

    file_changed = []
    for i in range(0, len(cname)):
        for j in range(0, len(pname)):
            m  = re.search(cname[i], pname[j])
            if m is not None:
                if ctime[i] > ptime[j]:
                    if (str(csize[i]) <=  str(psize[j])):
#
#--- if the file size is same as before or smaller, we assme that the file is replaced
#
                        error = check_for_error(pname[j])

                        if error != 'na':
                            record_error(cname[i], ctime[i], error)
#
#--- if the file size is larger this round, then a new output from cron job is appended to the old file
#
                    if str(csize[i]) > str(psize[j]):
                        error = check_for_error(pname[j], start = int(psize[j]))

                        if error != 'na':
                            record_error(cname[i], ctime[i], error)
                break


#--------------------------------------------------------------------------------------------------------------------------
#-- check_for_error: find errors reported in the file. check only newly appended part                                    --
#--------------------------------------------------------------------------------------------------------------------------

def check_for_error(file, start=0):

    """
    find errors reported in the file. check only newly appended part
    Input:  file    --- cron job output file name
            start   --- the last line of the last record. if this is not givne, check from the beginning
    Output: error_list --- a list of error messages collected from the file
    """

    f    = open(file, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    error_list = []
    for i in range(start, len(data)):
        ent  = data[i]
        lent = ent.lower()
#
#--- check the following parterns to identify the error messages in the file
#
        elist = ['error', 'cannot', 'permission denied', 'not found', 'failed', 'invalid', 'out of range']
        elist = elist + ['undefined']
#
#---if the line contains following messages, they are not real error; so ignore
#
        nlist = ['cleartool', 'file exists', 'cannot remove', '\/usr\/bin\/du']
    
        chk = 0
        for test in elist:
            m = re.search(test, lent)
            if m is not None:
                chk = 1

        if chk == 1:
            for test in nlist:
                m = re.search(test, lent)
                if m is  not None:
                    chk = 0
                    break
    
        if chk > 0:
            error_list.append(ent)

    error_list = list(set(error_list))

    if len(error_list) == 0:
        return 'na'
    else:
        return error_list

#--------------------------------------------------------------------------------------------------------------------------
#-- record_error: append the error messages in the error record file                                                    ---
#--------------------------------------------------------------------------------------------------------------------------

def record_error(fname, stime, error_list):

    """
    append the error messages in the error record file
    Input:  fname       --- a cron job output file name
            stime       --- the time of the last updated
            error_list  --- a list of the error detected from the file
    Output: <house_keeping>/Records/<machine>_<user>_error_list     --- the file contains error messages
    """

    file = house_keeping + 'Records/' +  machine + '_' + user + '_error_list'

    fo   = open(file, 'a')

    for ent in error_list:

        line = fname + ' : ' + str(stime) + ' : ' + ent + "\n"
        fo.write(line)

#--------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    check_cron_records()

