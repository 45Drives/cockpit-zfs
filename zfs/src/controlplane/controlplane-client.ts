/**
 * Control Plane IPC Bridge for cockpit-zfs.
 *
 * Communicates with cockpit-storage-encryption's api_service.py backend via
 * cockpit.spawn() + JSON-RPC on stdin. All functions gracefully return null/empty
 * when the control plane is not installed.
 */
import type {
  ProviderSummary,
  PolicySummary,
  StorageTarget,
  PolicyBinding,
  HostFipsStatus,
  ZfsTargetMetadata,
  ActionResult,
  BindingSyncResult,
} from './controlplane-types';

const API_SERVICE_PATH = '/opt/45drives/controlplane/api_service.py';

/** Cached availability — null means not yet checked */
let _availabilityCache: boolean | null = null;

// ─── Low-level transport ────────────────────────────────────────────────────

/**
 * Call the control plane backend via JSON-RPC over cockpit.spawn stdin.
 * Throws on transport or application errors.
 */
async function rpc<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
  const proc = cockpit.spawn(
    ['python3', API_SERVICE_PATH],
    { superuser: 'try', err: 'message' }
  );
  proc.input(JSON.stringify({ method, params }));
  const stdout = await proc;
  const response = JSON.parse(stdout);
  if (response.error) {
    const msg = typeof response.error === 'string'
      ? response.error
      : response.error.message ?? JSON.stringify(response.error);
    throw new Error(msg);
  }
  return response.result as T;
}

// ─── Availability ───────────────────────────────────────────────────────────

/**
 * Check whether the cockpit-storage-encryption control plane is installed.
 * Result is cached for the session.
 */
export async function isControlPlaneAvailable(): Promise<boolean> {
  if (_availabilityCache !== null) return _availabilityCache;
  try {
    const handle = cockpit.file(API_SERVICE_PATH, { superuser: 'try' });
    const content = await handle.read();
    handle.close();
    _availabilityCache = content != null && content.length > 0;
  } catch {
    _availabilityCache = false;
  }
  return _availabilityCache;
}

/** Reset the cached availability (e.g. after install/removal) */
export function resetAvailabilityCache(): void {
  _availabilityCache = null;
}

/**
 * Guard wrapper — returns null if control plane is unavailable, otherwise calls fn.
 */
async function guarded<T>(fn: () => Promise<T>): Promise<T | null> {
  const available = await isControlPlaneAvailable();
  if (!available) return null;
  return fn();
}

// ─── Provider queries ───────────────────────────────────────────────────────

export async function listProviders(): Promise<ProviderSummary[] | null> {
  return guarded(() => rpc<ProviderSummary[]>('providers.list'));
}

// ─── Policy queries ─────────────────────────────────────────────────────────

export async function listPolicies(): Promise<PolicySummary[] | null> {
  return guarded(() => rpc<PolicySummary[]>('policies.list'));
}

// ─── Target queries ─────────────────────────────────────────────────────────

export async function listZfsTargets(): Promise<StorageTarget[] | null> {
  return guarded(async () => {
    const raw = await rpc<any>('targets.list');
    const all: StorageTarget[] = Array.isArray(raw) ? raw : (raw?.items ?? []);
    return all.filter(t => t.type === 'zfs_dataset');
  });
}

export async function getTarget(targetId: string): Promise<StorageTarget | null> {
  return guarded(() => rpc<StorageTarget>('targets.get', { targetId }));
}

/** Look up a control plane target by ZFS dataset name (e.g. "tank/mydata") */
export async function getTargetByDatasetName(datasetName: string): Promise<StorageTarget | null> {
  const targets = await listZfsTargets();
  if (!targets) return null;
  return targets.find(t => t.identifier === datasetName) ?? null;
}

// ─── Binding queries ────────────────────────────────────────────────────────

export async function listBindings(): Promise<PolicyBinding[] | null> {
  return guarded(() => rpc<PolicyBinding[]>('bindings.list'));
}

