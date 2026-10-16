import argparse
import json
import os
import re
import shlex
import subprocess
import threading


def send_dataset(sendName, recvName, sendName2="", forceOverwrite=False, compressed=False, raw=False, recvHost="", recvPort=22, recvHostUser="", mBufferSize=1, mBufferUnit="G"):
    if not recvName or recvName.startswith("-") or "@" in recvName:
        raise ValueError("Invalid receiving dataset name")
    if not sendName or sendName.startswith("-") or "@" not in sendName:
        raise ValueError("Invalid sending snapshot name")
    if sendName2 and (sendName2.startswith("-") or "@" not in sendName2):
        raise ValueError("Invalid incremental snapshot name")
    port = str(recvPort)
    if recvHost:
        if not re.fullmatch(r"[A-Za-z0-9_.:-]+", recvHost) or recvHost.startswith("-"):
            raise ValueError("Invalid receiving host")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", recvHostUser) or recvHostUser.startswith("-"):
            raise ValueError("Invalid receiving user")
        if not port.isdigit() or not 1 <= int(port) <= 65535:
            raise ValueError("Invalid receiving port")
        if not re.fullmatch(r"\d+(?:\.\d+)?", str(mBufferSize)) or float(mBufferSize) <= 0 or mBufferUnit not in ("K", "M", "G", "T"):
            raise ValueError("Invalid mbuffer size")

    file_path = "full_output.json"
    progress = {"snapshot": sendName, "status": "ongoing", "sent": None, "totalSize": None}
    processes = []
    readers = []
    errors = []

    def write_progress():
        with open(file_path, "w") as output:
            output.write(json.dumps(progress) + "\n")

    def drain(process, label):
        try:
            for line in iter(process.stderr.readline, b""):
                text = line.decode("utf-8", errors="replace")
                process.diagnostics.append(text)
                if len(process.diagnostics) > 100:
                    del process.diagnostics[0]
                if label == "sender":
                    total = re.search(r"estimated size is ([\d.]+[KMGT]?)", text)
                    if total:
                        progress["totalSize"] = total.group(1)
                    sent = re.search(r"\d+:\d+:\d+\s+([\d.]+[KMGT]?)\s+(.+)", text)
                    if sent:
                        progress["sent"] = sent.group(1)
                        progress["snapshot"] = sent.group(2).strip()
                        write_progress()
        except Exception as error:
            errors.append(error)
        finally:
            process.stderr.close()

    def launch(argv, label, **options):
        process = subprocess.Popen(argv, stderr=subprocess.PIPE, **options)
        process.diagnostics = []
        processes.append((label, process))
        reader = threading.Thread(target=drain, args=(process, label), daemon=True)
        readers.append(reader)
        reader.start()
        return process

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        send_cmd = ["zfs", "send", "-v"]
        if compressed:
            send_cmd.append("-Lce")
        if raw:
            send_cmd.append("-w")
        if sendName2:
            send_cmd.extend(["-i", sendName2])
        send_cmd.append(sendName)
        sender = launch(send_cmd, "sender", stdout=subprocess.PIPE)
        upstream = sender
        if recvHost:
            upstream = launch(["mbuffer", "-s", "256k", "-m", str(mBufferSize) + mBufferUnit], "mbuffer", stdin=sender.stdout, stdout=subprocess.PIPE)
            sender.stdout.close()
        recv_cmd = ["zfs", "recv", "-v"]
        if forceOverwrite:
            recv_cmd.append("-F")
        recv_cmd.append(recvName)
        if recvHost:
            recv_cmd = ["ssh", "-p", port, recvHostUser + "@" + recvHost, shlex.join(recv_cmd)]
        launch(recv_cmd, "receiver", stdin=upstream.stdout, stdout=subprocess.DEVNULL)
        upstream.stdout.close()
        failures = []
        for label, process in reversed(processes):
            if process.wait() != 0:
                failures.append((label, process))
        for reader in readers:
            reader.join()
        if failures:
            raise RuntimeError("; ".join(label + " failed: " + "".join(process.diagnostics).strip() for label, process in failures))
        if errors:
            raise errors[0]
        progress["status"] = "finished"
        write_progress()
        print(json.dumps(progress))
    except Exception:
        for label, process in reversed(processes):
            if process.poll() is None:
                process.terminate()
        for label, process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            if process.stdout is not None:
                process.stdout.close()
        for reader in readers:
            reader.join()
        progress["status"] = "failed"
        try:
            write_progress()
        except OSError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser(description="Send ZFS snapshot")
    parser.add_argument("sendName")
    parser.add_argument("recvName")
    parser.add_argument("sendName2")
    parser.add_argument("forceOverwrite")
    parser.add_argument("compressed")
    parser.add_argument("raw")
    parser.add_argument("recvHost")
    parser.add_argument("recvPort")
    parser.add_argument("recvHostUser")
    parser.add_argument("mBufferSize")
    parser.add_argument("mBufferUnit")
    args = parser.parse_args()
    send_dataset(args.sendName, args.recvName, args.sendName2,
                 args.forceOverwrite.lower() == "true", args.compressed.lower() == "true",
                 args.raw.lower() == "true", args.recvHost, args.recvPort,
                 args.recvHostUser, args.mBufferSize, args.mBufferUnit)


if __name__ == "__main__":
    main()