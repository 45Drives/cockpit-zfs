import assert from 'node:assert/strict';
import test from 'node:test';
import { loadFunction, loadManagerMethod } from './source-loader.mjs';

const dependencies = {
    validateZfsName: name => assert.ok(name), ValueError: Error, unwrap: result => result,
    Command: class { constructor(argv) { this.argv = argv; } },
};
const reserve = loadManagerMethod('setPoolRefreservation', dependencies);
const create = loadManagerMethod('createPool', dependencies);

test('displayed reservation percentage uses the same usable dataset capacity', () => {
    const percentage = loadFunction('composables/loadData.ts', 'poolRefreservationPercent');
    assert.equal(percentage({ properties: { available: { parsed: 7000 }, used: { parsed: 4000 }, usedbyrefreservation: { parsed: 1000 }, refreservation: { parsed: 1000 } } }), 10);
    assert.equal(percentage(null), 0);
    assert.equal(percentage({ properties: {} }), 0);
});

function fixture(space = 'available\t7000\nused\t4000\nusedbyrefreservation\t1000\n') {
    const calls = [];
    const manager = { commandOptions: {}, formatVDevsArgv: () => ['/dev/fixture'],
        server: { execute: async command => {
            calls.push(command.argv);
            return { getStdout: () => command.argv[1] === 'get' ? space : '' };
        } },
    };
    manager.setPoolRefreservation = reserve.bind(manager);
    return { manager, calls };
}

test('pool creation reserves actual usable space independently of topology and auxiliary disk capacities', async () => {
    for (const type of ['mirror', 'raidz1', 'raidz2', 'raidz3']) {
        const { manager, calls } = fixture();
        await create.call(manager, { name: 'tank', vdevs: [{ type, disks: [{ capacity: '999999 GiB' }] }, { type: 'cache', disks: [{ capacity: '999999 GiB' }] }] }, { refreservationPercent: 10 });
        assert.equal(calls[0][0], 'zpool');
        assert.ok(!calls[0].some(arg => arg.startsWith('refreservation=')));
        assert.deepEqual(calls[1], ['zfs', 'get', '-Hp', '-o', 'property,value', 'available,used,usedbyrefreservation', 'tank']);
        assert.deepEqual(calls[2], ['zfs', 'set', 'refreservation=1000', 'tank']);
    }
});

test('zero reservation disables it without querying space; invalid percentages run no commands', async () => {
    const { manager, calls } = fixture();
    await reserve.call(manager, 'tank', 0);
    assert.deepEqual(calls, [['zfs', 'set', 'refreservation=none', 'tank']]);
    calls.length = 0;
    await assert.rejects(create.call(manager, { name: 'tank' }, { refreservationPercent: NaN }), /Invalid refreservation/);
    assert.deepEqual(calls, []);
});

test('failed post-create reservation explicitly reports the pool exists and never destroys it', async () => {
    const { manager, calls } = fixture('available\tinvalid\n');
    await assert.rejects(create.call(manager, { name: 'tank', vdevs: [] }, { refreservationPercent: 10 }), error => error.poolCreated === true && /was created/.test(error.message));
    assert.equal(calls.length, 2);
    assert.ok(!calls.some(argv => argv.includes('destroy')));
});