#!/usr/bin/python
import csv
from datetime import datetime  # , timedelta
import json
import os
import re
from subprocess import check_output, STDOUT, Popen, PIPE, CalledProcessError
import sys
from time import sleep
import xml.etree.ElementTree

import dateutil.parser
from math import ceil


# from fileinput import filename
# list of functions:
# call(cmd_list, prefix, output) - call a shell command streaming stdout
# __init__() - mainly initialize parameters from argv
# conduct_experiment() - prepare cluster for failure if failure experiment
#   or remove/add nodes in case it was changed from last configuration and wait
#   for cluster to balance
# prepare_nodes() - remove or add nodes according to 10/20 OSD configuration
# prepare_failure() - ONLY SUPPORTS LARGEFAIL! removes node, should start
#   measurement at the moment this function finishes.
# get_server_partition() - encodes osd num to its server and partition
# recover_osd() - recovers the failed osd and waits until cluster is balanced
# poll_until_health_ok() - poll ceph health until HEALTH_OK or up to 10 errors
# execute() - does the main script, measure, conduct experiment, and parse
#   the measurements eventually.
# parse_results() - parses the output files from each server to a proper csv
#   named results.txt
# write_measurement_row() - used to save redundant copy paste in parse_results
def call(cmd_list, prefix='', output=True):
	proc = Popen(cmd_list, stdout=PIPE, stderr=STDOUT)
	# Poll process for new output until finished
	while True:
		nextline = proc.stdout.readline()
		if nextline == '' and proc.poll() is not None:
			break
		if output:
			sys.stdout.write(prefix + nextline)
			sys.stdout.flush()
			
	output = proc.communicate()[0]
	exitCode = proc.returncode
	if (exitCode == 0):
		return output
	else:
		raise CalledProcessError(exitCode, cmd_list)

def run_command(command, write=False):
	try:
		out = check_output(command, shell=True, stderr=STDOUT)
		if (write and out):
			print out
	except Exception as e:
		if write: 
			print e
		
def parallelssh(command, write=False):
	try:
		# -oStrictHostKeyChecking=no 
		out = check_output("parallel-ssh -l ubuntu -h ../servers.txt -x \"-oStrictHostKeyChecking=no -i /home/shroman/.ssh/aws2.pem\" '" 
						+ command + "'", shell=True)
		if (write and out):
			print out
	except Exception as e:
		if write: 
			print e

def parallelscp(copy_from, copy_to, write=False):
	try:
		#-oStrictHostKeyChecking=no
		out = check_output("parallel-scp -l ubuntu -h ../servers.txt -x \"-oStrictHostKeyChecking=no -i /home/shroman/.ssh/aws2.pem\" "
			+ copy_from + " " + copy_to, shell=True)
		if (write and out):
			print out
	except Exception, e:
		if write: 
			print e
"""
This class initiates a single experiment, outputting the results from
self.servers to files $servername$.txt in the current dir of the script.
Notice that code type (zz/rs) will be specified in outer script since it needs
reinstallation of ceph.
"""
class ParallelPlatform:
	def __init__(self):
		# define dirs
		self.scdir = "/home/shroman/amz_sraid"
		self.scriptsdir = self.scdir + "/scripts"
		self.resultsdir = "/shroman/results"

		os.chdir(self.scdir)
		
		self.servers = {}
		# choose servers, must be ordered
		if (len(sys.argv) != 9):
			print "Please call the parallel platform in the following manner:"
			print "parallel_platform.py exp codec k r z random_name servers_num step_size"
			exit(0)
		# parse arguments:
		self.parse_arguments()
		self.parse_servers()
		self.servers_on_disk = int(ceil(float(self.servers_num) / (4 * len(self.servers))))


	def parse_arguments(self):
		self.exp = sys.argv[1]
		self.codec = sys.argv[2]
		self.k = sys.argv[3]
		self.r = sys.argv[4]
		self.z = sys.argv[5]
		self.n = int(self.k) + int(self.r) + int(self.z)
		self.random_name = sys.argv[6]
		self.is_write = (self.exp.startswith('w') or self.exp.startswith('W') or self.exp.startswith('e') or self.exp.startswith('E'))
		self.servers_num = int(sys.argv[7])
		if (self.servers_num < self.n):
			self.servers_num = self.n
		self.step_size = sys.argv[8]
		self.start_servers = not (self.exp.startswith('e') or self.exp.startswith('E'))


	def parse_servers(self):
		run_command("rm servers.txt")

		e = xml.etree.ElementTree.parse('client/config.xml').getroot()
		for conn in e.findall('connections'):
			for atype in conn.findall('server'):
				server = atype.get('host')
				self.servers[server] = self.servers.get(server, 0) + 1

		with open('servers.txt', 'w') as serversfile:
			for serv in self.servers.keys():
				serversfile.write("%s\n" % serv)

	def experiment_get_ready(self):
		print "removing old logs"
		run_command("sudo rm /shroman/results/*.log*")

		run_permissions_command = "chmod +x /server/*.sh /server/*.py"
		rm_stats_command = "sudo rm /server/stats.txt"
		rm_done_commend = "sudo rm /server/done"
		clear_cache_command = "sudo echo 3 | sudo tee /proc/sys/vm/drop_caches && sudo sync"

		# client clean up
		run_command(rm_stats_command)
		run_command(rm_done_commend)
		run_command(clear_cache_command)

		if (self.start_servers):
			# servers clean up
			if self.is_write :
				print "deleting data:"
				parallelssh("sudo rm -r /server/123*")
