#!/usr/bin/python
import re
import os
import glob
import sys
import ConfigParser
import time
import operator
from stat import *
from operator import itemgetter, attrgetter
from datetime import datetime
from dateutil.relativedelta import relativedelta

#==================Task Class================================
class Task:
	#Init the task
	#Folder and matching criteria are required, everything else is optional
	def __init__(self, desc, directory, match, age="0", keep="0", action="rm -f"):
		self.desc = desc
		self.directory = directory
		self.match = match
		self.age = self.date_converter(age)
		self.keep = keep
		self.action = action
	
	#Convert a human readable date to epoch time
	def date_converter(self, age):
		date_match = re.compile("([0-9]+)y-([0-9]+)m-([0-9]+)d-([0-9]+)h-([0-9]+)m").match(age)
		try:
			year=int(date_match.group(1))
			month=int(date_match.group(2))
			day=int(date_match.group(3))
			hour=int(date_match.group(4))
			minute=int(date_match.group(5))
		except AttributeError:
			print "Error under section '"+self.desc+"' age attribute is wrong. The format is '(year)y-(month)m-(day)d-(hour)h-(minute)m'"
			sys.exit(1)
		time_diff=datetime.now() + relativedelta(years = -year, months = -month, days= -day, hours= -hour, minutes= -minute)
		epoch=time.mktime(time_diff.timetuple())
		return time.time()-epoch
	
	#Run action on dir for matching parameters
	def execute(self):
		print "Execute task '"+self.desc+"'"
		old_file_tuples = []
		for file in os.listdir(self.directory):
			file = self.directory+"/"+file
			#if file matches our regex and is old
			if re.compile(self.match).match(file) and time.time() - os.stat(file)[ST_CTIME] > int(self.age):
				old_file_tuples.append((os.stat(file)[ST_CTIME], file))
		#Sort the old files, first by timestamp then by date
		old_file_tuples = sorted(old_file_tuples)
		for i in range(int(self.keep)):
			if len(old_file_tuples) == 0:
				break
			old_file_tuples.pop(len(old_file_tuples)-1)
		for file_tuple in old_file_tuples:
			print "Running command '"+self.action+"' on file '"+file_tuple[1]+"'"
			os.system(self.action+" "+file_tuple[1])

#==================Functions for main prog================================
#Read the maidconf file
def read_config():
	tasks = []
	config = ConfigParser.ConfigParser()
	config.read(os.environ['HOME']+"/.maidconf")
	for sec in config.sections():
		#Required values
		try:
			ddesc = sec
			ddirectory = config.get(sec, "directory")
			if ddirectory[0:1] == "~":
				ddirectory = os.environ['HOME']+ddirectory[1:]
			dmatch = config.get(sec, "match")
		except ConfigParser.NoOptionError:
			print "Error Parsing Config file under section '"+sec+"'"
			sys.exit(1)
		#Optional values. Defaults are also set here
		try:
			dage = config.get(sec, "age")
		except ConfigParser.NoOptionError:
			dage = "0y-0m-1d-0h-0m" #Anything over a day old
		try:
			dkeep = config.get(sec, "keep")
		except ConfigParser.NoOptionError:
			dkeep = "0" #Leave nothing behind
		try:
			daction = config.get(sec, "action")
		except ConfigParser.NoOptionError: 
			daction = "rm -f" #Erase matches
		task = Task(ddesc, ddirectory, dmatch, age=dage, keep=dkeep, action=daction)
		tasks.append(task)
	return tasks
	
#===================Main Prog======================= 
#Load up the task list
tasks = read_config()

for task in tasks:
	task.execute()
