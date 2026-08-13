import { legacy } from '@45drives/houston-common-lib';
import { convertTimestampToLocal, convertTimestampFormat } from '../composables/helpers';
// @ts-ignore
import get_snapshots_script from "../scripts/get-snapshots.py?raw";
// @ts-ignore
import send_dataset_script from "../scripts/send-snapshot.py?raw";
// @ts-ignore
import check_dataset_script from"../scripts/check-dataset.py?raw";
// @ts-ignore
import get_recent_snaps_script from"../scripts/find-last-common-snap.py?raw";
// @ts-ignore
import check_remote_snaps_script from"../scripts/check-remote-snapshots.py?raw";
import { NewSnapshot, SendingDataset, SnapSnippet } from '../types';

//['/usr/bin/env', 'python3', '-c', script, ...args ]
const {errorString, useSpawn } = legacy;
export async function getSnapshots() {
    try {
        // Use the script without any dataset name to get all snapshots
        const argument = `all`;

        const state = useSpawn(['/usr/bin/env', 'python3', '-c', get_snapshots_script, argument], { superuser: 'try' });
        const snapshots = (await state.promise()).stdout;
        return JSON.parse(snapshots!); 
    } catch (error) {
        console.error("Error fetching all snapshots:", error);
        return null;
    }
}


export async function getSnapshotsOfDataset(datasetName) {
    try {
        // Use the script with datasetName to get snapshots for that specific dataset
        const argument = `dataset:${datasetName}`;
        const command = ['/usr/bin/env', 'python3','-c', get_snapshots_script, argument]; // Pass the script and argument separately
        const state = useSpawn(command, { superuser: 'try' });
        const snapshots = (await state.promise()).stdout;
        return JSON.parse(snapshots!); // Assuming the snapshots are in JSON format
    } catch (error) {
        console.error(`Error fetching snapshots for dataset "${datasetName}":`, error);
        return null;
    }
}



export async function getSnapshotsOfPool(poolName) {
    try {
        const argument = `pool:${poolName}`;
        // Use the script with datasetName to get snapshots for that specific dataset
        const command = ['/usr/bin/env', 'python3','-c', get_snapshots_script, argument];
        const state = useSpawn(command, { superuser: 'try' });
        const snapshots = (await state.promise()).stdout;
        return JSON.parse(snapshots!); // Assuming the snapshots are in JSON format
    } catch (error) {
        console.error(`Error fetching snapshots for dataset "${poolName}":`, error);
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

        // console.log("****create cmdString: *****\n" , cmdString);
			
        const state = useSpawn(cmdString);
        const output = await state.promise();
        // console.log(output)
        return output.stdout;
    } catch (state) {
        const errorMessage = errorString(state);
        console.error(errorMessage);
        return { error: errorMessage };
    }
}

export async function destroySnapshot(snapshotName, destroyChildrenSameName, destroyAllChildren) {
    try {
        let cmdString = ['zfs', 'destroy'];

        if (destroyChildrenSameName) {
            cmdString.push('-r');
        }

        if (destroyAllChildren) {
            cmdString.push('-R');
        }

        cmdString.push(snapshotName)

        // console.log("****destroy cmdString: *****\n" , cmdString);
			
        const state = useSpawn(cmdString);
        const output = await state.promise();
        // console.log(output)
        return output.stdout;
    } catch (state) {
        const errorMessage = errorString(state);
        console.error(errorMessage);
        return { error: errorMessage };
    }
}

/**
 * Check if snapshots form a contiguous range within a dataset
 * @param snapshotNames - Array of full snapshot names (pool/dataset@snap)
 * @param allSnapshots - All snapshots in the dataset (sorted chronologically)
 * @returns Range info if contiguous, null otherwise
 */
