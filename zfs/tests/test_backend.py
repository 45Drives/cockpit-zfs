import ast
import contextlib
import io
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch


SCRIPTS = Path(__file__).resolve().parents[1] / "src" / "scripts"


def discovery_functions():
    tree = ast.parse((SCRIPTS / "get-disks.py").read_text())
    names = {"_dev_base", "_udev_alias_paths", "_enrich_alias_paths"}
    body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    namespace = {"subprocess": subprocess, "re": re}
    exec(compile(ast.Module(body=body, type_ignores=[]), "get-disks.py", "exec"), namespace)
    return namespace


class DiscoveryTests(unittest.TestCase):
    def test_aliases_are_preserved_and_enriched(self):
        functions = discovery_functions()
        links = [
            "/dev/disk/by-id/nvme-eui.000000000000000100a075244c9236bc",
            "/dev/disk/by-id/nvme-Micron_7450_MTFDKBG1T9TFR_24174C9236BC",
            "/dev/disk/by-path/pci-0000:41:00.0-nvme-1",
        ]
        response = subprocess.CompletedProcess([], 0, "DEVLINKS=" + " ".join(links), "")
        with patch.object(subprocess, "run", return_value=response):
            disks = functions["_enrich_alias_paths"]([{"sd_path": "/dev/nvme1n1"}])
        self.assertEqual(disks[0]["id_path"], links[0])
        self.assertEqual(disks[0]["alias_paths"], links)

    def test_missing_or_failed_udev_is_safe(self):
        functions = discovery_functions()
        for response in [subprocess.CompletedProcess([], 1, "", "missing"), subprocess.CompletedProcess([], 0, "", "")]:
            with self.subTest(response=response), patch.object(subprocess, "run", return_value=response):
                self.assertEqual(functions["_udev_alias_paths"]("/dev/nvme1n1"), {})

    def test_partition_normalization_preserves_nvme_namespace(self):
        normalize = discovery_functions()["_dev_base"]
        for path, expected in [
            ("/dev/nvme1n1p2", "/dev/nvme1n1"),
            ("/dev/sdab2", "/dev/sdab"),
            ("/dev/disk/by-id/nvme-Micron_serial_1-part1", "/dev/disk/by-id/nvme-Micron_serial_1"),
        ]:
            with self.subTest(path=path):
                self.assertEqual(normalize(path), expected)

    def test_lsblk_failures_and_malformed_output_are_not_empty_success(self):
        tree = ast.parse((SCRIPTS / "get-disks.py").read_text())
        body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "get_lsblk_disks"]
        import json
        namespace = {"subprocess": subprocess, "json": json, "logger": MagicMock(), "_map_by_vdev": lambda: {}, "_fanout_smart_and_udev": lambda candidates: ({}, {})}
        exec(compile(ast.Module(body=body, type_ignores=[]), "get-disks.py", "exec"), namespace)
        for response in [subprocess.CompletedProcess([], 1, "", "permission denied"), subprocess.CompletedProcess([], 0, "{}", "")]:
            with self.subTest(response=response), patch.object(subprocess, "run", return_value=response):
                with self.assertRaises(RuntimeError):
                    namespace["get_lsblk_disks"]()
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{"blockdevices":[]}', "")):
            self.assertEqual(namespace["get_lsblk_disks"](), [])


