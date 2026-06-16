# KMS Encryption Setup Guide

## Overview

Cockpit ZFS integrates with the **cockpit-storage-encryption** control plane to provide KMS-backed (Key Management Service) encryption for ZFS datasets. Instead of using manually-entered passphrases, datasets can be encrypted with keys managed by a centralized key management system, enabling:

- **Automated key lifecycle management** — key generation, rotation, and revocation
- **Enterprise key governance** — policy-based encryption with audit trails
- **Hands-free unlock** — datasets can be unlocked automatically without user intervention
- **FIPS compliance** — when used with compliant KMS providers

**Key Concepts:**

| Term | Description |
|------|-------------|
| **KMS Provider** | External key management system (e.g., QXVault, QX HSM) |
| **Key Policy** | Defines encryption algorithm, key rotation interval, and which provider to use |
| **Storage Target** | A ZFS dataset that the control plane tracks |
| **Policy Binding** | Links a key policy to a storage target, establishing governance |
| **DEK** | Data Encryption Key — the raw key that encrypts the dataset |
| **Transit Key** | The KMS key that wraps/unwraps the DEK (envelope encryption) |

---

## Prerequisites

| Component | Requirement |
|-----------|-------------|
| Cockpit ZFS | v1.2.19 or later (with control plane integration) |
| cockpit-storage-encryption | Installed and configured on the same host |
| KMS Provider | A running instance with at least one key policy configured |
| ZFS | Must support native encryption (OpenZFS 0.8+) |

### Storage Encryption Setup

Before using KMS encryption in Cockpit ZFS, you must have the **cockpit-storage-encryption** module installed and configured with:

1. A registered KMS provider (e.g., QXVault)
2. At least one key policy

