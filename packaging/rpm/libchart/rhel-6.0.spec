# Copyright (C) 2011 Ulteo SAS
# http://www.ulteo.com
# Author Samuel BOVEE <samuel@ulteo.com> 2011
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

Name: libchart
Version: 1.3
Release: 1

Summary: Simple PHP chart drawing library
License: GPL2
Group: Applications/web
Vendor: Ulteo SAS
Packager: Samuel Bovée <samuel@ulteo.com>
URL: http://www.ulteo.com
Distribution: RHEL 6.0

Source: %{name}-%{version}.tar.gz
Patch1: 01_no-image_1.3.diff
BuildArch: noarch

%description
Libchart is a free chart creation PHP library, that is easy to use.

###############################
%package -n php-libchart
###############################

Summary: Simple PHP chart drawing library
Group: Applications/web
Requires: php, php-gd

%description -n php-libchart
Libchart is a free chart creation PHP library, that is easy to use.

%prep -n php-libchart
%setup -q -n libchart
%patch1 -p1

%install -n php-libchart
PHPDIR=$RPM_BUILD_ROOT/usr/share/php
LIBCHARTDIR=$PHPDIR/libchart
mkdir -p $PHPDIR
cp -r libchart $PHPDIR
cp -r demo $LIBCHARTDIR

rmdir $LIBCHARTDIR/demo/generated
rm -rf $LIBCHARTDIR/images
rm $LIBCHARTDIR/COPYING $LIBCHARTDIR/ChangeLog $LIBCHARTDIR/README

%clean -n php-libchart
rm -rf $RPM_BUILD_ROOT

%files -n php-libchart
%defattr(-,root,root)
%doc libchart/COPYING
%doc libchart/ChangeLog
%doc libchart/README
/usr

%changelog -n php-libchart
* Wed Sep 20 2011 Samuel Bovée <samuel@ulteo.com> 1.3
- Initial release
