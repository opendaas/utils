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
import glob, time, shutil, pysvn

from ovdprefs import *
from ovdtools import run, save

class ovdebuild:

    # set all the variables we'll need
    def __init__(self, module, branch=DEFAULT_BRANCH, on_stdout=False):

        self._module = module
        self._branch = branch
        self._on_stdout = on_stdout

        self._svn_base = os.path.join(SVN_BASE_DIR, BRANCHES[self._branch][0])
        self._revno = "%05d" % \
            pysvn.Client().info(self._svn_base)["revision"].number

        self._dist_name = BRANCHES[self._branch][1]
        self._src_folder = PACKAGES[self._branch][self._module][0]
        self._module_name = PACKAGES[self._branch][self._module][1]

        if branch != 'xrdp':
            debian_folder = self._module_name
        else:
            debian_folder = self._src_folder

        self._module_dir = '%s/%s'%(self._svn_base, self._src_folder)
        self._svn_deb_dir = '%s/%s/%s/debian'%(self._svn_base, \
            BRANCHES[self._branch][3], debian_folder)

        self._upstream_version = self._get_base_version()
        self._tarballname = '%s-%s'%(self._module_name, self._upstream_version)
        self._upstream_version = self._upstream_version.replace('trunk', '')
        self._tarball_name = '%s_%s'%(self._module_name, self._upstream_version)

        self._repo_rev = self._get_repo_rev()
        local_rev = self._get_local_rev()
        self._version = '%s-%d' % (self._upstream_version, \
                                   max(self._repo_rev, local_rev) + 1)
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

        lines = open(os.path.join(self._svn_base, BRANCHES[self._branch][2]))\
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


    def _get_repo_rev(self):
        repo = BRANCHES[self._branch][1]
        package = self._module_name
        if repo.find('ovd') is not -1:
            package = "ulteo-" + package
        cmd = "%s '/home/gauvain/bin/ovdreprepro list %s %s | grep %s'" \
               % (SSH_CMD, repo, package, self._revno)
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


    def _get_local_rev(self):
        rev = 0
        for f in glob.glob("%s/%s/%s-*.dsc" % \
            (RESULTS_DIR, self._dist_name, self._tarball_name)):
            rev = max (rev, int(f.rpartition('-')[2].rpartition('.dsc')[0]))
        return rev


    def build_tarball(self):
        orig_name = self._tarball_name+'.orig.tar.gz'
        tarball_name = self._tarballname+'.tar.gz'
        orig_result = os.path.join(RESULTS_DIR, self._dist_name, orig_name)
        orig_path = None
        tarball_path = None

        def make_tarball(name=None):
            if self._src_folder is 'meta':
                return
            for cmd in PACKAGES[self._branch][self._module][2]:
                if not self._run (cmd, cwd=self._module_dir):
                    return self._log_end("Cannot build the tarball", 'tarball')
            shutil.move(os.path.join(self._module_dir, tarball_name), BUILD_DIR)
            if name:
                path = os.path.join(BUILD_DIR, tarball_name)
                self._log("os.rename(%s, %s)"%(path, name))
                os.rename(path, name)
                save(self._results_dir , name)
                return path
            else:
                save(self._results_dir , tarball_name)
                return os.path.join(BUILD_DIR, tarball_name)

        # get the source on local disk
        if os.path.exists(orig_result):
            self._log(" Getting the source tarball from disk:", True)
            shutil.copy(orig_result, BUILD_DIR)

        # get the source on repository
        elif self._repo_rev is not 0:
            self._log(" Getting the source tarball from repo:", True)
            self._run(['apt-get', 'source', '-d', '%s=%s' % \
                      (self._module_name, self._upstream_version)])
            save(self._results_dir , ['gz', 'dsc'])

        # make the tarball
        else:
            self._log(" Building the source tarball:", True)
            orig_path = make_tarball(orig_name)

        self._log_end()

        # apply patches
        self._patches = glob.glob('%s/%s_%s_*' % (PATCH_DIR, self._branch, self._module))
        series_path = os.path.join(PATCH_DIR, 'series')
        pc_path = os.path.join(self._svn_base, '.pc')
        if os.path.exists(series_path):
            os.unlink(series_path)
        if os.path.exists(pc_path):
            shutil.rmtree(pc_path, True)
        if self._patches:
            self._log(" Apply %d patches:"%(len(self._patches)), True)
            for patch in self._patches:
                self._run(['quilt', 'import', '-p0',\
                           'patches/'+patch.rpartition('/')[2]], cwd=BASE_DIR)
            if not self._run(['quilt', '--quiltrc', BASE_DIR+'/.quiltrc',\
                              'push', '-a'], cwd=self._svn_base):
                return self._log_end("Cannot apply patches", 'tarball')
            tarball_path = make_tarball()
            self._log_end()

        # extract sources
        if tarball_path is not None and os.path.isfile(tarball_path):
            self._run (['tar', 'zxf', tarball_path, '-C', BUILD_DIR])
        elif orig_path is not None and os.path.isfile(orig_path):
            self._run (['tar', 'zxf', orig_path, '-C', BUILD_DIR])
        else:
            if not os.path.isfile(self._src_dir):
                os.mkdir(self._src_dir)

        # copy the debian packaging files
        self._log("os.copytree(%s,%s)"%(self._svn_deb_dir, self._src_dir))
        shutil.copytree(self._svn_deb_dir, self._src_dir+'/debian')

        return True


    def build_source(self):

        self._log(" Building the source package:", True)

        os.system('rm -rf $(find %s -name .svn)'%self._src_dir)

        # generate a changelog
        cmd = ['dch', '--force-distribution', '-v', self._version,\
               '-D', self._dist_name.replace('.', '-'), 'New devel snaphot']
        if not self._run(cmd, cwd=self._src_dir):
            return self._log_end("Cannot generate a changelog", 'srcbuild')

        if self._repo_rev is 0:
            orig_opt = '-sa'
        else:
            orig_opt = '-sd'

        cmd = ['dpkg-buildpackage', '-S', '-us', '-uc', orig_opt]
        if self._run(cmd, cwd=self._src_dir):
            # hack to fix the debuild bug
            os.chdir(self._src_dir)
            deb_changes_file = '%s/%s_source.changes'%(BUILD_DIR, self._src_name)
            os.system("dpkg-genchanges -S %s -DDistribution=%s > %s 2> /dev/null" %\
                       (orig_opt, self._dist_name, deb_changes_file))
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

        # remove patches
        if self._patches:
            if not self._run(['quilt', '--quiltrc', BASE_DIR+'/.quiltrc',\
                              'pop', '-a'], cwd=self._svn_base):
                return self._log_end("Cannot remove patches", 'tarball')

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
        os.chdir(BUILD_DIR)
