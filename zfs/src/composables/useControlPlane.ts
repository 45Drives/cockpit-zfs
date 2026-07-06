/**
 * Vue composable for accessing the cockpit-storage-encryption control plane.
 *
 * Provides reactive state for control plane availability, ZFS targets,
 * policy bindings, and provider info. Integrates with cockpit-zfs's
 * provide/inject data flow.
 *
 * Usage in ZFS.vue:
 *   const cp = useControlPlane();
 *   provide('controlplane', cp);
 *
 * Usage in child components:
 *   const cp = inject<ControlPlaneState>('controlplane')!;
 *   if (cp.available.value) { ... }
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue';
import {
  isControlPlaneAvailable,
  listZfsTargets,
  listBindings,
  listProviders,
  listPolicies,
  getHostFipsStatus,
  verifyBinding as verifyBindingRpc,
  syncBinding as syncBindingRpc,
  fetchAndLoadKey as fetchAndLoadKeyRpc,
  parseZfsMetadata,
  encryptionManagerUrl,
  createEncryptedDatasetWithKms as createWithKmsRpc,
} from '../controlplane/controlplane-client';
import type {
  StorageTarget,
  PolicyBinding,
  PolicySummary,
  ProviderSummary,
  HostFipsStatus,
  EncryptionPosture,
  DatasetControlPlaneInfo,
  ActionResult,
  BindingSyncResult,
} from '../controlplane/controlplane-types';
import type { KmsCreateResult, KmsKeyFetchResult } from '../controlplane/controlplane-client';

export interface ControlPlaneState {
  /** Whether the control plane backend is installed on this host */
  available: Ref<boolean>;
  /** True while initial data is loading */
  loading: Ref<boolean>;
  /** Error message from the last load attempt, or empty string */
  error: Ref<string>;

  /** All ZFS dataset targets known to the control plane */
  targets: Ref<StorageTarget[]>;
  /** All policy bindings */
  bindings: Ref<PolicyBinding[]>;
  /** All key policies */
  policies: Ref<PolicySummary[]>;
  /** KMS providers */
  providers: Ref<ProviderSummary[]>;
  /** Host FIPS status */
  fipsStatus: Ref<HostFipsStatus | null>;

  /** Encryption posture summary */
  posture: ComputedRef<EncryptionPosture>;

  /** Lookup: get control plane info for a dataset by its ZFS name */
  getInfoForDataset: (datasetName: string) => DatasetControlPlaneInfo | null;

  /** Refresh all control plane data */
  refresh: () => Promise<void>;

  /** Verify a binding (KMS round-trip) */
  verifyBinding: (bindingId: string) => Promise<ActionResult | null>;
  /** Sync a binding's state */
  syncBinding: (bindingId: string) => Promise<BindingSyncResult | null>;

  /** Generate a deep-link URL to the encryption manager */
  encryptionManagerUrl: (targetId?: string, action?: string) => string;

  /** Create an encrypted dataset using a KMS-backed key */
  createEncryptedDatasetWithKms: (
    pool: string, name: string, policyId: string, properties?: Record<string, string>
  ) => Promise<KmsCreateResult | null>;

  /** Fetch & load a KMS-managed key for a locked dataset (replaces passphrase unlock) */
  fetchAndLoadKey: (datasetName: string) => Promise<KmsKeyFetchResult | null>;
}

export function useControlPlane(): ControlPlaneState {
  const available = ref(false);
  const loading = ref(false);
  const error = ref('');

  const targets = ref<StorageTarget[]>([]);
  const bindings = ref<PolicyBinding[]>([]);
  const policies = ref<PolicySummary[]>([]);
  const providers = ref<ProviderSummary[]>([]);
  const fipsStatus = ref<HostFipsStatus | null>(null);

  // Build lookup maps for fast access
  const targetsByName = computed(() => {
    const map = new Map<string, StorageTarget>();
    for (const t of targets.value) {
      map.set(t.identifier, t);
    }
    return map;
  });

  const bindingsByTarget = computed(() => {
    const map = new Map<string, PolicyBinding>();
    for (const b of bindings.value) {
      if (b.state !== 'unbound') {
        map.set(b.target_id, b);
      }
    }
    return map;
  });

  const policiesById = computed(() => {
    const map = new Map<string, PolicySummary>();
    for (const p of policies.value) {
      map.set(p.id, p);
    }
    return map;
  });

  // Encryption posture computed
  const posture = computed<EncryptionPosture>(() => {
    const total = targets.value.length;
    let encrypted = 0;
    let policyAssigned = 0;
    let policyVerified = 0;
    let unmanaged = 0;

    for (const t of targets.value) {
      const binding = bindingsByTarget.value.get(t.id);
      const meta = parseZfsMetadata(t);
      const isEncrypted = meta?.encryption != null && meta.encryption !== 'off';

      if (binding) {
        policyAssigned++;
        if (binding.state === 'verified') policyVerified++;
        if (isEncrypted) encrypted++;
      } else {
        unmanaged++;
        if (isEncrypted) encrypted++;
      }
    }

    return {
      total,
      encrypted,
      policyAssigned,
      policyVerified,
      unmanaged,
      unencrypted: total - encrypted,
    };
  });

  /** Get combined control plane info for a ZFS dataset by name */
  function getInfoForDataset(datasetName: string): DatasetControlPlaneInfo | null {
    const target = targetsByName.value.get(datasetName);
    if (!target) return null;

    const binding = bindingsByTarget.value.get(target.id) ?? null;
    const policy = binding ? policiesById.value.get(binding.policy_id) ?? null : null;
    const metadata = parseZfsMetadata(target);

    return { target, binding, policy, metadata };
  }

  /** Load all control plane data */
  async function refresh(): Promise<void> {
    loading.value = true;
    error.value = '';
    try {
      const isAvailable = await isControlPlaneAvailable();
      available.value = isAvailable;

      if (!isAvailable) {
        targets.value = [];
        bindings.value = [];
        policies.value = [];
        providers.value = [];
        fipsStatus.value = null;
        return;
      }

      // Fetch all data in parallel
      const [t, b, pol, prov, fips] = await Promise.all([
        listZfsTargets(),
        listBindings(),
        listPolicies(),
        listProviders(),
        getHostFipsStatus(),
      ]);

      targets.value = t ?? [];
      bindings.value = b ?? [];
      policies.value = pol ?? [];
      providers.value = prov ?? [];
      fipsStatus.value = fips;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      error.value = msg;
      console.error('[controlplane] Failed to load control plane data:', msg);
    } finally {
      loading.value = false;
    }
  }

  async function verifyBinding(bindingId: string): Promise<ActionResult | null> {
    return verifyBindingRpc(bindingId);
  }

  async function syncBinding(bindingId: string): Promise<BindingSyncResult | null> {
    return syncBindingRpc(bindingId);
  }

  async function createEncryptedDatasetWithKms(
    pool: string, name: string, policyId: string, properties?: Record<string, string>
  ): Promise<KmsCreateResult | null> {
    return createWithKmsRpc(pool, name, policyId, properties);
  }

  async function fetchAndLoadKey(datasetName: string): Promise<KmsKeyFetchResult | null> {
    return fetchAndLoadKeyRpc(datasetName);
  }

  return {
    available,
    loading,
    error,
    targets,
    bindings,
    policies,
    providers,
    fipsStatus,
    posture,
    getInfoForDataset,
    refresh,
    verifyBinding,
    syncBinding,
    encryptionManagerUrl,
    createEncryptedDatasetWithKms,
    fetchAndLoadKey,
  };
}
