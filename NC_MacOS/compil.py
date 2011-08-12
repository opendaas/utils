#! /usr/bin/python

# Copyright (C) 2011 Ulteo SAS
# http://www.ulteo.com
# Author Julien LANGLOIS <julien@ulteo.com> 2011
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import shutil
import subprocess
import sys
  
def usage():
	print "Usage: %s [-h|--help] version_name"%(sys.argv[0])
	print "\t-h|--help: print this help"
	print


if __name__ == "__main__":
	import getopt
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
	
	except getopt.GetoptError, err:
		print >> sys.stderr, str(err)
		usage()
		sys.exit(1)
	
	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
			sys.exit()
	
	if len(args) != 1:
		usage()
		sys.exit(2)
	
	
	path = os.path.dirname( os.path.realpath( __file__ ) )
	version = sys.argv[1]
	name = "ulteo-ovd-native-client-%s.app"%(version)
	
	
	java_src_path = os.path.join(path, "java")
	if not os.path.isdir(java_src_path):
		print >> sys.stderr, "No such directory '%s'"%(java_src_path)
		sys.exit(1)
	
	
	# Compilation
	subprocess_env = os.environ.copy()
	subprocess_env["OVD_VERSION"] =  version
	
	cmds = ["python autogen", "ant ovdNativeClient.jar -Dlanguages=true"]
	for cmd in cmds:
		print "exec '%s' into '%s'"%(cmd, java_src_path)
		p = subprocess.Popen(args = cmd,  shell = True, cwd = java_src_path, env = subprocess_env)
		# stdout = subprocess.STDOUT, stderr = subprocess.STDOUT,
		#, env = subprocess_env)
		p.wait()
		if p.returncode is not 0:
			print >> sys.stderr, "command '%s' return error %d"%(cmd, p.returncode)
			sys.exit(2)
	
	target_dir = os.path.join(path, name)
	if os.path.exists(target_dir):
		shutil.rmtree(target_dir)
	
	
	# Copy the jar file
	os.makedirs(target_dir)
	d = os.path.join(target_dir, "Contents", "Resources", "Java")
	
	os.makedirs(d)
	shutil.copyfile(os.path.join(java_src_path, "jars", "OVDNativeClient.jar"), os.path.join(d, "OVDNativeClient.jar"))
	
	
	# Info.plist
	f = file(os.path.join(path, "Info.plist.in"), "r")
	content = f.read()
	f.close()
	
	content = content.replace("@VERSION@", str(version))
	
	f = file(os.path.join(target_dir, "Contents", "Info.plist"), "w")
	f.write(content)
	f.close()
	
	# Make the java symlink
	d = os.path.join(target_dir, "Contents", "MacOS")
	os.makedirs(d)
	os.symlink("/System/Library/Frameworks/JavaVM.framework/Resources/MacOS/JavaApplicationStub", os.path.join(d, "JavaApplicationStub"))
	
	# Copy the last ressources
	ressources = []
	ressources.append(("PkgInfo", "Contents"))
	ressources.append(("ulteo.icns",  os.path.join("Contents", "Resources")))
	
	for (f, d) in ressources:
		d2 = os.path.join(target_dir, d)
		if not os.path.isdir(d2):
			os.makedirs(d2)
		
		src = os.path.join(path, "ressources", f)
		dst = os.path.join(d2, f)
		
		print " * Copying '%s' => '%s'"%(src, dst)
		shutil.copyfile(src, dst)
	
	# zip
	cmd = "zip --symlinks -r %s.zip %s"%(name, name)
	print "exec '%s' into '%s'"%(cmd, java_src_path)
	p = subprocess.Popen(args = cmd,  shell = True, cwd = path)
	p.wait()
	if p.returncode is not 0:
		print >> sys.stderr, "command '%s' return error %d"%(cmd, p.returncode)
		sys.exit(2)
	
	
	print ""
	print " Sucefully built !"
	print "result is '%s'"%(os.path.join(path, name+".zip"))
