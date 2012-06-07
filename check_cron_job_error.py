#!/usr/local/bin/python2.6

#########################################################################################################################
#                                                                                                                       #
#       check_cron_job_error.py: find new error messages from cron log files for a given machine and a given user       #
#                                                                                                                       #
#                                                                                                                       #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                                               #
#                                                                                                                       #
#               last update: Jun 7, 2012                                                                                #
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

#
#--- possible machine names and user name lists
#
cpu_list     = ['rhodes', 'colossus', 'r2d2']
usr_list     = ['mta', 'cus']
cpu_usr_list = ['rhodes_mta', 'rhodes_cus', 'colossus_mta', 'r2d2_mta']

#
#--- error log directory
#

error_log_dir = '/data/mta/Script/Cron_check/Error_logs/'

#
#--- html page location
#

html_dir = '/data/mta_www/mta_cron/'

#
#--- temp directory
#

tempdir = '/tmp/' + user + '/'

tempout = tempdir + 'ztemp'                             #--- temporary file to put data

#
#--- email list
#

admin = 'isobe@head.cfa.harvard.edu'
email_list = 'isobe@head.cfa.harvard.edu,swolk@head.cfa.harvard.edu,brad@head.cfa.harvard.edu'
email_list = 'isobe@head.cfa.harvard.edu'

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
    error_logs = error_log_dir + 'error_list_' + machine + '_' + user

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
        cmd = 'mv '+ error_logs_old + ' ' + error_log_dir + 'Past_logs/.'
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
#--- check whether this error message belongs to this machine (and the user)
#
        mchk = 0
        for comp in cron_file_name:
            m = re.search(comp, file)

            if m is not None:
                mchk = 1

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
                        sent = "".join(ent.split())             #---- removing all white spaces
                        chk = 0
                        for comp in prev_list:
                            scomp = "".join(comp.split())
                            if sent == scomp:
                                chk = 1
    
                        if chk ==  0:
                            prev_list.append(ent)
                            new_error.append(ent)
    
                    if len(new_error) > 0:
                        error_dict[file]     = prev_list
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
    old_log = error_logs + '~'
    cmd     = 'mv ' + error_logs + ' ' + old_log
    os.system(cmd)

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
        cmd = 'cat ' + tempout + ' | mailx -s "Subject: Cron Error : ' + user + ' on ' + machine + '"  ' + email_list
        os.system(cmd)
#
#--- add the error message to a recored 
#
        add_to_log()
#
#--- update html page
#
        update_html()
        update_main_html()


    else:
#
#--- if there is no error, notify that fact to admin
#
        f = open(tempout, 'w')
        line = '\nNo error is found today on ' + machine + ' by a user ' + user + '.\n'
        f.write(line)
        f.close()
        cmd = 'cat ' + tempout + ' | mailx -s "Subject: No Cron Error : ' + user + ' on ' + machine + '" ' + admin
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

#--------------------------------------------------------------------------------------------------------------------------
#-- add_to_log: appending error logs extracted Logs location to a record file which will be used for html               ---
#--------------------------------------------------------------------------------------------------------------------------

def add_to_log():

    """
    appending error logs extracted Logs location to a record file which will be used for html 
    no input, but it uses machine and user information to set up a file. 

    """
    tdate = current_time_from_machine()

    atemp = re.split('\s+|\t+', tdate)
    day   = atemp[0] 
    mon   = atemp[1]
    date  = atemp[2]
    if int(date) < 10:
        date = ' ' + date
    year  = atemp[5]

    tstamp= day + ' ' + mon + ' ' + date + ' ' + year       #---- this is the time format used for a log
#
#--- set a output file name
#
    dmon = tcnv.changeMonthFormat(mon)                      #--- chnage mon from letters to digit
    mon  = str(dmon)
    if dmon < 10:
        mon = '0' + mon
    
    file = error_log_dir + machine + '_' + user + '_' + mon + '_' + year
    f2   = open(file, 'a')

