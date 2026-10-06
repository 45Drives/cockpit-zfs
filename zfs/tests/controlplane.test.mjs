import assert from 'node:assert/strict';
import test from 'node:test';
import { loadFunction } from './source-loader.mjs';

test('control-plane availability closes file handles on a failed read', async () => {
    let closes = 0;
    const available = loadFunction('controlplane/controlplane-client.ts', 'isControlPlaneAvailable', {
        _availabilityCache: null, API_SERVICE_PATH: '/test/api_service.py',
        cockpit: { file: () => ({ read: async () => { throw new Error('permission denied'); }, close: () => { closes++; } }) },
    });
    assert.equal(await available(), false);
    assert.equal(closes, 1);
});

test('control-plane RPC writes JSON on stdin and parses successful responses', async () => {
    const requests = [];
    const process = Promise.resolve(JSON.stringify({ result: { success: true } }));
    process.input = value => requests.push(JSON.parse(value));
    const rpc = loadFunction('controlplane/controlplane-client.ts', 'rpc', {
        API_SERVICE_PATH: '/test/api_service.py', cockpit: { spawn: () => process },
    });
    assert.deepEqual(await rpc('bindings.verify', { id: 'binding-1' }), { success: true });
    assert.deepEqual(requests, [{ method: 'bindings.verify', params: { id: 'binding-1' } }]);
});

test('control-plane RPC rejects backend application errors', async () => {
    const process = Promise.resolve(JSON.stringify({ error: { message: 'provider unavailable' } }));
    process.input = () => {};
    const rpc = loadFunction('controlplane/controlplane-client.ts', 'rpc', {
        API_SERVICE_PATH: '/test/api_service.py', cockpit: { spawn: () => process },
    });
    await assert.rejects(rpc('bindings.verify'), /provider unavailable/);
});