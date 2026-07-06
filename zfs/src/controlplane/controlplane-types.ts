/**
 * Lightweight TypeScript types for the cockpit-storage-encryption control plane.
 * These are the minimal interfaces cockpit-zfs needs — not the full controlplane.ts.
 */

/** KMS provider summary */
export interface ProviderSummary {
  id: string;
  name: string;
  type: string; // 'qxvault' | 'qxhsm' | 'mock'
  url: string;
  status?: string;
}

/** Key policy summary */
export interface PolicySummary {
  id: string;
  name: string;
  algorithm: string;
  transit_key_name: string;
  provider_id: string;
  rotation_interval_days: number | null;
}

/** Storage target as returned by the control plane */
export interface StorageTarget {
  id: string;
  type: string;
  identifier: string;
  display_name: string;
  hostname: string;
  governance_state: string;
  metadata_json: string | null;
  discovered_at: string;
  updated_at: string;
}

/** Parsed ZFS dataset metadata from storage target */
export interface ZfsTargetMetadata {
  datasetPath: string;
  encryption: string;
  keyFormat: string;
  keyLocation: string;
  keyStatus: string;
  encryptionRoot: string;
  pbkdf2Iters: string;
}

/** Policy binding summary */
export interface PolicyBinding {
  id: string;
  policy_id: string;
  policy_name: string;
  target_id: string;
  state: string; // 'pending' | 'active' | 'verified' | 'error' | 'unbound'
  encryption_state: string; // 'unknown' | 'not_encrypted' | 'applying' | 'encrypted' | 'migrating' | 'verified'
  dek_key_version: number | null;
  apply_method: string | null;
  bound_by: string;
  bound_at: string;
  last_verified: string | null;
}

/** FIPS status of the host */
export interface HostFipsStatus {
  fipsEnabled: boolean;
  fipsMode: string;
  kernelFips: boolean;
}

/** Encryption posture counts for dashboard display */
export interface EncryptionPosture {
  total: number;
  encrypted: number;
  policyAssigned: number;
  policyVerified: number;
  unmanaged: number;
  unencrypted: number;
}

/** Combined control plane data for a single ZFS dataset */
export interface DatasetControlPlaneInfo {
  target: StorageTarget;
  binding: PolicyBinding | null;
  policy: PolicySummary | null;
  metadata: ZfsTargetMetadata | null;
}

/** Result from a verify or sync action */
export interface ActionResult {
  success: boolean;
  message?: string;
  error?: string;
}

/** Binding sync result */
export interface BindingSyncResult {
  synced: number;
  driftDetected: number;
  errors: number;
}
