#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# 
# 2024-01-03

__version__ = "0.7.1"
__author__ = "Igor Martynov (phx.planewalker@gmail.com)"



"""Simple Reporter. Send simple reports about system state via email.
"""


import sys
import os.path
import os
import datetime
import time
import configparser
import socket
import logging
import logging.handlers

import traceback

from jinja2 import Template, Environment, FileSystemLoader, select_autoescape, BaseLoader

from reporters import *
from tests import *
from base_functions import *



class TestLoader(object):
	"""loads all tests from config, creates representing Test objects"""
	
	def __init__(self, logger = None, config = None):
		super(TestLoader, self).__init__()
		self._logger = logger
		self._config = config
		self.tests = []
		self.tests_table = {} # dict which states which test type is handled by which class
		self.REQUIRE_ENABLED = False # True if section will be loaded only if enabled = True
		self.init_tests_table()
	
	
	def add_test(self, test_obj):
		self.tests.append(test_obj)
		self._logger.debug(f"add_test: added test {test_obj} ({test_obj.descr})")
	
	
	def init_tests_table(self):
		# currently, new test should be added to self.tests_table with its type as key
		self.tests_table = {}
		self.tests_table["df"] = DFTest
		self.tests_table["ifconfig"] = IfconfigTest
		self.tests_table["uptime"] = UptimeTest
		self.tests_table["dmesg"] = DmesgTest
		self.tests_table["zfs_zpool_status"] = ZFSZPoolStatusTest
		self.tests_table["zfs_zpool_list"] = ZFSZPoolListTest
		self.tests_table["smartctl"] = SmartctlTest
		self.tests_table["ping"] = PingTest
		self.tests_table["traceroute"] = TracerouteTest
		self.tests_table["df-trivial"] = DFTrivialTest
		self.tests_table["downtime"] = DowntimeTest
		self.tests_table["file_content"] = FileContentTest
		self.tests_table["datetime"] = DatetimeTest
		self.tests_table["ps"] = PSTest
		self.tests_table["service"] = ServiceTest
		self.tests_table["ifconfigme"] = IfconfigMeTest
		self.tests_table["file_exist"] = FileExistTest
		self.tests_table["remote_fs"] = RemoteFSTest
		self.tests_table["du"] = DUTest
		self._logger.debug(f"init_tests_table: inited with {len(self.tests_table.keys())} test types")
	
	
	def parse_config_section(self, section):
		self._logger.debug(f"parse_config_section: parsing section {section}")
		if self.REQUIRE_ENABLED and not (self._config.get(section, "enabled") == "True"):
			self._logger.info(f"parse_config_section: section {section} is disabled, ignoring")
			return
		_type = self._config.get(section, "type")
		_name = section # this is redundand, but still persist
		if _type in self.tests_table.keys():
			self.create_test(_type, section, _name)
			self._logger.debug(f"parse_config_section: section {section} parsed, test {_name} created")
		else:
			self._logger.error(f"parse_config_section: could not find type {_type} in tests_table, ignoring section")
			return
	
	
	def create_test(self, _type, section, _name):
		self._logger.debug(f"create_test: will create test for type {_type}, section: {section}")
		cls = self.tests_table[_type]
		# new_test = cls(logger = self._logger.getChild(self._config.get(section, "type") + "_" + section),
		new_test = cls(logger = self._logger.getChild(self._config.get(section, "type") + "_" + section),
			config = self._config,
			name = _name)
		self.add_test(new_test)
	
	
	def load_all(self):
		self._logger.info("load_all: starting")
		sections = self._config.sections()
		for section in sections:
			if section == "main":
				continue
			self.parse_config_section(section)
		self._logger.info(f"load_all: complete, loaded tests: {[_test.name for _test in self.tests]}")
		


