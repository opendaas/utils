# Copyright (C) 2011 Ulteo SAS
# http://www.ulteo.com
# Author Samuel BOVEE <samuel@ulteo.com> 2011
# Author Remi Collet <rpms@famillecollet.com> 2008
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

%define php_ver %((echo %{default_apiver}; php -i 2>/dev/null | sed -n 's/^PHP Version => //p') | tail -1)
%{!?php_extdir: %{expand: %%global php_extdir %(php-config --extension-dir)}}

%define pecl_name imagick
%define pecl_xmldir /usr/share/doc/packages/
# maybe not the good folder ! or remove it ?

Summary:       Extension to create and modify images using ImageMagick
Name:          php-imagick
Version:       3.0.1
Release:       1
License:       PHP
Group:         Development/Languages
Vendor:        Ulteo SAS
Packager:      Samuel Bovée <samuel@ulteo.com>
Distribution:  RHEL 6.0

Source:        http://pecl.php.net/get/%{pecl_name}-%{version}.tgz
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires: php-devel >= 5.1.3, php-pear, ImageMagick-devel >= 6.2.4

%if %{?php_zend_api}0
Requires:      php(zend-abi) = %{php_zend_api}
Requires:      php(api) = %{php_core_api}
%else
Requires:      php = %{php_ver}
%endif
Provides:      php-pecl(%{pecl_name}) = %{version}

%description
Imagick is a native php extension to create and modify images
using the ImageMagick API.

%prep
%setup -q -c
cd %{pecl_name}-%{version}

%build
cd %{pecl_name}-%{version}
%{_bindir}/phpize
%configure --with-imagick=%{prefix}
%{__make} %{?_smp_mflags}


%install
pushd %{pecl_name}-%{version}
%{__rm} -rf $RPM_BUILD_ROOT
%{__make} install INSTALL_ROOT=$RPM_BUILD_ROOT

# Drop in the bit of configuration
%{__mkdir_p} $RPM_BUILD_ROOT%{_sysconfdir}/php.d
%{__cat} > $RPM_BUILD_ROOT%{_sysconfdir}/php.d/%{pecl_name}.ini << 'EOF'
; Enable %{pecl_name} extension module
extension = %{pecl_name}.so

; Option not documented
imagick.locale_fix=0
EOF

popd
# Install XML package description
mkdir -p $RPM_BUILD_ROOT/%{pecl_xmldir}
install -pm 644 package.xml $RPM_BUILD_ROOT/%{pecl_xmldir}/%{name}.xml


%if 0%{?pecl_install:1}
%post
%{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :
%endif


%if 0%{?pecl_uninstall:1}
%postun
if [ $1 -eq 0 ] ; then
    %{pecl_uninstall} %{pecl_name} >/dev/null || :
fi
%endif


%clean
%{__rm} -rf $RPM_BUILD_ROOT


%files
%defattr(-, root, root, 0755)
%doc %{pecl_name}-%{version}/CREDITS %{pecl_name}-%{version}/TODO
%doc %{pecl_name}-%{version}/examples
%config(noreplace) %{_sysconfdir}/php.d/%{pecl_name}.ini
%{php_extdir}/%{pecl_name}.so
%{pecl_xmldir}/%{name}.xml
/usr/include/php/ext/imagick/*.h

%changelog
* Wed Sep 20 2011 Samuel Bovée <samuel@ulteo.com> 3.0.1-1
- Initial release
