const cockpit: any = (globalThis as any).cockpit;

const ADMIN_GROUPS = ["wheel", "sudo", "admin"]; // tweak for your distro

// Helper: wait for the permission object to resolve its initial state
function waitForPermission(perm: any): Promise<void> {
    return new Promise(resolve => {
        // If the library has already determined .allowed, resolve on next tick
        if (typeof perm.allowed !== "undefined") {
            resolve();
            return;
        }
        // Otherwise wait for the first 'changed' event
        const onChanged = () => {
            perm.removeEventListener?.("changed", onChanged);
            resolve();
        };
        perm.addEventListener?.("changed", onChanged);
        // Some cockpit versions also expose .watch; fall back to a microtask if events aren't available
        setTimeout(resolve, 0);
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
