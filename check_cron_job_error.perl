#!/usr/bin/perl 

#################################################################################################################
#														#
#	check_cron_job_error.perl: check cronjob error messages							#
#														#
#		author: t. isobe (tisobe@cfa.harvard.edu)							#
#														#
#		last update: Feb 06, 2012									#
#														#
#################################################################################################################

#
#--- find a user name
#

$tail = rand();
$tail = int(1000 * $tail);
$zout = 'zxc'."_$tail";

system("id  |cat > $zout");
$input = `cat $zout`;
@atemp = split(/\(/, $input);
@btemp = split(/\)/, $atemp[1]);
$user  = $btemp[0];
system("rm $zout");

chomp $user;

#
#--- find a machine name
#

system("uname -n |cat > $zout");
$machine = ` cat $zout `;
system("rm $zout");

chomp $machine;

#
#--- find today's date
#

($nsec, $nmin, $nhour, $nmday, $nmon, $nyear, $nwday, $nyday, $nisdst)= localtime(time);

$nyear = 1900 + $nyear;
$nmon  = $nmon + 1;
$nyday = $nyday + 1;

#
#--- check whether it is a leap year
#

$base  = 365;
$chk   = 4.0 * int(0.25 * $nyear);
if($chk == $nyear){
	$base = 366;
}

$ntime = $nyear + $nyday/$base;			#--- time in a fractional year

#
#--- set the path to Logs directory
#

$HOME = '/home/'."$user".'/';

#
#--- extract crontab list and extract information
#

system("crontab -l > ztemp");

open(FH, "./ztemp");

@min   = ();
@hour  = ();
@mday  = ();
@month = ();
@wday  = ();
@cmd   = ();
@logs  = ();
@mark  = ();
$cnt   = 0;

OUTER:
while(<FH>){
	if($_ =~ /#/){
		next OUTER;
	}
	chomp $_;
	@atemp = split(/\s+/, $_);
	@btemp = split(/$atemp[5]/, $_);
#
#--- we need to ignore the log created with ">>" ; so check whether it is '>' or ">>"
#
	if($btemp[1] =~ />>/){
		push(@mark, 1);
	}else{
		push(@mark, 0);
	}
	
	@ctemp = split(/>/, $btemp[1]);

	if($ctemp[1] !~ /\w/){
		$line = $ctemp[2];
		$line =~ s/ 2//g;
		$line =~ s/^\s+|\s+$//g;

		if($line !~ /Logs/){
			next OUTER;
		}
		push(@log, $line);
	}else{
		$line = $ctemp[1];
		$line =~ s/ 2//g;
		$line =~ s/^\s+|\s+$//g;

		if($line !~ /Logs/){
			next OUTER;
		}
		push(@log, $line);
	}

	push(@min,   $atemp[0]);
	push(@hour,  $atemp[1]);
	push(@mday,  $atemp[2]);
	push(@month, $atemp[3]);
	push(@wday,  $atemp[4]);
	$line = "$atemp[5] $ctemp[0]";
	push(@cmd,   $line);

	$cnt++;
}
close(FH);
system("rm ztemp");

#
#--- now start checking the errors
#

$wcnt = 0;
$ecnt = 0;

$zwarning = "zwarning_"."$user".'_'."$machine";
$zerror   = "zerror_"."$user".'_'."$machine";

open(OUT1, ">$zwarning");
open(OUT2, ">$zerror");