function detectSnapshotRange(
    snapshotNames: string[], 
    allSnapshots: string[]
): { dataset: string, start: string, end: string } | null {
    if (snapshotNames.length < 2) return null;

    // Extract dataset and snap names
    const parseSnapshot = (fullName: string) => {
        const atIndex = fullName.lastIndexOf('@');
        return {
            dataset: fullName.substring(0, atIndex),
            snap: fullName.substring(atIndex + 1)
        };
    };

    const parsed = snapshotNames.map(parseSnapshot);
    const dataset = parsed[0].dataset;

    // Check all snapshots are from same dataset
    if (!parsed.every(p => p.dataset === dataset)) return null;

    // Get indices of selected snapshots in the full sorted list
    const indices = snapshotNames
        .map(name => allSnapshots.indexOf(name))
        .filter(idx => idx !== -1)
        .sort((a, b) => a - b);

    if (indices.length !== snapshotNames.length) return null;

    // Check if indices are contiguous
    for (let i = 1; i < indices.length; i++) {
        if (indices[i] !== indices[i - 1] + 1) return null;
    }

    // Return range
    const startSnap = parseSnapshot(allSnapshots[indices[0]]).snap;
    const endSnap = parseSnapshot(allSnapshots[indices[indices.length - 1]]).snap;

    return { dataset, start: startSnap, end: endSnap };
}

/**
 * Destroy multiple snapshots efficiently using ZFS native range syntax when possible
 * @param snapshotNames - Array of snapshot names to destroy
 * @param allSnapshots - All snapshots in dataset (for range detection, optional)
 * @param onProgress - Optional callback for progress updates (current, total)
 * @param cancelSignal - Ref to check if operation should be cancelled
 * @returns Object with arrays of succeeded and failed snapshots and cancelled flag
 */
