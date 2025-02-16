import { legacy } from '@45drives/houston-common-lib';// @ts-ignore
import get_scan_script from "../scripts/get-scan-stats.py?raw";
// @ts-ignore
import get_disk_stats_script from "../scripts/get-disk-stats.py?raw";

//['/usr/bin/env', 'python3', '-c', script, ...args ]
const { BetterCockpitFile, errorString, useSpawn } = legacy;
export async function getScanGroup() {
	try {
		const cmdString = ['/usr/bin/env', 'python3', '-c', get_scan_script];
	
		const state = useSpawn(cmdString, { superuser: 'try' });
		const scans = (await state.promise()).stdout;
		return scans;
	} catch (state) {
		// const errorMessage = errorString(state);
		// console.error(errorMessage);
		// return { error: errorMessage };
		console.error(errorString(state));
		return null;
	}
}

export async function getDiskStats() {
	try {
		const cmdString = ['/usr/bin/env', 'python3', '-c', get_disk_stats_script];
		const state = useSpawn(cmdString, { superuser: 'try' });
		const diskStats = (await state.promise()).stdout;
		return diskStats;
	} catch (state) {
		// const errorMessage = errorString(state);
		// console.error(errorMessage);
		// return { error: errorMessage };
		console.error(errorString(state));
		return null;
	}
}