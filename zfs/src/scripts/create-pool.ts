import { useSpawn, errorString } from '@45drives/cockpit-helpers';
// @ts-ignore
import script_py from "./create-pool.py?raw";

//['/usr/bin/env', 'python3', '-c', script, ...args ]

export async function createPool() {

}

// export async function getPools() {
//     try {
//         const state = useSpawn(['/usr/bin/env', 'python3', '-c', script_py], { superuser: 'try' });
//         const pools = (await state.promise()).stdout;
//         return pools;
//     } catch (state) {
//         console.error(errorString(state));
//         return null;
//     }
// }