#
#--- append error logs to the error file
#
    dash   ='-----------------\n'
    border = '#############################################################################\n'

    f2.write('\n')
    f2.write(dash)
    f2.write(tstamp)
    f2.write('\n')
    f2.write(dash)

    f3  = open(tempout, 'r')
    data3 = [line for line in f3.readlines()]
    f3.close()

    for ent3 in data3:
        f2.write(ent3)
        f2.write('\n')

    f2.write('\n')
    f2.write(border)

    f2.close()


#--------------------------------------------------------------------------------------------------------------------------
#-- current_time_from_machine: using a date function on unix, get a current time                                        ---
#--------------------------------------------------------------------------------------------------------------------------

def current_time_from_machine():
#
#--- find today (machine) date
#

    tempdate = tempdir + 'zdate'
    cmd = 'date > ' + tempdate
    os.system(cmd)
    f     = open(tempdate, 'r')
    tdate = f.readline().strip()
    f.close()
    cmd = 'rm ' + tempdate
    os.system(cmd)

    return tdate

#--------------------------------------------------------------------------------------------------------------------------
#-- update_html: create/update error html page for a gvien machine and a user                                           ---
#--------------------------------------------------------------------------------------------------------------------------

def update_html():

    """
    create/update error html page for a gvien machine and a user
    input: error_list_<cpu>_<user>, wheren cpu and user are found from the machine running this and account using.
    output: cron_error_<cpu>_<usr>.html in html_dir.
    """

#
#--- find the current time
#
    [year, mon, day, hours, min, sec, weekday, yday, dst] = tcnv.currentTime('Local')

    syear = str(year)
    smon  = str(mon)
    lmon = tcnv.changeMonthFormat(mon)

    if mon < 10:
        smon = '0' + smon
#
#--- set the file name and a hmtl page name
#
    file = error_log_dir + machine + '_' + user + '_' + smon + '_' + syear
    html = html_dir + 'cron_error_' + machine + '_' + user + '_' + smon + '_' + syear + '.html'
#
#--- start writing the html page
#
    out  = open(html, 'w')
    line = '<!DOCTYPE html>\n'
    line = line + '<html>\n'
    line = line + '<head>\n'
    line = line + '<title>Cron Error Log for ' + user.upper() + ' on ' +  machine.upper() + ': ' + lmon + ' ' + syear + '</title>\n'
    line = line + '<link rel="stylesheet" type="text/css" href="/mta/REPORTS/Template/mta_style_short.css" />\n'
    line = line + '</head>\n'
    line = line + '<body>\n'
    line = line + '<h3 style="padding-bottom: 10px"> Cron Error Log for ' + user.upper() + ' on ' +  machine.upper() + ': ' + lmon + ' ' + syear + '</h3>\n\n'
    line = line + '<hr />\n'
    line = line + '<pre style="padding-left: 5px;padding-bottom:10px">\n' 

    out.write(line)