/** Get the active binding for a specific target */
export async function getBindingForTarget(targetId: string): Promise<PolicyBinding | null> {
  const bindings = await listBindings();
  if (!bindings) return null;
  return bindings.find(
    b => b.target_id === targetId && b.state !== 'unbound'
  ) ?? null;
}

// ─── FIPS status ────────────────────────────────────────────────────────────

export async function getHostFipsStatus(): Promise<HostFipsStatus | null> {
  return guarded(() => rpc<HostFipsStatus>('host.fipsStatus'));
}

// ─── ZFS dataset creation with KMS key ──────────────────────────────────────

export interface KmsCreateResult {
  success: boolean;
  targetId: string;
  bindingId: string;
  dataset: string;
  message: string;
}

/**
 * Create an encrypted ZFS dataset using a KMS-backed key from the control plane.
 * The backend generates a DEK via Transit, creates the dataset, and auto-binds it.
 */
export async function createEncryptedDatasetWithKms(
  pool: string,
  name: string,
  policyId: string,
  properties?: Record<string, string>,
): Promise<KmsCreateResult | null> {
  return guarded(() =>
    rpc<KmsCreateResult>('zfs.createEncrypted', { pool, name, policyId, properties })
  );
}

// ─── Lightweight write actions ──────────────────────────────────────────────

/** Verify a binding (KMS round-trip check) */
export async function verifyBinding(bindingId: string): Promise<ActionResult | null> {
  return guarded(() => rpc<ActionResult>('bindings.verify', { id: bindingId }));
}

/** Sync binding state from actual storage encryption status */
export async function syncBinding(bindingId: string): Promise<BindingSyncResult | null> {
  return guarded(() => rpc<BindingSyncResult>('bindings.sync', { id: bindingId }));
}

// ─── KMS key fetch (unlock support) ─────────────────────────────────────────

export interface KmsKeyFetchResult {
  success: boolean;
  dataset: string;
  keyPath: string;
  message: string;
}

/**
 * Fetch the wrapped DEK from the control plane, unwrap via Transit, write to
 * tmpfs, and call `zfs load-key`. Used by the lock/unlock flow when a dataset
 * has keylocation=file:// (KMS-managed key).
 */
export async function fetchAndLoadKey(datasetName: string): Promise<KmsKeyFetchResult | null> {
  return guarded(() =>
    rpc<KmsKeyFetchResult>('zfs.fetchAndLoadKey', { datasetArg: datasetName })
  );
}

// ─── Metadata helpers ───────────────────────────────────────────────────────

/** Parse metadata_json from a StorageTarget into typed ZFS metadata */
export function parseZfsMetadata(target: StorageTarget): ZfsTargetMetadata | null {
  if (!target.metadata_json) return null;
  try {
    const raw = typeof target.metadata_json === 'string'
      ? JSON.parse(target.metadata_json)
      : target.metadata_json;
    return raw as ZfsTargetMetadata;
  } catch {
    return null;
  }
}

// ─── Deep-link helpers ──────────────────────────────────────────────────────

const ENCRYPTION_MODULE_PATH = '/storage-encryption-test';

/** Build a deep-link URL to the cockpit-storage-encryption module */
export function encryptionManagerUrl(targetId?: string, action?: string): string {
  let url = `/cockpit/@localhost${ENCRYPTION_MODULE_PATH}/index.html`;
  const params: string[] = [];
  if (targetId) params.push(`target=${encodeURIComponent(targetId)}`);
  if (action) params.push(`action=${encodeURIComponent(action)}`);
  if (params.length > 0) url += '#' + params.join('&');
  return url;
}

/** Navigate to the encryption manager within the Cockpit shell */
export function navigateToEncryptionManager(targetId?: string, action?: string): void {
  const url = encryptionManagerUrl(targetId, action);
  // Cockpit modules run in iframes; navigate the top-level shell
  if (window.top) {
    window.top.location.href = url;
  } else {
    window.location.href = url;
  }
}
