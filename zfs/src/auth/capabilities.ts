const cockpit: any = (globalThis as any).cockpit;

const ADMIN_GROUPS = ["wheel", "sudo", "admin"]; // tweak for your distro

export async function getUserCaps() {
    const perm = await cockpit.permission({ admin: true });
    return {
        username: perm.user.name,
        uid: perm.user.id,
        groups: perm.user.groups,
        isRoot: perm.is_superuser,
        isAdminGroup: perm.allowed,
    };
}
