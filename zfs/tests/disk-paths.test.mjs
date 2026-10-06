import assert from 'node:assert/strict';
import { stripTypeScriptTypes } from 'node:module';
import test from 'node:test';
import { loadFunction, sourceFor } from './source-loader.mjs';

const lookup = loadFunction('composables/helpers.ts', 'getFullDiskInfo');
const matchDisk = loadFunction('composables/helpers.ts', 'matchDiskByVdevOrPath', {
    unref: value => value?.value ?? value,
});

function makeDisk(serial = '23264268F661') {
    return {
        name: 'nvme0n1', type: 'NVMe', guid: '', capacity: '447.1 GiB',
        path: '/dev/disk/by-id/original-pool-path', sd_path: '/dev/nvme0n1',
        vdev_path: '/dev/disk/by-vdev/mobo_nvme',
        phy_path: '/dev/disk/by-path/pci-0000:07:00.0-nvme-1',
        id_path: `/dev/disk/by-id/nvme-eui.${serial.toLowerCase()}`,
        alias_paths: [`/dev/disk/by-id/nvme-Micron_7450_MTFDKBA480TFR_${serial}`],
        errors: ['SMART health: POOR'],
    };
}

function makePreparation(disk = makeDisk()) {
    const poolConfig = { value: {
        name: 'test', autoexpand: 'on', autotrim: 'off',
        vdevs: [{ type: 'disk', diskIdentifier: 'phy_path', selectedDisks: [disk.name] }],
    } };
    const newPoolData = { value: { vdevs: [] } };
    const checks = { valid: true, exported: false };
    const fill = loadFunction('components/pool-creation-wizard/PoolConfig.vue', 'fillNewPoolData', {
        poolConfig, newPoolData, disks: { value: [disk] }, getFullDiskInfo: lookup,
        diskCheck: () => checks.valid, diskSizeMatch: () => true, replicationLevelCheck: () => true,
        diskBelongsToImportablePool: () => checks.exported,
        diskFeedback: { value: 'Invalid disk selection' }, diskSizeFeedback: { value: '' },
        isProperReplicationFeedback: { value: '' }, diskBelongsFeedback: { value: 'Disk belongs to exported pool' },
    });
    return { disk, poolConfig, newPoolData, checks, fill };
}

test('Add-VDev blocks exported alias partitions unless explicitly forced', () => {
    const disk = makeDisk();
    const newVDev = { value: { forceAdd: { force: false } } };
    const selectedDisks = { value: [disk.name] };
    const guard = loadFunction('components/pools/AddVDevModal.vue', 'diskBelongsToImportablePool', {
        newVDev, selectedDisks, allDisks: { value: [disk] }, diskBelongsFeedback: { value: '' },
        importablePools: { value: [{ name: 'exported', vdevs: [{ disks: [{ name: 'different-alias', path: disk.alias_paths[0] + '-part1' }] }] }] },
        matchDiskByVdevOrPath: matchDisk, getFullDiskInfo: lookup,
    });
    assert.equal(guard(), true);
    newVDev.value.forceAdd.force = true;
    assert.equal(guard(), false);
    newVDev.value.forceAdd.force = false;
    selectedDisks.value = ['missing'];
    assert.equal(guard(), false);
});

test('Add-VDev submits full selected paths atomically and rejects stale, duplicate, and in-use selections', async () => {
    const disk = makeDisk();
    const newVDev = { value: { disks: [], forceAdd: { force: false } } };
    const selectedDisks = { value: [disk.name] };
    const identifier = { value: 'phy_path' };
    const adding = { value: false };
    const calls = [];
    const notices = [];
    let exported = false;
    const add = loadFunction('components/pools/AddVDevModal.vue', 'addVDevBtn', {
        newVDev, selectedDisks, diskIdentifier: identifier, adding, allDisks: { value: [disk] },
        getFullDiskInfo: lookup, props: { pool: { properties: {} } },
        replicationLevelCheck: () => true, diskSizeMatch: () => true, diskCheck: () => true,
        diskBelongsToImportablePool: () => exported,
        zfsManager: { addVDevsToPool: async (pool, vdevs) => { calls.push(structuredClone(vdevs)); return {}; } },
        Notification: class { constructor(...args) { this.args = args; } }, pushNotification: notice => notices.push(notice),
        resetModalState: () => {}, showAddVDevModal: { value: true }, refreshAllData: async () => {},
    });
    for (const value of ['phy_path', 'sd_path']) {
        identifier.value = value;
        await add();
        assert.equal(calls.at(-1)[0].disks.length, 1);
        assert.equal(calls.at(-1)[0].disks[0].path, disk[value]);
    }
    const successful = calls.length;
    selectedDisks.value = ['missing']; await add();
    selectedDisks.value = [disk.name, disk.name]; await add();
    selectedDisks.value = [disk.name]; disk.guid = 'imported'; await add();
    disk.guid = ''; identifier.value = 'phy_path'; disk.phy_path = 'N/A'; await add();
    disk.phy_path = '/dev/disk/by-path/restored'; exported = true; await add();
    assert.equal(calls.length, successful);
    assert.equal(notices.filter(notice => notice.args[0] === 'Add VDev Failed').length, 4);
    assert.equal(adding.value, false);
    newVDev.value.forceAdd.force = true; await add();
    assert.equal(calls.length, successful + 1);
});

