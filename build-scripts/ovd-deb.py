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
import shutil
import time
from subprocess import Popen, STDOUT, PIPE
import glob
import atexit

BASE_DIR = '/home/gauvain/ovddebs'
LOCK_FILE = '%s/.locked'%BASE_DIR
LOGS_DIR = '%s/logs'%BASE_DIR
BUILD_DIR = '%s/build'%BASE_DIR
RESULTS_DIR = '%s/results'%BASE_DIR
SVN_BASE_DIR = '%s/svn'%BASE_DIR
DEFAULT_BRANCH = 'trunk'

AUTOTOOLS_CMD = [['./autogen.sh'], ['./configure'], ['make', 'distcheck']]
ANT_CMD = [['./bootstrap'], ['ant', 'dist']]

DEBUG = False

packages = { 'SessionManager': ['ovd-session-manager', AUTOTOOLS_CMD],
             'ApplicationServer': ['ovd-application-server', AUTOTOOLS_CMD],
             'chroot-apps': ['ovd-chroot-apps', AUTOTOOLS_CMD],
             'client/java': ['ovd-applets', ANT_CMD],
             'meta': ['ulteo-ovd', ''] }
# [ svn location, version base, repository ]
branches = { '1.1': ['branches/1.1', None, '1.1-staging'],
             '2.0': ['trunk', None, '2.0-staging'],
             'trunk': ['trunk', None, '2.0-staging'] }

sumup = {}

def log_start(message):
    print message + '... ',
    sys.stdout.flush()

def log_end(success):
    if success:
        print 'OK'
    else:
        print 'FAILED'

def init():
    svn_up()
    for branch in branches.keys():
        branches[branch][1] = get_base_version (branches[branch][0])

def svn_up():
    log_start("Updating the svn tree")
    log_end (run(['svn', 'up'], cwd=SVN_BASE_DIR))

def get_revno():
    os.chdir('%s/trunk'%SVN_BASE_DIR)
    cmd = """svn info SessionManager | awk '/^Revision: / {printf "%05d", $2}'"""
    revno = os.popen(cmd).readline()
    return revno

def get_base_version(branch):
    major = None
    minor = None
    build = None
    major_re = re.compile(r'^m4_define.*_version_major.*\[([^\[]*)].*')
    minor_re = re.compile(r'^m4_define.*_version_minor.*\[([^\[]*)].*')
    build_re = re.compile(r'^m4_define.*_version_build.*\[([^\[]*)].*')

    lines = open('%s/%s/SessionManager/configure.in.in'%(SVN_BASE_DIR, branch)).readlines()[:3]

    try:
        major = major_re.search(lines[0]).group(1)
        minor = minor_re.search(lines[1]).group(1)
        try:
            # the build field might be empty
            build = build_re.search(lines[2]).group(1).replace('@REVISION@', '')
        except:
            build = ''
        return '%s.%s%s'%(major, minor, build)
    except:
        return None

def parse_tarball_name(tarball_name):
    r = re.compile(r'(?P<package>.*)-(?P<version>.*).tar.gz')
    m = re.search(r,tarball_name)
    return m.group('package'), m.group('version')

def cleanup():
    os.unlink(LOCK_FILE)

def run(args, logfile=None, cwd=None):
    if DEBUG:
        if cwd:
            print "Cwd: " + cwd
        print "Running cmd "+" ".join(args)

    if logfile == -1:
        out = sys.stdout
    else:
        if logfile:
            out = open(logfile, 'a')
        else:
            out = open('/dev/null', 'a')

    process = Popen(args, stdout=out, stderr=STDOUT, cwd=cwd)
    process.communicate()

    if logfile != -1:
        out.close()

    if not process.returncode:
        return True
    return False