> **📖 See the [Storage Encryption Guide](https://github.com/45Drives/cockpit-storage-encryption/wiki) on the wiki for complete instructions on installing, configuring providers, and creating key policies.**

Once the Storage Encryption module is set up and you have at least one key policy available, proceed with the steps below to use KMS encryption in Cockpit ZFS.

---

## Step 1: Create an Encrypted Dataset with KMS

Once you have a provider and policy configured in the Storage Encryption module, you can create KMS-encrypted datasets directly from the Cockpit ZFS interface.

### Using the Pool Creation Wizard

1. Open **Cockpit ZFS** → navigate to the pool where you want to create a dataset
2. Click **Create File System** (or use the Pool Creation Wizard for new pools)
3. Enable **Encryption**
4. When the control plane is available, you'll see a **Key Source** selector:
   - **Passphrase** — traditional manual passphrase
   - **🔑 KMS Key Policy** — KMS-managed key
5. Select **KMS Key Policy**
6. Choose a policy from the dropdown (these are the policies configured in the Storage Encryption module)
7. Complete the remaining dataset properties and confirm

### What Happens Under the Hood

When you create a dataset with KMS encryption:

1. The control plane calls the KMS Transit engine to generate a new **Data Encryption Key (DEK)**
2. The plaintext DEK is used to create the ZFS dataset with `keylocation=file://`
3. The KMS wraps the DEK with the transit key (envelope encryption)
4. The wrapped DEK is stored in the control plane's binding record
5. The plaintext DEK is written to a tmpfs file and immediately zeroed after `zfs create`
6. A **policy binding** is created linking the policy to the new dataset target

The dataset is now encrypted with a key that only the KMS can unwrap.

---

## Step 2: Unlock KMS-Managed Datasets

When a KMS-encrypted dataset is locked (e.g., after a reboot), unlocking it does **not** require a passphrase.

### Manual Unlock via UI

1. Navigate to the dataset in Cockpit ZFS → File Systems list
2. Click the **Lock/Unlock** action
3. The UI detects the dataset is KMS-managed (based on `keylocation=file://` and an active binding)
4. Instead of a passphrase prompt, you'll see: _"This dataset is managed by KMS. The encryption key will be fetched from the key management system automatically."_
5. Optionally toggle **Mount File System** and **Forcefully Mount**
6. Click **Confirm**

### What Happens During Unlock

1. The control plane retrieves the wrapped DEK from its binding record
2. It calls the KMS Transit engine to **unwrap** the DEK
3. The plaintext DEK is written to a secure tmpfs file
4. `zfs load-key -L file:///path/to/tmpfs/key` is executed
5. The tmpfs key file is immediately deleted
6. The dataset is mounted (if requested)

### Automated Unlock on Boot

For datasets that should unlock automatically at boot, configure a systemd service that calls the control plane's fetch-and-load-key RPC for each KMS-managed dataset. The control plane handles all KMS communication.

---

---

## Troubleshooting

### Control Plane Not Detected

**Symptom:** The "KMS Key Policy" option doesn't appear in the encryption key source selector.

**Cause:** The `cockpit-storage-encryption` package is not installed, or the backend file is missing.

**Fix:**
```bash
# Verify the backend exists
ls /opt/45drives/controlplane/api_service.py

# If missing, install the package
sudo apt install cockpit-storage-encryption   # Debian/Ubuntu
sudo dnf install cockpit-storage-encryption   # RHEL/Rocky
```

### No Policies Available

**Symptom:** The policy dropdown is empty.

**Cause:** No key policies have been created in the Storage Encryption module, or the KMS provider is unreachable.

**Fix:** Refer to the [Storage Encryption Guide](https://github.com/45Drives/cockpit-storage-encryption/wiki) to configure providers and create key policies.

### KMS Unlock Fails

**Symptom:** "Failed to fetch KMS key" error when unlocking a dataset.

**Possible Causes:**
- KMS provider is offline or unreachable from this host
- The transit key has been deleted or rotated incompatibly
- The control plane token has expired
- Network firewall blocking the KMS URL

**Diagnosis:**
```bash
# Test connectivity to the KMS provider
curl -k https://vault.internal:8200/v1/sys/health

# Check control plane logs
journalctl -u cockpit.service | grep controlplane

# Verify the binding still exists
python3 /opt/45drives/controlplane/api_service.py <<< '{"method":"bindings.list","params":{}}'
```

### Dataset Shows as "Unmanaged"

**Symptom:** Dataset is encrypted but doesn't show a policy binding.

**Cause:** The dataset was encrypted with a passphrase (not KMS), or its binding was lost.

**Fix:** Use the Storage Encryption module to create a new binding for the dataset, or migrate it to KMS-managed encryption. See the [Storage Encryption Guide](https://github.com/45Drives/cockpit-storage-encryption/wiki).

---

## Security Considerations

1. **Transit Key Access**: The control plane token/credentials should have minimal permissions — only `transit/datakey` and `transit/decrypt` for the specific key.

2. **Tmpfs Key Storage**: Plaintext DEKs only exist momentarily on tmpfs during create/unlock operations and are immediately zeroed and deleted.

3. **Network Security**: Communication between the host and KMS provider should use TLS. Self-signed certificates are accepted by default but production deployments should use proper CA-signed certificates.

4. **Binding Integrity**: If a binding record is lost, the wrapped DEK is lost. Ensure the control plane's database is backed up.

5. **Key Rotation**: When a transit key is rotated in the KMS, existing wrapped DEKs can still be unwrapped (KMS maintains key versions). New wrap operations use the latest version.

---

## Summary

| Step | Action | Where |
|------|--------|-------|
| — | Install & configure `cockpit-storage-encryption` | [Storage Encryption Guide (wiki)](https://github.com/45Drives/cockpit-storage-encryption/wiki) |
| 1 | Create encrypted dataset with KMS policy | Cockpit ZFS → Pool Creation Wizard |
| 2 | Unlock datasets (auto KMS fetch) | Cockpit ZFS → File Systems → Lock/Unlock |
