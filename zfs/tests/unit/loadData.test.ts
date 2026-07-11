import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@45drives/houston-common-lib", () => ({ legacy: {} }));
vi.mock("../../src/composables/pools", () => ({ getPools: vi.fn() }));
vi.mock("../../src/composables/disks", () => ({ getDisks: vi.fn() }));
vi.mock("../../src/composables/datasets", () => ({ getDatasets: vi.fn() }));
vi.mock("../../src/composables/snapshots", () => ({
  getSnapshots: vi.fn(),
  getSnapshotsOfDataset: vi.fn(),
  getSnapshotsOfPool: vi.fn(),
}));
vi.mock("../../src/composables/scan", () => ({
  getDiskStats: vi.fn(),
  getScanGroup: vi.fn(),
}));

import { loadDisksExtraData } from "../../src/composables/loadData";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("loadDisksExtraData", () => {
  it("does not report a matched by-id alias as missing from the disk inventory", async () => {
    const ata = "/dev/disk/by-id/ata-MODEL_SERIAL_A";
    const wwn = "/dev/disk/by-id/wwn-0x5000000000000001";
    const disk = {
      name: "sda",
      type: "HDD",
      sd_path: "/dev/sda",
      phy_path: "/dev/disk/by-path/pci-0000:58:00.0-ata-2",
      vdev_path: "N/A",
      id_path: ata,
      id_paths: [ata, wwn],
      path: "/dev/sda",
      guid: "",
      stats: {},
    };
    const usedDisk = {
      path: `${wwn}-part1`,
      guid: "12345",
      stats: { readErrors: 0, writeErrors: 0, checksumErrors: 0 },
    };
    const pools = [{ vdevs: [{ stats: {}, disks: [usedDisk] }] }];
    const error = vi.spyOn(console, "error").mockImplementation(() => {});

    await loadDisksExtraData([disk], pools);

    expect(error).not.toHaveBeenCalledWith(
      "Original disk not found in the disks array",
    );
    expect(disk).toMatchObject({
      guid: usedDisk.guid,
      path: usedDisk.path,
      stats: usedDisk.stats,
    });
  });
});
