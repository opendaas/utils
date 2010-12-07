Name: libchart
Version: 1.2.2
Release: 1

Summary: Simple PHP chart drawing library
License: GPL2
Group: Applications/web
Vendor: Ulteo SAS
Packager: Samuel Bovée <samuel@ulteo.com>
URL: http://www.ulteo.com
Distribution: SLES 11 SP1

Source: %{name}-%{version}.tar.gz
Patch1: 01_no-image.diff
BuildArch: noarch
Buildroot: %{buildroot}

%description
Libchart is a free chart creation PHP library, that is easy to use.

###############################
%package -n php5-libchart
###############################

Summary: Simple PHP chart drawing library
Group: Applications/web
Requires: php5, php5-gd

%description -n php5-libchart
Libchart is a free chart creation PHP library, that is easy to use.

%prep -n php5-libchart
%setup -q -n libchart
%patch1 -p1

%install -n php5-libchart
PHPDIR=%{buildroot}/usr/share/php5
LIBCHARTDIR=$PHPDIR/libchart
mkdir -p $PHPDIR
cp -r libchart $PHPDIR
cp -r demo $LIBCHARTDIR

rmdir $LIBCHARTDIR/demo/generated
rm -rf $LIBCHARTDIR/images
rm $LIBCHARTDIR/COPYING $LIBCHARTDIR/ChangeLog $LIBCHARTDIR/README

%clean -n php5-libchart
rm -rf %{buildroot}

%files -n php5-libchart
%defattr(-,root,root)
%doc libchart/COPYING
%doc libchart/ChangeLog
%doc libchart/README
/usr

%changelog -n php5-libchart
* Thu Sep 03 2010 Samuel Bovée <samuel@ulteo.com> 1.2.1
- Initial release
