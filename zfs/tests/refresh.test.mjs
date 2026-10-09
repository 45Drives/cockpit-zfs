import assert from 'node:assert/strict';
import test from 'node:test';
import { loadFunction } from './source-loader.mjs';

const formatSnapshotCreation = loadFunction('composables/helpers.ts', 'formatSnapshotCreation');

test('snapshot epochs use local time with an explicit offset, including DST and midnight', () => {
    const previousTimezone = process.env.TZ;
    try {
        process.env.TZ = 'UTC';
        assert.equal(formatSnapshotCreation('0'), '1970-01-01 00:00:00 GMT');
        process.env.TZ = 'America/New_York';
        assert.equal(formatSnapshotCreation(Date.parse('2026-10-06T20:00:25Z') / 1000), '2026-10-06 16:00:25 GMT-4');
        assert.equal(formatSnapshotCreation(Date.parse('2026-01-06T20:00:25Z') / 1000), '2026-01-06 15:00:25 GMT-5');
        assert.equal(formatSnapshotCreation(Date.parse('2026-10-06T04:00:00Z') / 1000), '2026-10-06 00:00:00 GMT-4');
        for (const invalid of [null, undefined, '', ' ', 'None', '2026-10-06 20:00:25', NaN, Infinity, 1e20, true, false, [], {}, Symbol('invalid')]) {
            assert.equal(formatSnapshotCreation(invalid), '-');
        }
    } finally {
        if (previousTimezone === undefined) delete process.env.TZ;
        else process.env.TZ = previousTimezone;
    }
});

test('snapshot epochs preserve fractional-hour local offsets without locale formatting', () => {
    const previousTimezone = process.env.TZ;
    const format = loadFunction('composables/helpers.ts', 'formatSnapshotCreation', {
        Intl: { DateTimeFormat() { throw new Error('Locale formatting must not determine snapshot output'); } },
    });
    try {
        const epoch = Date.parse('2026-01-06T20:00:25Z') / 1000;
        for (const [timezone, expected] of [
            ['Asia/Kolkata', '2026-01-07 01:30:25 GMT+5:30'],
            ['Asia/Kathmandu', '2026-01-07 01:45:25 GMT+5:45'],
            ['America/St_Johns', '2026-01-06 16:30:25 GMT-3:30'],
        ]) {
            process.env.TZ = timezone;
            assert.equal(format(epoch), expected);
        }
    } finally {
        if (previousTimezone === undefined) delete process.env.TZ;
        else process.env.TZ = previousTimezone;
    }
});

test('all snapshot loaders format the numeric creation epoch, never backend date strings', async () => {
    const epoch = String(Date.parse('2026-10-06T20:00:25Z') / 1000);
    const snapshot = {
        name: 'tank/data@scheduler-2026.10.06-20.00.24', snapshot_name: 'scheduler-2026.10.06-20.00.24',
        properties: {
            guid: { value: '123' }, creation: { rawvalue: epoch, parsed: 'ambiguous backend date', value: 'another date' },
            clones: { parsed: [] }, referenced: {}, used: {},
        },
    };
    const fetch = async () => ({ 'tank/data': [snapshot] });
    for (const name of ['loadSnapshots', 'loadSnapshotsInPool', 'loadSnapshotsInDataset']) {
        const load = loadFunction('composables/loadData.ts', name, {
            getSnapshots: fetch, getSnapshotsOfPool: fetch, getSnapshotsOfDataset: fetch, formatSnapshotCreation,
            console: { log() {}, error(error) { throw error; } },
        });
        const snapshots = { value: [] };
        await load(snapshots, 'tank/data', null, null);
        assert.equal(snapshots.value[0].properties.creation.parsed, formatSnapshotCreation(epoch));
        assert.equal(snapshots.value[0].creationTimestamp, epoch);
        assert.equal(snapshots.value[0].name, snapshot.name);
    }
    assert.equal(snapshot.properties.creation.parsed, 'ambiguous backend date');
});

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