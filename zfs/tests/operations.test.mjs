import assert from 'node:assert/strict';
import test from 'node:test';
import { loadFunction, sourceFor } from './source-loader.mjs';

test('replication UI propagates send errors and always closes the progress watcher', async () => {
    for (const failed of [false, true]) {
        let closed = 0;
        const send = loadFunction('components/snapshots/SendSnapshot.vue', 'sendAndReadProgress', {
            BetterCockpitFile: class { close() { closed++; } }, readSendProgress: async () => {},
            sendSnapshot: async () => failed ? { error: 'sender failed' } : 'finished',
        });
        if (failed) await assert.rejects(send({}, []), /sender failed/);
        else await send({}, []);
        assert.equal(closed, 1);
    }
});

const detectRange = loadFunction('composables/snapshots.ts', 'detectSnapshotRange');

function bulkDeletion(spawn) {
    return loadFunction('composables/snapshots.ts', 'destroySnapshotsBulk', {
        detectSnapshotRange: detectRange, useSpawn: spawn, errorString: error => error.message,
    });
}

test('snapshot UI uses chronology for deletion even when display sorting makes selections adjacent', async () => {
    const chronological = ['pool/data@a', 'pool/data@middle', 'pool/data@b'];
    const selected = [chronological[0], chronological[2]];
    const source = sourceFor('components/snapshots/SnapshotsList.vue');
    const expression = /const allSnapNames = ([^\n]+);/.exec(source);
    assert.ok(expression);
    const getNames = new Function('snapshotsInFilesystem', 'sortedSnapshotsInFilesystem', `return ${expression[1]};`);
    for (const displayOrder of [[...selected, chronological[1]], [...chronological].reverse()]) {
        const allNames = getNames(
            { value: chronological.map(name => ({ name })) },
            { value: displayOrder.map(name => ({ name })) },
        );
        const commands = [];
        const destroy = bulkDeletion(argv => {
            commands.push(argv);
            return { promise: async () => ({ stdout: '' }) };
        });
        await destroy(selected, allNames);
        assert.deepEqual(commands, selected.map(name => ['zfs', 'destroy', name]));
    }
});

for (const scenario of ['creation', 'refresh', 'filesystem', 'zvol', 'reservation', 'success']) {
    test(`pool wizard handles ${scenario} outcome without inviting a duplicate creation`, async () => {
        const refs = Object.fromEntries(['finishPressed', 'creatingPool', 'poolCreated', 'filesystemCreated'].map(name => [name, { value: false }]));
        const showWizard = { value: true };
        const notifications = [];
        let refreshCalls = 0;
        let datasetCalls = 0;
        const finish = loadFunction('components/pool-creation-wizard/CreatePool.vue', 'finishBtn', {
            ...refs, showWizard, certifiedFipsProfile: { value: false },
            poolConfiguration: { value: {
                fillNewPoolData() {}, getDatasetCreationType: () => scenario === 'zvol' ? 'zvol' : 'filesystem',
                getZvolConfig: () => ({ name: 'volume' }),
            } },
            datasetCreationType: { value: '' }, zvolConfigData: { value: {} },
            zfsManager: { createPool: async () => {
                if (scenario === 'creation') throw new Error('create failed');
                if (scenario === 'reservation') throw Object.assign(new Error('reservation failed'), { poolCreated: true });
            } },
            refreshAllData: async () => {
                refreshCalls++;
                if (scenario === 'refresh' && refreshCalls === 1) throw new Error('refresh failed');
            },
            newFS: async () => {
                datasetCalls++;
                if (scenario === 'filesystem' || scenario === 'zvol') throw new Error('dataset failed');
            },
            extractProcessErr: error => error.message,
            pushNotification: notification => notifications.push(notification),
            Notification: class { constructor(title, message, severity) { Object.assign(this, { title, message, severity }); } },
        });
        await finish({ name: 'tank', vdevs: [] });
        assert.equal(showWizard.value, scenario === 'creation');
        assert.ok(Object.values(refs).every(ref => ref.value === false));
        assert.equal(datasetCalls, ['filesystem', 'zvol', 'success'].includes(scenario) ? 1 : 0);
        const error = notifications.find(notification => notification.severity === 'error');
        const titles = {
            creation: 'Pool Creation Failed', refresh: 'Pool Created; Refresh Failed',
            filesystem: 'Pool Created; Dataset Creation Failed', zvol: 'Pool Created; Dataset Creation Failed',
            reservation: 'Pool Created; Reservation Failed',
        };
        if (scenario === 'success') assert.equal(error, undefined);
        else {
            assert.equal(error.title, titles[scenario]);
            if (scenario !== 'creation') assert.match(error.message, /Pool 'tank' exists\./);
        }
        assert.equal(refreshCalls, scenario === 'creation' ? 0 : ['refresh', 'filesystem', 'zvol'].includes(scenario) ? 2 : 1);
    });
}

