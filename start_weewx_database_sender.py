#!/usr/bin/python
print "Tasos: Check AutoStarting Python Commands"

# In this, 'new' version, only the database as a CSV file will be sent ....

#################################################################
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os
import time
import ftplib
import datetime
import pysftp #sudo pip install pysftp
import subprocess # to collect the output of shell commands


path_here =  os.path.dirname(os.path.realpath(__file__))

############### RECONFIGURE TIME ####################
print ("Try to update System's time from google's clock")
try:
	os.system('sudo date -s "$(curl -s --head http://google.com | grep ^Date: | sed "s/Date: //g")"')
	print('System s time updated!\n')
except:
	print('System s time not updated, possible internet connection missing!!!!\n')

############### DUMP METEO DATALOGER DATA ################

# new method follows:
stop = 0
counter = 0
criterion = 0
while stop==0:
	counter = counter+1
	print('Trying to DUMP METEO data-logger for the '+str(counter)+'-th time')
	batcmd = "yes | sudo wee_device --dump"
	try:
		result = subprocess.check_output(batcmd, shell=True)
		criterion =  result.count("records added")
	except: # subprocess.CalledProcessError as e:
		print ('Re-try..\n')#result = e.result
	if criterion >= 1 or counter>=20: # at most 5 times cause maybe not now data OR data allready DUMPed
		stop =1
print('Data have been DUMPED, result of the command:\n'+result+'\n\n')
# if still problem, try the:
# process = subprocess.Popen(...
# eg read the: http://stackoverflow.com/questions/32942207/command-returned-non-zero-exit-status-1
#########################################################

############### Sqlite Data --> CSV data ################
print (" Transforming database to CSV file into '/var/lib/weewx/weewx_Last.csv' ")
CSV_full_filename = '/var/lib/weewx/weewx_Last.csv'
sdb_filename = '/var/lib/weewx/weewx.sdb'
# command = ['sqlite3 -header -csv "', sdb_filename,'" "select * from archive;" > ',OUT_full_filename]
command = 'sqlite3 -header -csv '+ sdb_filename+' "select * from archive;" > '+ CSV_full_filename
# print command
os.system(command)
print("\n\n")
#########################################################

'''
############### Copy CSV data locally, Compress them + Delete local CSV ################
# apt-get install zip
command = 'zip abc.zip file1 file2 file3'
#########################################################
'''

############################ LOAD Credentials Files !!!!! #######################
# read SFTP from file
sftp_exists = 0;
try:
	text_file = open(path_here+"/"+"SFTP_Details.txt", "r")
	SFTP_details = text_file.read().split('\n')
	text_file.close()
	sftp_exists=1;
except:
	print('SFTP Credentials dont exist here\n')

# read FTP from file
ftp_exists = 0;
try:
	text_file = open(path_here+"/"+"FTP_Details.txt", "r")
	FTP_details = text_file.read().split('\n')
	text_file.close()
	ftp_exists=1;
except:
	print('FTP Credentials dont exist here\n')


# read GMAIL from file
email_exists = 0;
try:
	text_file = open(path_here+"/"+"Gmail_account.txt", "r")
	GMAIL_details = text_file.read().split('\n')
	text_file.close()
	gmail_user = GMAIL_details[0]
	gmail_pwd = GMAIL_details[1]
	gmail_recepient = GMAIL_details[2]
	gmail_subject = GMAIL_details[3]
	del GMAIL_details
	email_exists=1;
except:
	print('EMAIL Credentials dont exist here\n')

del text_file
#########################################################


############################  SFTP or FTP UPLOAD  many tries #######################
print ("Try to upload COMPLETE weewx SQlite LIBRARY TO SFTP .....")

skt=1;
maxtries=20;
while (skt <= maxtries and sftp_exists==1):  ## try 20 times (if connection will be corrupted) to upload to SFTP
	try:
		cinfo = {'host':SFTP_details[0],'port':int(float(SFTP_details[1])),'username':SFTP_details[2], 'password':SFTP_details[3]}
		with pysftp.Connection(**cinfo) as sftp:
			source = CSV_full_filename
			destination = SFTP_details[4]+"/"+"weewx_" + (time.strftime("%Y_%m_%d_%H_%M")) + ".csv"
			sftp.put(source,destination)
			sftp.close()
		print "SFTP data uploaded correctly !\n\n"
		break
	except:
		print "\n Re-trying SFTP connection... for the "+str(skt)+"-th time of "+str(maxtries)
		skt=skt+1


################# SEND ME IP, WIRELESS STUFF AND FREE SPACE REMAINING ###############
# NEEDS THE: "sudo apt-get install python-setuptools","sudo easy_install pip", "sudo pip install requests",   "sudo pip install netifaces",    "sudo pip install wifi"
try:
	import requests, socket 
	from netifaces import interfaces, ifaddresses, AF_INET
