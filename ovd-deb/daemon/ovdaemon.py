#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, commands, signal, Queue
from pyinotify import ThreadedNotifier, WatchManager, \
                      ProcessEvent, EventsCodes

sys.path.append(os.path.join(sys.path[0], '..'))
from ovdprefs import *
from ovdtools import conftoxml

class PRec(ProcessEvent):

	def __init__(self, jobs_):
		self.jobs = jobs_

	def process_IN_CLOSE_WRITE(self, event_k):
		file_path = os.path.join(event_k.path,event_k.name)
		file_dirname = os.path.dirname(file_path)
		if os.path.isfile(file_path):
			f = open(file_path, 'r')
			contents = f.read()
			f.close()
			a_list = contents.split("|")
			if len(a_list) == 2:
				job_file = os.path.join(SPOOL_DIR, 'inprogress', event_k.name)
				self.jobs.put((a_list[0].strip(), a_list[1].strip(), job_file))
				os.rename(file_path, job_file)
				print "job added (%s,%s)"%(a_list[0].strip(), a_list[1].strip())

if __name__ == "__main__":
	jobs = Queue.Queue()
	wm = WatchManager()
	th_inotify = ThreadedNotifier(wm)
	th_inotify.start()
	d = wm.add_watch(os.path.join(SPOOL_DIR, 'incoming'), \
                     EventsCodes.IN_CLOSE_WRITE, PRec(jobs), False, False)

	loop = True
	def quit(Signum=None, Frame=None):
		global loop
		loop=False
	signal.signal(signal.SIGINT,  quit)
	signal.signal(signal.SIGTERM, quit)

	while loop:
		try:
			a_job = jobs.get(timeout=1)
		except Queue.Empty:
			continue
		branch, package, job_file = a_job[0], a_job[1], a_job[2]
		#TODO: do it with import...
		cmd = 'python %s --publish --branch %s %s' % \
				(os.path.join(BASE_DIR,'ovdeb.py'), branch, package)
		print "new job cmd ", cmd
		ret = commands.getstatusoutput(cmd)
		conftoxml()
		job_done = os.path.join(SPOOL_DIR, 'done', os.path.basename(job_file))
		os.rename(job_file, job_done)
		print "job done(%s,%s)" % (branch, package)

	if th_inotify.isAlive():
		th_inotify.stop()
