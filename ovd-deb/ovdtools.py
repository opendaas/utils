#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Samuel Bovée <samuel@ulteo.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, sys
import glob, shutil, pysvn
from subprocess import Popen, STDOUT

from ovdprefs import *

def display_cmd(cmd, msg, ssh=False):
    print "%s:"%msg,
    sys.stdout.flush()
    ret = run(cmd, ssh=ssh, logfile=os.path.join(LOGS_DIR, 'cmd_logs'))
    if ret: print "OK"
    else: print "FAILED"

def get_revno(svn_base):
    revno = pysvn.Client().info(svn_base)["revision"].number
    return "%05d"%revno

def get_repo_rev(branch, package, revno):
    repo = BRANCHES[branch][1]
    if repo.find('ovd') is not -1:
        package = "ulteo-" + package
    cmd = "%s '/home/gauvain/bin/ovdreprepro list %s %s | grep %s'" \
           % (SSH_CMD, repo, package, revno)
    result = os.popen(cmd).readline()
    if result == "":
        return 0
    result = result.split()[2]
    i = result.find('svn')+3
    repo_no = result[i:i+5]
    try:
        return int(result.rpartition('-')[2])
    except:
        return 0

def get_local_rev(branch, package):
    rev = 0
    for f in glob.glob("%s/%s/%s-*.dsc"%(RESULTS_DIR, branch, package)):
        rev = max (rev, int(f.rpartition('-')[2].rpartition('.dsc')[0]))
    return rev

def is_deb_built():
    cmd = "ls %s/*.deb"%BUILD_DIR
    result = os.popen(cmd).readline()
    if result == "":
        return False
    else:
        return True

def cleanup():
    os.unlink(LOCK_FILE)

def run(args, logfile=None, cwd=None, ssh=False):

    if logfile == -1:
        if cwd:
            print "Cwd: " + cwd
        print "Running cmd: "+''.join(args)
        out = sys.stdout
    else:
        if logfile:
            out = open(logfile, 'a')
        else:
            out = open('/dev/null', 'a')

    if ssh and SSH_CMD is not None:
        cmd = ''
        for i in args:
            cmd += i + ' '
        args = SSH_CMD.split(' ')
        args.append(cmd)

    process = Popen(args, stdout=out, stderr=STDOUT, cwd=cwd)
    process.communicate()

    if logfile != -1:
        out.close()

    if not process.returncode:
        return True
    return False

def save(folder, ext):
    if not os.path.isdir(folder):
        os.makedirs(folder)
    for ext in ext:
        for f in glob.glob("%s/*%s"%(BUILD_DIR, ext)):
            shutil.copy(f, folder)
