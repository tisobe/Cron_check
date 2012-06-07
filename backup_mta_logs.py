#!/usr/local/bin/python2.6

#########################################################################################################################
#															                                                            #
#	backup_mta_logs.py: mv all cron job log to Backup location.							                                #
#															                                                            #
#		t. isobe (isobe@cfa.harvard.edu)									                                            #
#															                                                            #
#		last update: May 30, 2012										                                                #
#															                                                            #
#########################################################################################################################

import sys
import os
import string
import re
import getpass

#------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------

def backup_mta_logs():

#
#--- check who is the user, and set a path to Log location
#
    user = getpass.getuser()
    user = user.strip()
    logdir = '/home/' + user + '/Logs/' 
    tmpdir = '/tmp/' + user + '/ztemp'

#
#--- get list of all files/directories
#
    cmd = 'ls -rlt ' + logdir + ' >' + tmpdir 
    os.system(cmd)

    f    = open(tmpdir, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    cmd = 'rm ' + tmpdir
    os.system(cmd)

#
#--- go though indivisually and if it is a directory, read out files in the diretory
#
    try:
        for ent in data:
       	    atemp = re.split('\s+|\t+', ent)
       	    m = re.search('Past_logs', ent)
            if (m is None) and (ent != logdir) and len(atemp) > 2:
#
#--- if the first letter of the first entry is 'd', it is a directory
#
	        if atemp[0][0] == 'd':
		    cmd = 'ls ' +  logdir + atemp[8] + '/ >' +  tmpdir
		    os.system(cmd)
		    f     = open(tmpdir, 'r')
		    sdata = [line.strip() for line in f.readlines()]
		    f.close()
		    cmd = 'rm ' + tmpdir
		    os.system(cmd)
    
		    for sent in sdata:
		        file = logdir + atemp[8] + '/' + sent
		        cmd  = 'mv ' + file + ' ' + logdir + 'Past_logs/' + atemp[8] + '/'
		        os.system(cmd)
	        else:
		    file = logdir + atemp[8] 
		    cmd  = 'mv ' + file + ' ' + logdir + 'Past_logs/'
		    os.system(cmd)

	f = open(tmpdir, 'w')
	line = ' Monthly Log files backup completed successfully for ' + user + '.\n'
	f.write(line)
	f.close()
#
#--- send out email to notify completion of backup
#
	cmd = 'cat ' + tmpdir + ' | mailx -s "Subject: Cron Log Backup\n" -rcus@head.cfa.harvard.edu isobe@head.cfa.harvard.edu'
	os.system(cmd)

	cmd = 'rm ' + tmpdir
	os.system(cmd)
        
    except:
#
#--- somehow the backup did not go well. notify the failure
#
	f = open(tmpdir, 'w')
	line = ' Monthly Log files backup failed for ' + user + '.\n'
	f.write(line)
	f.close()

	cmd = 'cat ' + tmpdir + ' | mailx -s "Subject: Cron Log Backup Failed\n" -rcus@head.cfa.harvard.edu isobe@head.cfa.harvard.edu'
	os.system(cmd)

	cmd = 'rm ' + tmpdir
	os.system(cmd)
        
#-------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    backup_mta_logs()
