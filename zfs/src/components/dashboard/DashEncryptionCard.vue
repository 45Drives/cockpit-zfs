<template>
	<div v-if="cp.available.value" class="w-full min-w-0 bg-plugin-header rounded-md border border-default overflow-hidden mt-2 mb-4 p-4 space-y-3">
		<!-- Header -->
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-2">
				<LockClosedIcon class="w-5 h-5 text-default" />
				<span class="font-semibold text-default">Encryption Governance</span>
			</div>
			<div class="flex items-center gap-2">
				<button class="btn btn-secondary btn-sm" @click="refresh" :disabled="cp.loading.value">
					<ArrowPathIcon class="w-4 h-4" :class="{ 'animate-spin': cp.loading.value }" />
				</button>
				<a href="#" @click.prevent="navigateToEncryptionManager()"
					class="text-xs text-primary hover:underline">
					Open Encryption Manager →
				</a>
			</div>
		</div>

		<!-- Loading -->
		<div v-if="cp.loading.value && cp.targets.value.length === 0" class="flex justify-center py-4">
			<LoadingSpinner :width="'w-8'" :height="'h-8'" :baseColor="'text-gray-200'" :fillColor="'fill-slate-500'" />
		</div>

		<!-- Error -->
		<div v-else-if="cp.error.value" class="text-sm text-danger">
			Control plane error: {{ cp.error.value }}
		</div>

		<!-- Content -->
		<template v-else>
			<!-- Posture Summary -->
			<div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
				<div class="bg-well rounded-md p-2">
					<div class="text-2xl font-bold text-default">{{ cp.posture.value.total }}</div>
					<div class="text-xs text-muted">Datasets</div>
				</div>
				<div class="bg-well rounded-md p-2">
					<div class="text-2xl font-bold" :class="cp.posture.value.encrypted > 0 ? 'text-green-600' : 'text-muted'">
						{{ cp.posture.value.encrypted }}
					</div>
					<div class="text-xs text-muted">Encrypted</div>
				</div>
				<div class="bg-well rounded-md p-2">
					<div class="text-2xl font-bold" :class="cp.posture.value.policyAssigned > 0 ? 'text-blue-600' : 'text-muted'">
						{{ cp.posture.value.policyAssigned }}
					</div>
					<div class="text-xs text-muted">KMS Managed</div>
				</div>
				<div class="bg-well rounded-md p-2">
					<div class="text-2xl font-bold" :class="cp.posture.value.unmanaged > 0 ? 'text-yellow-600' : 'text-green-600'">
						{{ cp.posture.value.unmanaged }}
					</div>
					<div class="text-xs text-muted">Unmanaged</div>
				</div>
			</div>

			<!-- Posture Bar -->
			<div v-if="cp.posture.value.total > 0" class="w-full h-2 bg-gray-200 rounded-full overflow-hidden flex">
				<div
					class="bg-green-500 h-full transition-all"
					:style="{ width: barWidth(cp.posture.value.policyVerified) }"
					title="Policy Verified"
				></div>
				<div
					class="bg-blue-400 h-full transition-all"
					:style="{ width: barWidth(cp.posture.value.policyAssigned - cp.posture.value.policyVerified) }"
					title="Policy Assigned"
				></div>
				<div
					class="bg-yellow-400 h-full transition-all"
					:style="{ width: barWidth(cp.posture.value.encrypted - cp.posture.value.policyAssigned) }"
					title="Encrypted (no policy)"
				></div>
			</div>
			<div v-if="cp.posture.value.total > 0" class="flex gap-3 text-xs text-muted">
				<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-green-500 inline-block"></span> Verified</span>
				<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-blue-400 inline-block"></span> Managed</span>
				<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-yellow-400 inline-block"></span> Encrypted Only</span>
				<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-gray-300 inline-block"></span> Unencrypted</span>
			</div>

			<!-- Provider Info -->
			<div v-if="primaryProvider" class="flex items-center gap-2 text-sm">
				<span class="text-muted">KMS Provider:</span>
				<span class="font-medium text-default">{{ primaryProvider.name }}</span>
				<span class="inline-block w-2 h-2 rounded-full" :class="providerDotClass"></span>
				<span class="text-xs text-muted">{{ primaryProvider.type }}</span>
			</div>
			<div v-else class="text-sm text-muted">
				No KMS provider configured —
				<a href="#" @click.prevent="navigateToEncryptionManager()" class="text-primary hover:underline">
					Configure in Encryption Manager
				</a>
			</div>

			<!-- FIPS Badge -->
			<div v-if="cp.fipsStatus.value" class="flex items-center gap-2 text-xs">
				<span
					class="inline-block px-2 py-0.5 rounded font-medium"
					:class="cp.fipsStatus.value.fipsEnabled ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'"
				>
					{{ cp.fipsStatus.value.fipsEnabled ? '🔒 FIPS Active' : '⚠ FIPS Not Active' }}
				</span>
			</div>
		</template>
	</div>
</template>

<script setup lang="ts">
import { inject, computed } from 'vue';
import { LockClosedIcon } from '@heroicons/vue/24/outline';
import { ArrowPathIcon } from '@heroicons/vue/24/outline';
import LoadingSpinner from '../common/LoadingSpinner.vue';
import type { ControlPlaneState } from '../../composables/useControlPlane';
import { navigateToEncryptionManager } from '../../controlplane/controlplane-client';

const cp = inject<ControlPlaneState>('controlplane')!;

/** Show the provider actually used by bound policies, excluding mock providers */
const primaryProvider = computed(() => {
	// Collect provider IDs referenced by policies that have active bindings
	const boundPolicyIds = new Set(
		cp.bindings?.value
			?.filter(b => b.state !== 'unbound')
			?.map(b => b.policy_id) ?? []
	);
	const usedProviderIds = new Set(
		cp.policies?.value
			?.filter(p => boundPolicyIds.has(p.id))
			?.map(p => p.provider_id) ?? []
	);
	// Prefer providers that are actively used, skip mock providers
	const used = cp.providers.value.filter(
		p => usedProviderIds.has(p.id) && p.type !== 'mock'
	);
	if (used.length > 0) return used[0];
	// Fall back to any non-mock provider
	const nonMock = cp.providers.value.filter(p => p.type !== 'mock');
	if (nonMock.length > 0) return nonMock[0];
	// Last resort: any provider
	return cp.providers.value.length > 0 ? cp.providers.value[0] : null;
});

const providerDotClass = computed(() => {
	const prov = primaryProvider.value;
	if (!prov) return 'bg-gray-400';
	if (prov.status === 'error') return 'bg-red-500';
	return 'bg-green-500';
});

function barWidth(count: number): string {
	if (cp.posture.value.total === 0) return '0%';
	const pct = Math.max(0, (count / cp.posture.value.total) * 100);
	return `${pct}%`;
}

async function refresh() {
	await cp.refresh();
}
</script>