class PoolParserTests(unittest.TestCase):
    def test_no_pools_and_failed_pool_query_are_distinct(self):
        tree = ast.parse((SCRIPTS / "get-pools.py").read_text())
        body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_pools_from_zpool_list_min"]
        namespace = {"subprocess": subprocess, "logger": MagicMock()}
        exec(compile(ast.Module(body=body, type_ignores=[]), "get-pools.py", "exec"), namespace)
        query = namespace["_pools_from_zpool_list_min"]
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "no pools available\n")):
            self.assertEqual(query(), [])
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "permission denied")):
            with self.assertRaisesRegex(RuntimeError, "permission denied"):
                query()

    def test_fallback_keeps_nested_replacements_and_plural_sections(self):
                tree = ast.parse((SCRIPTS / "get-pools.py").read_text())
                body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_parse_vdevs_from_status"]
                namespace = {"subprocess": subprocess, "os": os, "logger": MagicMock()}
                exec(compile(ast.Module(body=body, type_ignores=[]), "get-pools.py", "exec"), namespace)
                status = """  pool: tank
 state: ONLINE
config:

                NAME                                      STATE     READ WRITE CKSUM
                tank                                      ONLINE       0     0     0
                    mirror-0                                ONLINE       0     0     0
                        replacing-0                           ONLINE       0     0     0
                            /dev/disk/by-id/old-part1            OFFLINE      1     0     0
                            /dev/disk/by-id/new-part1            ONLINE       0     0     0
                        /dev/disk/by-id/other-part1            ONLINE       0     0     0
                    /dev/nvme2n1                             ONLINE       0     0     0
                logs
                    /dev/nvme3n1                             ONLINE       0     0     0
                special
                    mirror-1                                ONLINE       0     0     0
                        /dev/nvme4n1                           ONLINE       0     0     0
                        /dev/nvme5n1                           ONLINE       0     0     0
                cache
                    /dev/nvme6n1                             ONLINE       0     0     0
                spares
                    /dev/nvme7n1                             AVAIL        0     0     0

errors: No known data errors
"""
                with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, status, "")):
                        groups = namespace["_parse_vdevs_from_status"]("tank")
                self.assertEqual(len(groups["data"]), 2)
                mirror = groups["data"][0]
                self.assertEqual(mirror["children"][0]["type"], "replacing")
                self.assertEqual(len(mirror["children"][0]["children"]), 2)
                self.assertEqual(mirror["children"][1]["path"], "/dev/disk/by-id/other-part1")
                self.assertEqual(groups["log"][0]["path"], "/dev/nvme3n1")
                self.assertEqual(len(groups["special"][0]["children"]), 2)
                self.assertEqual(groups["cache"][0]["path"], "/dev/nvme6n1")
                self.assertEqual(groups["spare"][0]["status"], "AVAIL")


class EncryptionTests(unittest.TestCase):
    OPERATIONS = [
        ("unlock-encrypted-dataset.py", "unlock_locked_dataset", ["pool/data", "test-fixture-key"]),
        ("change-encrypted-key.py", "change_key", ["pool/data", "test-fixture-key"]),
        ("create-encrypted-dataset.py", "create_encrypted_dataset", [
            "atime=on", "casesensitivity=sensitive", "compression=lz4", "dedup=off",
            "dnodesize=auto", "xattr=sa", "recordsize=128K", "readonly=off", "quota=none",
            "encryption=aes-256-gcm", "keyformat=passphrase", "keylocation=prompt", "pool/data", "test-fixture-key",
        ]),
    ]

    def test_failed_zfs_commands_raise_and_remove_key_files(self):
        for filename, name, arguments in self.OPERATIONS:
            with self.subTest(operation=name):
                function = runpy.run_path(str(SCRIPTS / filename))[name]
                process = MagicMock(returncode=1)
                process.communicate.return_value = (b"", b"permission denied")
                with patch.object(subprocess, "Popen", return_value=process), patch.object(os, "remove", wraps=os.remove) as remove, contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(Exception, "permission denied"):
                        function(*arguments)
                    remove.assert_called_once()
                    self.assertFalse(Path(remove.call_args.args[0]).exists())

    def test_successful_zfs_commands_remove_key_files(self):
        for filename, name, arguments in self.OPERATIONS:
            with self.subTest(operation=name):
                function = runpy.run_path(str(SCRIPTS / filename))[name]
                process = MagicMock(returncode=0)
                process.communicate.return_value = (b"", b"")
                with patch.object(subprocess, "Popen", return_value=process), patch.object(os, "remove", wraps=os.remove) as remove, contextlib.redirect_stdout(io.StringIO()):
                    function(*arguments)
                    remove.assert_called_once()
                    self.assertFalse(Path(remove.call_args.args[0]).exists())
                self.assertEqual(process.communicate.call_args.kwargs["input"], b"test-fixture-key")

    def test_encryption_entrypoints_read_secrets_only_from_stdin(self):
        operations = [
            ("unlock-encrypted-dataset.py", "unlock_locked_dataset", ["pool/data"]),
            ("change-encrypted-key.py", "change_key", ["pool/data"]),
            ("encryption-key-validation.py", "check_key", ["pool/data"]),
            ("create-encrypted-dataset.py", "create_encrypted_dataset", ["zfs"] + self.OPERATIONS[2][2][:-1]),
        ]
        secret = ' test-fixture-key "quoted" '
        for filename, operation, arguments in operations:
            with self.subTest(operation=operation):
                main = runpy.run_path(str(SCRIPTS / filename))["main"]
                called = MagicMock(return_value=True)
                with patch.dict(main.__globals__, {operation: called}), patch.object(sys, "argv", [filename] + arguments), patch.object(sys, "stdin", io.StringIO(secret)), contextlib.redirect_stdout(io.StringIO()):
                    main()
                self.assertEqual(called.call_args.args[-1], secret)


