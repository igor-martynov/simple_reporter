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
	"""docstring for BaseTest"""
	
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(BaseTest, self).__init__()
		
		self._config = config
		self._conf_dict = conf_dict
		self._TYPE = "test"
		
		self.name = "BaseTest"
		self.descr = "BaseTest descr"
		
		self.error = None
		self.running = None
		self.complete = None
		self.date_start = None
		self.date_end = None
		
		self._report = ""
		self.error_text = ""
		self.ignored = False
		
		self.TEMPLATE_FILE = "base_template.jinja2"
		self._template = None
		self._logger = logger
		
		self.init_template()
		pass
	
	
	def init_template(self):
		# env = Environment(loader = PackageLoader("simple_reporter"), autoescape = select_autoescape())
		env = Environment(loader = FileSystemLoader([os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates"),]), autoescape = select_autoescape())
		self._template = env.get_template(self.TEMPLATE_FILE)
		self._logger.debug(f"init_template: loaded tempalte: {self._template}")
		pass
	
	
	def init_from_conf_dict(self):
		
		pass
	
	
	# @property
	# def report(self):
	# 	templ = Template("Test: {{ name}} ({{ descr }})\n\n {{ report }}\n\n\n")
	# 	return templ.render(name = self.name, descr = self.descr, report = self._report)
	
	
	@property
	def report_brief(self):	
		return ""
	
	
	@property
	def report(self):
		report = self._template.render(name = self.name, descr = self.descr, report = self._report, error_text = self.error_text)
		self._logger.debug(f"report: will return: {report}")
		return report
	
	
	def run(self):
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
		self.descr = "base cmd test"
		self.CMD_TO_RUN = "df"
		self._TYPE = "base"
		self.raw_cmd_result = ""
		
		self._os_type_dict = detect_OS()
	
	
	def pre_run(self):
		self._logger.info(f"pre_run: starting, CMD_TO_RUN: {self.CMD_TO_RUN}")
		self.mark_start()
		# os_dict = detect_OS()
		self._logger.debug(f"pre_run: detected os: {self._os_type_dict}")
		
	
	def post_run(self):
		
		self.mark_end()
		self._logger.debug(f"post_run: complete")
	
	
	def parse(self):
		""""""
		self._report = self.raw_cmd_result
		pass
	
	
	def run_cmd(self):
		self._logger.debug(f"run_cmd: will run command {self.CMD_TO_RUN}")
		try:
			self.raw_cmd_result = run_command(self.CMD_TO_RUN)
			self._logger.debug(f"run: got cmd_result: {self.raw_cmd_result}")
		except Exception as e:
			self._logger.error(f"run_cmd: got error {e}, traceback: {traceback.format_exc()}")
			self.error_text += str(e)
		return self.raw_cmd_result
	
	
	def run(self):
		self.pre_run()
		self.raw_cmd_result = self.run_cmd()
		self.parse()
		self.post_run()



class DFTrivialTest(BaseCMDTest):
	"""trivial df test, will use df utility and simply report df output"""
	
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(DFTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "df"
		self.descr = "disk free test"
		self.CMD_TO_RUN = "df"
		self._TYPE = "df-trivial"



class DFTest(BaseCMDTest):
	"""df test, will use df utility"""
	
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(DFTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "df"
		self.descr = "disk free test"
		self.CMD_TO_RUN = "df"
		self._TYPE = "df"



class UptimeTest(BaseCMDTest):
	"""UptimeTest"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(UptimeTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "uptime"
		self.descr = "uptime test"
		self.CMD_TO_RUN = "uptime"
		self._TYPE = "uptime"
	
	
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
		self._TYPE = "ifconfig"
		
		self.discovered_IPs = []
		self.discovered_IPs_dict = {}
		
		
	def parse(self):
		self.discovered_IPs = []
		splitted_cmd_list = self.raw_cmd_result.splitlines()
		dev = "N/A"
		ip = "N/A"
		for l in splitted_cmd_list:
			if " flags=" in l:
				dev = l.split(" ")[0]
			if "127.0.0.1" not in l and "inet " in l:
				ip = l.replace("inet ", "").split( )[0]
				self.discovered_IPs.append(ip)
				if dev not in self.discovered_IPs_dict.keys():
					self.discovered_IPs_dict[dev] = ip
				else:
					self.discovered_IPs_dict[dev] += ", " + ip
		self._report = self.raw_cmd_result
		self._logger.debug(f"parse: discovered_IPs: {self.discovered_IPs}, discovered_IPs_dict: {self.discovered_IPs_dict}")
	
		
	@property
	def report_brief(self):
		_report_brief = ""
		for ip in self.discovered_IPs:
			_report_brief += f"IP: {ip}" + "\n"
		return _report_brief
	


class DmesgTest(BaseCMDTest):
	"""DmesgTest"""
	
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(DmesgTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "dmesg"
		self.descr = "last lines of dmesg output"
		self.num_lines = 20
		self.CMD_TO_RUN = f"dmesg"
		self._TYPE = "dmesg"
		self.init_from_conf_dict()
	
	
	def parse(self):
		self._report = ""
		try:
			for l in self.raw_cmd_result.splitlines()[-self.num_lines:]:
				self._report += l + "\n"
		except Exception as e:
			self._logger.error(f"parse: got except {e}, traceback: {traceback.format_exc()}")
	
	
	def init_from_conf_dict(self):
		try:
			self.num_lines = int(self._conf_dict["last_lines"])
		except Exception as e:
			self._logger.error(f"init_from_section: got error while initing from section: {e}, traceback: {traceback.format_exc()}")



class ZFSInfoTest(BaseCMDTest):
	"""docstring for ZFSInfoTest"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(ZFSInfoTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "zfs"
		self.descr = "zpool status"
		self.CMD_TO_RUN = "zpool status"
		self._TYPE = "zfs_info"
		
	
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
		self._TYPE = "smartctl"
		self.detected_disks = []
		self.raw_cmd_result_list = []
	
	
	def _detect_disks(self):
		detected_os_dict = detect_OS()
		self.detected_disks = []
		if detected_os_dict["os_family"] == "FreeBSD":
			disk_tmp_list = glob.glob("/dev/da*")
			for d in disk_tmp_list:
				if "p" not in d:
					self.detected_disks.append(d)
		elif detected_os_dict["os_family"] == "RedHat" or detected_os_dict["os_family"] == "Debian" or detected_os_dict["os_family"] == "SuSE":
			disk_tmp_list = glob.glob("/dev/sd*") + glob.glob("/dev/vd*")
			for d in disk_tmp_list:
				if not d[-1].isnumeric():
					self.detected_disks.append(d)
		self._logger.debug(f"disk_tmp_list was: {disk_tmp_list}")
		self._logger.info(f"detected disks: {self.detected_disks}.")
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
			self._report += r + "\n\n"
	
	
	def run(self):
		self.pre_run()
		# detect disks
		self._detect_disks()
		
		self.run_cmd()
		self.parse()
		self.post_run()




class PingTest(BaseCMDTest):
	"""PingTest"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(PingTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "ping"
		self.descr = "ping test"
		self.CMD_TO_RUN = "ping"
		self._TYPE = "ping"
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



class TracerouteTest(BaseCMDTest):
	"""docstring for TracerouteTest"""
	def __init__(self, config = None, logger = None, conf_dict = None):
		super(TracerouteTest, self).__init__(config = config, logger = logger, conf_dict = conf_dict)
		self.name = "traceroute"
		self.descr = "traceroute test"
		self.CMD_TO_RUN = "traceroute"
		self._TYPE = "traceroute"
		self.host = ""
		pass
	
	
	def init_from_conf_dict(self):
		self.host = self._conf_dict["host"]
		self.CMD_TO_RUN = f"traceroute {self.host}"
		pass
	
	
	# unsupported
	# @property
	# def report_brief(self):
	# 	return f"traceroute: {self.raw_cmd_result}"
	
		

