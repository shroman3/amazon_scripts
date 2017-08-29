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
				if ((counter % 3) == 0):
					if machine:
						machines.append(machine)
					machine = [line.strip()]
				else:
					machine.append(line.strip())
				counter+=1
				
	machines.append(machine)
	return machines
				

def start_machines(machines):
	for region in machines:
		print region
		run_command("aws ec2 start-instances --instance-ids " + region[1] + " --region " + region[0])
		run_command("aws ec2 start-instances --instance-ids " + region[2] + " --region " + region[0])

def stop_machines(machines):
	for region in machines:
		print region
		run_command("aws ec2 stop-instances --instance-ids " + region[1] + " --region " + region[0])
		run_command("aws ec2 stop-instances --instance-ids " + region[2] + " --region " + region[0])
		
if __name__ == "__main__":
	if (len(sys.argv) != 3):
		print "Please call the start machines in the following manner:"
		print "start_machine.py start/stop filename"
		exit(0)
	command = sys.argv[1]
	filename = sys.argv[2]
	machines = parse_machines(filename)
	if command == "start":
		start_machines(machines)
	elif command == "stop":
		stop_machines(machines)
	else:
		print "Please call the start machines in the following manner:"
		print "start_machine.py start/stop"
		exit(0)