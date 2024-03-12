import { useSpawn, errorString } from '@45drives/cockpit-helpers';
import { convertTimestampToLocal, convertTimestampFormat } from '../composables/helpers';
// @ts-ignore
import get_snapshots_script from "../scripts/get-snapshots.py?raw";
// @ts-ignore
import send_dataset_script from "../scripts/send-dataset.py?raw";
// @ts-ignore
import check_dataset_script from"../scripts/check-dataset.py?raw";
// @ts-ignore
import get_recent_snaps_script from"../scripts/find-last-common-snap.py?raw";
// @ts-ignore
import check_remote_snaps_script from"../scripts/check-remote-snapshots.py?raw";

//['/usr/bin/env', 'python3', '-c', script, ...args ]

export async function getSnapshots() {
    try {
        const state = useSpawn(['/usr/bin/env', 'python3', '-c', get_snapshots_script], { superuser: 'try' });
        const snapshots = (await state.promise()).stdout;
        return snapshots;
    } catch (state) {
        console.error(errorString(state));
        return null;
    }
}

export async function createSnapshot(newSnap : NewSnapshot) {
    try {
        let cmdString = ['zfs', 'snapshot'];

        if (newSnap.snapChildren) {
            cmdString.push('-r');
        }

        cmdString.push(newSnap.filesystem + '@' + newSnap.name);

        console.log("****create cmdString: *****\n" , cmdString);
			
        const state = useSpawn(cmdString);
        const output = await state.promise();
        console.log(output)
        return output.stdout;
    } catch (state) {
        console.error(errorString(state));
        return null;
    }
}

export async function destroySnapshot(snapshot, destroyChildrenSameName, destroyAllChildren) {
    try {
        let cmdString = ['zfs', 'destroy'];

        if (destroyChildrenSameName) {
            cmdString.push('-r');
        }

        if (destroyAllChildren) {
            cmdString.push('-R');
        }

        cmdString.push(snapshot.name)

        console.log("****create cmdString: *****\n" , cmdString);
			
        const state = useSpawn(cmdString);
        const output = await state.promise();
        console.log(output)
        return output.stdout;
    } catch (state) {
        console.error(errorString(state));
        return null;
    }
}

export async function rollbackSnapshot(snapshot, destroyNewerSnaps, destroyAllNewer) {
    try {
        let cmdString = ['zfs', 'rollback'];

        if (destroyNewerSnaps) {
            cmdString.push('-r');
        }

        if (destroyAllNewer) {
            cmdString.push('-R');
        }

        cmdString.push(snapshot.name)

        console.log("****create cmdString: *****\n" , cmdString);
			
        const state = useSpawn(cmdString);
        const output = await state.promise();
        console.log(output)
        return output.stdout;
    } catch (state) {
        console.error(errorString(state));
        return null;
    }
}

export async function renameSnapshot(snapshotName, newName, renameChildren?) {
    try {
        let cmdString = ['zfs', 'rename'];

        if (renameChildren) {
            cmdString.push('-r');
        }

        cmdString.push(snapshotName);
        cmdString.push(newName);

        console.log("****create cmdString: *****\n" , cmdString);
			
        const state = useSpawn(cmdString);
        const output = await state.promise();
        console.log(output)
        return output.stdout;
    } catch (state) {
        console.error(errorString(state));
        return null;
    }
}

export async function cloneSnapshot(snapName, newParentFS, cloneName, createParent?) {
    try {
        let cmdString = ['zfs', 'clone'];

        if (createParent) {
            cmdString.push('-p');
        }

        cmdString.push(`${snapName}`);
        cmdString.push(`${newParentFS}/${cloneName}`);

        console.log("****create cmdString: *****\n" , cmdString);
			
        const state = useSpawn(cmdString);
        const output = await state.promise();
        console.log(output)
        return output.stdout;
    } catch (state) {
        console.error(errorString(state));
        return null;
    }
}

export async function sendSnapshot(sendingData : SendingDataset) {
	try {
        console.log('sendingData (snapshots.ts - sendSnapshot):', sendingData);

		const state = useSpawn(['/usr/bin/env', 'python3', '-c', send_dataset_script, sendingData.sendName, sendingData.recvName, sendingData.sendIncName!, sendingData.sendOpts.forceOverwrite!, sendingData.sendOpts.compressed, sendingData.sendOpts.raw, sendingData.recvHost, sendingData.recvPort, sendingData.recvHostUser, sendingData.mBufferConfig!.size, sendingData.mBufferConfig!.unit], { superuser: 'try', stderr: 'out'});

		const output = await state.promise();
		console.log('sendSnapshot completed');
		return output.stdout;
	} catch (state) {
		console.error(errorString(state));
		return null;
        // throw new Error('Snapshot send failed'); // Throw an error if the operation fails
	}
}

export async function doesDatasetExist(sendingData : SendingDataset) {
    try {
        console.log('sendingData (snapshots.ts - checkDataset):', sendingData);

		const state = useSpawn(['/usr/bin/env', 'python3', '-c', check_dataset_script, sendingData.recvName, sendingData.recvHost, sendingData.recvPort, sendingData.recvHostUser], { superuser: 'try', stderr: 'out'});

		const output = await state.promise();
		console.log(output);
		
		if (output.stdout.includes('True')) {
			return true;
		} else {
			return false;
		}
    } catch (state) {
		console.error(errorString(state));
		return null;
	}
}

export async function doesDatasetHaveSnaps(sendingData : SendingDataset) {
    try {
        console.log('sendingData (snapshots.ts - checkDataset):', sendingData);

		const state = useSpawn(['/usr/bin/env', 'python3', '-c', check_remote_snaps_script, sendingData.recvName, sendingData.recvHost, sendingData.recvPort, sendingData.recvHostUser], { superuser: 'try', stderr: 'out'});

		const output = await state.promise();
		console.log(output);
		
		if (output.stdout.includes('True')) {
			return true;
		} else {
			return false;
		}
    } catch (state) {
		console.error(errorString(state));
		return null;
	}
}

export async function getRecentSnaps(sendingData : SendingDataset) {
    try {
        console.log('sendingData (snapshots.ts - getRecentSnaps):', sendingData);

		const state = useSpawn(['/usr/bin/env', 'python3', '-c', get_recent_snaps_script, sendingData.recvName, sendingData.recvHost, sendingData.recvPort, sendingData.recvHostUser], { superuser: 'try', stderr: 'out'});

		const output = await state.promise();
		console.log(output);
		return output.stdout;

    } catch (state) {
		console.error(errorString(state));
		return null;
	}
}

export async function formatRecentSnaps(sendingData : SendingDataset, snapSnips : SnapSnippet[]) {
    try {
        const rawJSON = await getRecentSnaps(sendingData);

        if (rawJSON) {
            const parsedJSON = (JSON.parse(rawJSON));
            parsedJSON.forEach(snap => {
                if (snap) {
                    console.log('snap:', snap);
                    const snapSnip : SnapSnippet = {
                        name: snap.name,
                        guid: snap.guid,
                        creation: convertTimestampToLocal(convertTimestampFormat(snap.creation)),
                    }
                    console.log('snapSnip after:', snapSnip);
                    snapSnips.push(snapSnip);
                } else {
                    console.log('no recent snaps');
                }
               
            });
        } else {
            console.error("No data received from getRecentSnaps");
        }
        console.log('formatted snapSnips:', snapSnips);
	} catch(error) {
		console.error("An error occurred getting snapSnips:", error);
	}
}
