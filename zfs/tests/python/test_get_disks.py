import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[2] / "src" / "scripts" / "get-disks.py"
SPEC = importlib.util.spec_from_file_location("cockpit_zfs_get_disks", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class UdevAliasPathsTests(unittest.TestCase):
    def test_preserves_all_by_id_aliases_and_prefers_ata_for_legacy_field(self):
        ata = "/dev/disk/by-id/ata-MODEL_SERIAL_A"
        wwn = "/dev/disk/by-id/wwn-0x5000000000000001"
        result = SimpleNamespace(
            returncode=0,
            stdout=f"DEVLINKS={wwn} {ata} /dev/disk/by-diskseq/12\n",
            stderr="",
        )

        with patch.object(MODULE.subprocess, "run", return_value=result):
            aliases = MODULE._udev_alias_paths("/dev/sdd")

        self.assertEqual(aliases["id_paths"], [ata, wwn])
        self.assertEqual(aliases["id_path"], ata)


if __name__ == "__main__":
    unittest.main()
