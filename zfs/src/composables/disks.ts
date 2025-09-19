import { legacy, server, Command, unwrap } from '@45drives/houston-common-lib';
import { exec } from './helpers';
// @ts-ignore
import script_py from "../scripts/get-disks.py?raw";

const { errorString } = legacy;

export async function getDisks() {
	try {
		const { stdout, stderr } = await exec(["/usr/bin/env", "python3", "-u", "-c", script_py]);
		if (stderr) console.warn("getDisks warnings:", stderr);
		// Python prints a JSON string
		return stdout ?? "[]";
	} catch (err: any) {
		console.error("getDisks failed:", err);
		// Safety: always return a JSON string
		return JSON.stringify([]);
	}
}

export async function clearPartitions(disk: { name: string }) {
	try {
		const { stdout } = await exec(["wipefs", "-a", `/dev/${disk.name}`]);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function labelClear(disk: any) {
	try {
		const { stdout } = await exec(["zpool", "labelclear", disk.name]);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function attachDisk(diskVDevPoolData: {
	forceAttach?: boolean;
	poolName: string;
	existingDiskName: string;
	newDiskName: string;
}) {
	try {
		const cmd = ["zpool", "attach"];
		if (diskVDevPoolData.forceAttach) cmd.push("-f");
		cmd.push(
			diskVDevPoolData.poolName,
			diskVDevPoolData.existingDiskName,
			diskVDevPoolData.newDiskName
		);
		const { stdout } = await exec(cmd);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function detachDisk(poolName: string, diskName: string) {
	try {
		const { stdout } = await exec(["zpool", "detach", poolName, diskName]);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function offlineDisk(
	poolName: string,
	diskName: string,
	forceFault?: boolean,
	temporary?: boolean
) {
	try {
		const cmd = ["zpool", "offline"];
		if (forceFault) cmd.push("-f"); // fault instead of simple offline
		if (temporary) cmd.push("-t");  // temporary until reboot
		cmd.push(poolName, diskName);
		const { stdout } = await exec(cmd);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function onlineDisk(poolName: string, diskName: string, expand?: boolean) {
	try {
		const cmd = ["zpool", "online"];
		if (expand) cmd.push("-e");
		cmd.push(poolName, diskName);
		const { stdout } = await exec(cmd);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function replaceDisk(
	poolName: string,
	diskName: string,
	newDiskName: string,
	forceReplace?: boolean
) {
	try {
		const cmd = ["zpool", "replace"];
		if (forceReplace) cmd.push("-f");
		cmd.push(poolName, diskName, newDiskName);
		const { stdout } = await exec(cmd);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function trimDisk(
	poolName: string,
	diskName: string,
	isSecure?: boolean,
	action?: "pause" | "stop"
) {
	try {
		const cmd = ["zpool", "trim"];
		if (isSecure) cmd.push("-d");
		if (action === "pause") cmd.push("-s");
		if (action === "stop") cmd.push("-c");
		cmd.push(poolName, diskName);
		const { stdout } = await exec(cmd);
		return stdout;
	} catch (err: any) {
		const errorMessage = errorString(err);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}
