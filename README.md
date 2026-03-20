# Cockpit ZFS Manager

A ZFS storage management module for [Cockpit](https://cockpit-project.org/). Manage ZFS pools, file systems, snapshots, and disks through an intuitive web interface.

> **Note:** This project replaces the older [cockpit-zfs-manager](https://github.com/45Drives/cockpit-zfs-manager), which is no longer maintained. If you are currently using `cockpit-zfs-manager`, uninstall it before installing this module.

## Prerequisites

- A Linux system with **ZFS** installed and running (`zfsutils-linux` or equivalent)
- **Cockpit** web console installed and running
- **Python 3**
- **python3-libzfs** (the Python bindings for libzfs — see [Building python3-libzfs](#building-python3-libzfs))

> The module includes CLI-based fallbacks for environments where `python3-libzfs` cannot be installed. Core functionality (pools, VDev info, scrub/resilver status) will still work via `zpool` commands, but the full libzfs bindings are recommended for the best experience.

## Installation from Package (Recommended)

See the [releases page](https://github.com/45Drives/cockpit-zfs/releases) for pre-built packages for supported distributions.

## Building from Source

### System Requirements

| Requirement | Purpose |
|---|---|
| Node.js (>= 18) | Build the frontend |
| Yarn | JavaScript package manager |
| jq | JSON processing (used by Makefile) |
| moreutils (sponge) | Used by bootstrap script |
| make | Build automation |
| git | Clone repos & submodules |

### Build Steps

```bash
# Clone the repository (with submodules)
git clone --recurse-submodules https://github.com/45Drives/cockpit-zfs.git
cd cockpit-zfs

# Build the plugin
make

# Install system-wide (requires root)
sudo make install

# Restart cockpit to load the new module
sudo systemctl restart cockpit.socket
```

The module will be installed to `/usr/share/cockpit/zfs/`.

### Local Install (for development/testing)

```bash
make install-local
```

This installs to `~/.local/share/cockpit/zfs-test/` and does not require root.

---

## Building python3-libzfs

`python3-libzfs` provides the Python bindings for libzfs needed by the backend scripts. If pre-built packages are not available for your distribution, build from source:

### Ubuntu / Debian

```bash
# Install build dependencies
sudo apt install -y build-essential autoconf python3-dev libzfslinux-dev python3-setuptools python3-pip
pip3 install Cython==0.29.35

# Clone and build
git clone https://github.com/45Drives/python3-libzfs.git
cd python3-libzfs
./configure --prefix=/usr
make
sudo make install
```

### Rocky Linux / RHEL

```bash
# Install build dependencies
sudo dnf install -y gcc make autoconf python3-devel libzfs5-devel python3-setuptools python3-pip
pip3 install Cython==0.29.35

# Clone and build
git clone https://github.com/45Drives/python3-libzfs.git
cd python3-libzfs
./configure --prefix=/usr
make
sudo make install
```

### Troubleshooting python3-libzfs Build

| Error | Solution |
|---|---|
| `configure: error: A working zfs header is required` | Install ZFS development headers: `sudo apt install libzfslinux-dev` (Debian/Ubuntu) or `sudo dnf install libzfs5-devel` (RHEL/Rocky) |
| `ImportError: cannot import name 'setup' from 'setuptools'` | Install/upgrade setuptools: `pip3 install --upgrade setuptools` |
| `ModuleNotFoundError: No module named 'Cython'` | Install Cython: `pip3 install Cython==0.29.35` |

### Verifying the Installation

After installing `python3-libzfs`, verify it works:

```bash
python3 -c "import libzfs; print('libzfs OK')"
```

## Runtime Dependencies

The following packages should be installed on the target system:

- `cockpit`
- `python3`
- `python3-libzfs` (see above)
- `python3-dateutil`
- `sqlite3` (or `sqlite` on RHEL/Rocky)
- `jq`
- `msmtp` (for email notifications)

## Development

```bash
# Start the Vite dev server for hot-reload development
cd zfs
yarn dev
```

## License

GPL-3.0+