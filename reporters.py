#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# 

__author__ = "Igor Martynov (phx.planewalker@gmail.com)"



"""
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

from tests import *
from base import *


class BaseReporter(object):
	"""docstring for BaseReporter"""
	def __init__(self, config = None, logger = None):
		super(BaseReporter, self).__init__()
		self._config = config
		self._logger = logger

	
	def load_config(self):
		raise NotImplemented
	
	
	def send_report(self, report):
		raise NotImplemented
	
	

class EmailReporter(send_mail3, BaseReporter):
	"""docstring for EmailReporter - this is wrapper class for send_mail3. It can send reports via email"""
	
	def __init__(self, config = None, logger = None, sender = "", to = [], subject = "", message = ""):
		# super(EmailReporter, self).__init__(logger = logger, config = config, sender = sender, to = to, subject = subject, message = message)
		send_mail3.__init__(self, sender = sender, to = to, subject = subject, message = message, logger = logger)
		BaseReporter.__init__(self, logger = logger, config = config)
		# self._config = config
		# self._logger = logger
		
		self.RECIPIENT_DIVIDER = ","
		
		self.load_config()
		pass
	
	
	def load_config(self):
		target_section = ""
		for section in self._config.sections():
			if "type" not in self._config.options(section):
				self._logger.debug(f"load_config: no option 'type' in section {section}")
				continue
			if self._config.get(section, "type") == "reporter-email":
				if self._config.get(section, "enabled") != "True":
					self._logger.info(f"load_config: found section {section}, but it is disabled, ignoring")
					continue
				self._logger.debug(f"load_config: will use section {section}")
				try:
					self.sender = self._config.get(section, "sender")
					self.smtp_passwd = self._config.get(section, "smtp_password")
					self.smtp_username = self._config.get(section, "smtp_username")
					self.recipient_list = self._config.get(section, "to").split(self.RECIPIENT_DIVIDER)
					# print("D recipient_list: " + str(self._config.get(section, "to").split(self.RECIPIENT_DIVIDER)))
					self.SMTP_SERVER = self._config.get(section, "smtp_server")
					self.SMTP_PORT = int(self._config.get(section, "smtp_port"))
					self.USE_AUTH = True if self._config.get(section, "use_auth") == "True" else False
					self.USE_TLS = True if self._config.get(section, "use_tls") == "True" else False
					# self.subject = self._config.get(section, "email_subject")
					self.subject = Environment(loader = BaseLoader).from_string(self._config.get(section, "email_subject")).render(hostname = socket.getfqdn())
					self._logger.info("load_config: config load complete, ending section parsing")
				except Exception as e:
					self._logger.error(f"load_config: got error while parsing section, error: {e}, traceback: {traceback.format_exc()}")
				break
			pass
		
		pass
	
	
	def send_report(self, report):
		self._logger.debug("send_report: starting")
		self.message_text = report
		self.compose()
		self.send()
		self._logger.debug("send_report: complete")
		


class FileReporter(BaseReporter):
	"""docstring for FileReporter"""
	def __init__(self, config = None, logger = None):
		super(FileReporter, self).__init__(logger = logger, config = config)
		
		self.filename = "report.txt"
		self.load_config()
		pass
	
	
	def load_config(self):
		target_section = ""
		for section in self._config.sections():
			if "type" not in self._config.options(section):
				self._logger.debug(f"load_config: no option 'type' in section {section}")
				continue
			if self._config.get(section, "type") == "reporter-file":
				if self._config.get(section, "enabled") != "True":
					self._logger.info(f"load_config: found section {section}, but it is disabled, ignoring")
					continue
				self._logger.debug(f"load_config: will use section {section}")
				try:
					self.filename = self._config.get(section, "filename")
				except Exception as e:
					self._logger.error(f"load_config: got error while parsing section, error: {e}, traceback: {traceback.format_exc()}")
				break
	
	
	def send_report(self, report):
		with open(self.filename, "w") as f:
			f.write(report)
		self._logger.debug(f"send_report: report written to file {self.filename}")
	