export async function destroySnapshotsBulk(
    snapshotNames: string[], 
    allSnapshots?: string[],
    onProgress?: (current, total, currentSnapshot) => void,
    cancelSignal?: { value: boolean }
): Promise<{ succeeded: string[], failed: Array<{ snapshot: string, error: string }>, cancelled: boolean }> {
    const succeeded: string[] = [];
    const failed: Array<{ snapshot: string, error: string }> = [];
    const total = snapshotNames.length;

    try {
        // Try to use native ZFS range syntax if snapshots are contiguous
        const range = allSnapshots ? detectSnapshotRange(snapshotNames, allSnapshots) : null;

        if (range) {
            // Use native ZFS range deletion in batches for progress feedback
            // Batch size: destroy this many snapshots per range command to show progress
            const RANGE_BATCH_SIZE = 100;
            console.log(`Using ZFS range deletion: ${range.dataset}@${range.start}%${range.end}`);
            
            if (snapshotNames.length <= RANGE_BATCH_SIZE) {
                // Small enough to do in one shot
                if (onProgress) {
                    onProgress(0, total, `${range.dataset}@${range.start}%${range.end}`);
                }

                try {
                    const cmdString = ['zfs', 'destroy', `${range.dataset}@${range.start}%${range.end}`];
                    const state = useSpawn(cmdString);
                    await state.promise();
                    succeeded.push(...snapshotNames);
                    
                    if (onProgress) {
                        onProgress(total, total, null);
                    }
                } catch (state: any) {
                    const errorMessage = errorString(state);
                    snapshotNames.forEach(snap => {
                        failed.push({ snapshot: snap, error: errorMessage });
                    });
                }
            } else {
                // Large range - batch into smaller ranges for progress updates
                console.log(`Batching ${snapshotNames.length} snapshots into ranges of ${RANGE_BATCH_SIZE}`);
                let processed = 0;
                
                for (let i = 0; i < snapshotNames.length; i += RANGE_BATCH_SIZE) {
                    // Check for cancellation
                    if (cancelSignal?.value) {
                        console.log('Bulk destroy cancelled by user');
                        return { succeeded, failed, cancelled: true };
                    }

                    const batchSnaps = snapshotNames.slice(i, i + RANGE_BATCH_SIZE);
                    const batchStart = batchSnaps[0].split('@')[1];
                    const batchEnd = batchSnaps[batchSnaps.length - 1].split('@')[1];
                    const rangeCmd = `${range.dataset}@${batchStart}%${batchEnd}`;
                    
                    if (onProgress) {
                        onProgress(processed, total, rangeCmd);
                    }

                    try {
                        const cmdString = ['zfs', 'destroy', rangeCmd];
                        const state = useSpawn(cmdString);
                        await state.promise();
                        succeeded.push(...batchSnaps);
                    } catch (state: any) {
                        const errorMessage = errorString(state);
                        batchSnaps.forEach(snap => {
                            failed.push({ snapshot: snap, error: errorMessage });
                        });
                    }
                    
                    processed += batchSnaps.length;
                }

                if (onProgress) {
                    onProgress(processed, total, null);
                }
            }
        } else {
            // Use xargs piping approach for non-contiguous snapshots
            console.log(`Using xargs approach for ${snapshotNames.length} snapshots`);
            
            if (onProgress) {
                onProgress(0, total, 'Starting bulk destroy...');
            }

            // Create a single piped command: echo snapshots | xargs -n1 -P10 zfs destroy
            const snapshotList = snapshotNames.join('\n');
            const cmdString = [
                'bash', '-c',
                `echo '${snapshotList}' | xargs -n1 -P10 zfs destroy`
            ];

            try {
                // Show periodic progress updates during xargs execution
                // Since we can't track individual completions, we'll estimate
                let estimatedProgress = 0;
                const progressInterval = setInterval(() => {
                    if (estimatedProgress < total * 0.95) {
                        estimatedProgress += Math.max(1, Math.floor(total / 20)); // ~5% increments
                        if (onProgress) {
                            onProgress(estimatedProgress, total, 'Processing...');
                        }
                    }
                }, 500); // Update every 500ms

                const state = useSpawn(cmdString);
                await state.promise();
                
                clearInterval(progressInterval);
                
                // All succeeded
                succeeded.push(...snapshotNames);
                
                if (onProgress) {
                    onProgress(total, total, null);
                }
            } catch (state: any) {
                // With xargs, if it fails we don't know which ones failed
                // Fall back to individual deletion to get granular results
                console.log('xargs failed, falling back to individual deletion');
                let processed = 0;
                
                for (const snapshot of snapshotNames) {
                    // Check for cancellation
                    if (cancelSignal?.value) {
                        console.log('Bulk destroy cancelled by user');
                        return { succeeded, failed, cancelled: true };
                    }

                    if (onProgress) {
                        onProgress(processed, total, snapshot);
                    }

                    try {
                        const state = useSpawn(['zfs', 'destroy', snapshot]);
                        await state.promise();
                        succeeded.push(snapshot);
                    } catch (state: any) {
                        failed.push({ snapshot, error: errorString(state) });
                    }
                    
                    processed++;
                }

                if (onProgress) {
                    onProgress(processed, total, null);
                }
            }
        }
    } catch (error: any) {
        // Unexpected error
        snapshotNames.forEach(snap => {
            if (!succeeded.includes(snap)) {
                failed.push({ snapshot: snap, error: error.message || 'Unexpected error' });
            }
        });
    }

    return { succeeded, failed, cancelled: false };
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

        // console.log("****rollback cmdString: *****\n" , cmdString);
			
        const state = useSpawn(cmdString);
        const output = await state.promise();
        // console.log(output)
        return output.stdout;
    } catch (state) {
        const errorMessage = errorString(state);
        console.error(errorMessage);
        return { error: errorMessage };
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

        // console.log("****rename cmdString: *****\n" , cmdString);
			
        const state = useSpawn(cmdString);
        const output = await state.promise();
        // console.log(output)
        return output.stdout;
    } catch (state) {
        const errorMessage = errorString(state);
        console.error(errorMessage);
        return { error: errorMessage };
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

        // console.log("****clone cmdString: *****\n" , cmdString);
			
        const state = useSpawn(cmdString);
        const output = await state.promise();
        // console.log(output)
        return output.stdout;
    } catch (state) {
        const errorMessage = errorString(state);
        console.error(errorMessage);
        return { error: errorMessage };
    }
}

