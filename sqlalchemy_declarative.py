#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 


import sys
import os.path
import os
import datetime


import traceback


# SQL Alchemy
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


# logging
import logging
import logging.handlers


DeclarativeBase = declarative_base()




class TestResult(DeclarativeBase):
	"""docstring for TestResult"""
	
	__tablename__ = "task_results"
	id = Column(Integer, primary_key = True)
	TYPE = Column(String, nullable = False)
	name = Column(String, nullable = False) # this should be set to name of config section
	descr = Column(String, nullable = True)
	running = Column(Boolean, nullable = True, default = None)
	complete = Column(Boolean, nullable = True, default = None)
	failed = Column(Boolean, nullable = True, default = None) # if result is faulty 
	date_start = Column(DateTime, nullable = True)
	date_end = Column(DateTime, nullable = True)
	result = Column(String, nullable = True)
	result_brief = None
	error_text = Column(String, nullable = True)
	ignored = Column(Boolean, nullable = True, default = None)
	config_json = Column(String, nullable = True)
	
	pass
		