# 				parallelssh("sudo rm -r /server/logs")
			print "deleting stats:"
			parallelssh(rm_stats_command)
			parallelssh(rm_done_commend)
			
			parallelssh(run_permissions_command)
			parallelssh(clear_cache_command)
		
	def start_serevrs(self):
		if (self.start_servers):
			print "STARTING SERVERS"
			parallelssh("./startserver.sh")
			
	def stop_serevrs(self):
		if (self.start_servers):
			print "STOPING SERVERS"
			parallelssh("./stopserver.sh")

	def conduct_experiment(self):
		os.chdir("/client")
		try:
			# If the experiment is write need to load the file to memory before the experiment
			if (self.is_write):
				print "Reading input file before writing it"
				with open("0", mode='rb') as file:
					fileContent = file.read()
			self.experiment_start = datetime.utcnow()
			print self.exp + " " + self.codec + " experiment started at:",
			print self.experiment_start
			
#			 run_command("java -Xms5g -Xmx5g -jar client.jar " + self.exp + " " 
#						 + self.codec + " " + self.k + " " + self.r + " " + self.z + " " 
#						 + self.random_name + " " + str(self.servers_num) + " " + self.step_size, True)
			call(["java", "-Xms10g", "-Xmx10g", "-jar", "client.jar", self.exp, self.codec, self.k, self.r, self.z, self.random_name, str(self.servers_num), self.step_size])
			# "-Djava.security.egd=file:/dev/./urandom"
		except Exception, e:
			print "FAILED"
			print e
		
	def kill_measurements(self):
		# kill measurements
		os.chdir(self.scriptsdir)
		
		sleep(3)
		self.stop_serevrs()
		
		print "kill measurements by 'touch done'"
		touch_done_command = "touch /server/done"
		if (self.start_servers):
			parallelssh(touch_done_command)
		run_command(touch_done_command)
		# let clients finish
		print "sleep for 3 seconds for clienls -l ../results to finish"
		sleep(3)

	def execute(self):
		print "executing: " + self.exp + " " + self.codec

		os.chdir(self.scriptsdir)
		self.stop_serevrs()
		self.experiment_get_ready()
		self.start_serevrs()
		
		# start measurements...
		print "starting timer"
		timestart = datetime.utcnow()
		run_stats_parser_command = "nohup /server/stat_parser.py " + timestart.isoformat() + " >/dev/null 2>&1 &"
		run_command(run_stats_parser_command)
		if (self.start_servers):
			parallelssh(run_stats_parser_command)
			print "sleeping for 5 seconds"
			sleep(5)
		
		# conduct experiment...
		self.conduct_experiment()

		self.kill_measurements()
		
		self.copy_results_to_master()

		# parse experiment results
		self.parse_results()
		self.parse_codec_logs()
		self.parse_network_logs("io", ".logsio")
		self.parse_network_logs("server_network", ".logsn")
		self.parse_network_logs("client_network", ".logcn")

		
	def copy_results_to_master(self):
		os.chdir(self.scriptsdir)
		print "copy stats to results folder"
		if (self.start_servers):
			for serv in self.servers:
				run_command("scp -oStrictHostKeyChecking=no -i /home/shroman/.ssh/aws2.pem ubuntu@" + serv 
						+ ":/server/stats.txt /shroman/results/" + serv + ".stat")
				run_command("scp -oStrictHostKeyChecking=no -i /home/shroman/.ssh/aws2.pem ubuntu@" + serv 
						+ ":/server/logs/IO.logsio /shroman/results/IO_" + serv + ".logsio")
				for log in {"transmit", "recieve"}:
					run_command("scp -oStrictHostKeyChecking=no -i /home/shroman/.ssh/aws2.pem ubuntu@" + serv 
						+ ":/server/logs/" + log + ".logsn /shroman/results/" + log + "_" + serv + ".logsn")
			
		run_command("cp /client/logs/* /shroman/results/");
		run_command("cp /server/stats.txt /shroman/results/client.stat");

	def parse_results(self):
		print "parsing results..."
		os.chdir(self.resultsdir)
		output = open("results.csv", "a")
		csvwriter = csv.writer(output)
		csvwriter.writerow(['timestamp', 'inttime', 'exp', 'codec', 'random', 'k', 'r', 'z', 'machine', 'measurement', 'value'])
		
		files = [f for f in os.listdir('.') if (os.path.isfile(f) and f.endswith(".stat"))]
		for file in files:
#			 print file
			serv = file.split('.stat')[0]
			with open(file, "r") as f:
				data = json.load(f)
				for timerow in data:
					# parse time
					t = dateutil.parser.parse(timerow[0])
					# experiment haven't started
					if self.experiment_start is not None \
							and t < self.experiment_start:
						continue

					# didn't start measureent
					if "net" not in timerow[1] or "cpu" not in timerow[1]:
						continue

					self.write_measurement_row(csvwriter, "io_p1rB", timerow[1]["io"]["xvda1"][0], t, serv)
					self.write_measurement_row(csvwriter, "io_p1wB", timerow[1]["io"]["xvda1"][1], t, serv)
					# write network measurements
					self.write_measurement_row(csvwriter, "net_rcvB", timerow[1]["net"][0], t, serv)
					self.write_measurement_row(csvwriter, "net_tsmtB", timerow[1]["net"][1], t, serv)
					self.write_measurement_row(csvwriter, "net_rcvB_lo", timerow[1]["net"][2], t, serv)
					self.write_measurement_row(csvwriter, "net_tsmtB_lo", timerow[1]["net"][3], t, serv)
					# write cpu utilization
					self.write_measurement_row(csvwriter, "cpu", timerow[1]["cpu"], t, serv)
					

		output.close()

	"""
	Gets a csvwriter object, measurement name, value, current time and server.
	It calculates OSD num. in case there are 20 OSDs we'd like to add 2 entries
	for network, while in all other cases there's just 1 entry per call, i.e.
	in io there are 2 partitions one for each OSD so each call is for a partition.
	"""
	def write_measurement_row(self, csvwriter, measurement, value, time, server):
		printed_time = (time - self.experiment_start).total_seconds()

#		 osdnum = self.servers.index(server) * self.osd_per_node
#		 if int(self.osd_per_node) == 2 and measurement.startswith("io_p2"):
#			 osdnum += 1
		
		# ['timestamp', 'inttime', 'exp', 'codec', 'k', 'r', 'z', 'machine', 'measurement', 'value'])
		csvrow = [str(printed_time), str(int(printed_time)), self.exp, self.codec, self.random_name,
				  self.k, self.r, self.z, server, measurement, str(value)];
		
		csvwriter.writerow(csvrow)
#		 if measurement.startswith("net"):
#			 csvrow[-1] = str(value / 2.0)
#			 csvrow2 = csvrow[:]
#			 csvrow2[5] = osdnum + 1
#			 csvwriter.writerow(csvrow)
#			 csvwriter.writerow(csvrow2)
#		 else:  # all other cases, 1 entry per call
#			 csvwriter.writerow(csvrow)
	def parse_network_logs(self, name, extension):
		print "parsing " + name + " logs..."
		os.chdir(self.resultsdir)
		output = open(name + ".csv", "a")
		csvwriter = csv.writer(output)
		csvwriter.writerow(['exp', 'codec', 'random', 'k', 'r', 'z', 'servers_num', 'time', 'tag', 'size', 'server_id', 'log_type', 'machine'])
		
		files = [f for f in os.listdir('.') if (os.path.isfile(f) and f.endswith(extension))]
		for file in files:
#			 print file
			log_type = file.split(extension)[0]
			with open(file, "r") as f:
				for line in f:
					try:
						split = re.compile("\]*[\s\w,-:]*\[+").split(line)
						self.write_network_logs_row(csvwriter, log_type, split[2], split[3], split[4])
					except Exception, e:
						print e
						print line

		output.close()

	def write_network_logs_row(self, csvwriter, log_type, time, tag, size):
		# ['experiment', 'log_type', 'time', 'tag', 'size'])
		size = size.split(']')[0]
		split = log_type.split('_')
		if (len(split) == 1):
			split.append('client')
		csvrow = [self.exp, self.codec, self.random_name, self.k, self.r, self.z, self.servers_num, time, tag] + size.split(',') + split;
		csvwriter.writerow(csvrow)
		
	def parse_codec_logs(self):
		print "parsing codec logs..."
		os.chdir(self.resultsdir)
		output = open("codec.csv", "a")
		csvwriter = csv.writer(output)
		csvwriter.writerow(['exp', 'codec', 'random', 'k', 'r', 'z', 'servers_num', 'log_type', 'time', 'tag', 'size'])
		
		files = [f for f in os.listdir('.') if (os.path.isfile(f) and f.endswith(".logc"))]
		for file in files:
#			 print file
			log_type = file.split('.')[0]
			with open(file, "r") as f:
				for line in f:
					try:
						split = re.compile("\]*[\s\w,-:]*\[+").split(line)
						self.write_codec_logs_row(csvwriter, log_type, split[2], split[3], split[4])
					except Exception, e:
						print e
						print line

		output.close()

	def write_codec_logs_row(self, csvwriter, log_type, time, tag, size):
		# ['experiment', 'log_type', 'time', 'tag', 'size'])
		size = size.split(']')[0]
		csvrow = [self.exp, self.codec, self.random_name, self.k, self.r, self.z, self.servers_num, log_type, time, tag] + size.split(',');
		csvwriter.writerow(csvrow)

if __name__ == "__main__":
	p = ParallelPlatform()
	p.execute()