export async function sendSnapshot(sendingData : SendingDataset) {
	try {
        // console.log('sendingData (snapshots.ts - sendSnapshot):', sendingData);

		const state = useSpawn(['/usr/bin/env', 'python3', '-c', send_dataset_script, sendingData.sendName, sendingData.recvName, sendingData.sendIncName!, sendingData.sendOpts.forceOverwrite!, sendingData.sendOpts.compressed, sendingData.sendOpts.raw, sendingData.recvHost, sendingData.recvPort, sendingData.recvHostUser, sendingData.mBufferConfig!.size, sendingData.mBufferConfig!.unit], { superuser: 'try' });

		const output = await state.promise();
		// console.log('sendSnapshot completed');
		return output.stdout;
	} catch (state) {
		const errorMessage = errorString(state);
		console.error(errorMessage);
		return { error: errorMessage };
        // throw new Error('Snapshot send failed'); // Throw an error if the operation fails
	}
}

export async function doesDatasetExist(sendingData : SendingDataset) {
    try {
        // console.log('sendingData (snapshots.ts - checkDataset - doesDatasetExist):', sendingData);

		const state = useSpawn(['/usr/bin/env', 'python3', '-c', check_dataset_script, sendingData.recvName, sendingData.recvHost, sendingData.recvPort, sendingData.recvHostUser], { superuser: 'try'});

		const output = await state.promise();
		// console.log(output);
		
		if (output.stdout!.includes('True')) {
			return true;
		} else {
			return false;
		}
    } catch (state) {
		const errorMessage = errorString(state);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function doesDatasetHaveSnaps(sendingData : SendingDataset) {
    try {
        // console.log('sendingData (snapshots.ts - checkDataset - doesDatasetHaveSnaps):', sendingData);

		const state = useSpawn(['/usr/bin/env', 'python3', '-c', check_remote_snaps_script, sendingData.recvName, sendingData.recvHost, sendingData.recvPort, sendingData.recvHostUser], { superuser: 'try' });

		const output = await state.promise();
		// console.log(output);
		
		if (output.stdout!.includes('True')) {
			return true;
		} else {
			return false;
		}
    } catch (state) {
		const errorMessage = errorString(state);
		console.error(errorMessage);
		return { error: errorMessage };
	}
}

export async function getRecentSnaps(sendingData : SendingDataset) {
    try {
        // console.log('sendingData (snapshots.ts - getRecentSnaps):', sendingData);

		const state = useSpawn(['/usr/bin/env', 'python3', '-c', get_recent_snaps_script, sendingData.recvName, sendingData.recvHost, sendingData.recvPort, sendingData.recvHostUser], { superuser: 'try' });

		const output = await state.promise();
		// console.log(output);
		return output.stdout;

    } catch (state) {
		const errorMessage = errorString(state);
		console.error(errorMessage);
        return JSON.stringify({ error: errorMessage }); 
	}
}

export async function formatRecentSnaps(sendingData : SendingDataset, snapSnips : SnapSnippet[]) {
    try {
        const rawJSON = await getRecentSnaps(sendingData);

        if (rawJSON) {
            const parsedJSON = (JSON.parse(rawJSON));
            parsedJSON.forEach(snap => {
                if (snap) {
                    // console.log('snap:', snap);
                    const snapSnip : SnapSnippet = {
                        name: snap.name,
                        guid: snap.guid,
                        creation: convertTimestampToLocal(convertTimestampFormat(snap.creation)),
                    }
                    // console.log('snapSnip after:', snapSnip);
                    snapSnips.push(snapSnip);
                } else {
                    console.log('no recent snaps');
                }
               
            });
        } else {
            console.error("No data received from getRecentSnaps");
        }
        // console.log('formatted snapSnips:', snapSnips);
	} catch(error) {
		console.error("An error occurred getting snapSnips:", error);
        // const errorMessage = errorString(error);
        // console.error(errorMessage);
        // return { error: errorMessage };
	}
}
