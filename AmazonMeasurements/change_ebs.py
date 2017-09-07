#!/usr/bin/python

from subprocess import check_output, STDOUT
import sys

def run_command(command, write=True):
	try:
		out = check_output(command, shell=True, stderr=STDOUT)
		if (write and out):
			print out
	except Exception as e:
		if write: 
			print e
		
def parse_machines(filename):
	counter = 0;
	machines = []
	machine = None
	with open(filename, "r") as f:
			for line in f.readlines():
				if ((counter % 4) == 0):
					if machine:
						machines.append(machine)
					machine = [line.strip()]
				else:
					machine.append(line.strip())
				counter += 1
				
	machines.append(machine)
	return machines
				

def change_ebs(machines, optimized):
	for region in machines:
		print region
		run_command("aws ec2 modify-instance-attribute --instance-id " + region[1] + " --region " + region[0] + " " + optimized)
		run_command("aws ec2 modify-instance-attribute --instance-id " + region[2] + " --region " + region[0] + " " + optimized)
		run_command("aws ec2 modify-instance-attribute --instance-id " + region[3] + " --region " + region[0] + " " + optimized)

if __name__ == "__main__":
	if (len(sys.argv) != 3):
		print "Please call the change ebs optimized in the following manner:"
		print "change_ebs.py filename optimized[yes/no]"
		exit(0)
	filename = sys.argv[1]
	optimized = sys.argv[2]
	
	machines = parse_machines(filename)
	if optimized == "yes":
		change_ebs(machines, "--ebs-optimized")
	elif optimized == "no":
		change_ebs(machines, "--no-ebs-optimized")#--ebs-optimized | --no-ebs-optimized
	else:
		print "Please call the change ebs optimized in the following manner:"
		print "change_ebs.py filename optimized[yes/no]"