class SyntaxTests(unittest.TestCase):
    def test_backend_scripts_compile_without_execution(self):
        for script in SCRIPTS.glob("*.py"):
            with self.subTest(script=script.name):
                compile(script.read_text(), str(script), "exec")


class ReplicationTests(unittest.TestCase):
    def test_pipeline_preserves_destination_and_checks_every_process(self):
        from unittest.mock import mock_open
        send = runpy.run_path(str(SCRIPTS / "send-snapshot.py"))["send_dataset"]
        for remote in (False, True):
            for failed in (None, "sender", "receiver", "mbuffer"):
                if failed == "mbuffer" and not remote:
                    continue
                with self.subTest(remote=remote, failed=failed):
                    calls = []
                    def spawn(argv, **options):
                        label = "sender" if argv[:2] == ["zfs", "send"] else "mbuffer" if argv[0] == "mbuffer" else "receiver"
                        process = MagicMock(stdout=io.BytesIO(), stderr=io.BytesIO((label + " diagnostic\n").encode()))
                        process.wait.return_value = 1 if failed == label else 0
                        process.poll.return_value = process.wait.return_value
                        calls.append((argv, options, process))
                        return process
                    with patch.object(subprocess, "Popen", side_effect=spawn), patch.object(os.path, "exists", return_value=False), patch("builtins.open", mock_open()), contextlib.redirect_stdout(io.StringIO()):
                        options = {"recvHost": "receiver.invalid", "recvHostUser": "fixture", "recvPort": 22} if remote else {}
                        if failed:
                            with self.assertRaisesRegex(RuntimeError, failed + " failed"):
                                send("pool/data@new", "backup/data", "pool/data@base", forceOverwrite=True, **options)
                        else:
                            send("pool/data@new", "backup/data", "pool/data@base", forceOverwrite=True, **options)
                    self.assertEqual(len(calls), 3 if remote else 2)
                    self.assertEqual(calls[0][0], ["zfs", "send", "-v", "-i", "pool/data@base", "pool/data@new"])
                    self.assertNotIn("destroy", " ".join(str(call[0]) for call in calls))
                    receive = calls[-1][0]
                    self.assertEqual(receive, ["ssh", "-p", "22", "fixture@receiver.invalid", "zfs recv -v -F backup/data"] if remote else ["zfs", "recv", "-v", "-F", "backup/data"])
                    for argv, options, process in calls:
                        process.wait.assert_called()
                        self.assertTrue(process.stderr.closed)
                    self.assertTrue(calls[0][2].stdout.closed)

    def test_spawn_failure_is_not_reported_as_success(self):
        send = runpy.run_path(str(SCRIPTS / "send-snapshot.py"))["send_dataset"]
        with patch.object(subprocess, "Popen", side_effect=OSError("zfs executable missing")), patch.object(os.path, "exists", return_value=False), patch("builtins.open", __import__('unittest.mock', fromlist=['mock_open']).mock_open()), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(OSError, "zfs executable missing"):
                send("pool/data@snap", "backup/data")


if __name__ == "__main__":
    unittest.main()