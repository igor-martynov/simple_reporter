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

from base_functions import *


"""Test classes here.
Each test checks something, and then generates report.

"""



class BaseTest(object):
	"""Base class for tests
	
	supposed workflow is:
		- init
		- collect data
		- parse data
		- generate report
	"""
	
	_os_type_dict = detect_OS() # this should be static
	
	
	def __init__(self, config = None, logger = None, name = "BaseTest"):
		super(BaseTest, self).__init__()
		self._config = config
		self.TYPE = "BaseTest_type"
		self.name = name # this should be set to name of config section
		self.descr = "BaseTest description"
		self.running = None
		self.complete = None
		self.failed = None # if result is faulty 
		self.date_start = None
		self.date_end = None
		self.result = ""
		self.result_brief = None
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
		self.mark_start()
		self.collect()
		self.parse()
		self.mark_end()
		# raise NotImplemented
	
	
	def collect(self):
		"""Collect required data"""
		raise NotImplemented
	
	
	def parse(self):
		"""Parse collected data"""
		pass
	
	
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
	
	def __init__(self, config = None, logger = None, name = "base_cmd_test generic name"):
		super(BaseCMDTest, self).__init__(config = config, logger = logger, name = name)
		
		self.descr = "base command test"
		self.CMD_TO_RUN = "df"
		self.TYPE = "base"
		self.raw_cmd_result = ""
	
	
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
	
	
	def collect(self):
		self.raw_cmd_result = self.run_cmd()



class BaseTestWithHistory(BaseTest):
	"""BaseTestWithHistory - use this as parent if you need test with history"""
	
	def __init__(self, config = None, logger = None, name = "base_test_with_history"):
		super(BaseTestWithHistory, self).__init__(config = config, logger = logger, name = name)
		self._DB_table = "baseTable"
	
	

class DFTrivialTest(BaseCMDTest):
	"""trivial df test, will use df utility and simply report df output"""
	
	def __init__(self, config = None, logger = None, name = "df-trivial"):
		super(DFTrivialTest, self).__init__(config = config, logger = logger, name = name)
		# self.name = "df-trivial"
		self.descr = "disk free test (trivial)"
		self.CMD_TO_RUN = "df"
		self.TYPE = "df-trivial"



# TODO: will be modernized
class DFTest(BaseCMDTest):
	"""extended df test, will use df utility"""
	
	def __init__(self, config = None, logger = None, name = "df"):
		super(DFTest, self).__init__(config = config, logger = logger, name = name)
		# self.name = "df"
		self.descr = "disk free test using df command"
		self.CMD_TO_RUN = "df"
		self.TYPE = "df"



class UptimeTest(BaseCMDTest):
	"""checks system uptime"""
	
	def __init__(self, config = None, logger = None, name = "uptime"):
		super(UptimeTest, self).__init__(config = config, logger = logger, name = name)
		# self.name = "uptime"
		self.descr = "system uptime using uptime command"
		self.CMD_TO_RUN = "uptime"
		self.TYPE = "uptime"
	
	
	@property
	def report_brief(self):
		result_brief = self.raw_cmd_result.replace("\n", "")
		return f"Uptime: {result_brief}"



class DatetimeTest(BaseTest):
	"""checks system datetime with Python datetime class"""
	
	def __init__(self, config = None, logger = None, name = "datetime"):
		super(DatetimeTest, self).__init__(config = config, logger = logger, name = name)
		# self.name = "datetime"
		self.TYPE = "datetime"
		self.descr = "system date and time time using Python datetime"
		self._FORMAT = "%Y-%m-%d %H:%M:%S %Z"
	
	
	def collect(self):
		result_str = f"Date: {datetime.datetime.now().strftime(self._FORMAT)}"
		self.result = result_str
		self.result_brief = result_str
	
	
	def parse(self):
		# nothing to parse here
		pass



