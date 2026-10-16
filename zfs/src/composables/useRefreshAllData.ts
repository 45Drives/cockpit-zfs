// src/composables/useRefreshAllData.ts
import { ref, type Ref } from "vue";
import type { ZPool, VDevDisk, ZFSFileSystemInfo } from "@45drives/houston-common-lib";
import type { PoolScanObjectGroup, PoolDiskStats, Activity } from "../types";

import {
    loadDisksThenPools,
    loadDatasets,
    loadScanObjectGroup,
    loadDiskStats
} from "./loadData";

import { loadScanActivities, loadTrimActivities } from "./helpers";

type RefreshCtx = {
    poolData: Ref<ZPool[]>;
    diskData: Ref<VDevDisk[]>;
    filesystemData: Ref<ZFSFileSystemInfo[]>;

    disksLoaded: Ref<boolean>;
    poolsLoaded: Ref<boolean>;
    fileSystemsLoaded: Ref<boolean>;

    scanObjectGroup: Ref<PoolScanObjectGroup>;
    poolDiskStats: Ref<PoolDiskStats>;

    scanActivities: Ref<Map<string, Activity>>;
    trimActivities: Ref<Map<string, Activity>>;
};

type RefreshOpts = {
    keepOldOnEmpty?: boolean;
    rebuildActivitiesOnSwap?: boolean; // default true
};

export function useRefreshAllData(ctx: RefreshCtx, opts: RefreshOpts = {}) {
    const keepOldOnEmpty = opts.keepOldOnEmpty ?? false;
    const rebuildActivitiesOnSwap = opts.rebuildActivitiesOnSwap ?? true;

    let inFlight: Promise<void> | null = null;

    const isRefreshing = ref(false);

    function refreshAllData() {
        if (inFlight) return inFlight;
        inFlight = (async () => {
            isRefreshing.value = true;
            try {
                ctx.disksLoaded.value = false;
                ctx.poolsLoaded.value = false;
                ctx.fileSystemsLoaded.value = false;

                const nextDisks = ref<VDevDisk[]>([]);
                const nextPools = ref<ZPool[]>([]);
                const nextDatasets = ref<ZFSFileSystemInfo[]>([]);

                try {
                    if (await loadDisksThenPools(nextDisks, nextPools) === false) {
                        throw new Error('Disk or pool discovery failed; previous inventory was retained.');
                    }
                    if (await loadDatasets(nextDatasets) === false) {
                        throw new Error('Dataset discovery failed; previous inventory was retained.');
                    }

                    const gotPools = nextPools.value.length > 0;
                    const shouldSwap = keepOldOnEmpty ? gotPools : true;

                    if (shouldSwap) {
                        ctx.diskData.value = nextDisks.value;
                        ctx.poolData.value = nextPools.value;
                        ctx.filesystemData.value = nextDatasets.value;

                        if (rebuildActivitiesOnSwap) {
                            ctx.scanActivities.value = new Map<string, Activity>();
                            ctx.trimActivities.value = new Map<string, Activity>();
                            await loadScanActivities(ctx.poolData, ctx.scanActivities);
                            await loadTrimActivities(ctx.poolData, ctx.trimActivities);
                        }
                    }

                    await loadScanObjectGroup(ctx.scanObjectGroup);
                    await loadDiskStats(ctx.poolDiskStats);
                    if (shouldSwap) {
                        const names = new Set(ctx.poolData.value.map(pool => pool.name));
                        ctx.scanObjectGroup.value = Object.fromEntries(Object.entries(ctx.scanObjectGroup.value).filter(([name]) => names.has(name)));
                        ctx.poolDiskStats.value = Object.fromEntries(Object.entries(ctx.poolDiskStats.value).filter(([name]) => names.has(name)));
                    }
                } finally {
                    ctx.disksLoaded.value = true;
                    ctx.poolsLoaded.value = true;
                    ctx.fileSystemsLoaded.value = true;
                }
            } finally {
                isRefreshing.value = false;
            }
        })();
        inFlight.then(() => (inFlight = null), () => (inFlight = null));
        return inFlight;
    }


    return { refreshAllData, isRefreshing };
}
