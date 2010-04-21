#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Gauvain Pocentek <gpocentek@linutop.com>
# Modify by:
#        Laurent Clouet <laurent@ulteo.com> 2010
#        Samuel Bovée <samuel@ulteo.com> 2010
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
import pysvn

DEFAULT_BRANCH = 'ovd3'
# { tagname : [ svn_repository, repo_target, file_base_version], debian_folder }
branches = {
    'ovd25'  : ['ovd/branches/2.5', '2.5-staging', 'SessionManager/configure.in.in', 'debian'],
    'ovd3'  : ['ovd/trunk',  'trunk', 'SessionManager/configure.in.in', 'debian'],
    'xrdp'  : ['xrdp/trunk', 'trunk', 'configure.ac.in', ''],
}

AUTOTOOLS_CMD = [['./autogen.sh'], ['make', 'distcheck']]
ANT_CMD = [['./bootstrap'], ['ant', 'dist']]
PYTHON_CMD = [['./autogen.py'], ['python', 'setup.py', 'sdist', '--dist-dir=.']]

ANY_ARCH = ['amd64', 'i386']
ALL_ARCH = ['all']

# { tagname : [self._src_folder, self._module_name, command, arch]}
packages = {
    'ovd25':{
        'java'     : ['client/java', 'ovd-applets', ANT_CMD, ALL_ARCH],
        'sm'       : ['SessionManager', 'ovd-session-manager', AUTOTOOLS_CMD, ALL_ARCH],
        'aps'      : ['ApplicationServer', 'ovd-application-server', AUTOTOOLS_CMD, ANY_ARCH],
        'chroot'   : ['chroot-apps', 'ovd-chroot-apps', AUTOTOOLS_CMD, ANY_ARCH],
    },
    'ovd3':{
        'sm'       : ['SessionManager', 'ovd-session-manager', AUTOTOOLS_CMD, ALL_ARCH],
        'web'      : ['WebInterface', 'ovd-webinterface', AUTOTOOLS_CMD, ALL_ARCH],
        'chroot'   : ['chroot-apps', 'ovd-chroot-apps', AUTOTOOLS_CMD, ANY_ARCH],
        'shell'    : ['ApplicationServer/OvdShells', 'ovd-shells', PYTHON_CMD, ALL_ARCH],
        'slave'     : ['OvdServer', 'ovd-slaveserver', PYTHON_CMD, ALL_ARCH],
        'java'     : ['client/java', 'ovd-applets', ANT_CMD, ALL_ARCH],
        'settings' : ['ApplicationServer/desktop', 'ovd-desktop-settings', AUTOTOOLS_CMD, ALL_ARCH],
        'desktop'  : ['', 'ovd-desktop', '', ALL_ARCH],
    },
    'xrdp':{
        'xrdp'    : ['',            'xrdp',        AUTOTOOLS_CMD, ANY_ARCH],
    }
}

BASE_DIR = '/home/samuel/ovd-deb'
LOCK_FILE = BASE_DIR+'/.locked'
LOGS_DIR = BASE_DIR+'/logs'
BUILD_DIR = BASE_DIR+'/build'
RESULTS_DIR = BASE_DIR+'/results'
SVN_BASE_DIR = '/home/samuel/svn'
SSH_CMD = 'ssh gauvain@firex.ulteo.com -p 222'

sumup = {}

def svn_up(branch):
    print "Updating the svn tree:",
    sys.stdout.flush()
    cwd = "%s/%s"%(SVN_BASE_DIR, branches[branch][0])
    ret = run(['svn', 'up'], cwd=cwd)
    if ret: print "OK"
    else: print "FAILED"

def get_revno(svn_base):
    revno = pysvn.Client().info(svn_base)["revision"].number
    return "%05d"%revno

def get_repo_rev(branch, package, revno):
    repo = branches[branch][1]
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
        for f in glob.glob("%s/*.%s"%(BUILD_DIR, ext)):
            shutil.copy(f, folder)