class IfconfigTest(BaseCMDTest):
	"""checks network configuration using ifconfig utility"""
	def __init__(self, config = None, logger = None, name = "ifconfig"):
		super(IfconfigTest, self).__init__(config = config, logger = logger, name = name)
		self.descr = "network interfaces test using ifconfig"
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
		result_brief_list = []
		for dev, ip in self.discovered_IPs_dict.items():
			result_brief_list.append(f"IP on {dev}: {ip}")
		result_brief = "\n".join(result_brief_list)
		return result_brief if result_brief != "" else None
	


class DmesgTest(BaseCMDTest):
	"""checks dmesg output"""
	
	def __init__(self, config = None, logger = None, name = "dmesg"):
		super(DmesgTest, self).__init__(config = config, logger = logger, name = name)
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
			self.num_lines = self._config.getint(self.name, "last_lines")
		except Exception as e:
			self._logger.error(f"init_from_section: got error while initing from section: {e}, traceback: {traceback.format_exc()}")



class ZFSZPoolStatusTest(BaseCMDTest):
	"""ZFSZPoolStatusTest"""
	def __init__(self, config = None, logger = None, name = "zfs_zpool_status"):
		super(ZFSZPoolStatusTest, self).__init__(config = config, logger = logger, name = name)
		self.descr = "zpool status"
		self.CMD_TO_RUN = "zpool status"
		self.TYPE = "zfs_zpool_status"
	
	
	def parse(self):
		if "state: DEGRADED" in self.raw_cmd_result:
			self.error_text += "ONE OR MORE POOL DEGRADED!"
			self.failed = True
		if "state: UNAVAIL" in self.raw_cmd_result:
			self.error_text += "ONE OR MORE POOL UNAVAILABLE!"
			self.failed = True
		if "state: FAULTED" in self.raw_cmd_result:
			if "state: UNAVAIL" in self.raw_cmd_result:
				self.error_text += "ONE OR MORE POOL HAS FAILED!"
				self.failed = True
		super(ZFSZPoolStatusTest, self).parse()	
		
	
	def run(self):
		if self._os_type_dict["os_family"] != "FreeBSD":
			self._logger.info(f"run: unsupported OS detected: {self._os_type_dict['os_family']}, returning None")
			self.ignored = True
			return
		self.raw_cmd_result = self.run_cmd()
		self.parse()



class ZFSZPoolListTest(BaseCMDTest):
	"""ZFSZPoolListTest - show output of command zpool list"""
	def __init__(self, config = None, logger = None, name = "zfs_zpool_list"):
		super(ZFSZPoolListTest, self).__init__(config = config, logger = logger, name = name)
		self.descr = "zpool list"
		self.CMD_TO_RUN = "zpool list"
		self.TYPE = "zfs_zpool_list"
		
	
	def run(self):
		if self._os_type_dict["os_family"] != "FreeBSD":
			self._logger.info(f"run: unsupported OS detected: {self._os_type_dict['os_family']}, returning None")
			self.ignored = True
			return
		self.raw_cmd_result = self.run_cmd()
		self.parse()



class RemoteFSTest(BaseCMDTest):
	"""RemoteFSTest - show mounted remote FSs, like nfs or smb"""
	def __init__(self, config = None, logger = None, name = "remote_fs_test"):
		super(RemoteFSTest, self).__init__(config = config, logger = logger, name = name)
		self.descr = "list of remote FS mounted"
		self.CMD_TO_RUN = "df -hT" 
		self.TYPE = "remote_fs"
		self.SUPPORTED_FS = ["nfs", "cifs", "smb", "sshfs"]
	
	
	def parse(self):
		self.result = ""
		raw_lines = []
		try:
			for l in self.raw_cmd_result.splitlines():
				for fs in self.SUPPORTED_FS:
					if fs in l:
						raw_lines.append(l)
		except Exception as e:
			self._logger.error(f"parse: got error {e}, traceback: {traceback.format_exc()}")
			return
		for rl in raw_lines:
			self.result += rl + "\n"



