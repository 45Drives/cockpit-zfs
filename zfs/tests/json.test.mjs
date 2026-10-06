import assert from 'node:assert/strict';
import test from 'node:test';
import { loadFunction } from './source-loader.mjs';

const sanitizeRawJson = loadFunction('utils/json.ts', 'sanitizeRawJson');
const safeParse = loadFunction('utils/json.ts', 'safeParse', { sanitizeRawJson });
const unpackArray = loadFunction('utils/json.ts', 'unpackArray', { safeParse });

test('mixed log output preserves complete nested payloads and quoted delimiters', () => {
    const data = [{ name: 'disk', stats: { errors: [] }, text: 'brace } bracket ] quote " slash \\' }];
    const raw = `[warning] scanning disks\n${JSON.stringify(data)}\n[info] complete`;
    assert.deepEqual(unpackArray(raw), { data });
});

test('empty discovery is distinct from malformed, missing, and failed responses', () => {
    assert.deepEqual(unpackArray('[]'), { data: [] });
    assert.deepEqual(unpackArray({ ok: true, data: [] }), { data: [], error: undefined });
    for (const raw of ['', null, 'not json', '[{"name":"incomplete"}', { unexpected: [] }, { ok: false, data: [] }]) {
        assert.ok(unpackArray(raw).error, String(raw));
    }
    assert.deepEqual(unpackArray({ error: 'permission denied' }), { data: [], error: 'permission denied' });
});

test('truncated nested payloads do not turn inner objects into successful discovery', () => {
    assert.ok(unpackArray('[{"name":"disk","stats":{}}').error);
    assert.equal(sanitizeRawJson('broken output', '{}'), '{}');
});

test('real inventory loaders explicitly distinguish success from failure', async () => {
    const responses = { disks: '[]', pools: '[]', datasets: '[]' };
    const loadPools = loadFunction('composables/loadData.ts', 'loadDisksThenPools', {
        getDisks: async () => responses.disks, getPools: async () => responses.pools, unpackArray,
        loadDisksExtraData: async () => {},
    });
    const loadDatasets = loadFunction('composables/loadData.ts', 'loadDatasets', {
        getDatasets: async () => responses.datasets, unpackArray,
    });
    assert.equal(await loadPools({ value: [] }, { value: [] }), true);
    assert.equal(await loadDatasets({ value: [] }), true);
    responses.disks = '{"error":"permission denied"}';
    assert.equal(await loadPools({ value: [] }, { value: [] }), false);
    responses.disks = '[]';
    responses.pools = 'truncated output';
    assert.equal(await loadPools({ value: [] }, { value: [] }), false);
    responses.datasets = null;
    assert.equal(await loadDatasets({ value: [] }), false);
});