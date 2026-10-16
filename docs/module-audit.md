# ZFS Module Audit and Fixes Record

Date: 2026-10-06

## Scope

Reviewed command generation, disk selection and reporting, pool creation/import,
attach/replace, dataset settings and encryption, snapshot deletion and replication,
refresh coordination, JSON handling, fallback backend parsing, and control-plane IPC.
This is a source review with mocked regression tests, not an exhaustive security
certification or a live-storage integration test. Existing unrelated shared-submodule
changes were left untouched.

## Follow-Up Findings Fixed

### Passphrases Removed from Process Arguments

Create, unlock, change-key, and validation now send passphrases through Cockpit
process stdin. All four Python entrypoints read stdin instead of secret positional
arguments, preserving whitespace. Validation failures return a real boolean false;
the frontend accepts only the exact successful response. Tests inspect argv and
stdin at both ends. Existing encryption exit checks and temporary key-file cleanup
remain in place. This removes argv exposure, not the need to protect process memory,
stdin access, temporary key files, and the host itself.

### Replication No Longer Pre-Deletes the Destination

The recursive `zfs destroy -R` helpers and their calls have been removed. Force
Overwrite uses only native `zfs receive -F`, preserving the incremental baseline
until receive applies the stream. Every sender, mbuffer, and receiver exit is checked;
stderr is drained concurrently, parent pipe handles are closed, and startup failures
terminate and reap launched children. SSH uses a quoted remote command and validated
host/user/port inputs. Progress reaches finished only after every stage succeeds.
The UI propagates failure instead of showing Snapshot Sent and closes its watcher.

**Important:** `-F` remains destructive: ZFS can roll back destination changes and
remove newer snapshots. Receive is not an atomic transaction, and this change does
not guarantee restoration after interruption. It does not promise to replace a
destination's encryption or arbitrarily incompatible dataset tree. Mocked tests cover
local/remote incremental commands and failures in each stage; live recovery is unverified.

### Successful Empty Refreshes Clear Stale Inventory

Successful disk, pool, and dataset discovery swaps the complete scratch inventory,
including an empty pool list. Statistics for removed pools are pruned. Transport,
parser, and backend command failures now have explicit failure responses; loaders
return failure and refresh retains the previous coherent inventory. Backend pool
discovery still falls back from libzfs to CLI, but permission failures no longer
look like no pools. Known no-pools output remains a successful empty result.
Explicit `keepOldOnEmpty: true` remains an opt-in compatibility behavior, not the
default. Tests cover empty replacement, failure retention, shared concurrent refresh,
flag cleanup, retry, malformed lsblk responses, and failed pool queries.

### Reservations Use Actual Usable Root-Dataset Space

The shared manager creates the pool without an estimated reservation, then queries
root-dataset numeric properties through `zfs get -Hp`. Capacity is
`available + used - usedbyrefreservation`, excluding the existing reservation's
accounting inflation. This respects ZFS-reported usable space rather than raw
mirror/RAIDZ or auxiliary-device capacity. Creation, editing, Add-VDev updates, and
displayed percentages use the same basis. Zero disables reservation with `none`;
non-finite percentages and invalid or unsafe-integer byte values are rejected.
The unawaited duplicate wizard reservation call has been removed.

If reservation fails after creation, the error explicitly says the pool already
exists. The wizard refreshes and closes to prevent an accidental repeat creation;
it does not destroy the pool or proceed to child-dataset creation. Set the reservation
and create the desired child dataset separately after resolving the error. Tests
cover mirror/RAIDZ fixtures, large auxiliary devices, zero, invalid values, displayed
percentage, and post-create failure without destructive rollback. Only this repo's
houston-common copy was edited; its source change must be included when syncing the submodule.

### Add-VDev Matches Exported Aliases and Validates Submission

Exported-pool protection now uses the canonical alias/partition matcher instead of
display-name equality. Force checks use `forceAdd.force`, not the always-truthy
options object; this also restores size and replication-level checks. Submission
prepares disks atomically, sends the selected full path, and rejects missing,
duplicate, imported, or unavailable-identifier selections rather than silently
omitting them. Busy state and refresh failures are handled explicitly. A successfully
added VDev is not offered for repeat addition after a reservation update failure.
Tests cover differing by-id aliases, partitions, force override, repeated attempts,
full selected paths, and invalid selections. Force does not bypass imported-disk checks.

### Mixed-Output JSON Parsing Rejects Invalid Discovery

The parser first accepts an entire JSON response, then scans balanced complete
objects/arrays while respecting quoted delimiters and escapes. It no longer extracts
a nested partial object from a truncated array. Discovery accepts only arrays or
valid data/error envelopes; missing, malformed, and failed responses are errors,
not empty inventory. Pool fallback logging goes to stderr. Tests cover bracketed
log prefixes, nesting, escaping, truncation, error envelopes, valid empty responses,
and the actual inventory loaders. For mixed output, the last complete JSON block
wins; stdout should still contain only one payload, and this is not a log protocol.

## Original Disk Detection and Creation Fixes