class DebBuild:
    def __init__(self, module, branch='trunk', release=False, publish=True, on_stdout=False):
        # set all the variables we'll need
        self._revno = get_revno()
        self._module = module
        self._do_release = release
        self._do_publish = publish
        self._on_stdout = on_stdout
        self._svn_base = '%s/%s'%(SVN_BASE_DIR,branches[branch][0])
        self._module_path = '%s/%s'%(self._svn_base,module)
        self._debian_path = '%s/debian/%s/debian'%(self._svn_base,packages[self._module][0])
        self._schroot_target = branches[branch][2]
        self._distro_target = self._schroot_target.replace('.', '-')

        if self._module != 'meta':
            self._tarball_name = '%s-%s%s.tar.gz'%(packages[self._module][0],branches[branch][1],self._revno)
            self._tarball_path = '%s/%s'%(self._module_path,self._tarball_name)
            self._package, self._version = parse_tarball_name(self._tarball_name)
            if not self._do_release:
                self._deb_version = '%s-0ulteo0'%self._version
            else:
                self._deb_version = self._get_changelog_version()
            self._deb_orig_name = '%s_%s.orig.tar.gz'%(self._package,self._version)
            self._deb_orig_path = '%s/%s'%(BUILD_DIR,self._deb_orig_name)
            self._deb_src_dir = '%s/%s-%s'%(BUILD_DIR,self._package,self._version)
            self._deb_src_debian_dir = '%s/debian'%self._deb_src_dir
            self._deb_dsc_changes_name = '%s_%s.dsc'%(self._package,self._deb_version)
            # TODO: guess arch
            self._deb_binary_changes_name = '%s_%s_i386.changes'%(self._package,self._deb_version)
            self._deb_binary_changes_file = '%s/%s'%(BUILD_DIR, self._deb_binary_changes_name)
        else:
            self._package = 'ulteo-ovd'
            if not self._do_release:
                self._version = '%s%s'%(branches[branch][1],self._revno)
                self._deb_version = self._version
            else:
                self._version = branches[branch][1]
                self._deb_version = self._get_changelog_version()
            self._deb_dsc_changes_name = '%s_%s.dsc'%(self._package,self._deb_version)
            self._deb_binary_changes_name = '%s_%s_i386.changes'%(self._package,self._deb_version)
            self._deb_binary_changes_file = '%s/%s'%(BUILD_DIR, self._deb_binary_changes_name)
            self._deb_src_dir  = '%s/%s-%s'%(BUILD_DIR,self._package,self._version)

        self._logfile_name = '%s-%s_%s.txt' % (self._package, self._deb_version, int(time.time()))
        self._logfile_dir = '%s/%s' % (LOGS_DIR, self._schroot_target)
        if not os.path.isdir(self._logfile_dir):
            os.makedirs(self._logfile_dir)
        self._logfile = '%s/%s'%(self._logfile_dir, self._logfile_name)

        self._sumup = { 'srcbuild': True,
                        'debbuild': True,
                        'publish': True }


    def _log(self, message):
        f = open(self._logfile, 'a')
        f.write(message)
        f.close()

    def _run(self, args, log=True, cwd=None):
        if log:
            if not self._on_stdout:
                return run(args, self._logfile, cwd)
            else:
                return run(args, -1, cwd)
        else:
            return run(args, cwd=cwd)

    def _get_changelog_version(self):
        changelog = '%s/changelog' % self._debian_path
        f = open(changelog)
        line = f.readline()
        f.close()
        r = re.compile(r'(?P<name>.*) \((?P<version>.*)\) (?P<target>.*); urgency=(?P<urgency>.*)')
        try:
            return r.search(line).group('version')
        except:
            return None

    def _make_dist(self):
        ret = True
        for cmd in packages[self._module][1]:
            ret = self._run (cmd, log=True, cwd=self._module_path)
            if not ret:
                break
        return ret

    def _build_source(self):
        log_start(" Building the source tarball")
        if self._module != 'meta':
            if not self._make_dist():
                log_end(False)
                return False
            os.rename(self._tarball_path, self._deb_orig_path)
            self._run(['tar', 'zxf', self._deb_orig_path, '-C', BUILD_DIR], False, self._svn_base)
            shutil.copytree(self._debian_path, '%s/debian'%self._deb_src_dir)
        else:
            shutil.copytree('%s/debian/%s'%(self._svn_base,self._package),
                             '%s/ulteo-ovd-%s'%(BUILD_DIR,self._version))
        log_end(True)

        # TODO: drop svn dirs using python
        os.system('rm -rf $(find %s -name .svn)'%self._deb_src_dir)

        # generate a changelog if we're not releasing
        if not self._do_release:
            cmd = ['dch', '--force-distribution',
                          '-D', self._distro_target,
                          '-v', self._deb_version,
                          'New devel snaphot']
            if not self._run(cmd, False, self._deb_src_dir):
                return False
        log_start(" Building the source package")
        if not self._run(['debuild', '-S', '-sa', '-us', '-uc'], True, self._deb_src_dir):
            log_end(False)
            return False
        log_end(True)

        return True

    def build_deb(self):
        self._log('Building %s for %s\n' % (self._deb_dsc_changes_name, self._schroot_target))
        if not self._build_source():
            self._sumup['srcbuild'] = False
            return False

        log_start(" Building the binary package")
        cmd = ['sbuild', '-n', '--force-orig-source',
                         '-A', '-s', '-d', self._schroot_target,
                         self._deb_dsc_changes_name]
        ret = self._run(cmd, cwd=BUILD_DIR)
        log_end(ret)
        if not ret:
            self._sumup['debbuild'] = False

        return ret

    def publish(self):
        log_start(" Publishing the package")
        if self._do_publish:
            ret = self._run(['dput', 'ovd-local', self._deb_binary_changes_file], cwd=BUILD_DIR)
            if ret:
                ret = self._run(['/home/gauvain/bin/update-ovd-repo.sh'], cwd=BUILD_DIR)

            if not ret:
                self._sumup['publish'] = False

            log_end(ret)

        else:
            target_dir = '%s/%s'%(RESULTS_DIR,self._schroot_target)
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir)
            for ext in ['gz','deb','udeb','dsc']:
                for f in glob.glob("%s/*.%s"%(BUILD_DIR, ext)):
                    shutil.copy(f, target_dir)

            log_end(True)

    def get_sumup(self):
        return (self._logfile, self._sumup)



