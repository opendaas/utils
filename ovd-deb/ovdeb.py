#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Samuel Bovée <samuel@ulteo.com>
# Author Laurent CLOUET <laurent@ulteo.com>
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
import getopt, atexit, time, shutil

from ovdprefs import *
from ovdtools import *
from ovdebuild import ovdebuild

def display_cmd(cmd, msg, ssh=False):
    print "%s:"%msg,
    sys.stdout.flush()
    ret = run(cmd, ssh=ssh, logfile=os.path.join(LOGS_DIR, 'cmd_logs'))
    if ret: print "OK"
    else: print "FAILED"

try:
    opts, args = getopt.getopt(sys.argv[1:], 'horpb:',
                     ['help', 'stdout', 'release', 'publish', 'branch=', 'xml'])
except getopt.GetoptError, err:
    print >> sys.stderr, 'Error parsing the command line'
    sys.exit(1)

# defaults options
publish, release, on_stdout = False, False, False
branch = DEFAULT_BRANCH

for o, a in opts:

    if o in ('-r', '--do-release'):
        release = True

    if o in ('-p', '--publish'):
        publish = True

    if o in ('-o', '--stdout'):
        on_stdout = True

    if o in ('-b', '--branch'):
        if BRANCHES.has_key(a):
            branch = a
        else:
            print "Unknown branch: '%s'"%a
            sys.exit(1)

    if o in ('--xml'):
        print conftoxml().toprettyxml()
        sys.exit(0)

    if o in ('-h', '--help'):
        print """\
ovd-deb [-p|--publish] [-b|--branch branches] [-r|--release] [-o|--stdout]
ovd-deb --xml
ovd-deb [-h|--help]"""
        sys.exit(0)

if len(args) < 1:
    to_build = PACKAGES[branch].keys()
else:
    to_build = []
    for k in args:
        if PACKAGES[branch].has_key(k):
            to_build.append(k)
        else:
            print 'Unknown module: %s\n'%k
if on_stdout:
    print to_build

if len(to_build) == 0:
    print 'Nothing to build.'
    sys.exit(0)

while os.path.isfile(LOCK_FILE):
    print 'Build system locked; waiting...'
    try:
        time.sleep(5)
    except:
        sys.exit(2)
open(LOCK_FILE, 'w').close()
def cleanup():
    os.unlink(LOCK_FILE)
atexit.register(cleanup)

quilt_file = os.path.join(BASE_DIR, '.quiltrc')
f = open(quilt_file, 'w')
f.write("QUILT_PATCHES=%s/patches\n"%BASE_DIR)
f.close()

display_cmd(['sudo', 'apt-get', 'update'], "Update the apt cache packaging")
svn_base = os.path.join(SVN_BASE_DIR, BRANCHES[branch][0])
if not release:
    display_cmd(['svn', '-R', 'revert', svn_base],
                "Revert the subversion repository")
display_cmd(['svn', 'up', svn_base], "Update the subversion repository")

sumup = {}

for module in to_build:
    rminfolder(BUILD_DIR)
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)
    os.chdir(BUILD_DIR)

    print '\nBuild started for module %s (%s)' %\
        (PACKAGES[branch][module][1], BRANCHES[branch][0])

    deb = ovdebuild(module, branch, release, on_stdout)
    for arch in PACKAGES[branch][module][3]:
        deb.build_deb(arch)
    deb.remove_patch()
    if publish:
        deb.publish()
    sumup[module] = deb.get_sumup()

if publish:
    display_cmd(['/home/gauvain/bin/ovdweb'], \
                "\nUpdate the OVD package website", ssh=True)
    print "Update XML repo file: ",
    sys.stdout.flush()
    xml = conftoxml().toxml()
    fd = open('/var/cache/ovdeb/repo.xml', 'w')
    fd.write(xml)
    fd.close()
    print "OK"

text = '\n'
for module in sumup.keys():
    failure = False
    for step in sumup[module][1].keys():
        if not sumup[module][1][step]:
            failure = step
            break
    if failure:
        result = "FAILURE (%s), log in %s" % (step, sumup[module][0])
    else:
        result = "BUILT"
    text += "%s -> %s\n" % (module, result)

print text