#
#--- write the content of error_list
#
    f    = open(file, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    for ent in data:
        out.write(ent)
        out.write('\n')

    line = '</pre>\n'
    line = line + '<br /><hr /><br />\n'
    line = line + 'Back to <a href="http://asc.harvard.edu/mta_days/mta_cron/cron_error_main.html">Top Page</a>\n'
    line = line + '\n</body>\n'
    line = line + '</html>\n'
    out.write(line)

    out.close()


#--------------------------------------------------------------------------------------------------------------------------
#--- update_main_html: update the main cron error log html page                                                         ---
#--------------------------------------------------------------------------------------------------------------------------

def update_main_html():

    """
    update the main cron error log html page 
    input: get from the list from indivisula html page, e.g., cron_error_rhodes_mta.html
    output: cron_error_main.html
    """

#
#--- create a list of file name (header)
#

#    file_list = []
#    for cpu in cpu_list:
#        for name in usr_list:
#            filename = cpu + '_' + name
#            file_list.append(filename)

    file_list = cpu_usr_list                    #-- we may go back to above scheme in future, but this si fine for now

#
#--- find current time
#
    [year, mon, day, hours, min, sec, weekday, yday, dst] = tcnv.currentTime('Local')

    syear = str(year)
    smon  = str(mon)
    lmon = tcnv.changeMonthFormat(mon)

    if mon < 10:
        smon = '0' + smon

#
#--- start writing the html page
#
    html = html_dir +  'cron_error_main.html'

    out  = open(html, 'w')
    line = '<!DOCTYPE html>\n'
    line = line + '<html>\n'
    line = line + '<head>\n'
    line = line + '<title>Cron Error Main page</title>\n'
    line = line + '<link rel="stylesheet" type="text/css" href="/mta/REPORTS/Template/mta_style_short.css" />\n'
    line = line + '</head>\n'
    line = line + '<body>\n'
    line = line + '<h2 style="padding-bottom: 10px"> Cron Error Log</h2>\n\n'
    line = line + '<pre style="padding-left: 5px;padding-bottom:10px">\n' 
    line = line + '<hr />\n'
    line = line + '<table border=2 cellpadding = 5 cellspacing =5>\n'
    line = line + '<tr><th>Period</th>'
    out.write(line)

    for ent in file_list:
        atemp = re.split('_', ent)
        line = '<th>' + atemp[1] + ' on ' + atemp[0]  + '</th>'
        out.write(line)

    out.write('</tr>\n')
#
#--- find the names of each html file (e.g. cron_error_rhodes_mta_06_2012.html)
#
    templist = tempdir + 'zlist'
    cmd = 'ls ' + html_dir + '> ' + templist
    os.system(cmd)
    f    = open(templist, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()
    cmd = 'rm ' + templist
    os.system(cmd)

    error_file_list = []

    for ent in data:
        m1 = re.search('.html', ent)
        m2 = re.search('cron_error_main.html', ent)
        if (m1 is not None) and (m2 is None):
            error_file_list.append(ent)

#
#--- start printing each row; column is ordered newest to oldeest
#
    year_list = range(2012, year + 1)
    year_list.reverse()
    month_list = range(1,13)
    month_list.reverse()

    for dyear in year_list:
        for dmonth in month_list:
            if dyear == 2012 and dmonth < 6:                    #---- this is the year/month the script was started
                break

            if dyear <= year and dmonth <=  mon:

                lmon = tcnv.changeMonthFormat(dmonth)           #--- convert month in digit to letters

                line = '<tr><th>' + lmon + ' ' + str(dyear) + '</th>'
                out.write(line)
#
#--- check which file (e.g. cron_error_rhodes_mta_06_2012.html) actually exists
#
                for fent in file_list:
                    smon  = str(dmonth)
                    if dmonth < 10:
                        smon = '0' + smon
                    fname = 'cron_error_' + fent + '_' + smon + '_' + str(dyear) + '.html'
                    chk = 0
                    for comp in error_file_list:
                        if fname == comp:
                            chk = 1
                            break
                    if chk > 0:
#
#--- if exist, create a link
#
                        line = '<td style="color:red;text-align:center"><a href="' + fname + '">Error List</a></td>'
                    else:
                        line = '<td style="text-align:center">No Error</td>'
                    out.write(line)
                out.write('</tr>\n')

    out.write('</table>\n\n')

    out.write('<br /> <hr />\n')

    tdate = current_time_from_machine()

    line = '<pstyle="font-size:95%"><em>Last Update: ' + tdate + '</em><br />\n'
    line = line + 'If you have any questions about this page, contact <a href="mailto:tisobe@head.cfa.harvard.edu">tisobe@head.cfa.harvard.edu</a>.</p>\n'
    out.write(line)

    line = '\n</body>\n'
    line = line + '</html>\n'
    out.write(line)

    out.close()




#-----------------------------------------------------------------

if __name__ == '__main__':

    check_cron()
#    update_html()
#    update_main_html()

