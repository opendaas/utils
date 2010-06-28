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
import glob, shutil
from subprocess import Popen, STDOUT
from xml.dom.minidom import Document

from ovdprefs import *

def run(args, logfile=None, cwd=None, ssh=False):

    if logfile == -1:
        if cwd:
            print "Cwd: " + cwd
        print "Running cmd: "+' '.join(args)
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

def get_repo_version(branch, package):
    cmd = "%s 'ovdreprepro -T dsc list %s %s'" % (SSH_CMD, branch, package)
    result = os.popen(cmd).readline()
    if result:
        return result[:len(result)-1].rpartition(' ')[2]
    else:
        return ''

def save(folder, ext):
    if not os.path.isdir(folder):
        os.makedirs(folder)
    for ext_ in ext:
        for f in glob.glob("%s/*%s"%(BUILD_DIR, ext_)):
            shutil.copy(f, folder)

def rminfolder(dir_):
    for filename in os.listdir(dir_):
        try:
            path = os.path.join(dir_, filename)
            os.remove(path)
        except OSError:
            if sys.exc_value.errno is 21:
                shutil.rmtree(path)

def conftoxml():
    doc = Document()
    packages_node = doc.createElement('root')
    doc.appendChild(packages_node)
    for (svn_repo, packages_dic) in PACKAGES.items():
        branch_node = doc.createElement('branch')
        branch_node.setAttribute('repo', svn_repo)
        for (package_name, v) in packages_dic.items():
            package_name_node = doc.createElement('package')
            package_name_node.setAttribute('alias', package_name)
            package_name_node.setAttribute('directory', v[0])
            package_name_node.setAttribute('name', v[1])
            package_name_node.setAttribute('version', \
                get_repo_version(BRANCHES[svn_repo][1], v[1]))
            branch_node.appendChild(package_name_node)
        packages_node.appendChild(branch_node)
    xml = doc.toxml()
    fd = open(os.path.join(CACHE_DIR, 'repo.xml'), 'w')
    fd.write(xml)
    fd.close()
    return doc
