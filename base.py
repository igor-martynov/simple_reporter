
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
	# versions
	if result_dict["os_family"] == "Debian":
		with open("/etc/debian_version", "r") as f:
			content = f.read()
			result_dict["major_version"], result_dict["minor_version"] = content.replace("\n", "").split(".")
	return result_dict


class send_mail3(object):
	"""new send_mail for python3, rewrited to support gmail and SMTP authentication
	supported features:
		attachments
		utf-8
		
	"""
	
	def __init__(self, sender = "", to = [], subject = "", message = "", logger = None):
		super(send_mail3, self).__init__()
		
		self._logger = logger
		
		self.sender = sender # отправитель в виде "mail@domain.com"
		self.smtp_username = "" # 
		self.smtp_passwd = "" # 
		self.SMTP_SERVER = "" # 
		self.SMTP_PORT = 25 # 
		self.USE_AUTH = False # True if auth required
		self.USE_TLS = False # 
		
		self.recipient_list = to # лист со строками email-ов получателей
		self.subject = subject # строка с темой письма
		self.message_text = message # текст письма строкой. Допустимы переводы строки
		self.message_html = "" # письмо в виде HTML # TODO: пока не используется
		self.message = None # объект сообщения
		
		self.attachment_files = [] # список путей к аттачментам
		
		self.DEBUG = False # True if use debug
		self.VERBOSE = False # расширенные сообщения
		
		self._composed = False
		
		
	
	def compose(self):
		"""подготовить письмо к отправке"""
		# TODO: 
		
		self.message = MIMEMultipart()
		self.message["Subject"] = self.subject
		self.message["To"] = ", ".join(self.recipient_list)
		self.message["From"] = self.sender
		
		if self._logger: self._logger.info(f"compose: will use message obj {self.message}")
		
		# добавляем текстовую часть
		if len(self.message_text) != 0:
			# text_msg_part = MIMEText(self.message_text, "text")
			text_msg_part = MIMEText(self.message_text)
			self.message.attach(text_msg_part)
		
		# прикладываем файлы
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
				# raise # убрал чтобы не всплыло в продакшне
				pass
		self._composed = True
		
	
	def send(self):
		"""отправление сообщения"""
		# TODO: testing
		
		# сборка письма
		if not self._composed:
			self.compose()
		
		# отправка
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
			# raise
			if self._logger: self._logger.error("send: Unable to send the email. Error: " + str(sys.exc_info()[0]) + ", " + str(e) + ", traceback: " + traceback.format_exc())
			pass



