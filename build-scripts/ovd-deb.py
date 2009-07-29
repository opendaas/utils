#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Gauvain Pocentek <gpocentek@linutop.com>
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

import os, sys, re
import getopt
import time

BASE_DIR = '/home/gauvain/ovddebs'
LOCK_FILE = '%s/.locked'%BASE_DIR
BUILD_DIR = '%s/build'%BASE_DIR
RESULTS_DIR = '%s/results'%BASE_DIR
SVN_BASE_DIR = '%s/ovd'%BASE_DIR
DEFAULT_BRANCH = 'trunk'


packages = { 'SessionManager': 'ovd-session-manager',
             'ApplicationServer': 'ovd-application-server',
             'chroot-apps': 'ovd-chroot-apps',
             'meta': 'ulteo-ovd' }
# [ svn location, version base, repository ]
branches = { '1.1': ['branches/1.1', '1.1~~+svn', '1.1-staging'],
             '2.0': ['trunk', '2.0~~+svn', '2.0-staging'],
             'trunk': ['trunk', '2.0~~+svn', '2.0-staging'] }

sumup = {}

def svn_up ():
    os.chdir(SVN_BASE_DIR)
    os.system("svn up")

def get_revno ():
    os.chdir("%s/trunk"%SVN_BASE_DIR)
    cmd = """svn info SessionManager | awk '/^Revision: / {printf "%05d", $2}'"""
    revno = os.popen(cmd).readline()
    return revno

def make_dist (module_path):
    return os.system ('cd %s && ./autogen.sh && ./configure && make dist'%module_path)

def parse_tarball_name (tarball_name):
    r = re.compile(r"(?P<package>.*)-(?P<version>.*).tar.gz")
    m = re.search(r,tarball_name)
    return m.group('package'), m.group('version')

class DebBuild:
    def __init__(self, module, branch='trunk', publish=True):
        # set all the variables we'll need
        self.revno = get_revno()
        self.module = module
        self.publish = publish
        self.svn_base = "%s/%s"%(SVN_BASE_DIR,branches[branch][0])
        self.module_path = "%s/%s"%(self.svn_base,module)
        self.debian_path = "%s/debian/%s/debian"%(self.svn_base,packages[module])
        self.schroot_target = branches[branch][2]
        self.distro_target = self.schroot_target.replace(".", "-")

        if self.module != 'meta':
            self.tarball_name = "%s-%s%s.tar.gz"%(packages[module],branches[branch][1],self.revno)
            self.tarball_path = "%s/%s"%(self.module_path,self.tarball_name)
            self.package, self.version = parse_tarball_name(self.tarball_name)
            self.deb_version = "%s-0ulteo0"%self.version
            self.deb_orig_name = "%s_%s.orig.tar.gz"%(self.package,self.version)
            self.deb_orig_path = "%s/%s"%(BUILD_DIR,self.deb_orig_name)
            self.deb_src_dir = "%s/%s-%s"%(BUILD_DIR,self.package,self.version)
            self.deb_src_debian_dir = "%s/debian"%self.deb_src_dir
            self.deb_dsc_changes_name = "%s_%s.dsc"%(self.package,self.deb_version)
            # FIXME: guess arch
            self.deb_binary_changes_name = "%s_%s_i386.changes"%(self.package,self.deb_version)
        else:
            self.package = 'ulteo-ovd'
            self.version = '%s%s'%(branches[branch][1],self.revno)
            self.deb_version = self.version
            self.deb_dsc_changes_name = "%s_%s.dsc"%(self.package,self.deb_version)
            self.deb_binary_changes_name = "%s_%s_i386.changes"%(self.package,self.deb_version)
            self.deb_src_dir  = "%s/%s-%s"%(BUILD_DIR,self.package,self.version)


    def _build_source(self):
        os.chdir(self.svn_base)
        if self.module != 'meta':
            ret = make_dist (self.module_path)
            if ret:
                raise "make_dist() failed (%s)" % self.module
            os.rename(self.tarball_path, self.deb_orig_path)
            os.system('tar zxf %s -C %s'%(self.deb_orig_path,BUILD_DIR))
            os.system('cp -R %s %s'%(self.debian_path,self.deb_src_dir))
        else:
            os.system('cp -R %s/debian/%s %s/ulteo-ovd-%s'%(self.svn_base,self.package,BUILD_DIR,self.version))
        os.system('rm -rf $(find %s -name .svn)'%self.deb_src_dir)

        os.chdir(self.deb_src_dir)
        cmd = 'dch --force-distribution -D %s -v %s New devel snaphot'%(self.distro_target,self.deb_version)
        os.system(cmd)
        os.system('debuild -S -sa -us -uc')



    def build_deb(self):
        self._build_source()
        os.chdir(BUILD_DIR)
        cmd = 'sbuild --force-orig-source -A -s -d %s %s'%(self.schroot_target,self.deb_dsc_changes_name)
        os.system(cmd)

        if os.path.isfile(self.deb_binary_changes_name):
            return self.deb_binary_changes_name
        else:
            return False

    def do_publish(self):
        os.chdir(BUILD_DIR)
        if self.publish:
            os.system('dput ovd-local %s'%changes)
            os.system('/home/gauvain/bin/update-ovd-repo.sh')
        else:
            target_dir = "%s/%s"%(RESULTS_DIR,self.schroot_target)
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir)
            for ext in ['gz','deb','udeb','dsc']:
                cmd = "cp -v *.%s %s"%(ext,target_dir)
                os.system(cmd)





if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'nb:', ['no-publish', 'branch'])
    except getopt.GetoptError, err:
        print >> sys.stderr, "Error parsing the command line"
        sys.exit(1)

    # defaults
    publish = True
    branch = DEFAULT_BRANCH

    for o, a in opts:
        if o in ('-n', '--no-publish'):
            publish = False
        if o in ('-b', '--branch'):
            if branches.has_key(a):
                branch = a
            else:
                print "Unknown branch: %s"%a
                sys.exit(1)

    if len(args) < 1:
        to_build = packages.keys()
    else:
        to_build = []
        for k in args:
            if packages.has_key(k):
                to_build.append(k)
            else:
                print "Unknown module: %s\n"%k

    if len(to_build) == 0:
        print "Nothing to build."
        sys.exit(0)

    while os.path.isfile(LOCK_FILE):
        print 'Build system locked; waiting...'
        time.sleep(5)
    open(LOCK_FILE, 'w').close()

    svn_up()

    for module in to_build:
        os.system("rm -rf %s/*"%BUILD_DIR)

        print "Now building module %s\n"%module
        deb = DebBuild(module,branch,publish)
        changes = deb.build_deb()
        if not changes:
            print "ERROR: module %s not built"%module
            sumup[module] = False
        else:
            deb.do_publish()
            sumup[module] = True


    txt = "\nSumup:\n"
    for module in sumup.keys():
        txt += "  %s => "%module
        if sumup[module]:
            txt += "built\n"
        else:
            txt += "FAILED\n"

    print txt

    os.unlink(LOCK_FILE)
