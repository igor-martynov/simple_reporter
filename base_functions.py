
import sys
import os.path
import os
import datetime
import time
import math
import glob


import multiprocessing
import threading
import sqlite3

import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# logging
import logging
import logging.handlers

import traceback



def get_hostname():
	import socket
	return socket.gethostname()


def normalize_path_to_dir(path_to_dir):
	if path_to_dir.startswith(" "):
		path_to_dir = path_to_dir[1:]
	if path_to_dir.endswith("/"):
		return path_to_dir[:-1]
	else:
		return path_to_dir


def run_command(cmdstring):
	import subprocess
	import shlex
	
	if len(cmdstring) == 0:
		return -1
	args = shlex.split(cmdstring)
	run_proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
	result = subprocess.Popen.communicate(run_proc)[0].decode("utf-8")
	return result


def detect_OS():
	"""Ansible-like detection of OS type, distribution and version, will return dict"""
	result_dict = {"os_family": None, "distribution": None, "major_version": None, "minor_version": None, "release": None}
	# os_family
	if os.path.isfile("/etc/redhat-release"):
		result_dict["os_family"] = "RedHat"
	if os.path.isfile("/etc/SuSE-release"):
		result_dict["os_family"] = "SuSE"
	if os.path.isfile("/etc/debian_version"):
		result_dict["os_family"] = "Debian"
	if os.path.isfile("/bin/freebsd-version"):
		result_dict["os_family"] = "FreeBSD"
	# version
	if result_dict["os_family"] == "Debian":
		with open("/etc/debian_version", "r") as f:
			content = f.read()
			result_dict["major_version"], result_dict["minor_version"] = content.replace("\n", "").split(".")
	if result_dict["os_family"] == "FreeBSD":
		try:
			tmp = run_command("freebsd-version")
			result_dict["major_version"], result_dict["minor_version"] = tmp.split("-")[0].split(".")
		except Exception as e:
			pass
	# print(f"D detected os: {result_dict}")
	return result_dict


# TODO: tested in Linux, should be tested more
def parse_uptime(uptime_str):
	"""
	currently has error in parsing
	20:17:33 up 2 days, 57 min,  1 user,  load average: 0.25, 0.06, 0.02
	"""
	uptime_timedelta = None
	days = 0
	hours = 0
	minutes = 0
	
	try:
		# stage1 - get substring
		substr1 = uptime_str.split(" up ")[1]
		substr2 = substr1.split(" user")[0]
		sublist3 = substr2.split(", ")
		substr = ", ".join(sublist3[:-1])
		
		# stage2 - parse substring into ints
		if "day" in substr: # if uptime is more than 1 day
			days = int(substr.split(" day")[0])
			substr_no_day = substr.split("days, ")[1] if "days, " in substr else substr.split("day, ")[1]
			if substr_no_day.startswith(" "):
				substr_no_day = substr_no_day[1:]
		else:
			substr_no_day = substr		
		if "min" in substr: # if uptime is counted in minutes (0..59 min)
			minutes = int(substr.split(" min")[0])
		else:
			hours = int(substr_no_day.split(":")[0])
			minutes = int(substr_no_day.split(":")[1])
		
	except Exception as e:
		print(f"parse_uptime: got exception {e}, traceback: {traceback.format_exc()}")
	return datetime.timedelta(days = days, hours = hours, minutes = minutes)


def get_uptime():
	uptime_cmd_result = run_command("uptime")
	return parse_uptime(uptime_cmd_result)


def save_heartbeat(heartbeat_file):
	with open(heartbeat_file, "w") as f:
		datetime_now_str = datetime.datetime.now().isoformat()
		f.write(datetime_now_str)
		return True
	return False


def read_heartbeat(heartbeat_file):
	with open(heartbeat_file, "r") as f:
		content = f.read()
		heartbeat_datetime = datetime.datetime.fromisoformat(content)
		return heartbeat_datetime


