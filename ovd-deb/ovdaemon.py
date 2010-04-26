#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, time, threading, urllib2, urllib, mimetypes, md5, commands, shutil, tarfile, bz2, user, signal
import xml.dom.minidom
import commands
import Queue
import os,logging,pwd
from pyinotify import ProcessEvent
from pyinotify import ThreadedNotifier, WatchManager
from pyinotify import ProcessEvent, EventsCodes

spool_dir = os.path.join('/', 'tmp','packages')

class PRec(ProcessEvent):
	def __init__(self, jobs_):
		self.jobs = jobs_

	def process_IN_CLOSE_WRITE(self, event_k):
		file_path = os.path.join(event_k.path,event_k.name)
		file_dirname = os.path.dirname(file_path)
		if os.path.isfile(file_path):
			#print "PRec::process_IN_CREATE '%s'"%(file_path)
			f = open(file_path, 'r')
			contents = f.read()
			f.close()
			a_list = contents.split("|")
			if len(a_list) == 2:
				job_file = os.path.join(spool_dir, 'inprogress', event_k.name)
				self.jobs.put((a_list[0].strip(), a_list[1].strip(), job_file))
				#print "os.rename(%s,%s)"%(file_path, job_file)
				os.rename(file_path, job_file)
				print "job added (%s,%s)"%(a_list[0], a_list[1])

if __name__ == "__main__":
	jobs = Queue.Queue()

	wm = WatchManager()
	th_inotify = ThreadedNotifier(wm)
	th_inotify.start()

	d = wm.add_watch(path=os.path.join(spool_dir, 'incoming'), mask=EventsCodes.IN_CLOSE_WRITE, proc_fun=PRec(jobs),rec=False,auto_add=False)

	while True:
		a_job = jobs.get()
		cmd = 'python /home/gauvain/ovddebs/ovd-deb-package.py -b %s %s'%(a_job[0], a_job[1])
		#cmd = 'python /home/gauvain/ovddebs/ovd-deb-package.py --publish -b %s %s'%(a_job[0], a_job[1])
		#print "start ",a_job
		print "new job cmd ", cmd
		ret = commands.getstatusoutput(cmd)
		#print ret
		job_file = a_job[2]
		job_done = os.path.join(spool_dir, 'done', os.path.basename(job_file))

		os.rename(job_file, job_done)
		print "job done"