class SimpleReporter(object):
	""""""
	
	def __init__(self,
		log_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "simple_reporter.log"),
		config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "simple_reporter.conf"),
		verbose = False):
		super(SimpleReporter, self).__init__()
		
		self.LOG_FILE = log_file
		self.verbose = verbose
		self.CONFIG_FILE = config_file
		self._config = configparser.ConfigParser()
		self._logger = None
		
		self.tests = []
		self.reporters = []
		self._test_loader = None
		
		self.tests_failed = []
		self.tests_ignored = []
		self.tests_OK = []
		
		self.heartbeat_file = "/var/tmp/heartbeat"
		
		self.TEMPLATE_FILE = "main.jinja2"
		self._template = None
		self.report_text = ""
		if self.verbose: print(f"Using config file {self.CONFIG_FILE}")
		self.rotate_logs()

	
	def rotate_logs(self):
		"""will rotate .log file to .log.old, thus new log file will be used on each start"""
		OLD_LOG_POSTFIX = ".old"
		if os.path.isfile(self.LOG_FILE + OLD_LOG_POSTFIX):
			os.unlink(self.LOG_FILE + OLD_LOG_POSTFIX)
		try:
			os.rename(self.LOG_FILE, self.LOG_FILE + OLD_LOG_POSTFIX)
		except Exception as e:
			if self.verbose: print(f"could not rotate log file {self.LOG_FILE}, will use unrotated file!")
	
	
	def init_logger(self):
		self._logger = logging.getLogger("simple_reporter")
		self._logger.setLevel(logging.DEBUG)
		fh = logging.FileHandler(self.LOG_FILE)
		fh.setLevel(logging.DEBUG)
		formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
		fh.setFormatter(formatter)
		self._logger.addHandler(fh)
		self._logger.debug("======== simple_reporter starting, version " + __version__ + " ========")
		self._logger.info(f"using config {self.CONFIG_FILE}")
	
	
	def _load_config_section_main(self):
		# logging
		if os.sep not in self._config.get("main", "log_file"):
			self.LOG_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), self._config.get("main", "log_file"))
			if self.verbose: print(f"Using relative path to log file: {self.LOG_FILE}")
		else:
			self.LOG_FILE = self._config.get("main", "log_file")
			if self.verbose: print(f"Using absolute path to log file: {self.LOG_FILE}")
		if self._config.has_option("main", "brief_section_enabled") and self._config.get("main", "brief_section_enabled") == "yes":
			pass
		self.init_logger()
	
	
	def _load_config_section_other(self):
		"""load config sections that are not main and not tests"""
		sections = self._config.sections()
		for section in sections:
			if section == "main": # this section should be already persed above
				continue
			# reporter-email
			if self._config.get(section, "type") == "reporter-email" and self._config.get(section, "enabled") == "True":
				self._logger.debug(f"_load_config_section_other: got section for reporter-email: {section}")
				self.reporters.append(EmailReporter(config = self._config, logger = self._logger.getChild("EmailReporter")))
			# reporter-file
			if self._config.get(section, "type") == "reporter-file" and self._config.get(section, "enabled") == "True":
				self._logger.debug(f"_load_config_section_other: got section for reporter-file: {section}")
				self.reporters.append(FileReporter(config = self._config, logger = self._logger.getChild("FileReporter")))
	
	
	def load_config(self):
		self._config.read(self.CONFIG_FILE)
		self._load_config_section_main()
		self._load_config_section_other()
		self._logger.debug(f"load_config: complete, file {self.CONFIG_FILE} loaded")
		if self.verbose: print("config loaded")
	
	
	def init_test_loader(self):
		self._test_loader = TestLoader(logger = self._logger.getChild("TestLoader"), config = self._config)
		
	
	def init_tests(self):
		self._logger.debug("init_tests: starting")
		self.tests = []
		self._test_loader.load_all()
		self.tests = self._test_loader.tests
		self._logger.info(f"init_tests: complete, inited {len(self.tests)} tests")
	
	
	def init_template(self):
		env = Environment(loader = FileSystemLoader([os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates"),]), autoescape = select_autoescape())
		self._template = env.get_template(self.TEMPLATE_FILE)
	
	
	def init_all(self):
		self.load_config()
		self.init_template()
		self.init_test_loader()
		self.init_tests()
	
	
	def run_tests(self):
		self._logger.info(f"run_tests: starting execution of tests - {len(self.tests)} in list")
		for t in self.tests:
			try:
				t.run()
				if self.verbose: print(f"test {t.name} - type {t.TYPE} - complete")
			except Exception as e:
				self._logger.error(f"run_tests: got error while running test {t}: {e}, traceback: {traceback.format_exc()}")
				if self.verbose: print(f"test {t.name} - type {t.TYPE} - ERROR - {e}")
		self._logger.info("run_tests: complete")
	
	
	def get_simple_stats(self):
		self.tests_failed = []
		self.tests_ignored = []
		self.tests_OK = []
		for t in self.tests:
			if t.failed:
				self.tests_failed.append(t)
			elif not t.failed and not t.ignored:
				self.tests_OK.append(t)
			elif t.ignored:
				self.tests_ignored.append(t)
	
	
	def compile_report(self):
		os_type_dict = detect_OS()
		self.report_text = self._template.render(version = __version__,
			host = get_hostname(),
			datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			tests = self.tests,
			os_type_dict = os_type_dict,
			config_file = self.CONFIG_FILE)
		self._logger.debug("compile_report: complete")
	
	
	def send_message(self, message):
		self.report_text = f"\n{message}\n"
		self.send_report()
		
	
	def add_test(self, test_obj):
		self.tests.append(test_obj)
		self._logger.debug(f"add_test: added test {test_obj} ({test_obj.descr})")
	
	
	def send_report(self):
		self._logger.info(f"send_report: starting, will be used reporters: {self.reporters} ({len(self.reporters)} total)")
		if self.verbose: print("sending report...")
		for reporter in self.reporters:
			reporter.send_report(self.report_text)
		self._logger.debug("send_report: complete")
		if self.verbose: print("report sent OK")
	
	
	def save_heartbeat(self):
		"""save heartbeat to file"""
		heartbeat_test = None
		for t in self.tests:
			if t.TYPE == "downtime":
				heartbeat_test = t
		if heartbeat_test is not None:
			save_heartbeat(heartbeat_test.heartbeat_file)
			self._logger.info(f"save_heartbeat: saved to file {heartbeat_test.heartbeat_file}")
			if self.verbose: print(f"heartbeat saved to file {heartbeat_test.heartbeat_file}")
		else:
			self._logger.error("save_heartbeat: to configured heartbeat test found in config, will not save heartbeat.")


def determine_config():
	# determine config
	
	# current user
	current_user = get_current_user()
	current_user_home = f"/home/{current_user}" if current_user != "root" else "/root"
	CONFIG_FILE_NAME = "simple_reporter.conf"
	CONFIG_FILE_LIST = [f"/etc/{CONFIG_FILE_NAME}",
		f"{current_user_home}/{CONFIG_FILE_NAME}",
		os.path.join(os.path.abspath(os.path.dirname(__file__)), CONFIG_FILE_NAME),
		f"./{CONFIG_FILE_NAME}", ]
	
	for c in CONFIG_FILE_LIST:
		if os.path.isfile(c):
			return c
	

if __name__ == "__main__":
	CONFIG_FILE = determine_config()	

	# dumb cmdline args parsing
	arguments = sys.argv[1:]
	if "-h" in arguments or "--help" in arguments:
		print("""Usage:
	--collect-only - only collect data and save state (if possible), do not report
	-m, --message - send message only, do not collect
	-v, --verbose - be verbose
	""")
		sys.exit(0)
	if "--collect-only" in arguments:
		COLLECT_ONLY = True
	else:
		COLLECT_ONLY = False
	if "-v" in arguments or "--verbose" in arguments:
		VERBOSE = True
	else:
		VERBOSE = False
	if "-c" in arguments:
		CONFIG_FILE = arguments[arguments.index("-c") + 1]
	if "--config" in arguments:
		CONFIG_FILE = arguments[arguments.index("--config") + 1]
	message = None
	if "-m" in arguments or "--message" in arguments:
		if "--message" in arguments:
			pos = arguments.index("--message")
		else:
			pos = arguments.index("-m")
		message = " ".join(arguments[pos + 1:])
	
		
	sr = SimpleReporter(verbose = VERBOSE, config_file = CONFIG_FILE)
	sr.init_all()
	
	
	if COLLECT_ONLY:
		print("COLLECT_ONLY: Saving heartbeat only...")
		sr.save_heartbeat()
		sys.exit(0)
	if message is not None:
		sr.send_message(message)
		sys.exit(0)
	
	
	sr.run_tests()
	if not COLLECT_ONLY:
		sr.compile_report()
		sr.send_report()
	
	pass