OUTER:
for($i = 0; $i < $cnt; $i++){
#
#--- if the log is created with ">>" direction, ignore
#
	if($mark[$i] > 0){
		next OUTER;
	}
#
#--- find out when the last log is crated
#

	$input = `ls -l $log[$i]`;
	@atemp = split(/\s+/, $input);
	$umon  = change_month_format($atemp[5]);
	$uday  = $atemp[6];

	if($atemp[7] =~ /:/){
		$uyday = find_ydate($nyear, $umon, $uday);
		if($uyday > $nyday){
			$uyear = $nyear -1;
		}else{
			$uyear = $nyear;
		}
		$utime = $atemp[7];
	}else{
		$uyear = $atemp[7];
		$uyday = find_ydate($uyear, $umon, $uday);
		$utime = '00:00';
	}

#
#--- compare the log creation date and cron activation time; if there a large descrepancy, mark it.
#

	$base = 365;
	$chk  = 4 * int(0.25 * $uyear);
	if($chk == $uyear){
		$base = 366;
	}
	$utime = $uyear + $uyday/$base;
	$diff  = 365 * ( $ntime - $utime);

	$uchk  = 0;
	if($diff > 1){
		if($wday[$i] =~ /\*/){
			if($mday[$i] =~ /\*/){
				if($month[$i] =~ /\*/){
#
#--- for the case cron job is set off every day
#
					$uchk = 1;
				}else{
					if($mday[$i] =~ /\*/){
						$cday = 1;
					}else{
						$cday = $mday[$i];
					}
					if($month[$i] > $nmon){
						$cyear  = $nyear - l;
					}else{
						$cyear  = $nyear;
					}
					$cydate = find_ydate($cyear, $month[$i], $cday);
					$base = 365;
					$chk  = 4.0 * int(0.25 * $cyear);

					if($cyear == $chk){
						$base = 366;
					}

					$ctime = $cyear + $cydate/$base;
					$cdiff = 365 * ($ntime - $ctime);
#
#---- set length appropiate to compare: a year, a month, or  two days (for the case cron job runs everyday)
#
					$comp_val = 365;
					if($day[$i] =~ /\*/){
						$comp_val = 2;
					}elsif($month[$i] =~ /\*/){
						$comp_val = 30;
					}

					if(abs($cdiff - $diff) > $comp_val){
						$uchk = 1;
					}
				}
			}else{
#
#--- case the date of the month is set for cron job
#
				if($month[$i] =~/\*/){
					if($diff > 31){
						$uchk = 1;
					}
				}else{
					$cday = $mday[$i];

					if($month[$i] > $nmon){
						$cyear  = $nyear - l;
					}else{
						$cyear  = $nyear;
					}
					$cydate = find_ydate($cyear, $month[$i], $cday);
					$base = 365;
					$chk  = 4.0 * int(0.25 * $cyear);

					if($cyear == $chk){
						$base = 366;
					}

					$ctime = $cyear + $cydate/$base;
					$cdiff = 365 * ($ntime - $ctime);


					$comp_val = 365;
					if($day[$i] =~ /\*/){
						$comp_val = 2;
					}elsif($month[$i] =~ /\*/){
						$comp_val = 30;
					}

					if(abs($cdiff - $diff) > $comp_val){
						$uchk = 1;
					}
				}
			}
		}else{
#
#---- for the case week day is set for cron job
#
			if($diff > 4){
				$uchk = 1;
			}
		}
	}

		
#
#--- if cron job is not running for a while, sent warning 
#
	if($uchk > 0){
		print OUT1 "$cmd[$i]\n";
		$lmon = change_month_format($umon);
		print OUT1 "\tseems not active. The last update: $lmon $uday, $uyear ";
		print OUT1 "(cron set: $min[$i] : $hour[$i] : $mday[$i] : $month[$i] : $wday[$i] )\n\n";
		$wcnt++;
	}else{
#
#--- check the log has "error" message
#
		$input = `cat $log[$i]`;

		if($input =~ /Error/ || $input =~ /Can/){
	
			print OUT2 "$cmd[$i]\n";
	
			@lines = split(/\n/, $input);
			@error_save = ();
			OUTER2:
			foreach $ent (@lines){
				if($ent =~ /Error/ || $ent =~ /Can/){
					foreach $comp (@error_save){
						if($ent =~ /$comp/){
							next OUTER2;
						}
					}
					push(@error_save, $ent);
					print OUT2 "\t\t$ent\n\n";
	
				}
			}
			close(FH);
			$ecnt++;
		}
	}
}
close(OUT2);
close(OUT1);


#
#--- if there are any warnings/errors, print a file, and send out email
#

