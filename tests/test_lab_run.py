"""Synthetic input-preservation tests; no game artifacts or devices needed."""
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

try:
    from tools.lab_run import create_run, snapshot, extract_apk, compare_archive
except ImportError:
    create_run = snapshot = extract_apk = compare_archive = None


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'inputs'
        self.source.mkdir()
        self.file = self.source / 'payload'
        self.file.write_bytes(b'abc')

    def require(self, function):
        self.assertIsNotNone(function, 'Plan 2 functionality absent')

    def archive(self, entries):
        path = self.root / 'archive.zip'
        with zipfile.ZipFile(path, 'w') as z:
            for name, payload in entries:
                z.writestr(name, payload)
        return path

    def test_create_private_run_and_reject_reuse(self):
        self.require(create_run)
        run = self.root / 'runs/one'
        create_run(run, [self.source])
        self.assertEqual(stat.S_IMODE(run.stat().st_mode), 0o700)
        with self.assertRaises(FileExistsError):
            create_run(run, [self.source])

    def test_reject_input_destination_and_symlink_alias(self):
        self.require(create_run)
        alias = self.root / 'alias'
        alias.symlink_to(self.source, target_is_directory=True)
        for path in (self.source / 'run', alias / 'run'):
            with self.assertRaises(ValueError):
                create_run(path, [self.source])
        self.assertEqual(list(self.source.iterdir()), [self.file])

    def test_snapshot_records_relative_size_and_independent_known_hash(self):
        self.require(snapshot)
        result = snapshot(self.root, [self.source])
        self.assertEqual(result['files'], [{'relative_path': 'inputs/payload', 'size': 3,
            'sha256': 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'}])
        self.assertEqual(self.file.read_bytes(), b'abc')

    def test_snapshot_missing_root_is_not_silently_empty(self):
        self.require(snapshot)
        with self.assertRaises((ValueError, FileNotFoundError)):
            snapshot(self.root, [self.root / 'missing'])

    def test_snapshot_rejects_symlink_escape(self):
        self.require(snapshot)
        (self.source / 'leak').symlink_to(self.root / 'outside')
        with self.assertRaises(ValueError):
            snapshot(self.root, [self.source])

    def test_extract_only_exact_member_to_exclusive_output(self):
        self.require(extract_apk)
        archive = self.archive([('Pixel Gun 3D [11.3.1].apk', b'abc')])
        out = self.root / 'out.apk'
        record = extract_apk(archive, out)
        self.assertEqual(out.read_bytes(), b'abc')
        self.assertEqual(record['sha256'], hashlib.sha256(b'abc').hexdigest())
        with self.assertRaises(FileExistsError):
            extract_apk(archive, out)
        self.assertEqual(out.read_bytes(), b'abc')

    def test_existing_partial_extraction_is_not_deleted(self):
        self.require(extract_apk)
        archive = self.archive([('Pixel Gun 3D [11.3.1].apk', b'abc')])
        out = self.root / 'out.apk'
        partial = self.root / 'out.apk.partial'
        partial.write_bytes(b'sentinel')
        with self.assertRaises(FileExistsError):
            extract_apk(archive, out)
        self.assertEqual(partial.read_bytes(), b'sentinel')
        self.assertFalse(out.exists())

    def test_unexpected_or_traversal_member_never_published(self):
        self.require(extract_apk)
        for name in ('wrong.apk', '../Pixel Gun 3D [11.3.1].apk'):
            archive = self.archive([(name, b'abc')])
            out = self.root / 'out.apk'
            with self.assertRaises(ValueError):
                extract_apk(archive, out)
            self.assertFalse(out.exists())

    def test_duplicate_exact_apk_rejected(self):
        self.require(extract_apk)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            archive = self.archive([('Pixel Gun 3D [11.3.1].apk', b'a'),
                                    ('Pixel Gun 3D [11.3.1].apk', b'b')])
        with self.assertRaises(ValueError):
            extract_apk(archive, self.root / 'out.apk')
        self.assertFalse((self.root / 'out.apk').exists())

    def test_archive_comparison_reports_missing_extra_and_different(self):
        self.require(compare_archive)
        archive = self.archive([('payload', b'abc'), ('missing', b'z')])
        records = [dict(relative_path='payload', size=3, sha256=hashlib.sha256(b'bad').hexdigest()),
                   dict(relative_path='extra', size=1, sha256=hashlib.sha256(b'x').hexdigest())]
        result = compare_archive(archive, records)
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['missing_unpacked'], ['missing'])
        self.assertEqual(result['extra_unpacked'], ['extra'])
        self.assertEqual(result['different'], ['payload'])

    def test_commands_capture_exit_stdout_stderr_without_reuse(self):
        import sys
        from tools import lab_run
        command = getattr(lab_run, 'record_command', None)
        self.require(command)
        run = self.root / 'run'
        run.mkdir()
        argv = [sys.executable, '-c', 'import sys; print("out"); print("err", file=sys.stderr); sys.exit(7)']
        result = command(run, 'sample', argv)
        self.assertEqual(result['returncode'], 7)
        self.assertEqual((run / 'logs/sample.stdout').read_text(), 'out\n')
        self.assertEqual((run / 'logs/sample.stderr').read_text(), 'err\n')
        self.assertEqual(json.loads((run / 'logs/sample.json').read_text())['argv'], argv)
        with self.assertRaises(FileExistsError):
            command(run, 'sample', argv)

    def test_existing_command_metadata_prevents_execution(self):
        import sys
        from tools import lab_run
        command = getattr(lab_run, 'record_command', None)
        self.require(command)
        run = self.root / 'run'
        (run / 'logs').mkdir(parents=True)
        metadata = run / 'logs/sample.json'
        metadata.write_text('sentinel')
        marker = self.root / 'executed'
        argv = [sys.executable, '-c', 'from pathlib import Path; import sys; Path(sys.argv[1]).touch()', str(marker)]
        with self.assertRaises(FileExistsError):
            command(run, 'sample', argv)
        self.assertFalse(marker.exists(), 'Command reran despite existing evidence')
        self.assertEqual(metadata.read_text(), 'sentinel')

    def test_commands_timeout_is_not_success(self):
        import sys
        from tools import lab_run
        command = getattr(lab_run, 'record_command', None)
        self.require(command)
        run = self.root / 'run'
        run.mkdir()
        result = command(run, 'timeout', [sys.executable, '-c', 'import time; time.sleep(5)'], timeout=0.05)
        self.assertEqual(result['returncode'], 124)
        self.assertTrue(result['timeout'])

    def test_non_zip_not_assumed_equivalent(self):
        self.require(compare_archive)
        result = compare_archive(self.file, [])
        self.assertEqual(result['status'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