if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                           'okrnb:',
                          ['stdout', 'keeplog', 'release', 'no-publish', 'branch'])
    except getopt.GetoptError, err:
        print >> sys.stderr, 'Error parsing the command line'
        sys.exit(1)

    # defaults
    release = False
    publish = True
    keeplog = False
    on_stdout = False
    branch = DEFAULT_BRANCH

    for o, a in opts:
        if o in ('-n', '--no-publish'):
            publish = False
        if o in ('-b', '--branch'):
            if branches.has_key(a):
                branch = a
            else:
                print 'Unknown branch: %s'%a
                sys.exit(1)
        if o in ('-r', '--release'):
            release = True
        if o in ('-k', '--keeplog'):
            keeplog = True
        if o in ('-o', '--stdout'):
            on_stdout = True

    if len(args) < 1:
        to_build = packages.keys()
    else:
        to_build = []
        for k in args:
            if packages.has_key(k):
                to_build.append(k)
            else:
                print 'Unknown module: %s\n'%k

    # check if the required modules are available, drop them if not
    if branch in ['2.0', 'trunk']:
        try:
            to_build.remove('meta')
        except:
            pass
    if branch in ['1.1']:
        try:
            to_build.remove('client/java')
        except:
            pass

    if len(to_build) == 0:
        print 'Nothing to build.'
        sys.exit(0)

    atexit.register(cleanup)

    while os.path.isfile(LOCK_FILE):
        print 'Build system locked; waiting...'
        time.sleep(5)
    open(LOCK_FILE, 'w').close()

    init()

    for module in to_build:
        shutil.rmtree(BUILD_DIR, True)
        os.makedirs(BUILD_DIR)

        print '\nBuild started for module %s (%s)' % (module, branch)
        deb = DebBuild(module,branch,release,publish,on_stdout)
        if deb.build_deb():
            deb.publish()

        sumup[module] = deb.get_sumup()

    text = '\n'
    for module in sumup.keys():
        failure = False
        for step in sumup[module][1].keys():
            if not sumup[module][1][step]:
                failure = step
        text += '%s => ' % module
        if failure:
            text += "FAILURE (%s), log in %s\n" % (step, sumup[module][0])
        else:
            text += "BUILT\n"
            if not keeplog:
                os.unlink(sumup[module][0])

    print text
