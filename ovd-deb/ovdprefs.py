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

DEFAULT_BRANCH = 'ovd3'

# { tagname : [ svn_repository, repo_target, file_base_version], debian_folder }
BRANCHES = {
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
PACKAGES = {
    'ovd25':{
        'java'    : ['client/java', 'ovd-applets', ANT_CMD, ALL_ARCH],
        'sm'      : ['SessionManager', 'ovd-session-manager', AUTOTOOLS_CMD, ALL_ARCH],
        'aps'     : ['ApplicationServer', 'ovd-application-server', AUTOTOOLS_CMD, ANY_ARCH],
        'chroot'  : ['chroot-apps', 'ovd-chroot-apps', AUTOTOOLS_CMD, ANY_ARCH],
    },
    'ovd3':{
        'sm'      : ['SessionManager', 'ovd-session-manager', AUTOTOOLS_CMD, ALL_ARCH],
        'web'     : ['WebInterface', 'ovd-webinterface', AUTOTOOLS_CMD, ALL_ARCH],
        'chroot'  : ['chroot-apps', 'ovd-chroot-apps', AUTOTOOLS_CMD, ANY_ARCH],
        'shell'   : ['ApplicationServer/OvdShells', 'ovd-shells', PYTHON_CMD, ALL_ARCH],
        'slave'   : ['OvdServer', 'ovd-slaveserver', PYTHON_CMD, ALL_ARCH],
        'java'    : ['client/java', 'ovd-applets', ANT_CMD, ALL_ARCH],
        'settings': ['ApplicationServer/desktop', 'ovd-desktop-settings', AUTOTOOLS_CMD, ALL_ARCH],
        'desktop' : ['meta', 'ovd-desktop', '', ALL_ARCH],
    },
    'xrdp':{
        'xrdp'    : ['', 'xrdp', AUTOTOOLS_CMD, ANY_ARCH],
    }
}

BASE_DIR = '/home/samuel/ovd-deb'
LOCK_FILE = BASE_DIR+'/.locked'
LOGS_DIR = BASE_DIR+'/logs'
BUILD_DIR = BASE_DIR+'/build'
RESULTS_DIR = BASE_DIR+'/results'
PATCH_DIR = BASE_DIR+'/patches'
SVN_BASE_DIR = '/home/samuel/svn'
SSH_CMD = 'ssh gauvain@firex.ulteo.com -p 222'