if($ecnt == 0 && $wcnt == 0){

#
#--- for the case no error/warning, just sent email to tell a test that this script is still running
#
	open(OUT, "> $zout");
	print OUT "No Cron Error Today for $user on $machine.\n";
	close(OUT);
	system("cat ./$zout | mailx -s\"No Cron Error Today:  $user on $machine\n\" -rcus\@head.cfa.harvard.edu isobe\@head.cfa.harvard.edu");
	system("rm $zout");

}else{

#
#--- if there are errors/warnings, create a log file and send out email to appropirate people
#
	
	if($nyday < 10){
		$dyday = '00'."$nyday";
	}elsif($nyday < 100){
		$dyday = '0'."$nyday";
	}else{
		$dyday = $nyday;
	}

	$out_file = 'cron_warning_'."$user".'_'."$machine".'_'."$nyear$dyday";

	if($wcnt > 0){
		open(OUT, ">$out_file");
		print OUT "-------\n";
		print OUT "Warning\n";
		print OUT "-------\n\n";
		close(OUT);
		system("cat $zwarning >> $out_file");
	}

	if($ecnt > 0){
		if($wcnt > 0){
			open(OUT, ">>$out_file");
			print OUT "\n\n";
		}else{
			open(OUT, ">$out_file");
		}

		print OUT "-------\n";
		print OUT "Errors \n";
		print OUT "-------\n\n";
		close(OUT);
		system("cat $zerror >> $out_file");
	}
	
	system("cat $out_file | mailx -s\"Subject: Cron Errors --- $user on $machine\n\" -rcus\@head.cfa.harvard.edu isobe\@head.cfa.harvard.edu");
	system("mv $out_file /data/mta/Script/Cron_check/Error_logs/");
	system("chmod 775 /data/mta/Script/Cron_check/Error_logs/$out_file");
	system("chgrp mtagroup  /data/mta/Script/Cron_check/Error_logs/$out_file");
}


system("rm $zwarning $zerror");


############################################################
### change_month_format: change month format             ###
############################################################

sub change_month_format{
        my ($month, $omonth);
        ($month) = @_;
        if($month =~ /\d/){
                if($month == 1){
                        $omonth = 'Jan';
                }elsif($month == 2){
                        $omonth = 'Feb';
                }elsif($month == 3){
                        $omonth = 'Mar';
                }elsif($month == 4){
                        $omonth = 'Apr';
                }elsif($month == 5){
                        $omonth = 'May';
                }elsif($month == 6){
                        $omonth = 'Jun';
                }elsif($month == 7){
                        $omonth = 'Jul';
                }elsif($month == 8){
                        $omonth = 'Aug';
                }elsif($month == 9){
                        $omonth = 'Sep';
                }elsif($month == 10){
                        $omonth = 'Oct';
                }elsif($month == 11){
                        $omonth = 'Nov';
                }elsif($month == 12){
                        $omonth = 'Dec';
                }
        }else{
                if($month =~ /jan/i){
                        $omonth = 1;
                }elsif($month =~ /feb/i){
                        $omonth = 2;
                }elsif($month =~ /mar/i){
                        $omonth = 3;
                }elsif($month =~ /apr/i){
                        $omonth = 4;
                }elsif($month =~ /may/i){
                        $omonth = 5;
                }elsif($month =~ /jun/i){
                        $omonth = 6;
                }elsif($month =~ /jul/i){
                        $omonth = 7;
                }elsif($month =~ /aug/i){
                        $omonth = 8;
                }elsif($month =~ /sep/i){
                        $omonth = 9;
                }elsif($month =~ /oct/i){
                        $omonth = 10;
                }elsif($month =~ /nov/i){
                        $omonth = 11;
                }elsif($month =~ /dec/i){
                        $omonth = 12;
                }
        }
        return $omonth;
}

##################################################
### find_ydate: change month/day to y-date     ###
##################################################

sub find_ydate {

##################################################
#       Input   $tyear: year
#               $tmonth: month
#               $tday:   day of the month
#
#       Output  $ydate: day from Jan 1<--- returned
##################################################

        my($tyear, $tmonth, $tday, $ydate, $chk);
        ($tyear, $tmonth, $tday) = @_;

        if($tmonth == 1){
                $ydate = $tday;
        }elsif($tmonth == 2){
                $ydate = $tday + 31;
        }elsif($tmonth == 3){
                $ydate = $tday + 59;
        }elsif($tmonth == 4){
                $ydate = $tday + 90;
        }elsif($tmonth == 5){
                $ydate = $tday + 120;
        }elsif($tmonth == 6){
                $ydate = $tday + 151;
        }elsif($tmonth == 7){
                $ydate = $tday + 181;
        }elsif($tmonth == 8){
                $ydate = $tday + 212;
        }elsif($tmonth == 9){
                $ydate = $tday + 243;
        }elsif($tmonth == 10){
                $ydate = $tday + 273;
        }elsif($tmonth == 11){
                $ydate = $tday + 304;
        }elsif($tmonth == 12 ){
                $ydate = $tday + 334;
        }
        $chk = 4 * int (0.25 * $tyear);
        if($chk == $tyear && $tmonth > 2){
                $ydate++;
        }
        return $ydate;
}

