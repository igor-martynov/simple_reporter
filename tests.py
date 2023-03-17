#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 


import sys
import os.path
import os
import datetime
import time
import glob


from jinja2 import Template, Environment, FileSystemLoader, select_autoescape

from base import *


"""Test classes here.

Each test checks something, and generates report

"""



class BaseTest(object):
	"""Base class for tests"""
	
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(BaseTest, self).__init__()
		
		self._config = config
		self._conf_dict = conf_dict
		self.TYPE = "test"
		
		self.name = "BaseTest" # this should be name of config section
		self.descr = "BaseTest description"
		
		self.running = None
		self.complete = None
		self.failed = None # result is faulty 
		self.date_start = None
		self.date_end = None
		
		self.result = ""
		self.result_brief = ""
		self.error_text = ""
		self.ignored = False
		
		self.TEMPLATE_FILE = "base_template.jinja2"
		self._template = None
		self._logger = logger
		
		self.init_template()
	
	
	@property
	def execution_failed(self):
		return True if len(self.error_text) == 0 else False 
	
	
	def init_template(self):
		env = Environment(loader = FileSystemLoader([os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates"),]), autoescape = select_autoescape())
		self._template = env.get_template(self.TEMPLATE_FILE)
		self._logger.debug(f"init_template: loaded tempalte: {self._template}")
	
	
	def init_from_conf_dict(self):
		pass
	
	
	@property
	def report_brief(self):	
		return self.result_brief
	
	
	@property
	def report(self):
		report = self._template.render(name = self.name, descr = self.descr, report = self.result, error_text = self.error_text)
		self._logger.debug(f"report: will return: {report}")
		return report
	
	
	def run(self):
		raise NotImplemented
	
	
	def collect(self):
		"""Collect required data"""
		raise NotImplemented
	
	
	def mark_start(self):
		self.running = True
		self.complete = False
		self.date_start = datetime.datetime.now()
	
	
	def mark_end(self):
		self.running = False
		self.complete = True
		self.date_end = datetime.datetime.now()
	
	
	
class BaseCMDTest(BaseTest):
	"""Base Test which use shell command
	
	This is also an example of class usage
	
	"""
	
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(BaseCMDTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		
		self.name = "base_cmd_test"
		self.descr = "base command test"
		self.CMD_TO_RUN = "df"
		self.TYPE = "base"
		self.raw_cmd_result = ""
		self._os_type_dict = detect_OS()
	
	
	def pre_run(self):
		self._logger.info(f"pre_run: starting, CMD_TO_RUN: {self.CMD_TO_RUN}")
		self.mark_start()
		self._logger.debug(f"pre_run: detected os: {self._os_type_dict}")
		
	
	def post_run(self):
		self.mark_end()
		self._logger.debug(f"post_run: complete")
	
	
	def parse(self):
		self.result = self.raw_cmd_result
	
	
	def run_cmd(self):
		self._logger.debug(f"run_cmd: will run command {self.CMD_TO_RUN}")
		try:
			self.raw_cmd_result = run_command(self.CMD_TO_RUN)
			# self._logger.debug(f"run: got cmd_result: {self.raw_cmd_result}")
		except Exception as e:
			self._logger.error(f"run_cmd: got error {e}, traceback: {traceback.format_exc()}")
			self.error_text += str(e)
		return self.raw_cmd_result
	
	
	def run(self):
		self.pre_run()
		self.raw_cmd_result = self.run_cmd()
		self.parse()
		self.post_run()



class BaseTestWithHistory(BaseTest):
	"""docstring for BaseTestWithHistory"""
	
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(BaseTestWithHistory, self).__init__(config = config, logger = logger, conf_dict = conf_dic)
		self._DB_table = "baseTable"
		
		pass
	
	
		


class DFTrivialTest(BaseCMDTest):
	"""trivial df test, will use df utility and simply report df output"""
	
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(DFTrivialTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "df-trivial"
		self.descr = "disk free test (trivial)"
		self.CMD_TO_RUN = "df"
		self.TYPE = "df-trivial"



# TODO: will be modernized
class DFTest(BaseCMDTest):
	"""extended df test, will use df utility"""
	
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(DFTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "df"
		self.descr = "disk free test"
		self.CMD_TO_RUN = "df"
		self.TYPE = "df"



class UptimeTest(BaseCMDTest):
	"""UptimeTest"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(UptimeTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "uptime"
		self.descr = "uptime test"
		self.CMD_TO_RUN = "uptime"
		self.TYPE = "uptime"
	
	
	@property
	def report_brief(self):
		return f"Uptime: {self.raw_cmd_result}"



class IfconfigTest(BaseCMDTest):
	"""IfconfigTest"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(IfconfigTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "ifconfig"
		self.descr = "ifconfig test"
		self.CMD_TO_RUN = "ifconfig -a"
		self.TYPE = "ifconfig"
		
		self.discovered_IPs = []
		self.discovered_IPs_dict = {}
		
		
	def parse(self):
		self.discovered_IPs = []
		splitted_cmd_list = self.raw_cmd_result.splitlines()
		dev = "N/A"
		ip = "N/A"
		for l in splitted_cmd_list:
			if not " flags=" in l and not "inet" in l:
				continue
			if " flags=" in l:
				dev = (l.split(" ")[0])[0:-1]
			if "127.0.0.1" not in l and "inet " in l:
				ip = l.replace("inet ", "").split( )[0]
				self.discovered_IPs.append(ip)
				if dev not in self.discovered_IPs_dict.keys():
					self.discovered_IPs_dict[dev] = ip
				else:
					self.discovered_IPs_dict[dev] += ", " + ip
			
		if dev == "N/A" or dev == "":
			self.failed = True
			self.error_text += "Could not detect device name"
			self._logger.info("parse: set failed = True because could not detect device name")
		if ip == "N/A" or ip == "":
			self.failed = True
			self.error_text += "Could not detect IP"
			self._logger.info("parse: set failed = True because could not detect IP")			
		self.result = self.raw_cmd_result
		self._logger.debug(f"parse: discovered_IPs: {self.discovered_IPs}, discovered_IPs_dict: {self.discovered_IPs_dict}")
	
		
	@property
	def report_brief(self):
		result_brief = ""
		for dev, ip in self.discovered_IPs_dict.items():
			result_brief += f"IP {dev}: {ip}" + "\n"
		return result_brief
	


class DmesgTest(BaseCMDTest):
	"""DmesgTest"""
	
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(DmesgTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "dmesg"
		self.descr = "last lines of dmesg output"
		self.num_lines = 20
		self.CMD_TO_RUN = f"dmesg"
		self.TYPE = "dmesg"
		self.init_from_conf_dict()
	
	
	def parse(self):
		self.result = ""
		try:
			for l in self.raw_cmd_result.splitlines()[-self.num_lines:]:
				self.result += l + "\n"
		except Exception as e:
			self._logger.error(f"parse: got except {e}, traceback: {traceback.format_exc()}")
	
	
	def init_from_conf_dict(self):
		try:
			self.num_lines = int(self._conf_dict["last_lines"])
		except Exception as e:
			self._logger.error(f"init_from_section: got error while initing from section: {e}, traceback: {traceback.format_exc()}")



class ZFSZPoolStatusTest(BaseCMDTest):
	"""docstring for ZFSZPoolStatusTest"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(ZFSZPoolStatusTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "zfs"
		self.descr = "zpool status"
		self.CMD_TO_RUN = "zpool status"
		self.TYPE = "zfs_zpool_status"
		
	
	def run(self):
		if self._os_type_dict["os_family"] != "FreeBSD":
			self._logger.info(f"run: unsupported OS detected: {self._os_type_dict['os_family']}, returning None")
			self.ignored = True
			return
		self.pre_run()
		self.raw_cmd_result = self.run_cmd()
		self.parse()
		self.post_run()



class ZFSZPoolListTest(BaseCMDTest):
	"""docstring for ZFSZPoolListTest"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(ZFSZPoolListTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "zfs"
		self.descr = "zpool list"
		self.CMD_TO_RUN = "zpool list"
		self.TYPE = "zfs_zpool_list"
		
	
	def run(self):
		if self._os_type_dict["os_family"] != "FreeBSD":
			self._logger.info(f"run: unsupported OS detected: {self._os_type_dict['os_family']}, returning None")
			self.ignored = True
			return
		self.pre_run()
		self.raw_cmd_result = self.run_cmd()
		self.parse()
		self.post_run()



class SmartctlTest(BaseCMDTest):
	"""docstring for SmartctlTest"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(SmartctlTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "smartctl"
		self.descr = "SMART info"
		self.CMD_TO_RUN = "smartctl -a "
		self.TYPE = "smartctl"
		self.detected_disks = []
		self.raw_cmd_result_list = []
	
	
	def _detect_disks(self):
		detected_os_dict = detect_OS()
		self.detected_disks = []
		if detected_os_dict["os_family"] == "FreeBSD":
			disk_tmp_list = glob.glob("/dev/da*")
			self._logger.debug(f"_detect_disks: got glob result: {disk_tmp_list}")
			for d in disk_tmp_list:
				if "p" not in d:
					self.detected_disks.append(d)
		elif detected_os_dict["os_family"] == "RedHat" or detected_os_dict["os_family"] == "Debian" or detected_os_dict["os_family"] == "SuSE":
			disk_tmp_list = glob.glob("/dev/sd*") + glob.glob("/dev/vd*")
			self._logger.debug(f"_detect_disks: got glob result: {disk_tmp_list}")
			for d in disk_tmp_list:
				if not d[-1].isnumeric():
					self.detected_disks.append(d)
		self._logger.info(f"_detect_disks: detected disks: {self.detected_disks}.")
		return self.detected_disks
	
	
	def run_cmd(self):
		self.raw_cmd_result_list = []
		for d in self.detected_disks:
			try:
				res = run_command(self.CMD_TO_RUN + d)
				self._logger.debug(f"run_cmd: for disk {d} got result {res}")
				self.raw_cmd_result_list.append(res)
			except Exception as e:
				self._logger.error(f"run_cmd: was running command for disk {d}, got error {e}, traceback is: {traceback.format_exc()}")
		
		
	def parse(self):
		for r in self.raw_cmd_result_list:
			self.result += r + "\n\n"
	
	
	def run(self):
		self.pre_run()
		self._detect_disks()
		self.run_cmd()
		self.parse()
		self.post_run()



class PingTest(BaseCMDTest):
	"""PingTest
	
	possible errors:
	From 10.70.255.252 icmp_seq=1 Destination Host Unreachable
	ping: ya1123132123.ru: Name or service not known
	
	"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(PingTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "ping"
		self.descr = "ping test"
		self.CMD_TO_RUN = "ping"
		self.TYPE = "ping"
		self.host = ""
		self.count = 4
		
	
	
	def init_from_conf_dict(self):
		self.host = self._conf_dict["host"]
		self.count = int(self._conf_dict["count"])
		self.CMD_TO_RUN = f"ping -c {self.count} {self.host}"
		pass
	
	
	@property
	def report_brief(self):
		return f"Ping: {self.raw_cmd_result}"
	
	
	def run(self):
		self.init_from_conf_dict()
		self.pre_run()
		self.raw_cmd_result = self.run_cmd()
		self.parse()
		self.post_run()
		pass
	
	
	# TODO: uneder construction
	def parse(self):
		"""should parse these outputs:
		Name or service not known
		3 packets transmitted, 3 received, 0% packet loss, time 5ms
		6 packets transmitted, 0 received, 100% packet loss, time 130ms
		
		"""
		return None
	
	

class TracerouteTest(BaseCMDTest):
	"""docstring for TracerouteTest"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(TracerouteTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "traceroute"
		self.descr = "traceroute test"
		self.CMD_TO_RUN = "traceroute"
		self.TYPE = "traceroute"
		self.host = ""
	
	
	def init_from_conf_dict(self):
		self.host = self._conf_dict["host"]
		self.CMD_TO_RUN = f"traceroute {self.host}"
	
	
	def run(self):
		self.init_from_conf_dict()
		self.pre_run()
		self.raw_cmd_result = self.run_cmd()
		self.parse()
		self.post_run()
	
	

# TODO: under construction and testing
class DowntimeTest(BaseTest):
	"""report last downtime"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(DowntimeTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "downtime"
		self.TYPE = "downtime"
		self.descr = "downtime test"
		self.heartbeat_file = conf_dict["heartbeat_file"]
		self.period_s = int(conf_dict["heartbeat_period_s"])
		self.last_heartbeat = None
		self.boot_time = None
		self.downtime_start = None
		self.downtime_end = None
		self.downtime_s = None
	
	
	def run(self):
		self.last_heartbeat = read_heartbeat(self.heartbeat_file)
		self.compile_report()
	

	def compile_report(self):
		self._logger.debug("compile_report: starting")
		now = datetime.datetime.now()
		uptime_timedelta = get_uptime()
		self.boot_time = now - uptime_timedelta
		self._logger.debug(f"compile_report: boot_time detected as {self.boot_time}")
		self.downtime_start = None
		self.downtime_end = None
		
		if self.last_heartbeat + datetime.timedelta(seconds = self.period_s) < now and self.last_heartbeat < self.boot_time:
			# no heartbeat for more than self.period_s seconds
			self.downtime_start = self.last_heartbeat
			self.downtime_end = self.boot_time
			self.downtime_s = (self.downtime_end - self.downtime_start).total_seconds()
			self.result_brief = f"Downtime: {self.downtime_s}s ({humanify_seconds(self.downtime_s)}), from {self.downtime_start} till {self.downtime_end} "
			self.result = self.result_brief
		elif self.last_heartbeat + datetime.timedelta(seconds = self.period_s) >= now:
			self.result_brief = "Downtime: no downtime detected"
			self.result = self.result_brief
			pass
		else:
			self.result_brief = f"Downtime: no downtime detected, but last heartbeat was too long ago... ({humanify_seconds((datetime.datetime.now() - self.last_heartbeat).total_seconds())} since last heartbeat)"
			self.result = self.result_brief
		self._logger.debug("compile_report: complete")



class FileContentTest(BaseTest):
	"""report content of text file"""
	
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(FileContentTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "file_content"
		self.TYPE = "file_content"
		self.descr = "Get content of file"
		self.path = ""
		self.init_from_conf_dict()
	
	
	def init_from_conf_dict(self):
		self.path = self._conf_dict["path"]
		self.descr = f"Сontent of file {self.path}"
	
	
	def run(self):
		self.mark_start()
		if not os.path.isfile(self.path):
			self.failed = True
			self._logger.error(f"run: could not find file {self.path}")
			return False
		with open(self.path, "r") as f:
			self.result = f.read()
			self._logger.debug(f"length of file: {len(self.result)}")
		self.mark_end()

