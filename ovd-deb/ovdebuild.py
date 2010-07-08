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
from xml.dom.minidom import parse

from ovdprefs import *
from ovdtools import run, save

class ovdebuild:

    # set all the variables we'll need
    def __init__(self, module, branch=DEFAULT_BRANCH, \
                 release=False, stable=False, on_stdout=False):

        self._module = module
        self._branch = branch
        self._on_stdout = on_stdout
        self._stable = stable
        self._release = release or self._stable

        self._svn_base = os.path.join(SVN_BASE_DIR, BRANCHES[self._branch][0])
        self._revno = "%05d" % \
            pysvn.Client().info(self._svn_base)["revision"].number

        self._dist_name = BRANCHES[self._branch][1]
        self._svn_folder = PACKAGES[self._branch][self._module][0]
        self._module_name = PACKAGES[self._branch][self._module][1]

        # prepare log system
        logfile_dir = '%s/%s' % (LOGS_DIR, self._dist_name)
        self._logfile = '%s/%s-%s_%s.txt'%\
            (logfile_dir, self._module_name, self._revno,  int(time.time()))
        if not os.path.isdir(logfile_dir):
            os.makedirs(logfile_dir)

        if self._svn_folder is not META:
            self._svn_dir = os.path.join(self._svn_base, self._svn_folder)

            # launch the autogen
            if os.path.exists(os.path.join(self._svn_dir, "autogen")):
                self._log(" Prepare the source (autogen):", True)
                self._run(['./autogen'], cwd=self._svn_dir)
                self._log_end()
        else:
            self._svn_dir = ''

        # find the good debian folder
        debdir = "%s/%s" % (self._svn_base, BRANCHES[self._branch][2])
        svn_deb_dirs = [debdir+'/debian',
             '%s/%s/debian' % (debdir, self._module_name),
             '%s/%s' % (debdir, self._module_name) ]
        for path in svn_deb_dirs:
            if os.path.exists(path):
                self._svn_deb_dir=path
                break

        self._repo_rev = self._get_repo_rev()
        self._base_version = self._get_base_version()
        if self._stable:
            self._version = self._get_changelog_version()
            self._upstream_version =  self._version.partition('-')[0]
            self._tarball_name = '%s_%s'%(self._module_name, self._upstream_version)
        else:
            self._upstream_version = self._base_version.replace('trunk', '')
            self._tarball_name = '%s_%s'%(self._module_name, self._upstream_version)
            if self._release:
                self._version = self._upstream_version+'-1'
            else:
                self._version = '%s-%d' % (self._upstream_version, \
                                max(self._repo_rev, self._get_local_rev()) + 1)

        self._src_name = '%s_%s'%(self._module_name, self._version)
        self._src_dir = os.path.join(BUILD_DIR, self._tarball_name)
        self._results_dir = os.path.join(RESULTS_DIR, self._dist_name)

        self._patches = []
        self._sumup = { 'tarball': True, 'srcbuild': True,\
                        'debbuild': True, 'publish': True }
        self._log(" Version release: %s\n"%self._version, True)

        if self._release:
            self._log(" Cleaning for new release:", True)

            # clean local results save
            for f in glob.glob("%s/%s/%s_%s*" % (RESULTS_DIR, \
                self._dist_name, self._module_name, self._upstream_version)):
                os.remove(f)

            # clean the source on the repository
            ret = True
            #TODO: remove stable when get_repo_revno will fix
            if self._repo_rev or self._stable:
                ret = self._run(['ovdreprepro', 'removesrc', self._dist_name, \
                                 self._module_name], ssh=True)
                self._repo_rev = 0
            if ret:
                self._log_end()
            else:
                self._log_end("cannot clean for new release", 'debbuild')

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
            print ' FAILED - '+msg
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

        if os.path.exists(os.path.join(self._svn_dir, "setup.py")):
            sys.path.append(self._svn_dir)
            imported = __import__('setup', fromlist=['setup_args'])
            sys.path.remove(self._svn_dir)
            return imported.setup_args['version']

        elif os.path.exists(os.path.join(self._svn_dir, "build.xml")):
                dom = parse(os.path.join(self._svn_dir, "build.xml"))
                for p in dom.getElementsByTagName('property'):
                    if p.getAttribute('name') == "version":
                        return p.getAttribute('value')

        elif  os.path.exists(os.path.join(self._svn_dir, "configure.ac.in")) or \
              os.path.exists(os.path.join(self._svn_dir, "configure.in.in")):
            major_re = re.compile(r'^m4_define.*_version_major.*\[([^\[]*)].*')
            minor_re = re.compile(r'^m4_define.*_version_minor.*\[([^\[]*)].*')
            build_re = re.compile(r'^m4_define.*_version_build.*\[([^\[]*)].*')
            config = glob.glob(self._svn_dir+"/configure.??.in")[0]
            lines = open(config).readlines()[:3]
            major = major_re.search(lines[0]).group(1)
            minor = minor_re.search(lines[1]).group(1)
            try:
                build = build_re.search(lines[2]).group(1)
            except AttributeError:
                build = ''
            version = '%s.%s%s'%(major, minor, build)
            return version.replace('@REVISION@', self._revno)

        elif self._svn_folder is META:
            fd = open(os.path.join(self._svn_deb_dir, "version"), 'r')
            version = fd.readline()
            fd.close()
            version = version[:len(version)-1]
            return version.replace('@REVISION@', self._revno)

        else:
            raise Exception("no way to find how get the base version")


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


    # TODO: improve when there is no revno
    def _get_repo_rev(self):
        cmd = "%s 'ovdreprepro list %s %s | grep %s'" \
               % (SSH_CMD, self._dist_name, self._module_name, self._revno)
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
        orig_result = os.path.join(RESULTS_DIR, self._dist_name, orig_name)

        def make_tarball(rename=None):
            self._log(" Building the source tarball:", True)
            cmd = PACKAGES[self._branch][self._module][2]
            if not self._run (cmd, cwd=self._svn_dir):
                return self._log_end("Cannot build the tarball", 'tarball')

            # move tarball in build directory
            tarball = '%s-%s.tar.gz'%(self._module_name, self._base_version)
            shutil.move(os.path.join(self._svn_dir, tarball), BUILD_DIR)
            if rename:
                os.rename(os.path.join(BUILD_DIR, tarball), rename)
                tarball = rename

            # save and extract tarball
            save(self._results_dir , tarball)
            self._run (['tar', 'zxf', os.path.join(BUILD_DIR, tarball), \
                        '-C', BUILD_DIR])
            return self._log_end()

        # metapackage: no need to make tarball
        if self._svn_folder is META:
            if not os.path.isfile(self._src_dir):
                os.mkdir(self._src_dir)

        # make tarball in default case
        elif (self._release):
            if not make_tarball(orig_name):
                return False

        # get the source on local disk
        elif os.path.exists(orig_result):
            self._log(" Getting the source tarball from disk:", True)
            shutil.copy(orig_result, BUILD_DIR)
            self._log_end()

        # get the source on repository
        elif self._repo_rev:
            self._log(" Getting the source tarball from repo:", True)
            self._run(['apt-get', 'source', '-d', '%s=%s-%d' % \
                      (self._module_name, self._upstream_version, self._repo_rev)])
            save(self._results_dir , ['gz', 'dsc'])
            self._log_end()

        # make tarball in default case
        elif not make_tarball(orig_name):
            return False

        # apply patches
        self._patches = glob.glob('%s/%s_%s_*.patch' % \
                            (PATCH_DIR, self._branch, self._module))
        if self._patches:
            self._log(" Apply %d patches:"%(len(self._patches)), True)
            series_path = os.path.join(PATCH_DIR, 'series')
            if os.path.exists(series_path):
                os.unlink(series_path)
            pc_path = os.path.join(self._svn_base, '.pc')
            if os.path.exists(pc_path):
                shutil.rmtree(pc_path, True)
            for patch in self._patches:
                self._run(['quilt', 'import', '-p0',\
                           'patches/'+patch.rpartition('/')[2]], cwd=BASE_DIR)
            if not self._run(['quilt', '--quiltrc', BASE_DIR+'/.quiltrc',\
                              'push', '-a'], cwd=self._svn_base):
                return self._log_end("Cannot apply patches", 'tarball')
            self._log_end()
            if not make_tarball():
                return False

        # copy the debian packaging files
        self._log("os.copytree(%s,%s)"%(self._svn_deb_dir, self._src_dir))
        shutil.copytree(self._svn_deb_dir, self._src_dir+'/debian')
        if os.path.exists(self._svn_dir+'/init'):
            init_path = glob.glob(self._svn_dir+'/init/*')[0]
            shutil.copyfile(init_path, "%s/debian/%s.init" % \
                (self._src_dir, init_path.rpartition('/')[2]) )

        return True


    def build_source(self):

        self._log(" Building the source package:", True)

        # remove .svn folders if there are
        os.system('rm -rf $(find %s -name .svn)'%self._src_dir)

        # generate a changelog
        if not self._stable:
            cmd = ['dch', '--force-distribution', '-v', self._version, '-b',\
                   '-D', self._dist_name.replace('.', '-'), 'New devel snaphot']
            if not self._run(cmd, cwd=self._src_dir):
                return self._log_end("Cannot generate a changelog", 'srcbuild')

        # choose if we want include orig sources or not
        if self._repo_rev:
            orig_opt = '-sd'
        else:
            orig_opt = '-sa'

        # launch dpkg-source
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

        save(self._results_dir , ['deb'])
        return self._log_end()


    def remove_patch(self):
        if self._patches:
            if not self._run(['quilt', '--quiltrc', BASE_DIR+'/.quiltrc',\
                              'pop', '-a'], cwd=self._svn_base):
                return self._log_end("Cannot remove patches", 'tarball')


    def publish(self):
        self._log(" Publishing all packages:", True)

        for f in glob.glob(BUILD_DIR + '/*.changes'):
            ret = self._run(['dput', 'firex', f])

        if ret:
            ret = self._run(['update-ovd-repo.sh'], ssh=True)
        if ret:
            self._run(['ovdreprepro', 'flood', \
                        self._dist_name], ssh=True)
            return self._log_end()

        return self._log_end("Cannot publish the package", 'publish')


    def get_sumup(self):
        return (self._logfile, self._sumup)
        os.chdir(BUILD_DIR)
