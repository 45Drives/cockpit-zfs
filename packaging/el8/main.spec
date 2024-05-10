Name: ::package_name::
Version: ::package_version::
Release: ::package_build_version::%{?dist}
Summary: ::package_description_short::
License: ::package_licence::
URL: ::package_url::
Source0: %{name}-%{version}.tar.gz
BuildArch: ::package_architecture_el::
Requires: ::package_dependencies_el_el8::

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
::package_title::
::package_description_long::

%prep
%setup -q

%build
make OS_PACKAGE_RELEASE=el8

%install
make DESTDIR=%{buildroot} install

%files
/usr/share/cockpit/zfs/*

%changelog
* Fri May 10 2024 Jordan Keough <jkeough@45drives.com> 0.1.0-10-1
- Fixed major bug with missing disks causing pools to break
* Mon Mar 11 2024 Jordan Keough <jkeough@45drives.com> 0.1.0-7
- wip bug fixing for root_dataset property
* Mon Mar 11 2024 Jordan Keough <jkeough@45drives.com> 0.1.0-6
- wip bug fixing for root_dataset property
* Mon Mar 11 2024 Jordan Keough <jkeough@45drives.com> 0.1.0-5
- wip bug fixing for root_dataset property
* Mon Mar 11 2024 Jordan Keough <jkeough@45drives.com> 0.1.0-4
- wip bug fix for root_dataset property again
* Mon Mar 11 2024 Jordan Keough <jkeough@45drives.com> 0.1.0-3
- wip bug fix for root_dataset property
* Mon Mar 11 2024 Jordan Keough <jkeough@45drives.com> 0.1.0-2
- bug fix for scan property
* Fri Mar 08 2024 Jordan Keough <jkeough@45drives.com> 0.1.0-1
- initial release