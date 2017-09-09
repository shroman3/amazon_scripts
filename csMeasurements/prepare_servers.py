#!/usr/bin/python
import os
from subprocess import check_output, STDOUT

def parallelscp(copy_from, copy_to, write=True):
	try:
		#-oStrictHostKeyChecking=no
		out = check_output("parallel-scp -l ubuntu -h ../servers.txt -x \"-oStrictHostKeyChecking=no -i /home/shroman/.ssh/aws2.pem\" "
			+ copy_from + " " + copy_to, shell=True)
		if (write and out):
			print out
	except Exception, e:
		if write: 
			print e
		
def parallelssh(command, write=True):
	try:
		# -oStrictHostKeyChecking=no 
		out = check_output("parallel-ssh -l ubuntu -h ../servers.txt -x \"-oStrictHostKeyChecking=no -i /home/shroman/.ssh/aws2.pem\" '" 
						+ command + "'", shell=True)
		if (write and out):
			print out
	except Exception as e:
		if write: 
			print e

def run_command(command, write=True):
	try:
		out = check_output(command, shell=True, stderr=STDOUT)
		if (write and out):
			print out
	except Exception as e:
		if write: 
			print e
			
def prepare_servers():
	os.chdir("/home/shroman/amz_sraid/scripts")
	print "PREPARE CLIENT"
	run_command("cp ../client/* /client/")
	run_command("cp ../server/* /server/")
	run_command("chmod +x /server/*.sh")
	run_command("chmod +x /server/*.py")
	print "PREPARE SERVERS"
	parallelscp("../server/*", "/server/")
	parallelssh("chmod +x /server/*.sh")
	parallelssh("chmod +x /server/*.py")

if __name__ == "__main__":
	prepare_servers()