class SmartctlTest(BaseCMDTest):
	"""SmartctlTest"""
	def __init__(self, config = None, logger = None, name = "smartctl"):
		super(SmartctlTest, self).__init__(config = config, logger = logger, name = name)
		self.descr = "SMART info using smartctl command"
		self.CMD_TO_RUN = "smartctl -a "
		self.TYPE = "smartctl"
		self.detected_disks = []
		self.raw_cmd_result_list = []
	
	
	def _detect_disks(self):
		self.detected_disks = []
		if self._os_type_dict["os_family"] == "FreeBSD":
			disk_tmp_list = glob.glob("/dev/da*") # currently only da* disks are searched
			self._logger.debug(f"_detect_disks: got glob result: {disk_tmp_list}")
			for d in disk_tmp_list:
				if "p" not in d:
					self.detected_disks.append(d)
		elif self._os_type_dict["os_family"] == "RedHat" or self._os_type_dict["os_family"] == "Debian" or self._os_type_dict["os_family"] == "SuSE":
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
		self._detect_disks()
		self.run_cmd()
		self.parse()



class PingTest(BaseCMDTest):
	"""PingTest
	
	possible errors:
	From 10.70.255.252 icmp_seq=1 Destination Host Unreachable
	ping: ya1123132123.ru: Name or service not known
	
	"""
	def __init__(self, config = None, logger = None, name = "ping"):
		super(PingTest, self).__init__(config = config, logger = logger, name = name)
		self.descr = "ping test"
		self.CMD_TO_RUN = "ping"
		self.TYPE = "ping"
		self.host = ""
		self.count = 4
	
	
	def init_from_conf_dict(self):
		try:
			self.host = self._config.get(self.name, "host")
			self.count = self._config.getint(self.name, "count")
			self.CMD_TO_RUN = f"ping -c {self.count} {self.host}"
		except Exception as e:
			self._logger.error(f": got error: {e}, traceback: {traceback.format_exc()}")
	
	
	@property
	def report_brief(self):
		for l in self.raw_cmd_result.splitlines():
			if " transmitted," in l:
				result_brief = l.replace("\n", "")
				return f"Ping {self.host}: {result_brief}"
		return f"Ping {self.host}: {self.raw_cmd_result}"

	
	def run(self):
		self.init_from_conf_dict()
		self.raw_cmd_result = self.run_cmd()
		self.parse()
	
	
	# TODO: uneder construction
	def parse(self):
		"""should parse these outputs:
		Name or service not known
		3 packets transmitted, 3 received, 0% packet loss, time 5ms
		6 packets transmitted, 0 received, 100% packet loss, time 130ms
		
		"""
		return None
	
	

class TracerouteTest(BaseCMDTest):
	"""checks traceroute"""
	
	def __init__(self, config = None, logger = None, name = "traceroute"):
		super(TracerouteTest, self).__init__(config = config, logger = logger, name = name)
		# self.name = "traceroute"
		self.descr = "traceroute test"
		self.CMD_TO_RUN = "traceroute"
		self.TYPE = "traceroute"
		self.host = ""
	
	
	def init_from_conf_dict(self):
		self.host = self._config.get(self.name, "host")
		self.CMD_TO_RUN = f"traceroute {self.host}"
	
	
	def run(self):
		self.init_from_conf_dict()
		self.raw_cmd_result = self.run_cmd()
		self.parse()
	


