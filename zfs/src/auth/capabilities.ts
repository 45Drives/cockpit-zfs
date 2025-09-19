const cockpit: any = (globalThis as any).cockpit;

const ADMIN_GROUPS = ["wheel", "sudo", "admin"]; // tweak for your distro

export async function getUserCaps() {
    const u = await cockpit.user(); // { name, id, groups, ... }
    const groups: string[] = Array.isArray(u.groups) ? u.groups : [];
    const isRoot = u.name === "root" || u.id === 0;
    const isAdminGroup = groups.some(g => ADMIN_GROUPS.includes(g));
    return { username: u.name, uid: u.id, groups, isRoot, isAdminGroup };
}
