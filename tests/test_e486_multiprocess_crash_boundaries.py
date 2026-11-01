"""E486: POSIX multi-process publication and process-death boundaries (research only)."""
import multiprocessing as mp
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from e476_registry_contract import EpochDefinition, EpochRegistry
from e477_pinned_registry_snapshot import load_pinned, publish_once, sha256, snapshot_bytes

NS = bytes(range(1, 17))


def _payload(index):
    registry = EpochRegistry(NS)
    assert registry.register(7, EpochDefinition(f"origin-{index}", "nanoseconds", "monotonic", "none"))
    return snapshot_bytes(registry)


def _race_worker(target, barrier, results, index):
    try:
        barrier.wait(timeout=10)
        publish_once(Path(target), _payload(index))
        results.put(("published", index))
    except FileExistsError:
        results.put(("already_exists", index))
    except BaseException as exc:
        results.put(("error", f"{type(exc).__name__}: {exc}"))


def _crash_worker(target, stage):
    # Exit deliberately bypasses Python finally, unlike injected OSError.
    import e477_pinned_registry_snapshot as module
    if stage == "before_link":
        def crash_link(*_args):
            os._exit(41)
        module.os.link = crash_link
    else:
        real_fsync = os.fsync
        calls = 0
        def crash_after_link(fd):
            nonlocal calls
            calls += 1
            if calls == 2:
                os._exit(42)
            return real_fsync(fd)
        module.os.fsync = crash_after_link
    publish_once(Path(target), _payload(0))
    os._exit(99)  # Should never reach here.


@unittest.skipUnless(os.name == "posix" and "fork" in mp.get_all_start_methods() and hasattr(os, "O_DIRECTORY"), "POSIX fork and directory fsync required")
class MultiprocessCrashBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.ctx = mp.get_context("fork")

    def _join(self, processes):
        for process in processes:
            process.join(timeout=15)
        stuck = [p for p in processes if p.is_alive()]
        for process in stuck:
            process.terminate()
        for process in stuck:
            process.join(timeout=5)
        self.assertFalse(stuck, "child processes exceeded timeout")

    def test_eight_independent_processes_one_valid_winner(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "snapshot.json"
            barrier = self.ctx.Barrier(8)
            results = self.ctx.Queue()
            processes = [self.ctx.Process(target=_race_worker, args=(str(target), barrier, results, i)) for i in range(8)]
            try:
                for process in processes:
                    process.start()
                self._join(processes)
                self.assertTrue(all(p.exitcode == 0 for p in processes))
                outcomes = [results.get(timeout=5) for _ in processes]
                self.assertEqual([kind for kind, _ in outcomes].count("published"), 1, outcomes)
                self.assertEqual([kind for kind, _ in outcomes].count("already_exists"), 7, outcomes)
                winner = next(i for kind, i in outcomes if kind == "published")
                data = target.read_bytes()
                self.assertEqual(data, _payload(winner))
                self.assertEqual(snapshot_bytes(load_pinned(data, sha256(data), NS)), data)
                self.assertEqual(sorted(p.name for p in Path(folder).iterdir()), ["snapshot.json"])
            finally:
                results.close()
                results.join_thread()

    def test_process_death_before_link_leaves_orphan_temp_no_target(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "snapshot.json"
            child = self.ctx.Process(target=_crash_worker, args=(str(target), "before_link"))
            child.start()
            self._join([child])
            self.assertEqual(child.exitcode, 41)
            self.assertFalse(target.exists())
            leftovers = list(Path(folder).glob(".e477-*"))
            self.assertEqual(len(leftovers), 1)
            self.assertEqual(leftovers[0].read_bytes(), _payload(0))

    def test_process_death_after_link_leaves_visible_target_and_orphan_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "snapshot.json"
            child = self.ctx.Process(target=_crash_worker, args=(str(target), "after_link"))
            child.start()
            self._join([child])
            self.assertEqual(child.exitcode, 42)
            data = target.read_bytes()
            self.assertEqual(data, _payload(0))
            self.assertEqual(snapshot_bytes(load_pinned(data, sha256(data), NS)), data)
            leftovers = list(Path(folder).glob(".e477-*"))
            self.assertEqual(len(leftovers), 1)
            self.assertEqual(leftovers[0].read_bytes(), data)
            self.assertNotEqual(leftovers[0], target)


if __name__ == "__main__":
    unittest.main(verbosity=2)