class PSTest(BaseCMDTest):
	"""checks process list with ps utility"""
	
	def __init__(self, config = None, logger = None, name = "pstest"):
		super(PSTest, self).__init__(config = config, logger = logger, name = name)
		self.descr = "ps aux output"
		self.CMD_TO_RUN = "ps aux"
		self.TYPE = "ps"
		self.process_substr = None
	
	
	def init_from_conf_dict(self):
		if self._config.has_option(self.name, "process_substr"):
			self.process_substr = self._config.get(self.name, "process_substr")
			self._logger.debug(f"init_from_conf_dict: got process_substr = {self.process_substr}")
		else:
			self._logger.debug("init_from_conf_dict: no sectionin config")
		
		
	@property
	def report_brief(self):
		if self.process_substr is None:
			self._logger.debug(f"report_brief: {self.raw_cmd_result}")
			return f"ps: {len(self.raw_cmd_result.splitlines()) - 1} processes"
		else:
			tmp_result_list = []
			for line in self.raw_cmd_result.splitlines():
				if self.process_substr in line:
					tmp_result_list.append(line)
			return f"ps: {len(tmp_result_list)} processes of \"{self.process_substr}\""
	
	
	def parse(self):
		if self.process_substr is None:
			return None
		result_tmp_list = []
		for line in self.raw_cmd_result.splitlines():
			if self.process_substr in line:
				result_tmp_list.append(line.replace("\n", ""))
		self.result = "\n".join(result_tmp_list)
	
	
	def run(self):
		self.init_from_conf_dict()
		self.raw_cmd_result = self.run_cmd()
		self.parse()

	

# TODO: under construction and testing
class DowntimeTest(BaseTest):
	"""report last downtime"""
	def __init__(self, config = None, logger = None, name = "downtime"):
		super(DowntimeTest, self).__init__(config = config, logger = logger, name = name)
		self.TYPE = "downtime"
		self.descr = "downtime test using internal functions"
		self.heartbeat_file = self._config.get(self.name, "heartbeat_file")
		self.period_s = self._config.getint(self.name, "heartbeat_period_s")
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
	
	def __init__(self, config = None, logger = None, name = "file_content"):
		super(FileContentTest, self).__init__(config = config, logger = logger, name = name)
		self.TYPE = "file_content"
		self.descr = "show content of file"
		self.path = ""
		self.max_lines = None
		self.total_lines = None
		self.init_from_conf_dict()
	
	
	def init_from_conf_dict(self):
		self.path = self._config.get(self.name, "path")
		self.descr = f"Сontent of file {self.path}"
		self.max_lines = self._config.getint(self.name, "max_lines") if self._config.has_option(self.name, "max_lines") else None
		self._logger.debug(f"init_from_conf_dict: got max_lines: {self.max_lines}")
		
		
	def collect(self):
		if not os.path.isfile(self.path):
			self.failed = True
			self.result = f"file {self.path} is not present"
			self._logger.error(f"collect: could not find file {self.path}")
			return False
		with open(self.path, "r") as f:
			full_file_content = f.read()
		lines_list = full_file_content.splitlines()
		self.total_lines = len(lines_list)
		self._logger.debug(f"collect: num of strings: {self.total_lines}")
		if self.max_lines is None:
			self._logger.debug(f"collect: max_lines not defined in config, reporting full file {self.path}")
			self.result = full_file_content
		else:
			if self.total_lines > self.max_lines:
				self._logger.debug(f"collect: cropping file to {self.max_lines} lines")
				self.result = "\n".join(lines_list[- self.max_lines:])
			else:
				self._logger.debug(f"collect: max_lines IS defined in config, but total_lines < max_lines, so reporting full file {self.path}")
				self.result = full_file_content
		self._logger.debug(f"collect: length of file: {len(self.result)}")



class FileExistTest(BaseTest):
	"""Check if path exist and it's a file. Otherwise fail"""
	
	def __init__(self, config = None, logger = None, name = "file_exist"):
		super(FileExistTest, self).__init__(config = config, logger = logger, name = name)
		self.TYPE = "file_exist"
		self.descr = "check if file exist"
		self._file_exist = None
		self._file_size = None
		self._file_perm = None
		self.init_from_conf_dict()
		
	
	def init_from_conf_dict(self):
		self.path = self._config.get(self.name, "path")
		self.descr = f"check if file {self.path} exist"
	
	
	def collect(self):
		if not os.path.isfile(self.path):
			self.failed = True
			self.result = f"file {self.path} is not present"
			self._logger.error(f"collect: could not find file {self.path}")
			return False
		self._file_exist = True
		self._logger.info(f"collect: file exist: {self.path}")
	
	
	def parse(self):
		if not self._file_exist:
			self.result = f"file {self.path} does not exist"
			return
		self.result = f"file {self.path} exist"


