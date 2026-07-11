import { describe, expect, it, vi } from "vitest";

vi.mock("@45drives/houston-common-lib", () => ({ legacy: {} }));

import { matchDiskByVdevOrPath } from "../../src/composables/helpers";

describe("matchDiskByVdevOrPath", () => {
  it("matches a partitioned ATA ZFS path through any equivalent by-id alias", () => {
    const ata = "/dev/disk/by-id/ata-MODEL_SERIAL_A";
    const disk = {
      name: "sdd",
      sd_path: "/dev/sdd",
      phy_path: "/dev/disk/by-path/pci-0000:58:00.0-ata-2",
      vdev_path: "N/A",
      id_path: "/dev/disk/by-id/wwn-0x5000000000000001",
      id_paths: [
        "/dev/disk/by-id/wwn-0x5000000000000001",
        ata,
      ],
    } as any;

    expect(matchDiskByVdevOrPath([disk], `${ata}-part1`)).toBe(disk);
  });
});
