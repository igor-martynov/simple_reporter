#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# 
# 2022-07-05

__version__ = "0.5.6"
__author__ = "Igor Martynov (phx.planewalker@gmail.com)"



"""Simple Reporter. Send simple reports via email.
"""


import sys
import os.path
import os
import datetime
import time
# import glob
import configparser
import socket

# logging
import logging
import logging.handlers

import traceback

from jinja2 import Template, Environment, FileSystemLoader, select_autoescape, BaseLoader

from reporters import *
from tests import *
from base import *



class TestLoader(object):
	"""loads all tests from config, creates representing Test objects"""
	
	def __init__(self, logger = None, config = None):
		super(TestLoader, self).__init__()
		self._logger = logger
		self._config = config
		self.tests = []
		self.tests_table = {}
		
		self.REQUIRE_ENABLED = True
		
		self.init_tests_table()
		pass
	
	
	def add_test(self, test_obj):
		self.tests.append(test_obj)
		self._logger.debug(f"add_test: added test {test_obj} ({test_obj.descr})")
	
	
	def init_tests_table(self):
		self.tests_table = {}
		self.tests_table["df"] = DFTest
		self.tests_table["ifconfig"] = IfconfigTest
		self.tests_table["uptime"] = UptimeTest
		self.tests_table["dmesg"] = DmesgTest
		self.tests_table["zfs_info"] = ZFSInfoTest
		self.tests_table["smartctl"] = SmartctlTest
		self.tests_table["ping"] = PingTest
		self.tests_table["traceroute"] = TracerouteTest
		self.tests_table["df-trivial"] = DFTrivialTest
		# self.tests_table[""] = 
		
		self._logger.debug(f"init_tests_table: inited with {len(self.tests_table.keys())} test types")
		pass
	
	
	def parse_config_section(self, section):
		self._logger.debug(f"parse_config_section: parsing section {section}")
		if self.REQUIRE_ENABLED and not (self._config.get(section, "enabled") == "True"):
			self._logger.info(f"parse_config_section: section {section} is disabled, ignoring")
			return
		_type = self._config.get(section, "type")
		if _type in self.tests_table.keys():
			self.create_test(_type, section)
			self._logger.debug(f"parse_config_section: section {section} parsed, test created")
		else:
			self._logger.error(f"parse_config_section: could not find type {_type} in tests_table")
			return
		pass
	
	
	def create_test(self, _type, section):
		self._logger.debug(f"create_test: will create test for type {_type}, section: {section}")
		cls = self.tests_table[_type]
		new_test = cls(logger = self._logger.getChild(self._config.get(section, "type") + "_" + section), config = self._config, conf_dict = self._config[section])
		self.add_test(new_test)
		
		pass
	
	
	def load_all(self):
		self._logger.info("load_all: starting")
		sections = self._config.sections()
		for section in sections:
			if section == "main":
				continue
			self.parse_config_section(section)
		self._logger.info("load_all: complete")
		pass
		


class SimpleReporter(object):
	"""docstring for SimpleReporter"""
	
	def __init__(self):
		super(SimpleReporter, self).__init__()
		
		self.LOG_FILE = "./simple_reporter.log"
		self.CONFIG_FILE = "./simple_reporter.conf"
		self._config = configparser.ConfigParser()
		# self._config.read(self.CONFIG_FILE)
		
		self._logger = None
		
		# 
		self.tests = []
		self.reporters = []
		self._test_loader = None
		
		self.TEMPLATE_FILE = "main.jinja2"
		self._template = None
		self.report_text = ""
		self.rotate_logs()
		pass

	
	def rotate_logs(self):
		"""will rotate .log file to .log.old, thus new log file will be used on each start"""
		OLD_LOG_POSTFIX = ".old"
		if os.path.isfile(self.LOG_FILE + OLD_LOG_POSTFIX):
			os.unlink(self.LOG_FILE + OLD_LOG_POSTFIX)
		try:
			os.rename(self.LOG_FILE, self.LOG_FILE + OLD_LOG_POSTFIX)
		except Exception as e:
			print(f"could not rotate log file {self.LOG_FILE}, will use unrotated file!")
	
	
	def init_logger(self):
		self._logger = logging.getLogger("simple_reporter")
		self._logger.setLevel(logging.DEBUG)
		fh = logging.FileHandler(self.LOG_FILE)
		fh.setLevel(logging.DEBUG)
		formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
		fh.setFormatter(formatter)
		self._logger.addHandler(fh)
		
		self._logger.debug("======== simple_reporter starting, version " + __version__ + " ========")
		pass
	
	
	def _load_config_section_main(self):
		# logging
		if os.sep not in self._config.get("main", "log_file"):
			self.LOG_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), self._config.get("main", "log_file"))
			print(f"Using relative path to log file: {self.LOG_FILE}")
		else:
			self.LOG_FILE = self._config.get("main", "log_file")
			print(f"Using absolute path to log file: {self.LOG_FILE}")
		if self._config.get("main", "brief_section_enabled") == "yes":
			pass
		self.init_logger()
	
	
	def _load_config_section_other(self):
		sections = self._config.sections()
		for section in sections:
			if section == "main": # this section should be already persed above
				continue

			# reporter-email
			if self._config.get(section, "type") == "reporter-email" and self._config.get(section, "enabled") == "True":
				# conf_dict = self._config[section]
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
		self._logger.debug("load_config: complete")
		pass
	
	
	def init_test_loader(self):
		self._test_loader = TestLoader(logger = self._logger.getChild("TestLoader"), config = self._config)
		
	
	def init_tests(self):
		self._logger.debug("init_tests: starting")
		self.tests = []
		
		self._test_loader.load_all()
		self.tests = self._test_loader.tests
		self._logger.info(f"init_tests: complete, inited {len(self.tests)} tests")
		pass
	
	
	def init_template(self):
		env = Environment(loader = FileSystemLoader([os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates"),]), autoescape = select_autoescape())
		self._template = env.get_template(self.TEMPLATE_FILE)
	
	
	def run_tests(self):
		self._logger.info(f"run_tests: starting execution of tests - {len(self.tests)} in list")
		for t in self.tests:
			try:
				t.run()
			except Exception as e:
				self._logger.error(f"run_tests: got error while running {t}: {e}, traceback: {traceback.format_exc()}")
		self._logger.info("run_tests: complete")
		pass
	
	
	def compile_report(self):
		os_type_dict = detect_OS()
		self.report_text = self._template.render(version = __version__,
			host = get_hostname(),
			datetime = datetime.datetime.now(),
			tests = self.tests,
			os_type = os_type_dict["os_family"])
		self._logger.debug(f"compile_report: report is: {self.report_text}")
		pass
	
	
	def add_test(self, test_obj):
		self.tests.append(test_obj)
		self._logger.debug(f"add_test: added test {test_obj} ({test_obj.descr})")
	
	
	def send_report(self):
		self._logger.info(f"send_report: starting, will be used reporters: {self.reporters} ({len(self.reporters)} total)")
		for reporter in self.reporters:
			reporter.send_report(self.report_text)
			print(f"D sending report with reporter {reporter}")
			pass
		self._logger.debug("send_report: complete")




if __name__ == "__main__":
	sr = SimpleReporter()
	sr.load_config()
	# sr.init_tests()
	sr.init_template()
	sr.init_test_loader()
	sr.init_tests()
	sr.run_tests()
	sr.compile_report()
	sr.send_report()
	pass


