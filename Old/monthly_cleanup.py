#!/usr/local/bin/python2.6

import sys
import os
import string
import re
import getpass

#------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------

def monthly_cleanup():

#
#--- check who is the user, and set a path to Log location
#
    user    = getpass.getuser()
    user    = user.strip()
    logdir  = '/home/' + user + '/Logs/'
    pastdir = logdir + 'Past_logs/'

    cmd     = 'mv ' + logdir + '/*.cron ' + pastdir
    os.system(cmd)

    try:
        cmd     = 'mv ' + logdir + '/*/*.cron ' + pastdir
        os.system(cmd)
    except:
        pass

#------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    monthly_cleanup()