except ImportError: # 1rst time running = Installation
	os.system("sudo apt-get install python-setuptools")
	os.system("sudo easy_install pip")
	os.system("sudo pip install requests") 
	os.system("sudo pip install netifaces") 
	os.system("sudo pip install wifi") 
	import requests, socket 
	from netifaces import interfaces, ifaddresses, AF_INET



filename = "REPORT_" + (time.strftime("%Y_%m_%d_%H_%M_%S")) + ".txt"
print (" Writing file: " + filename)

if  os.path.isdir(path_here+"/Reports"): ## check if directory exists ....
	full_fname = path_here+'/Reports/'+filename 
else:
	os.system("sudo mkdir "+path_here+"/Reports")
	full_fname = path_here+'/Reports/'+filename 

#full_fname = path_here+'/Reports/'+filename 
file = open(full_fname, "w");

# write down my ip !!!
r=requests.get(r'http://jsonip.com')
ip = r.json()['ip']
print 'Your IP is',ip
file.write('Your IP is : '+ip+'\n')

for ifaceName in interfaces():
	addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET,[{'addr':'No IP address'}])]
	print '%s: %s' % (ifaceName,', '.join(addresses))
	file.write(ifaceName+' : ' +', :'.join(addresses)+'\n')
	
## write down the discovered  WIFIs !!!!
try:     ####### if there is WiFi Connection ....
	from wifi import Cell,Scheme
	file.write('\n'+'=== WIFIs ==='+'\n')
	
	for cell in Cell.all('wlan0'):
		if cell.encrypted :
			KEIMENO  = "ssid = "+ cell.ssid + " signal = "+str(cell.signal)+ " Encrypted = "+str(cell.encrypted)+" address = "+cell.address + " Encryption = " + cell.encryption_type
			print KEIMENO
			file.write(KEIMENO+'\n')
		else: 
			KEIMENO = "ssid = "+ cell.ssid + " signal = "+str(cell.signal)+ " Encrypted = "+str(cell.encrypted)+" address = "+cell.address
			print KEIMENO
			file.write(KEIMENO+'\n')
except:
	print ("WiFi s not Written on the report file ....");


## FREE DISK SPACE ##
stat = os.statvfs('/home/')
empty_space_MB = (stat.f_frsize * stat.f_bavail)/1024/1024
print " free Space Avaiable = "+str(empty_space_MB)+"MB"
file.write('\n'+'=== Free Space Avaiable ==='+'\n')
file.write(" free Space Avaiable = "+str(empty_space_MB)+"MB"+'\n')
file.close()

report_uploaded_sftp = 0;
if (sftp_exists==1) :
	try:
		cinfo = {'host':SFTP_details[0],'port':int(float(SFTP_details[1])),'username':SFTP_details[2], 'password':SFTP_details[3]}
		with pysftp.Connection(**cinfo) as sftp:
			destination = SFTP_details[4]+"/"+filename
			sftp.put(full_fname,destination)
			sftp.close()
			report_uploaded_sftp = 1;
		print "Report uploaded on SFTP \n"
	except:
		print "Report not uploaded on SFTP !!!\n\n"

report_uploaded_ftp = 0;
if (ftp_exists==1) :
	try:
		s = ftplib.FTP(FTP_details[0],FTP_details[1],FTP_details[2]) 
		f = open(full_fname,'rb')   
		try:
			s.cwd(FTP_details[3])
			print("REport will be uploaded to"+FTP_details[3]+" DIR of the FTP")
		except:
			print("REport will be uploaded to main DIR of the FTP")
		s.storbinary('STOR ' + filename, f)   
		f.close()                                
		s.quit()
		report_uploaded_ftp = 1
		print "Report uploaded on FTP \n"
	except:
		print "Report not uploaded on FTP !!!\n\n"

if (report_uploaded_sftp == 1 or report_uploaded_ftp==1):
	os.system("sudo rm "+full_fname)
	print "Report local file deleted !!! \n"

#################  IF IT IS THE FIRST DAY OF MONTH && MONTH=EVEN EMPTY THE DATABASE !!!! #############################
wra = time.strftime("%H")
mera_mina = time.strftime("%d")
path_here =  os.path.dirname(os.path.realpath(__file__))

now = datetime.datetime.now();
minas_nmr  = now.month;
if (minas_nmr%2 ==0):
	print('This is an EVEN month');
else:
	print('This is an ODD month');
	
### EMPTY THE DATABASE !!!!
if (mera_mina == "01" and minas_nmr%2 ==0 and int(float(wra))<=24 ): #deleted hour criterion
	os.system("sudo mv /var/lib/weewx/weewx.sdb  /var/lib/weewx/weewx_" + (time.strftime("%Y_%m_%d_%H_%M")) + ".sdb")
	print ("Database has been emptied !!!")
	os.system("sudo rm "+path_here+"/Meteo_Data/*")
	print ("Local files that where not uploaded to SFTP/FTP Have been deleted!!!")