test('snapshot range batches follow chronology rather than selection order', async () => {
    const snapshots = Array.from({ length: 105 }, (_, index) => `pool/data@s${index}`);
    const commands = [];
    const destroy = bulkDeletion(argv => {
        commands.push(argv);
        return { promise: async () => ({ stdout: '' }) };
    });
    const result = await destroy([...snapshots].reverse(), snapshots);
    assert.deepEqual(commands, [
        ['zfs', 'destroy', 'pool/data@s0%s99'],
        ['zfs', 'destroy', 'pool/data@s100%s104'],
    ]);
    assert.equal(result.succeeded.length, 105);
    assert.deepEqual(result.failed, []);
});

test('non-contiguous snapshot deletion uses literal arguments and records partial failures once', async () => {
    const commands = [];
    const destroy = bulkDeletion(argv => {
        commands.push(argv);
        return { promise: async () => {
            if (argv[2] === 'pool/data@busy') throw new Error('snapshot is held');
            return { stdout: '' };
        } };
    });
    const literal = "pool/data@quote'$(not-a-command)";
    const progress = [];
    const result = await destroy(['pool/data@good', 'pool/data@busy', literal], undefined, current => progress.push(current));
    assert.equal(commands.length, 3);
    assert.deepEqual(commands[2], ['zfs', 'destroy', literal]);
    assert.deepEqual(result.succeeded, ['pool/data@good', literal]);
    assert.deepEqual(result.failed, [{ snapshot: 'pool/data@busy', error: 'snapshot is held' }]);
    assert.equal(progress.at(-1), 3);
});

test('cancelled snapshot deletion starts no command, including the small-range path', async () => {
    const destroy = bulkDeletion(() => { throw new Error('must not execute'); });
    const snapshots = ['pool/data@first', 'pool/data@second'];
    const result = await destroy(snapshots, snapshots, undefined, { value: true });
    assert.deepEqual(result, { succeeded: [], failed: [], cancelled: true });
});

test('snapshot deletion stops scheduling after a completed batch is cancelled', async () => {
    const cancel = { value: false };
    const commands = [];
    const destroy = bulkDeletion(argv => {
        commands.push(argv);
        return { promise: async () => { cancel.value = true; return { stdout: '' }; } };
    });
    const result = await destroy(Array.from({ length: 25 }, (_, index) => `pool/data@s${index}`), undefined, undefined, cancel);
    assert.equal(commands.length, 10);
    assert.equal(result.succeeded.length, 10);
    assert.equal(result.cancelled, true);
});

for (const operation of ['Attach', 'Replace']) {
    test(`${operation.toLowerCase()} prepares complete device paths without removing vdev members`, async () => {
        const existing = { name: 'old', path: '/dev/disk/by-id/existing-part1' };
        const replacement = { name: 'nvme1n1', guid: '', phy_path: '/dev/disk/by-path/pci-nvme-1', sd_path: '/dev/nvme1n1', vdev_path: '/dev/disk/by-vdev/mobo_nvme' };
        const members = [existing];
        const refs = Object.fromEntries(['oldDisk', 'newDisk', 'diskNewPath', 'diskNewName', 'diskExistPath', 'diskExistName'].map(name => [name, { value: '' }]));
        const diskIdentifier = { value: 'phy_path' };
        const allDisks = { value: [replacement] };
        const dependencies = {
            ...refs, props: { disk: existing, vDev: { disks: members } }, diskIdentifier, allDisks,
            selectedDisk: { value: replacement.name }, diskSizeFeedback: { value: '' },
            phyPathPrefix: '/dev/disk/by-path/', sdPathPrefix: '/dev/',
        };
        const file = `components/disks/${operation}DiskModal.vue`;
        const prepare = loadFunction(file, 'setDiskNamePath', dependencies);
        assert.equal(prepare(), true);
        assert.equal(prepare(), true);
        assert.deepEqual(members, [existing]);
        assert.equal(refs.diskNewPath.value, replacement.phy_path);
        assert.equal(refs.diskExistName.value, existing.path);
        const data = { value: { poolName: 'pool', forceAttach: false, forceReplace: false } };
        const calls = [];
        const adding = { value: false };
        const submit = loadFunction(file, `${operation.toLowerCase()}DiskBtn`, {
            ...refs, adding, diskVDevPoolData: data, setDiskNamePath: prepare,
            diskSizeMatch: () => true, diskBelongsToImportablePool: () => false,
            attachDisk: async value => { calls.push(value.newDiskName); return ''; },
            replaceDisk: async (pool, old, path) => { calls.push(path); return ''; },
            showAttachDiskModal: { value: true }, showReplaceDiskModal: { value: true },
            refreshAllData: async () => {}, pushNotification: () => {}, Notification: class {},
        });
        await submit();
        assert.deepEqual(calls, [replacement.phy_path]);
        assert.equal(adding.value, false);
        allDisks.value = [];
        assert.equal(prepare(), false);
        assert.deepEqual(members, [existing]);
    });
}