# TODO: under construction and testing
class ServiceTest(BaseCMDTest):
	"""Show status of target service self.service_name"""
	
	def __init__(self, config = None, logger = None, name = "servicetest"):
		super(ServiceTest, self).__init__(config = config, logger = logger, name = name)
		self.descr = "service status"
		self.CMD_TO_RUN = ""
		self.TYPE = "service"
		self.service_name = ""
		self.systemctl_is_used = False
	
	
	def init_from_conf_dict(self):
		if self._config.has_option(self.name, "service_name"):
			self.service_name = self._config.get(self.name, "service_name")
			self.descr = f"status of {self.service_name} service"
			self._logger.debug(f"init_from_conf_dict: got service_name = {self.service_name}")
		else:
			self._logger.error("init_from_conf_dict: no section in config")
		if (self._os_type_dict["os_family"] == "RedHat" and self._os_type_dict["major_version"] >= 7) \
			or (self._os_type_dict["os_family"] == "SuSE" and self._os_type_dict["major_version"] >= 12) \
			or (self._os_type_dict["os_family"] == "Debian" and self._os_type_dict["major_version"] >= 10):
			self.systemctl_is_used = True
			self.CMD_TO_RUN = f"systemctl status {self.service_name}"
		if (self._os_type_dict["os_family"] == "RedHat" and self._os_type_dict["major_version"] < 7) \
			or (self._os_type_dict["os_family"] == "SuSE" and self._os_type_dict["major_version"] < 12) \
			or (self._os_type_dict["os_family"] == "Debian" and self._os_type_dict["major_version"] < 10) \
			or (self._os_type_dict["os_family"] == "FreeBSD"):
			self.systemctl_is_used = False
			self.CMD_TO_RUN = f"service {self.service_name} status"
	
	
	def parse(self):
		if self.service_name == "":
			return None
		if self.systemctl_is_used:
			if self.raw_cmd_result == "-1":
				self.error = True
				self.result = f"got error running systemctl, please check configuration"
				return



class IfconfigMeTest(BaseCMDTest):
	"""Test outer IP using public web service ifconfig.me/ip"""
	
	def __init__(self, config = None, logger = None, name = "ifconfigmetest"):
		super(IfconfigMeTest, self).__init__(config = config, logger = logger, name = name)
		self.descr = "request extermal IP address from ifconfig.me web service"
		self.TYPE = "ifconfigme"
		self.URL = "https://ifconfig.me/ip"
		self.CMD_TO_RUN = f"curl -s {self.URL}"



class DUTest(BaseCMDTest):
	"""Test disk usage (using du) of dir"""
	
	def __init__(self, config = None, logger = None, name = "dutest"):
		super(DUTest, self).__init__(config = config, logger = logger, name = name)
		self.descr = "simple du (disk usage) test"
		self.TYPE = "du"
		# self.CMD_TO_RUN = f"du -sh"
		self.summarize = False
		self._dive_into_subdirs = False
		self.init_from_conf_dict()
		
	
	def init_from_conf_dict(self):
		self._dive_into_subdirs = True if self._config.get(self.name, "path") == "True" else False
		self.path = self._config.get(self.name, "path")
		self.summarize = True if (self._config.has_option(self.name, "summarize") and self._config.get(self.name, "summarize") == "True") else False
		# self.CMD_TO_RUN = f"du -sh {os.path.join(self.path, '*')}"
		self.CMD_TO_RUN = f"du -sh {self.path}" if self.summarize else f"du -h {self.path}"
		pass