def humanify_seconds(iseconds):
	day_max_s = 24 * 3600
	hour_max_s = 3600
	week_max_s = day_max_s * 7
	weeks = 0
	days = 0
	hours = 0
	minutes = 0
	seconds = 0
	
	weeks = int(iseconds // week_max_s)
	remain = iseconds - weeks * week_max_s
	days = int(remain // day_max_s)
	remain = remain - days * day_max_s
	hours = int(remain // hour_max_s)
	remain = remain - hours * hour_max_s
	minutes = int(remain // 60)
	remain = remain - minutes * 60
	seconds = int(remain)
	
	if weeks != 0:
		result = f"{weeks} weeks, {days} days, {hours:01d}:{minutes:01d}:{seconds:01d}"
	elif days != 0:
		result = f"{days} days, {hours:01d}:{minutes:01d}:{seconds:01d}"
	else:
		result = f"{hours:01d}:{minutes:01d}:{seconds:01d}"
	return result



class send_mail3(object):
	"""new send_mail for python3, rewrited to support gmail and SMTP authentication
	supported features:
		attachments
		utf-8
		
	"""
	
	def __init__(self, sender = "", to = [], subject = "", message = "", logger = None):
		super(send_mail3, self).__init__()
		
		self._logger = logger
		
		self.sender = sender # sender in standard form "mail@domain.com"
		self.smtp_username = "" # 
		self.smtp_passwd = "" # 
		self.SMTP_SERVER = "" # 
		self.SMTP_PORT = 25 # 
		self.USE_AUTH = False # True if auth required
		self.USE_TLS = False # 
		
		self.recipient_list = to # list of recimients, i.e ["mail1@example.com",]
		self.subject = subject # email subject
		self.message_text = message # body text, can contain "\n"
		self.message_html = "" # message body in HTML # TODO: currently unused
		self.message = None # message object
		
		self.attachment_files = [] # list of paths of attachments
		
		self.DEBUG = False # True if use debug
		self.VERBOSE = False # True if should be verbose
		
		self._composed = False
		
		
	
	def compose(self):
		"""compose message and prepare for dispatch"""
		# TODO: 
		
		self.message = MIMEMultipart()
		self.message["Subject"] = self.subject
		self.message["To"] = ", ".join(self.recipient_list)
		self.message["From"] = self.sender
		
		if self._logger: self._logger.info(f"compose: will use message obj {self.message}")
		
		# adding message part
		if len(self.message_text) != 0:
			# text_msg_part = MIMEText(self.message_text, "text")
			text_msg_part = MIMEText(self.message_text)
			self.message.attach(text_msg_part)
		
		# adding attachments
		for f in self.attachment_files:
			try:
				attachment_msg = MIMEBase('application', "octet-stream")
				with open(f, 'rb') as of:
					attachment_msg.set_payload(of.read())
				
				encoders.encode_base64(attachment_msg)
				attachment_msg.add_header('Content-Disposition', 'attachment', filename = os.path.basename(f))
				self.message.attach(attachment_msg)
				
			except Exception as e:
				print("Unable to open one of the attachments. Error: " + str(sys.exc_info()[0]) + ", " + str(e) + ", traceback: " + traceback.format_exc())
				pass
		self._composed = True
		
	
	def send(self):
		"""send message"""
		if not self._composed:
			self.compose()
		try:
			with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT) as smtp_obj:
				# smtp_obj.connect()
				if self.DEBUG:
					smtp_obj.set_debuglevel(True)
				# smtp_obj.ehlo()
				
				if self.USE_TLS:
					smtp_obj.starttls()
				smtp_obj.ehlo()
				if self.USE_AUTH:
					smtp_obj.login(self.smtp_username, self.smtp_passwd)
				smtp_obj.sendmail(self.sender, self.recipient_list, self.message.as_string())
				smtp_obj.close()
			if self._logger: self._logger.info("send: message send successfuly")
		except Exception as e:
			print("Unable to send the email. Error: " + str(sys.exc_info()[0]) + ", " + str(e) + ", traceback: " + traceback.format_exc())
			if self._logger: self._logger.error("send: Unable to send the email. Error: " + str(sys.exc_info()[0]) + ", " + str(e) + ", traceback: " + traceback.format_exc())
			pass