test('dataset updates accept numeric zero and use valid ZFS reset values', async () => {
    const commands = [];
    const configure = loadFunction('composables/datasets.ts', 'configureDataset', {
        hasChanges: () => true, errorString: error => error.message,
        useSpawn: argv => { commands.push(argv); return { promise: async () => ({ stdout: '' }) }; },
    });
    await configure({ name: 'pool/data', quota: 0, refreservation: 0, readonly: 'off' });
    assert.deepEqual(commands, [['zfs', 'set', 'readonly=off', 'quota=none', 'refreservation=none', 'pool/data']]);
    assert.equal(await configure({ name: 'pool/data', quota: '', refreservation: undefined }), '');
    assert.equal(commands.length, 1);
});

test('partition clearing uses the underlying block device rather than a bay/display name', async () => {
    const commands = [];
    const clear = loadFunction('composables/disks.ts', 'clearPartitions', {
        exec: async argv => { commands.push(argv); return { stdout: '' }; }, errorString: error => error.message,
    });
    await clear({ name: '1-1', sd_path: '/dev/sdd' });
    await clear({ name: 'nvme0n1' });
    assert.deepEqual(commands, [['wipefs', '-a', '/dev/sdd'], ['wipefs', '-a', '/dev/nvme0n1']]);
    const invalid = await clear({ name: '1-1' });
    assert.match(invalid.error, /No valid block-device/);
    assert.equal(commands.length, 2);
});

test('disk operation wrappers preserve full targets and requested flags', async () => {
    const commands = [];
    const dependencies = { exec: async argv => { commands.push(argv); return { stdout: '' }; }, errorString: error => error.message };
    await loadFunction('composables/disks.ts', 'offlineDisk', dependencies)('pool', '/dev/disk/by-id/disk-part1', true, true);
    await loadFunction('composables/disks.ts', 'onlineDisk', dependencies)('pool', '/dev/disk/by-id/disk-part1', true);
    await loadFunction('composables/disks.ts', 'trimDisk', dependencies)('pool', '/dev/nvme0n1', true, 'pause');
    await loadFunction('composables/disks.ts', 'replaceDisk', dependencies)('pool', 'old-guid', '/dev/disk/by-path/new', true);
    assert.deepEqual(commands, [
        ['zpool', 'offline', '-f', '-t', 'pool', '/dev/disk/by-id/disk-part1'],
        ['zpool', 'online', '-e', 'pool', '/dev/disk/by-id/disk-part1'],
        ['zpool', 'trim', '-d', '-s', 'pool', '/dev/nvme0n1'],
        ['zpool', 'replace', '-f', 'pool', 'old-guid', '/dev/disk/by-path/new'],
    ]);
});

test('pool import preserves recovery, readonly, mount, and rename options', async () => {
    const commands = [];
    const importPool = loadFunction('composables/pools.ts', 'importPool', {
        exec: async argv => { commands.push(argv); return { stdout: '' }; }, errorString: error => error.message,
    });
    await importPool({ poolGUID: '123', forceImport: true, ignoreMissingLog: true, mountFileSystems: false, recoveryMode: true, altRoot: '/mnt/test', readOnly: true, renamePool: true, newPoolName: 'renamed' });
    assert.deepEqual(commands, [[
        'zpool', 'import', '-f', '-m', '-N', '-F',
        '-d', '/dev/disk/by-vdev', '-d', '/dev/disk/by-path', '-d', '/dev',
        '-o', 'altroot=/mnt/test', '-o', 'readonly=on', '123', 'renamed',
    ]]);
});

test('all legacy encryption calls send passphrases through stdin, never argv', async () => {
    const commands = [];
    const inputs = [];
    const dependencies = {
        create_encrypted_dataset_script: 'create-script', change_passphrase_script: 'change-script',
        validate_passphrase_script: 'validate-script', unlock_dataset_script: 'unlock-script',
        errorString: error => error.message,
        useSpawn: argv => {
            commands.push(argv);
            return { proc: { input: value => inputs.push(value) }, promise: async () => ({ stdout: 'true\n' }) };
        },
    };
    const secret = ' test-fixture-key "quoted" ';
    await loadFunction('composables/datasets.ts', 'createEncryptedDataset', dependencies)({ parent: 'pool', name: 'data', quota: 0 }, secret);
    await loadFunction('composables/datasets.ts', 'changePassphrase', dependencies)('pool/data', secret);
    assert.equal(await loadFunction('composables/datasets.ts', 'isPassphraseValid', dependencies)('pool/data', secret), true);
    await loadFunction('composables/datasets.ts', 'unlockFileSystem', dependencies)({ name: 'pool/data' }, secret);
    assert.deepEqual(inputs, [secret, secret, secret, secret]);
    assert.ok(commands.every(argv => !argv.some(argument => argument.includes(secret))));
    assert.ok(commands.slice(1).every(argv => argv.at(-1) === 'pool/data'));
});