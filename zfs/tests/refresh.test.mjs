import assert from 'node:assert/strict';
import test from 'node:test';
import { loadFunction } from './source-loader.mjs';

function refreshFixture(loader) {
    const ref = value => ({ value });
    const ctx = {
        poolData: ref([{ name: 'old' }]), diskData: ref([]), filesystemData: ref([]),
        disksLoaded: ref(true), poolsLoaded: ref(true), fileSystemsLoaded: ref(true),
        scanObjectGroup: ref({}), poolDiskStats: ref({}), scanActivities: ref(new Map()), trimActivities: ref(new Map()),
    };
    const useRefresh = loadFunction('composables/useRefreshAllData.ts', 'useRefreshAllData', {
        ref, loadDisksThenPools: loader, loadDatasets: async () => {},
        loadScanObjectGroup: async () => {}, loadDiskStats: async () => {},
        loadScanActivities: async () => {}, loadTrimActivities: async () => {},
    });
    return { ctx, useRefresh };
}

test('concurrent refresh calls share one load and swap a coherent inventory', async () => {
    let resolve;
    let calls = 0;
    const pending = new Promise(done => { resolve = done; });
    const { ctx, useRefresh } = refreshFixture(async (disks, pools) => {
        calls++;
        await pending;
        disks.value = [{ name: 'nvme0n1' }];
        pools.value = [{ name: 'new' }];
    });
    const state = useRefresh(ctx);
    const first = state.refreshAllData();
    const second = state.refreshAllData();
    assert.equal(first, second);
    assert.equal(state.isRefreshing.value, true);
    resolve();
    await first;
    assert.equal(calls, 1);
    assert.equal(ctx.poolData.value[0].name, 'new');
    assert.equal(ctx.diskData.value[0].name, 'nvme0n1');
    assert.equal(state.isRefreshing.value, false);
});

test('failed refresh preserves inventory, resets flags, and allows a retry without unhandled rejection', async () => {
    let calls = 0;
    const { ctx, useRefresh } = refreshFixture(async (disks, pools) => {
        calls++;
        if (calls === 1) throw new Error('inventory unavailable');
        pools.value = [{ name: 'recovered' }];
    });
    const state = useRefresh(ctx);
    await assert.rejects(state.refreshAllData(), /inventory unavailable/);
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(ctx.poolData.value[0].name, 'old');
    assert.equal(state.isRefreshing.value, false);
    assert.ok(ctx.disksLoaded.value && ctx.poolsLoaded.value && ctx.fileSystemsLoaded.value);
    await state.refreshAllData();
    assert.equal(ctx.poolData.value[0].name, 'recovered');
});

test('successful empty discovery clears the last pool and stale statistics by default', async () => {
    const { ctx, useRefresh } = refreshFixture(async () => {});
    ctx.scanObjectGroup.value = { old: {} };
    ctx.poolDiskStats.value = { old: [] };
    await useRefresh(ctx).refreshAllData();
    assert.deepEqual(ctx.poolData.value, []);
    assert.deepEqual(ctx.scanObjectGroup.value, {});
    assert.deepEqual(ctx.poolDiskStats.value, {});
});

test('explicit discovery failure preserves the entire previous inventory', async () => {
    const { ctx, useRefresh } = refreshFixture(async () => false);
    const previous = ctx.poolData.value;
    await assert.rejects(useRefresh(ctx).refreshAllData(), /previous inventory was retained/);
    assert.equal(ctx.poolData.value, previous);
});