### send me the Backups (SFTP)!!!
if (mera_mina == "01" and minas_nmr%2 ==0 and sftp_exists==1): # and int(float(wra))>7
	print ("Try to upload BACKUPED weewx ALL THE FILES TO SFTP .....")
	skt=1;
	maxtries=20;
	while skt <= maxtries :
		try:
			cinfo = {'host':SFTP_details[0],'port':int(float(SFTP_details[1])),'username':SFTP_details[2], 'password':SFTP_details[3]}
			with pysftp.Connection(**cinfo) as sftp:
				print(" Connected to SFTP For complete backups Uploading ....");
				source_dir ='/var/lib/weewx/';
				remote_dir = SFTP_details[4]+"/"+"backup_"+(time.strftime("%Y_%m_%d_%H_%M"))+"/"
				try:  # check If the directory we need to upload exists !!!!!
					sftp.chdir(remote_dir)  # Test if remote_path exists
					print "Remote dir exists"
				except IOError:
					sftp.mkdir(remote_dir)  # Create remote_path
					print "Remote dir created!!!"
				print "Trying upload to the : SERVER/"+remote_dir
				sftp.put_d(source_dir, remote_dir, preserve_mtime=True) # or put_r ???
				sftp.close()
			print "SFTP data uploaded correctly !\n\n"
			break
		except:
			print (" NOT Connected to SFTP For complete backups Uploading ....");
			print "\n Re-trying SFTP connection... for the "+str(skt)+"-th time of "+str(maxtries)
			skt  = skt +1;


### send me the Backups (FTP)!!!
if (mera_mina == "01" and minas_nmr%2 ==0 and int(float(wra))>7 and ftp_exists==1):
	print ("Not yet programmed to upload the BACKUPED weewx files TO FTP .....")

################################################################################



########################### SEND EMAILS  #################################3
# print " Try to send email ...."
now1 = time.strftime("%c")
#print "Current date & time = " + time.strftime("%c")
wra = time.strftime("%H")
#print "Current Hour(00-23) = " + wra #time.strftime("%H")
mera = time.strftime("%w")
#print "Current Day(0(Sunday)-6)  = " + mera #time.strftime("%w")


def mail(to, subject, text, attach):
   msg = MIMEMultipart()

   msg['From'] = gmail_user
   msg['To'] = to
   msg['Subject'] = subject

   msg.attach(MIMEText(text))

   part = MIMEBase('application', 'octet-stream')
   part.set_payload(open(attach, 'rb').read())
   Encoders.encode_base64(part)
   part.add_header('Content-Disposition',
           'attachment; filename="%s"' % os.path.basename(attach))
   msg.attach(part)

   mailServer = smtplib.SMTP("smtp.gmail.com", 587)
   mailServer.ehlo()
   mailServer.starttls()
   mailServer.ehlo()
   mailServer.login(gmail_user, gmail_pwd)
   mailServer.sendmail(gmail_user, to, msg.as_string())
   # Should be mailServer.quit(), but that crashes...
   mailServer.close()
   

   
wra_nmr  = now.hour;
print ("Now time = "+str(wra_nmr))
mera_nmr  = datetime.datetime.today().weekday();  # where Monday is 0 and Sunday is 6.
print ("Now weekday = "+str(mera_nmr))

'''
if (mera_nmr == 0 and wra_nmr >= 17):   #deutera apogeuma
	mail(gmail_recepient,gmail_subject,"This is a email sent with python","/home/weewx/archive/weewx.sdb");
	print ("email sent")
elif (mera_nmr == 3 and wra_nmr>= 10 and wra_nmr<18):#pempti prwi-apogeuma
	mail(gmail_recepient,gmail_subject,"This is a email sent with python","/home/weewx/archive/weewx.sdb");
	print ("email sent")
else:
	print("email not sent..., will be sent another day....")
'''


if (mera_nmr == 0):   # 0==deutera , 3 = pempti
	mail(gmail_recepient,gmail_subject,"This is a email sent with python",CSV_full_filename);
	print ("email sent")
else:
	print("email not sent..., will be sent another day....\n\n")

	
	
	
############### SUNDAY  = Lucky Day --> You Receive a Database File Too  (only SFTP) #################
SDB_full_filename = '/var/lib/weewx/weewx.sdb'
if (mera_nmr == 6):   # 0==deutera , 3 = pempti
	try:
		cinfo = {'host':SFTP_details[0],'port':int(float(SFTP_details[1])),'username':SFTP_details[2], 'password':SFTP_details[3]}
		with pysftp.Connection(**cinfo) as sftp:
			source = SDB_full_filename
			destination = SFTP_details[4]+"/"+"weewx_" + (time.strftime("%Y_%m_%d_%H_%M")) + ".sdb"
			sftp.put(source,destination)
			sftp.close()
			print "SFTP data uploaded correctly !\n\n"
	except:
		print (" NOT Connected to SFTP for SDB backups Uploading, C U next Sunday ....");


############### SHUTDOWN ##############################
# ending and shutdown
print ("Power Off Machine in 7 minutes (Ctrl+C to cancel)")
time.sleep(7*60)
os.system("sudo poweroff")






