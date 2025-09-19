import { ref } from 'vue';
import { getImportablePools, getImportableDestroyedPools } from "./pools";
import { VDev } from '@45drives/houston-common-lib';
import { ImportablePoolData } from '../types';
import { safeParse } from '../utils/json';

// const vDevs = ref<ImportablePoolvDevData[]>([]);
const vDevs = ref<VDev[]>([]);
const errors: string[] = [];

export function parseImportVDevData(vDev, poolName, vDevType) {
    try {
        // console.log('vDevData Importing:', vDev);
        const vDevData : VDev = {
            name: vDev.name,
            type: vDevType,
            status: vDev.status,
            guid: vDev.guid,
            stats: vDev.stats,
            disks: vDev.children,
            poolName: poolName,
            selectedDisks: [],
            // console.log("loaded Disks:", allDisks);
        }

        vDevs.value.push(vDevData);

    } catch (error) {
        // Handle any errors that may occur during the asynchronous operation
        console.error("An error occurred getting vdevs for Importable pools:", error);
    }
}

export async function loadImportablePools(importablePools, allDisks, existingPools) {
    try {
        const rawJSON = await getImportablePools();
        // const parsedJSON = JSON.parse(rawJSON!);
        const parsedJSON = safeParse<any[]>(rawJSON, []);
        // console.log('Importable Pools JSON:', parsedJSON);

        //loops through pool JSON
        for (let i = 0; i < parsedJSON.length; i++) {
            //calls parse function for each type of VDev that could be in the Pool, then pushes the VDev data to VDev array
			parsedJSON[i].groups.data.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'data'));
			parsedJSON[i].groups.cache.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'cache'));
			parsedJSON[i].groups.dedup.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'dedup'));
			parsedJSON[i].groups.log.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'log'));
			parsedJSON[i].groups.spare.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'spare'));
			parsedJSON[i].groups.special.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'special'));
            
            //adds pool data from JSON into pool data object, pushes into array 
            const poolData : ImportablePoolData = {
                name: parsedJSON[i].name,
                status: parsedJSON[i].status,
                guid: parsedJSON[i].guid,
                properties: parsedJSON[i].properties,
                scan: parsedJSON[i].scan,
                vdevs: vDevs.value,
                isDestroyed: false,
				errors: errors,
            }
           // console.log("ImportablePoolData", i , ": ", poolData);
            importablePools.push(poolData);
            vDevs.value = [];
        }
            
        // console.log("loaded Importable Pools:", importablePools);

        // await loadDisksExtraData(allDisks.value, existingPools.value);

        // console.log("loaded Disks:", allDisks);

    } catch (error) {
        // Handle any errors that may occur during the asynchronous operation
        console.error("An error occurred getting Importable pools:", error);
    }
}

export async function loadImportableDestroyedPools(importablePools, allDisks, existingPools) {
    try {
		const rawJSON = await getImportableDestroyedPools();
		// const parsedJSON = JSON.parse(rawJSON!);
        const parsedJSON = safeParse<any[]>(rawJSON, []);
		// console.log('Destroyed Pools JSON:', parsedJSON);
		
		for (let i = 0; i < parsedJSON.length; i++) {
			//calls parse function for each type of VDev that could be in the Pool, then pushes the VDev data to VDev array
			parsedJSON[i].groups.data.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'data'));
			parsedJSON[i].groups.cache.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'cache'));
			parsedJSON[i].groups.dedup.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'dedup'));
			parsedJSON[i].groups.log.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'log'));
			parsedJSON[i].groups.spare.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'spare'));
			parsedJSON[i].groups.special.forEach(vDev => parseImportVDevData(vDev, parsedJSON[i].name, 'special'));
            
            const poolData : ImportablePoolData = {
                name: parsedJSON[i].name,
                status: parsedJSON[i].status,
                guid: parsedJSON[i].guid,
                properties: parsedJSON[i].properties,
                scan: parsedJSON[i].scan,
                vdevs: vDevs.value,
                isDestroyed: true,
				errors: errors,
            }
           // console.log("DestroyedImportablePoolData", i , ": ", poolData);
            importablePools.push(poolData);
            vDevs.value = [];
		}
            
        console.log("loaded Importable Destroyed Pools:", importablePools);

        // await loadDisksExtraData(allDisks.value, existingPools.value);

        // console.log("loaded Disks:", allDisks);

    } catch (error) {
        // Handle any errors that may occur during the asynchronous operation
        console.error("An error occurred getting destroyed importable pools:", error);
    }
}