class DebBuild:
    def __init__(self, module, branch=DEFAULT_BRANCH, release=False, on_stdout=False):

        # set all the variables we'll need
        self._module = module
        self._branch = branch
        self._do_release = release
        self._on_stdout = on_stdout

        self._svn_base = '%s/%s'%(SVN_BASE_DIR, branches[self._branch][0])
        self._revno = get_revno(self._svn_base)

        self._dist_name = branches[self._branch][1]
        self._src_folder = packages[self._branch][self._module][0]
        self._module_name = packages[self._branch][self._module][1]

        if branch != 'xrdp':
            debian_folder = self._module_name
        else:
            debian_folder = self._src_folder

        self._module_dir = '%s/%s'%(self._svn_base, self._src_folder)
        self._svn_deb_dir = '%s/%s/%s/debian'%(self._svn_base, \
            branches[self._branch][3], debian_folder)

        self._upstream_version = self._get_base_version()
        self._tarballname = '%s-%s'%(self._module_name, self._upstream_version)
        self._upstream_version = self._upstream_version.replace('trunk', '')
        self._tarball_name = '%s_%s'%(self._module_name, self._upstream_version)

        repo_rev = get_repo_rev(self._branch, self._module_name, self._revno)
        local_rev = get_local_rev(self._dist_name, self._tarball_name)
        self._deb_rev = max(repo_rev, local_rev) + 1
        self._version = '%s-%d' % (self._upstream_version, self._deb_rev)
        self._src_name = '%s_%s'%(self._module_name, self._version)
        self._src_dir = os.path.join(BUILD_DIR, self._tarballname)
        self._results_dir = os.path.join(RESULTS_DIR, self._dist_name)

        logfile_dir = '%s/%s' % (LOGS_DIR, self._dist_name)
        self._logfile = '%s/%s-%s_%s.txt'%\
            (logfile_dir, self._module_name, self._revno,  int(time.time()))
        if not os.path.isdir(logfile_dir):
            os.makedirs(logfile_dir)

        self._sumup = { 'tarball': True, 'srcbuild': True,\
                        'debbuild': True, 'publish': True }

        self._log(" Version release: %s\n"%self._version, True)

    def _log(self, msg, out=False):
        if out:
            print msg,
            sys.stdout.flush()
        elif self._on_stdout:
            print msg
            f = open(self._logfile, 'a')
            f.write(msg+'\n')
            f.close()

    def _log_end(self, msg=None, sumup=None):
        if msg is None:
            print 'OK'
            return True
        else:
            self._sumup[sumup] = False
            print 'FAILED - '+msg
            return False

    def _run(self, args, log=True, cwd=BUILD_DIR, ssh=False):
        if log:
            if not self._on_stdout:
                return run(args, self._logfile, cwd, ssh=ssh)
            else:
                return run(args, -1, cwd, ssh=ssh)
        else:
            return run(args, cwd=cwd)

    def _get_base_version(self):
        major_re = re.compile(r'^m4_define.*_version_major.*\[([^\[]*)].*')
        minor_re = re.compile(r'^m4_define.*_version_minor.*\[([^\[]*)].*')
        build_re = re.compile(r'^m4_define.*_version_build.*\[([^\[]*)].*')

        lines = open(os.path.join(self._svn_base, branches[self._branch][2]))\
                    .readlines()[:3]
        try:
            major = major_re.search(lines[0]).group(1)
            minor = minor_re.search(lines[1]).group(1)
            # the build field might be empty
            try:
                build = build_re.search(lines[2]).group(1).replace('@REVISION@', self._revno)
            except:
                build = ''
            version = '%s.%s%s'%(major, minor, build)
            return version
        except:
            return None

    def _get_changelog_version(self):
        changelog = '%s/changelog' % self._svn_deb_dir
        f = open(changelog)
        line = f.readline()
        f.close()
        r = re.compile(r'(?P<name>.*) \((?P<version>.*)\) (?P<target>.*); urgency=(?P<urgency>.*)')
        try:
            return r.search(line).group('version')
        except:
            return None


    def build_tarball(self):
        orig_path = '%s/%s.orig.tar.gz'%(BUILD_DIR, self._src_name)
        orig_results = glob.glob('%s/%s/%s-*.orig.tar.gz' % (RESULTS_DIR, \
                        self._dist_name, self._tarball_name))

        def prepare_src():
            if os.path.isfile(orig_path):
                self._run (['tar', 'zxf', orig_path, '-C', BUILD_DIR])
            else:
                if not os.path.isfile(self._src_dir):
                    os.mkdir(self._src_dir)
            self._log("os.copytree(%s,%s)"%(self._svn_deb_dir, self._src_dir))
            shutil.copytree(self._svn_deb_dir, self._src_dir+'/debian')

        def make_tarball():
            self._log(" Building the source tarball:", True)
            if self._src_folder is not '':
                for cmd in packages[self._branch][self._module][2]:
                    if not self._run (cmd, cwd=self._module_dir):
                        return self._log_end("Cannot build the tarball", 'tarball')
                # copy the tarball in BUILD_DIR
                tarball_path = os.path.join(self._module_dir, self._tarballname+'.tar.gz')
                self._log("os.rename(%s,%s)"%(tarball_path, orig_path))
                os.rename(tarball_path, orig_path)
                save(self._results_dir , ['orig.tar.gz'])
            prepare_src()

        # force to make a release
        if self._do_release:
            make_tarball()

        # get the source on local disk
        elif orig_results:
            self._log(" Getting the source tarball from disk:", True)
            deb_rev = max(orig_results).rpartition('-')[2].rpartition('.orig.tar.gz')[0]
            result_name = '%s-%s' % (self._tarball_name, deb_rev)
            result_files = glob.glob("%s/%s*" % (self._results_dir, result_name))
            for f in result_files:
                shutil.copy(f, BUILD_DIR)
            dsc_file = result_name+'.dsc'
            if os.path.isfile(dsc_file):
                self._run(['dpkg-source', '-x', dsc_file, self._src_dir])
            else:
                prepare_src()

        # get the source on repo if svn rev/repo are equal
        # TODO: improve this part
        elif False:
            self._log(" Getting the source tarball from repo:", True)
            if self._run(['apt-get', 'source', self._module_name]):
                save(self._results_dir , ['gz', 'dsc'])
            else:
                return self._log_end("The source tarball is not found", 'tarball')

        # make a release in any other cases
        else:
            make_tarball()

        return self._log_end()


    def build_source(self):

        self._log(" Building the source package:", True)

        os.system('rm -rf $(find %s -name .svn)'%self._src_dir)
        # TODO: apply a patch system HERE

        # generate a changelog
        cmd = ['dch', '--force-distribution', '-v', self._version,\
               '-D', self._dist_name.replace('.', '-'), 'New devel snaphot']
        if not self._run(cmd, cwd=self._src_dir):
            return self._log_end("Cannot generate a changelog", 'srcbuild')

        #if self._deb_rev <= 1:
        opt = "a"
        #else:
        #    opt = "d"

        cmd = ['dpkg-buildpackage', '-S', '-s'+opt, '-us', '-uc']
        if self._run(cmd, cwd=self._src_dir):
            # hack to fix the debuild bug
            os.chdir(self._src_dir)
            deb_changes_file = '%s/%s_source.changes'%(BUILD_DIR, self._src_name)
            os.system("dpkg-genchanges -S -s%s -DDistribution=%s > %s 2> /dev/null"%\
                       (opt, self._dist_name, deb_changes_file))
            save(self._results_dir , ['gz', 'dsc'])
        else:
            return self._log_end("Cannot building the source package", 'srcbuild')

        return self._log_end()


    def build_deb(self, arch):

        if not os.path.exists(self._src_dir):
            if not self.build_tarball():
                return self._log_end("Cannot get the orig source", 'debbuild')

        src_changes_file = '%s/%s_source.changes'%(BUILD_DIR, self._src_name)
        if not os.path.exists(src_changes_file):
            if not self.build_source():
                return self._log_end("Cannot build the source", 'debbuild')

        self._log(" Building the %s packages:"%arch, True)

        dsc_file = '%s/%s.dsc'%(BUILD_DIR, self._src_name)
        cmd = ['sbuild', '-n', '-A', '-c', 'hardy-'+arch,\
               '-d', self._dist_name, dsc_file]
        if glob.glob(BUILD_DIR + "/*_all.deb") != [] and arch != "all" :
            cmd.remove('-A')
        if not self._run(cmd):
            return self._log_end("sbuild cannot make the package", 'debbuild')

        save(self._results_dir , ['deb'])
        return self._log_end()


    def publish(self):
        self._log(" Publishing all packages:", True)

        for f in glob.glob(BUILD_DIR + '/*.changes'):
            ret = self._run(['dput', 'firex', f])

        if ret:
            ret = self._run(['/home/gauvain/bin/update-ovd-repo.sh'], ssh=True)
        if ret:
            self._run(['/home/gauvain/bin/ovdreprepro', 'flood', \
                        self._dist_name], ssh=True)
            self._run(['/home/gauvain/bin/ovd-needs-building'], ssh=True)
            return self._log_end()

        return self._log_end("Cannot publish the package", 'publish')


    def get_sumup(self):
        return (self._logfile, self._sumup)


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                           'okrpb:',
                          ['stdout', 'keeplog', 'release', 'publish', 'branch'])
    except getopt.GetoptError, err:
        print >> sys.stderr, 'Error parsing the command line'
        sys.exit(1)

    # defaults options
    release, publish, keeplog, on_stdout = False, False, False, False
    branch = DEFAULT_BRANCH

    for o, a in opts:
        if o in ('-p', '--publish'):
            publish = True
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
        to_build = packages[branch].keys()
    else:
        to_build = []
        for k in args:
            if packages[branch].has_key(k):
                to_build.append(k)
            else:
                print 'Unknown module: %s\n'%k
    if on_stdout:
        print to_build

    if len(to_build) == 0:
        print 'Nothing to build.'
        sys.exit(0)

    atexit.register(cleanup)

    while os.path.isfile(LOCK_FILE):
        print 'Build system locked; waiting...'
        time.sleep(5)
    open(LOCK_FILE, 'w').close()

    svn_up(branch)

    for module in to_build:
        shutil.rmtree(BUILD_DIR, True)
        os.makedirs(BUILD_DIR)
        os.chdir(BUILD_DIR)

        print '\nBuild started for module %s (%s)' %\
            (packages[branch][module][1], branches[branch][0])

        deb = DebBuild(module, branch, release, on_stdout)
        for arch in packages[branch][module][3]:
            deb.build_deb(arch)
        if publish:
            deb.publish()
        sumup[module] = deb.get_sumup()

    if publish:
        print '\n[Updating the OVD package list website]'
        run(['/home/gauvain/bin/ovdweb.sh'], ssh=True)

    text = '\n'
    for module in sumup.keys():
        failure = False
        for step in sumup[module][1].keys():
            if not sumup[module][1][step]:
                failure = step
                break
        text += '%s => ' % module
        if failure:
            text += "FAILURE (%s), log in %s\n" % (step, sumup[module][0])
        else:
            text += "BUILT\n"
            if keeplog:
                text += ", log in %s\n" % sumup[module][0]
            else:
                os.unlink(sumup[module][0])
    print text