test('alternate aliases and partitions match distinct disks', () => {
    const first = makeDisk('24174C9236BC');
    const second = { ...makeDisk('24174C923DDF'), name: 'nvme1n1', sd_path: '/dev/nvme1n1' };
    const disks = [first, second];
    for (const disk of disks) {
        assert.equal(matchDisk(disks, disk.alias_paths[0] + '-part1'), disk);
        assert.equal(matchDisk({ value: disks }, disk.id_path), disk);
        const legacy = { ...disk, alias_paths: [] };
        assert.equal(matchDisk([legacy], disk.alias_paths[0]), undefined);
    }
    assert.equal(matchDisk(disks, '/dev/disk/by-id/nvme-Micron_7450_MTFDKBA480TFR_24174C9236BD'), undefined);
    assert.equal(matchDisk([{ sd_path: '/dev/sdab' }], '/dev/sda'), undefined);
});

test('lookup supports full paths and alternate alias names without mutating inventory', () => {
    const disk = makeDisk();
    const original = structuredClone(disk);
    for (const name of [disk.name, disk.phy_path, disk.alias_paths[0], disk.alias_paths[0].split('/').at(-1)]) {
        const found = lookup([disk], name);
        assert.ok(found);
        assert.notEqual(found, disk);
    }
    assert.deepEqual(disk, original);
});

test('pool preparation honors identifiers and independent pool options without accumulating vdevs', () => {
    const { disk, poolConfig, newPoolData, fill } = makePreparation();
    const original = structuredClone(disk);
    for (const identifier of ['phy_path', 'sd_path', 'vdev_path']) {
        poolConfig.value.vdevs[0].diskIdentifier = identifier;
        fill();
        fill();
        assert.equal(newPoolData.value.vdevs.length, 1);
        assert.equal(newPoolData.value.vdevs[0].disks[0].path, disk[identifier]);
    }
    assert.equal(newPoolData.value.autoexpand, 'on');
    assert.equal(newPoolData.value.autotrim, 'off');
    assert.deepEqual(disk, original);
});

test('pool preparation rejects missing, duplicate, in-use, and unavailable-path selections atomically', () => {
    const { disk, poolConfig, newPoolData, fill } = makePreparation();
    fill();
    const saved = structuredClone(newPoolData.value);
    poolConfig.value.vdevs[0].selectedDisks.push('missing');
    assert.throws(fill, /no longer available/);
    assert.deepEqual(newPoolData.value, saved);
    poolConfig.value.vdevs[0].selectedDisks = [disk.name, disk.name];
    assert.throws(fill, /more than once/);
    poolConfig.value.vdevs[0].selectedDisks = [disk.name];
    disk.guid = '123';
    assert.throws(fill, /imported pool/);
    disk.guid = '';
    disk.phy_path = 'unknown';
    assert.throws(fill, /No valid phy_path/);
});

test('final preparation reruns configuration and exported-pool checks', () => {
    const { checks, fill } = makePreparation();
    checks.valid = false;
    assert.throws(fill, /Invalid disk selection/);
    checks.valid = true;
    checks.exported = true;
    assert.throws(fill, /exported pool/);
});

