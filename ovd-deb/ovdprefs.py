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

import os

DEFAULT_BRANCH = 'ovd30'

# { tagname : [ svn_repository, repo_target, file_base_version], debian_folder }
BRANCHES = {
    'ovd25' : ['ovd/branches/2.5', '2.5-staging', 'debian'],
    'ovd30'  : ['ovd/trunk',  'trunk', 'packaging/debian'],
    'xrdp'  : ['xrdp/trunk', 'trunk', ''],
    'vdi'   : ['vdi', 'trunk', 'packaging/debian'],
}

AUTOTOOLS_CMD = [['./autogen.sh'], ['make', 'distcheck']]
ANT_CMD = [['ant', 'dist']]
PYTHON_CMD = [['python', 'setup.py', 'sdist', '--dist-dir=.']]
META_CMD = []

ANY_ARCH = ['amd64', 'i386']
ALL_ARCH = ['all']
META = None

# { tagname : [self._src_folder, self._module_name, command, arch]}
PACKAGES = {

    'ovd25':{
        'java'    : ['client/java', 'ovd-applets', ANT_CMD, ALL_ARCH],
        'sm'      : ['SessionManager', 'ovd-session-manager', \
                     AUTOTOOLS_CMD, ALL_ARCH],
        'aps'     : ['ApplicationServer', 'ovd-application-server', \
                     AUTOTOOLS_CMD, ANY_ARCH],
        'chroot'  : ['chroot-apps', 'ovd-chroot-apps', AUTOTOOLS_CMD, ANY_ARCH],
    },

    'ovd30':{
        'sm'      : ['SessionManager', 'ovd-session-manager', \
                     AUTOTOOLS_CMD, ALL_ARCH],
        'web'     : ['WebInterface', 'ovd-webinterface', \
                     AUTOTOOLS_CMD, ALL_ARCH],
        'shell'   : ['ApplicationServer/OvdShells', 'ovd-shells', \
                     PYTHON_CMD, ALL_ARCH],
        'slave'   : ['OvdServer', 'ovd-slaveserver', PYTHON_CMD, ALL_ARCH],
        'java'    : ['client/java', 'ovd-java-clients', ANT_CMD, ALL_ARCH],
        'settings': ['ApplicationServer/desktop', 'ovd-desktop-settings', \
                     AUTOTOOLS_CMD, ANY_ARCH],
        'launcher': ['client/java/OVDIntegratedLauncher', \
                     'ovd-integrated-launcher', AUTOTOOLS_CMD, ANY_ARCH],
        'cups'    : ['utils/cups2all', 'cups2all', AUTOTOOLS_CMD, ALL_ARCH],
        'subsys'  : [META, 'ovd-subsystem', META_CMD, ALL_ARCH],
        'desktop' : [META, 'ovd-desktop', META_CMD, ALL_ARCH],
    },

    'xrdp':{
        'xrdp'    : ['', 'xrdp', [['make', 'distcheck']], ANY_ARCH],
    },

    'vdi':{
        'guest'   : ['host', 'vdi-guest', PYTHON_CMD, ALL_ARCH],
        'host'    : ['host', 'vdi-host',  PYTHON_CMD, ALL_ARCH],
    }
}

HOME = os.path.expanduser('~')
SVN_BASE_DIR = HOME+'/svn'
BASE_DIR     = HOME+'/ovd-deb'
BUILD_DIR    = HOME+'/ovd-deb/build'
LOCK_FILE    = BASE_DIR+'/.locked'
LOGS_DIR     = BASE_DIR+'/logs'
RESULTS_DIR  = BASE_DIR+'/results'
PATCH_DIR    = BASE_DIR+'/patches'
SPOOL_DIR    = "/var/spool/ovdeb"
CACHE_DIR    = "/var/cache/ovdeb"
SSH_CMD      = "ssh gauvain@firex.ulteo.com -p 222"
