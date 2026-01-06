import { legacy } from "@45drives/houston-common-lib";
import { exec } from "./helpers";
// @ts-ignore
import get_scan_script from "../scripts/get-scan-stats.py?raw";
// @ts-ignore
import get_disk_stats_script from "../scripts/get-disk-stats.py?raw";

const { errorString } = legacy;

export async function getScanGroup(): Promise<string> {
	try {
		const { stdout, stderr } = await exec(["/usr/bin/env", "python3", "-c", get_scan_script]);
		if (stderr) console.warn("getScanGroup warnings:", stderr);
		return stdout || "{}";
	} catch (err: any) {
		console.error(errorString(err));
		return "{}";
	}
}

export async function getDiskStats(): Promise<string> {
	try {
		const { stdout, stderr } = await exec(["/usr/bin/env", "python3", "-c", get_disk_stats_script]);
		if (stderr) console.warn("getDiskStats warnings:", stderr);
		return stdout || "{}";
	} catch (err: any) {
		console.error(errorString(err));
		return "{}";
	}
}
