#!/usr/bin/python

from subprocess import check_output, STDOUT
import sys

def run_command(command, write=False):
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
				

def change_machines(machines, instance_type):
	for region in machines:
		print region
		run_command("aws ec2 modify-instance-attribute --instance-id " + region[1] + " --region " + region[0] + " --instance-type " + instance_type)
		run_command("aws ec2 modify-instance-attribute --instance-id " + region[2] + " --region " + region[0] + " --instance-type " + instance_type)
		run_command("aws ec2 modify-instance-attribute --instance-id " + region[3] + " --region " + region[0] + " --instance-type " + instance_type)

if __name__ == "__main__":
	if (len(sys.argv) != 3):
		print "Please call the change machines in the following manner:"
		print "change_machines.py filename c4.xlarge/m3.medium"
		exit(0)
	filename = sys.argv[1]
	instance_type = sys.argv[2]
	if instance_type != "c4.xlarge" and instance_type != "m3.medium" :
		print "Please call the change machines in the following manner:"
		print "change_machines.py filename c4.xlarge/m3.medium"
		exit(0)
	machines = parse_machines(filename)
	change_machines(machines, instance_type)