test('preparation errors are notified and busy flags reset before any ZFS command', async () => {
    const flags = Array.from({ length: 5 }, () => ({ value: false }));
    const notices = [];
    let commands = 0;
    const finish = loadFunction('components/pool-creation-wizard/CreatePool.vue', 'finishBtn', {
        finishPressed: flags[0], creatingPool: flags[1], poolCreated: flags[2],
        filesystemCreated: flags[3], showWizard: flags[4],
        poolConfiguration: { value: { fillNewPoolData: () => { throw new Error('missing disk'); } } },
        zfsManager: { createPool: () => { commands++; } },
        extractProcessErr: error => error.message, pushNotification: notice => notices.push(notice),
        Notification: class { constructor(title, message) { this.title = title; this.message = message; } },
    });
    await finish({});
    assert.equal(commands, 0);
    assert.equal(notices[0].message, 'missing disk');
    assert.ok(flags.every(flag => flag.value === false));
});

test('identifier labels tolerate a missing disk or missing path', () => {
    const label = loadFunction('composables/helpers.ts', 'getDiskIDName', { ref: value => ({ value }) });
    assert.equal(label([], 'phy_path', 'missing'), '');
    assert.equal(label([{ name: 'nvme0n1' }], 'phy_path', 'nvme0n1'), '');
});

test('NVMe discovery retains configured device aliases and raw-device fallback', async () => {
    const inventory = makeDisk();
    const load = loadFunction('composables/loadData.ts', 'loadDisks', {
        getDisks: async () => JSON.stringify([inventory]),
        unpackArray: raw => ({ data: JSON.parse(raw) }),
        isCapacityPatternInvalid: () => false, formatCapacityString: value => value, changeUnitToBinary: value => value,
    });
    const disks = { value: [] };
    await load(disks);
    assert.equal(disks.value[0].vdev_path, inventory.vdev_path);
    assert.deepEqual(disks.value[0].alias_paths, inventory.alias_paths);
    inventory.vdev_path = 'N/A';
    disks.value = [];
    await load(disks);
    assert.equal(disks.value[0].vdev_path, inventory.sd_path);
});

test('alias-matched enrichment keeps leaf stats instead of mirror aggregate stats', async () => {
    const clean = loadFunction('composables/loadData.ts', 'cleanDiskPath');
    const enrich = loadFunction('composables/loadData.ts', 'loadDisksExtraData', {
        cleanDiskPath: clean, matchDiskByVdevOrPath: matchDisk,
    });
    const disk = makeDisk();
    const disks = [disk];
    const stats = { read_errors: 2, write_errors: 0 };
    await enrich(disks, [{ vdevs: [{ stats: { read_errors: 9 }, disks: [{ path: disk.alias_paths[0] + '-part1', guid: '123', stats }] }] }]);
    assert.deepEqual(disks[0].stats, stats);
    assert.equal(disks[0].guid, '123');
});

test('importable parsing and protection handle nested and single leaves without clearing SMART errors', () => {
    const vDevs = { value: [] };
    const parse = loadFunction('composables/loadImportables.ts', 'parseImportVDevData', { vDevs });
    const disk = makeDisk();
    const leaf = { type: 'disk', name: disk.alias_paths[0].split('/').at(-1), path: disk.alias_paths[0] + '-part1', children: [] };
    parse({ name: 'mirror-0', children: [{ name: 'replacing-0', children: [leaf] }] }, 'exported', 'data');
    parse(leaf, 'single', 'data');
    assert.equal(vDevs.value[0].disks[0], leaf);
    assert.equal(vDevs.value[1].disks[0], leaf);
    const source = sourceFor('components/pool-creation-wizard/PoolConfig.vue');
    const start = source.indexOf('const diskBelongsToImportablePool = () => {');
    assert.ok(start >= 0);
    const code = stripTypeScriptTypes(source.slice(start, source.indexOf('\n};', start) + 3));
    const poolConfig = { value: { forceCreate: false, vdevs: [{ selectedDisks: [disk.name] }] } };
    const dependencies = {
        disks: { value: [disk] }, poolConfig, importablePools: { value: [{ name: 'exported', vdevs: vDevs.value }] },
        diskBelongsFeedback: { value: '' }, getFullDiskInfo: lookup, matchDiskByVdevOrPath: matchDisk,
    };
    const check = new Function(...Object.keys(dependencies), `${code}\nreturn diskBelongsToImportablePool;`)(...Object.values(dependencies));
    assert.equal(check(), true);
    assert.ok(disk.errors.includes('SMART health: POOR'));
    const warnings = structuredClone(disk.errors);
    assert.equal(check(), true);
    assert.deepEqual(disk.errors, warnings);
    poolConfig.value.forceCreate = true;
    assert.equal(check(), false);
});