"""Hand-built fixtures catch ordering, ambiguity, escape and invalid publication."""
import hashlib
import json
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
import unittest

try:
    from tools.prepare_unity_data import prepare_data
except ImportError:
    prepare_data = None


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.apk = self.root / 'apk'
        self.obb = self.root / 'obb'
        self.apk.mkdir()
        self.obb.mkdir()
        self.out = self.root / 'output/Data'
        self.manifest = self.root / 'output/manifest.json'

    def put(self, root, name, payload=b'abc'):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return path

    def before(self):
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for root in [self.apk, self.obb] for p in root.rglob('*')
                if p.is_file() and not p.is_symlink()}

    def execute(self, output=None, manifest=None):
        self.assertIsNotNone(prepare_data, 'Staging functionality absent')
        return prepare_data(self.apk, self.obb, output or self.out, manifest or self.manifest)

    def rejected(self, output=None, manifest=None):
        before = self.before()
        with self.assertRaises((ValueError, FileExistsError)):
            self.execute(output, manifest)
        self.assertEqual(self.before(), before, 'Source bytes changed on error')
        self.assertFalse(self.out.exists(), 'Invalid output published')
        self.assertFalse(self.manifest.exists(), 'Invalid manifest published')

    def test_numeric_indices_zero_to_twelve_not_lexical(self):
        for i in range(13):
            self.put(self.apk, f'asset.split{i}', f'{i},'.encode())
        before = self.before()
        result = self.execute()
        self.assertEqual((self.out / 'asset').read_bytes(), b'0,1,2,3,4,5,6,7,8,9,10,11,12,')
        self.assertEqual(list(self.out.glob('*.split*')), [])
        self.assertEqual(result['split_groups'], 1)
        self.assertEqual(result['fragments'], 13)
        self.assertEqual(self.before(), before)

    def test_missing_intermediate_fragment(self):
        self.put(self.apk, 'asset.split0')
        self.put(self.apk, 'asset.split2')
        self.rejected()

    def test_sequence_must_start_at_zero(self):
        self.put(self.apk, 'asset.split1')
        self.rejected()

    def test_duplicate_numeric_index_with_different_spelling(self):
        for name in ['asset.split0', 'asset.split1', 'asset.split01']:
            self.put(self.apk, name)
        self.rejected()

    def test_apk_obb_path_collision(self):
        self.put(self.apk, 'Managed/script.dll')
        self.put(self.obb, 'Managed/script.dll', b'different')
        self.rejected()

    def test_base_file_and_fragments_are_ambiguous(self):
        self.put(self.apk, 'asset')
        self.put(self.obb, 'asset.split0')
        self.rejected()

    def test_output_in_input_is_rejected(self):
        self.put(self.apk, 'file')
        self.rejected(output=self.apk / 'generated')
        self.assertFalse((self.apk / 'generated').exists())

    def test_dotdot_destination_cannot_bypass_input_guard(self):
        (self.root / 'outside').mkdir()
        escaped = self.root / 'outside/../apk/generated'
        self.rejected(output=escaped)
        self.assertFalse((self.apk / 'generated').exists())

    def test_manifest_in_input_is_rejected(self):
        self.put(self.apk, 'file')
        self.rejected(manifest=self.obb / 'manifest.json')

    def test_output_symlink_alias_is_rejected(self):
        (self.root / 'alias').symlink_to(self.apk, target_is_directory=True)
        self.rejected(output=self.root / 'alias/new')

    def test_input_symlink_escape_is_rejected(self):
        outside = self.put(self.root, 'outside', b'secret')
        (self.apk / 'leak').symlink_to(outside)
        self.rejected()
        self.assertEqual(outside.read_bytes(), b'secret')

    def test_existing_output_is_not_overwritten(self):
        self.out.mkdir(parents=True)
        sentinel = self.put(self.out, 'sentinel')
        with self.assertRaises(FileExistsError):
            self.execute()
        self.assertEqual(sentinel.read_bytes(), b'abc')
        self.assertFalse(self.manifest.exists())

    def test_existing_manifest_is_not_overwritten(self):
        self.manifest.parent.mkdir()
        self.manifest.write_text('sentinel')
        with self.assertRaises(FileExistsError):
            self.execute()
        self.assertEqual(self.manifest.read_text(), 'sentinel')
        self.assertFalse(self.out.exists())

    def test_managed_sidecar_hashes_provenance_and_independent_copy(self):
        dll = self.put(self.apk, 'Managed/script.dll', b'abc')
        self.put(self.obb, 'asset.resource', b'FSB5payload')
        before = self.before()
        self.execute()
        doc = json.loads(self.manifest.read_text())
        records = {r['relative_path']: r for r in doc['files']}
        self.assertTrue(doc['complete'])
        self.assertEqual(doc['status'], 'PASS')
        self.assertEqual(records['Managed/script.dll']['sha256'],
                         'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
        self.assertEqual(records['Managed/script.dll']['sources'][0]['relative_path'], 'Managed/script.dll')
        copied = self.out / 'Managed/script.dll'
        self.assertNotEqual(copied.stat().st_ino, dll.stat().st_ino)
        self.assertEqual(copied.stat().st_nlink, 1)
        self.assertEqual(self.before(), before)
        self.assertEqual(stat.S_IMODE(self.out.stat().st_mode), 0o700)

    def unity15(self, size):
        return struct.pack('>4I', 12, size, 15, 40) + b'\x00\x00\x00\x00' + b'5.3.7p1\x00' + b'\x00' * 36

    def test_unity15_wrong_file_size_is_not_published(self):
        self.put(self.apk, 'level0', self.unity15(999))
        self.rejected()

    def test_unity15_matching_header_is_size_checked_not_semantic(self):
        self.put(self.apk, 'level0', self.unity15(64))
        self.execute()
        record = json.loads(self.manifest.read_text())['files'][0]
        self.assertEqual(record['kind'], 'unity_serialized')
        self.assertEqual(record['validation']['declared_size'], 64)
        self.assertFalse(record['validation']['semantic_objects_verified'])

    def test_fsb5_fragments_not_interpreted_as_unity_serialized(self):
        self.put(self.obb, 'sharedassets94.resource.split0', b'FSB5')
        self.put(self.obb, 'sharedassets94.resource.split1', b'payload')
        result = self.execute()
        record = json.loads(self.manifest.read_text())['files'][0]
        self.assertEqual(record['kind'], 'fsb5')
        self.assertNotIn('declared_size', record['validation'])
        self.assertEqual(result['serialized_split_groups'], 0)
        self.assertEqual(result['fsb5_split_groups'], 1)

    def test_file_directory_collision_is_not_published(self):
        self.put(self.apk, 'path')
        self.put(self.obb, 'path/child')
        self.rejected()

    def test_cli_validation_failure_is_nonzero_and_no_output(self):
        self.put(self.apk, 'bad.split2')
        cli = Path(__file__).resolve().parents[1] / 'tools/prepare_unity_data.py'
        self.assertTrue(cli.exists(), 'CLI functionality absent')
        result = subprocess.run([sys.executable, str(cli), '--apk-data', str(self.apk),
             '--obb-data', str(self.obb), '--output-data', str(self.out), '--manifest', str(self.manifest)],
             capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.manifest.exists())


if __name__ == '__main__':
    unittest.main()
