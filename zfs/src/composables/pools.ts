import { legacy, ZPool, server, Command, unwrap } from '@45drives/houston-common-lib';
import { convertSizeToBytes } from './helpers';
// @ts-ignore
import get_pools_script from "../scripts/get-pools.py?raw";
// @ts-ignore
import get_importable_pools_script from "../scripts/get-importable-pools.py?raw";
// @ts-ignore
import get_importable_destroyed_pools_script from "../scripts/get-importable-destroyed-pools.py?raw";
import { PoolEditConfig } from '../types';
import { sanitizeRawJson } from '../utils/json';
import { toText } from '../utils/streams';

//['/usr/bin/env', 'python3', '-c', script, ...args ]
const { errorString, useSpawn } = legacy;

// Helper: execute and return both streams
async function exec(cmd: string[]) {
	return await unwrap(server.execute(new Command(cmd)));
}

export async function getPools() {
	try {
		const { stdout, stderr } = await exec(['/usr/bin/env', 'python3', '-c', get_pools_script]);
		if (stderr) console.warn('getPools warnings:', stderr);
		return sanitizeRawJson(toText(stdout) ?? '', '[]');
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return JSON.stringify({ error: errorMessage });
	}
}


export async function setRefreservation(pool: ZPool, refreservationPercent: number) {
	try {
		const sizeInBytes = convertSizeToBytes(pool.properties.size);
		const refreservationBytes = (sizeInBytes / 100) * refreservationPercent;
		const { stdout } = await exec(['zfs', 'set', `refreservation=${refreservationBytes}`, pool.name]);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function destroyPool(pool: ZPool, forceDestroy?: boolean) {
	try {
		const cmdArgs = ['zpool', 'destroy'];
		if (forceDestroy) cmdArgs.push('-f');
		cmdArgs.push(pool.name);

		const result = await unwrap(server.execute(new Command(cmdArgs)));

		if (result.stderr) {
			console.warn('Destroy command warnings:', result.stderr);
		}
		return result.stdout;

	} catch (err: any) {
		console.error('Error during destroyPool:', err);
		const stderr = err.stderr || '';
		const errorMessage = errorString(err);

		if (
			stderr.includes("dataset does not exist") ||
			stderr.includes("no such pool") ||
			stderr.includes("cannot open")
		) {
			console.warn(`Pool ${pool.name} already gone. Treating as successful destroy.`);
			return '';
		}

		if (stderr.includes("is busy")) {
			return { error: 'Pool is busy. Please ensure no active processes are using it and try again.' };
		}

		if (stderr.includes("cannot unmount")) {
			console.warn(`Unmount failed for pool: ${pool.name}. Retrying forced unmount...`);

			try {
				await unwrap(server.execute(new Command(['zpool', 'list', '-H', pool.name])));
				await unwrap(server.execute(new Command(['zfs', 'unmount', '-f', pool.name])));
				return destroyPool(pool, true);
			} catch (checkErr: any) {
				if (
					checkErr.stderr?.includes("no such pool") ||
					checkErr.stderr?.includes("dataset does not exist") ||
					checkErr.stderr?.includes("cannot open")
				) {
					console.warn(`Pool ${pool.name} not found after failed destroy. Skipping retry.`);
					return '';
				}
				throw checkErr;
			}
		}

		return { error: errorMessage };
	}
}


const properties = [
	"failmode",
	"comment",
	"autoexpand",
	"autoreplace",
	"autotrim",
	"delegation",
	"listsnapshots",
];

export async function configurePool(pool: PoolEditConfig) {
	try {
		if (hasChanges(pool)) {
			for (const property of properties) {
				if (property in pool) {
					const cmd = ['zpool', 'set', `${property}=${(pool as any)[property]}`, pool.name];
					await exec(cmd);
					// preserve tiny spacing between sets, as before
					await new Promise(resolve => setTimeout(resolve, 250));
				}
			}
		} else {
			console.log("There are no selected properties to change.");
		}
		return { success: true };
	} catch (error: any) {
		const errorMessage = errorString(error);
		console.error(errorMessage);
		return { success: false, error: errorMessage };
	}
}

function hasChanges(pool) {
	for (const property of properties) {
		if (property in pool) return true;
	}
	return false;
}

export async function clearErrors(poolName: string, deviceName?: string) {
	try {
		const cmd = ['zpool', 'clear', poolName];
		if (deviceName) cmd.push(deviceName);
		const { stdout } = await exec(cmd);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function trimPool(pool: ZPool, isSecure?: boolean, action?: "pause" | "stop") {
	try {
		const cmd = ['zpool', 'trim'];
		if (isSecure) cmd.push('-d');
		if (action === 'pause') cmd.push('-s');
		if (action === 'stop') cmd.push('-c');
		cmd.push(pool.name);
		const { stdout } = await exec(cmd);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function scrubPool(pool: ZPool, action?: "pause" | "stop") {
	try {
		const cmd = ['zpool', 'scrub'];
		if (action === 'pause') cmd.push('-p');
		if (action === 'stop') cmd.push('-s');
		cmd.push(pool.name);
		const { stdout } = await exec(cmd);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function resilverPool(pool: ZPool) {
	try {
		const { stdout } = await exec(['zpool', 'resilver', pool.name]);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}



export async function exportPool(pool: ZPool, force?: boolean) {
	try {
		const cmd = ['zpool', 'export'];
		if (force) cmd.push('-f');
		cmd.push(pool.name);
		const { stdout } = await exec(cmd);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function getImportablePools() {
	try {
		const { stdout, stderr } = await exec(['/usr/bin/env', 'python3', '-c', get_importable_pools_script]);
		if (stderr) console.warn('getImportablePools warnings:', stderr);
		return sanitizeRawJson(toText(stdout) ?? '', '[]');
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return JSON.stringify({ error: errorMessage });
	}
}

export async function getImportableDestroyedPools() {
	try {
		const { stdout, stderr } = await exec(['/usr/bin/env', 'python3', '-c', get_importable_destroyed_pools_script]);
		if (stderr) console.warn('getImportableDestroyedPools warnings:', stderr);
		return sanitizeRawJson(toText(stdout) ?? '', '[]');
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return JSON.stringify({ error: errorMessage });
	}
}

export async function importPool(pool: {
	isDestroyed?: boolean;
	forceImport?: boolean;
	ignoreMissingLog?: boolean;
	mountFileSystems?: boolean;
	recoveryMode?: boolean;
	altRoot: string;
	readOnly?: boolean;
	poolGUID: string;
	renamePool?: boolean;
	newPoolName?: string;
	name?: string; // for logs
}) {
	try {
		const cmd = ['zpool', 'import'];

		if (pool.isDestroyed) cmd.push('-Df');
		if (pool.forceImport) cmd.push('-f');
		if (pool.ignoreMissingLog) cmd.push('-m');
		if (pool.mountFileSystems === false) cmd.push('-N');
		if (pool.recoveryMode) cmd.push('-F');

		cmd.push('-d', '/dev/disk/by-vdev');
		cmd.push('-d', '/dev/disk/by-path');
		cmd.push('-d', '/dev');

		if (pool.altRoot) cmd.push('-o', `altroot=${pool.altRoot}`);
		if (pool.readOnly) cmd.push('-o', 'readonly=on');

		cmd.push(pool.poolGUID);

		if (pool.renamePool && pool.newPoolName) {
			cmd.push(pool.newPoolName);
		}

		const { stdout } = await exec(cmd);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}


export async function removeVDevFromPool(vdev: { name: string }, pool: { name: string }) {
	try {
		const { stdout } = await exec(['zpool', 'remove', pool.name, vdev.name]);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function upgradePool(pool: ZPool) {
	try {
		const { stdout } = await exec(['zpool', 'upgrade', pool.name]);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}