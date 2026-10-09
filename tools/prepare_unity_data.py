"""Build an independent APK/OBB Data view, with numeric splits and provenance.

Only header/size consistency is checked, NOT semantic object integrity.
Existing outputs, ambiguous paths, symlinks and incomplete splits are rejected.
Run in a private, single-writer directory; input trees must remain immutable.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import tempfile

BLOCK_SIZE = 1024 * 1024
SPLIT = re.compile(r'^(.*)\.split([0-9]+)$')


def _no_symlinks(path):
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError(f'Symlink path rejected: {path}')


def _validate(path):
    size = path.stat().st_size
    with path.open('rb') as stream:
        header = stream.read(128)
    validation = {'status': 'PASS', 'semantic_objects_verified': False}
    if header.startswith(b'FSB5'):
        return 'fsb5', {**validation, 'scope': 'signature only; audio not decoded'}
    if len(header) >= 20:
        metadata_size, declared_size, version, data_offset = struct.unpack('>4I', header[:16])
        if version == 15:
            if (declared_size != size or metadata_size > size - 20
                    or data_offset < 20 or data_offset > size or header[16] not in (0, 1)):
                raise ValueError(f'Invalid Unity v15 header/size: {path.name}')
            return 'unity_serialized', {**validation, 'scope': 'header and file size only',
                'format_version': version, 'declared_size': declared_size,
                'unity_version': header[20:].split(b'\x00', 1)[0].decode('ascii', errors='replace')}
    return 'opaque', {**validation, 'scope': 'copied bytes/hash only; format not validated'}


def prepare_data(apk_data: Path, obb_data: Path, output_data: Path, manifest_path: Path) -> dict:
    apk_data, obb_data, output_data, manifest_path = map(
        lambda p: Path(p).absolute(), (apk_data, obb_data, output_data, manifest_path))
    for path in [apk_data, obb_data, output_data, manifest_path]:
        _no_symlinks(path)
    apk_data, obb_data, output_data, manifest_path = map(
        lambda p: p.resolve(), (apk_data, obb_data, output_data, manifest_path))
    for source in [apk_data, obb_data]:
        if not source.is_dir():
            raise ValueError(f'Input directory missing: {source}')
        for dest in [output_data, manifest_path]:
            if dest.is_relative_to(source) or source.is_relative_to(dest):
                raise ValueError('Destination overlaps input tree')
    if manifest_path.is_relative_to(output_data) or output_data.is_relative_to(manifest_path):
        raise ValueError('Manifest must be separate from Data tree')
    if output_data.exists() or manifest_path.exists():
        raise FileExistsError('Output or manifest already exists')

    paths = {}
    for role, source in [('apk', apk_data), ('obb', obb_data)]:
        for path in sorted(source.rglob('*')):
            if path.is_symlink():
                raise ValueError(f'Input symlink rejected: {path}')
            if path.is_dir():
                continue
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError('Only regular source files are supported')
            rel = path.relative_to(source).as_posix()
            if rel in paths:
                raise ValueError(f'APK/OBB collision: {rel}')
            paths[rel] = (role, path)

    groups, plain = {}, {}
    for rel, source in paths.items():
        match = SPLIT.fullmatch(rel)
        if match:
            base, index = match[1], int(match[2])
            fragments = groups.setdefault(base, {})
            if index in fragments:
                raise ValueError(f'Duplicate split index: {rel}')
            fragments[index] = (rel, *source)
        else:
            plain[rel] = [(rel, *source)]
    for base, fragments in groups.items():
        if base in plain:
            raise ValueError(f'Base file and splits both exist: {base}')
        if sorted(fragments) != list(range(len(fragments))):
            raise ValueError(f'Incomplete split sequence: {base}')
        plain[base] = [fragments[i] for i in range(len(fragments))]
    for rel in plain:
        if any(p.as_posix() in plain for p in Path(rel).parents if p != Path('.')):
            raise ValueError(f'File/directory collision: {rel}')

    output_data.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    files = []
    # Nothing final is published until all input files have been copied/validated.
    with tempfile.TemporaryDirectory(prefix='.data-', dir=output_data.parent) as temporary:
        stage = Path(temporary) / 'Data'
        stage.mkdir(mode=0o700)
        for rel, sources in sorted(plain.items()):
            target = stage / rel
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            sources_record = []
            total_hash = hashlib.sha256()
            size = 0
            with target.open('xb') as out:
                for source_rel, role, source in sources:
                    h, source_size = hashlib.sha256(), 0
                    with source.open('rb') as stream:
                        while block := stream.read(BLOCK_SIZE):
                            out.write(block)
                            total_hash.update(block)
                            h.update(block)
                            source_size += len(block)
                            size += len(block)
                    sources_record.append({'tree': role, 'relative_path': source_rel,
                                           'size': source_size, 'sha256': h.hexdigest()})
            kind, validation = _validate(target)
            files.append({'relative_path': rel, 'sources': sources_record, 'kind': kind,
                          'size': size, 'sha256': total_hash.hexdigest(), 'validation': validation})
        summary = {'files': len(files), 'bytes': sum(f['size'] for f in files),
                   'split_groups': len(groups), 'fragments': sum(len(g) for g in groups.values()),
                   'serialized_split_groups': sum(f['relative_path'] in groups and f['kind'] == 'unity_serialized' for f in files),
                   'fsb5_split_groups': sum(f['relative_path'] in groups and f['kind'] == 'fsb5' for f in files)}
        # Reserve the final name exclusively. Private single-writer run is required.
        output_data.mkdir(mode=0o700)
        for child in stage.iterdir():
            child.rename(output_data / child.name)
        manifest_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with manifest_path.open('x', encoding='utf-8') as stream:
            json.dump({'complete': True, 'status': 'PASS', 'summary': summary, 'files': files}, stream, indent=2)
            stream.write('\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ['apk-data', 'obb-data', 'output-data', 'manifest']:
        parser.add_argument('--' + option, required=True, type=Path)
    args = parser.parse_args()
    try:
        result = prepare_data(args.apk_data, args.obb_data, args.output_data, args.manifest)
    except (OSError, ValueError) as error:
        parser.exit(1, f'BLOCKED: {error}\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