- Discovery preserves every udev DEVLINKS alias, not just the first by-id path.
  This fixes Micron NVMe namespace/serial versus EUI alias mismatches; Kingston
  devices appeared unaffected only because their selected and stored aliases agreed.
  Alias inventory updates on discovery/refresh, not through a continuous udev watcher.
- Inventory retains aliases and configured by-vdev paths, including NVMe devices.
- Disk matching recognizes alternate by-id/by-path/by-vdev paths, partition suffixes,
  and NVMe namespace names without matching distinct disks by a loose prefix.
- Full-disk lookup returns a copy and supports full or stripped alias names without
  mutating shared inventory; missing disk identifiers no longer throw.
- Leaf statistics remain attached to the actual matched NVMe disk, rather than
  inheriting a mirror's aggregate statistics or failing a second name-only lookup.
- Pool creation sends the selected Hardware Path or Block Device path, independently
  copies autoexpand/autotrim, and prepares disks/vdevs atomically without retry accumulation.
- Final preparation reruns disk, size, replication, and exported-pool checks. Missing,
  duplicate, already-imported, and invalid-path selections fail before any create command.
  Preparation errors notify the user and reset busy state.
- Importable-pool parsing flattens nested replacement groups and single-disk leaves.
  Exported-pool checks recognize aliases without clearing unrelated SMART warnings.

## Findings Fixed in This Audit

- Bulk snapshot deletion now uses literal argument arrays instead of a shell/xargs
  command, reports individual outcomes, and stops scheduling new batches on cancellation.
- Snapshot range batches follow chronological inventory order, not selection order.
- Attach preparation no longer removes existing vdev members with `pop()`.
- Attach and replace send the selected full device path rather than a display basename.
- Attach/replace reject unavailable or already-imported disks, recognize exported-pool
  aliases, and clear busy state after exceptions.
- Numeric zero resets for quota and reservation are sent; reservation resets use
  `none`, not the invalid value `off`. Empty edits do not execute an invalid `zfs set`.
- Partition clearing uses the underlying block-device path, not the bay name.
- Encrypted create/unlock/change-key failures raise errors and preserve temporary-file cleanup.
- Replication startup failures propagate instead of printing an error and exiting successfully.
- Refresh cleanup no longer creates a separate unhandled rejected promise.
- Fallback pool parsing recognizes `logs`/`spares` and preserves nested replacing groups.
- Failed control-plane availability reads close their file handles.

Earlier fixes for creation identifiers, NVMe aliases, leaf statistics, preparation
retries, stale selections, and exported-pool parsing remain covered by the suite.

## Automated Verification

Run `npm test` or `yarn test` at the repository root. Node.js 22.13+ and Python 3
are required. No dependency installation or live Cockpit/ZFS/libzfs/SSH service is
required. CI runs the same command and gates package building on its result.

The JavaScript tests load actual function declarations, remove TypeScript syntax,
and inject mocked transports and reactive state. They are behavior-focused unit
tests, not Vue component mounting tests or full TypeScript typechecks. Syntax checks
parse frontend TypeScript/Vue script blocks and all backend Python scripts without
executing them. Python behavior tests use mocked subprocesses and temporary fixture
key files; all fixture files are cleaned up.

## Integration Gates Still Needed

- A disposable pool using mixed by-id/by-path/by-vdev identifiers, including NVMe namespaces.
- Offline, online, attach, replace, import/export, trim, and scrub on supported ZFS releases.
- Confirmed handling of a successfully empty inventory versus permission/transport failures.
- Encrypted create, wrong-key failure, successful unlock, and key change on disposable datasets.
- KMS provider success/failure and Cockpit privilege escalation in an actual browser session.
- Local and remote replication, interrupted streams, and overwrite recovery on disposable targets.
- Vue rendering, template compilation, full typechecking, and visual/accessibility checks.

## Disposable Replication Acceptance Checks

Run these manually on explicitly designated disposable source/destination datasets,
never a production destination. Automated unit tests do not execute this checklist.

1. Full local send to a new destination; verify data and snapshot identity and success status.
2. Create a common base snapshot, send a later snapshot incrementally with Force Overwrite,
  and verify the baseline is not destroyed before receive.
3. Add a newer destination snapshot and unsnapshotted changes. Confirm a non-forced
  receive rejects divergence; confirm a forced receive performs the documented rollback.
4. Put unrelated descendants and clones on the disposable destination. Confirm there
  is no blanket pre-send deletion; record native receive's actual accept/reject behavior.
5. Repeat full and incremental sends over a real configured SSH target and mbuffer.
6. Interrupt each stage, reject an incompatible destination, and test insufficient space.
  Verify failure notifications, no finished status, no orphaned processes, and the
  destination's recoverable state. Do not assume interrupted receive is atomic.
7. Exercise compressed/raw encrypted streams against supported ZFS versions, including
  incompatible encryption, and confirm Force Overwrite is not presented as encryption replacement.

## Updating This Record

Add subsequent fixes here with their changed behavior, focused tests, and unverified
integration risks. Keep completed fixes separate from outstanding validation gates.