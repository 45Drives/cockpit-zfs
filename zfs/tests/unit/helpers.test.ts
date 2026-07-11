import { describe, expect, it, vi } from "vitest";

vi.mock("@45drives/houston-common-lib", () => ({ legacy: {} }));

import {
  convertTimestampToLocal,
  matchDiskByVdevOrPath,
} from "../../src/composables/helpers";

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

describe("convertTimestampToLocal", () => {
  it("treats a timezone-aware space-separated value like its ISO equivalent", () => {
    expect(convertTimestampToLocal("2026-07-10 14:43:27+00:00")).toBe(
      convertTimestampToLocal("2026-07-10T14:43:27Z"),
    );
  });

  it("retains the existing UTC assumption for a naive scan timestamp", () => {
    expect(convertTimestampToLocal("2026-07-10 14:43:27")).toBe(
      convertTimestampToLocal("2026-07-10T14:43:27Z"),
    );
  });

  it.each(["", "not-a-date", null, undefined])(
    "returns N/A for invalid input %p",
    (value) => expect(convertTimestampToLocal(value as any)).toBe("N/A"),
  );
});
