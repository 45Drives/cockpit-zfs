const cockpit: any = (globalThis as any).cockpit;

const ADMIN_GROUPS = ["wheel", "sudo", "admin"]; // tweak for your distro

// Helper: wait for the permission object to resolve its initial state.
// Cockpit sets .allowed to null while pending, then true/false once resolved.
function waitForPermission(perm: any): Promise<void> {
    return new Promise(resolve => {
        // Already determined (true or false, not null/undefined)
        if (perm.allowed != null) {
            resolve();
            return;
        }
        let settled = false;
        const settle = () => {
            if (settled) return;
            settled = true;
            perm.removeEventListener?.("changed", onChanged);
            clearTimeout(fallbackTimer);
            resolve();
        };
        // Wait for the 'changed' event that fires once polkit resolves
        const onChanged = () => settle();
        perm.addEventListener?.("changed", onChanged);
        // Fallback in case the changed event never fires (some cockpit versions)
        const fallbackTimer = setTimeout(settle, 3000);
    });
}

export async function getUserCaps() {
    // Get user info (this is where name/id/groups come from)
    const user = await cockpit.user(); // => { name, id, groups, ... }

    // Create a permission object for “admin” actions
    const perm = cockpit.permission({ admin: true });

    // Give the permission object a beat to populate .allowed (handles async refresh)
    await waitForPermission(perm);

    const groups: string[] = Array.isArray(user.groups) ? user.groups : [];
    const isRoot = user.name === "root" || user.id === 0;

    // Two ways to consider “admin”:
    // 1) Via Cockpit’s permission resolution (preferred)
    // 2) Fallback to group membership (helps on distros without polkit mapping)
    const isAdminByPermission = !!perm.allowed;
    const isAdminByGroup = groups.some(g => ADMIN_GROUPS.includes(g));

    return {
        username: user.name,
        uid: user.id,
        groups,
        isRoot,
        isAdminGroup: isAdminByPermission || isAdminByGroup,
    };
}
