"""Plan 2 input identity and evidence helpers. No installs or device operations."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import zipfile

BLOCK_SIZE = 1024 * 1024
APK_MEMBER = 'Pixel Gun 3D [11.3.1].apk'


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(stream):
    h = hashlib.sha256()
    size = 0
    while block := stream.read(BLOCK_SIZE):
        h.update(block)
        size += len(block)
    return size, h.hexdigest()


def hash_file(path):
    with Path(path).open('rb') as stream:
        size, sha = digest(stream)
    return {'size': size, 'sha256': sha}


def create_run(path, inputs):
    path = Path(path).absolute()
    resolved = path.resolve()
    for source in inputs:
        source = Path(source).resolve()
        if resolved.is_relative_to(source) or source.is_relative_to(resolved):
            raise ValueError('Run overlaps an input tree')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.mkdir(mode=0o700)  # exclusive; never reuse a prior run
    return path.resolve()


def snapshot(base, roots):
    base = Path(base).resolve()
    entries = []
    for root in roots:
        root = Path(root)
        if root.is_symlink():
            raise ValueError('Input symlink is not allowed')
        if not root.exists():
            raise FileNotFoundError(root)
        if not (root.is_file() or root.is_dir()):
            raise ValueError('Input root must be a file or directory')
        paths = [root] if root.is_file() else root.rglob('*')
        for path in paths:
            if path.is_symlink():
                raise ValueError('Input symlink is not allowed')
            if path.is_dir():
                continue
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError('Only regular input files are supported')
            entries.append({'relative_path': path.resolve().relative_to(base).as_posix(),
                            **hash_file(path)})
    entries.sort(key=lambda e: e['relative_path'])
    return {'created_at': utc_now(), 'files': entries, 'file_count': len(entries),
            'total_bytes': sum(e['size'] for e in entries)}


def safe_members(archive):
    seen = set()
    for info in archive.infolist():
        path = PurePosixPath(info.filename)
        if (path.is_absolute() or '..' in path.parts or '\\' in info.filename
                or str(path) != info.filename.rstrip('/') or not path.parts):
            raise ValueError('Unsafe archive member')
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise ValueError('Archive symlink is not allowed')
        if info.filename in seen:
            raise ValueError('Duplicate archive member')
        seen.add(info.filename)
        yield info


def extract_apk(archive_path, output_path):
    output_path = Path(output_path)
    if output_path.exists() or output_path.is_symlink():
        raise FileExistsError(output_path)
    with zipfile.ZipFile(archive_path) as archive:
        entries = list(safe_members(archive))
        if len(entries) != 1 or entries[0].filename != APK_MEMBER or entries[0].is_dir():
            raise ValueError('Unexpected APK archive members')
        temp = output_path.with_name(output_path.name + '.partial')
        owned_temp = temp.open('xb')  # cleanup only a temporary we created
        try:
            with owned_temp as dst, archive.open(entries[0]) as src:
                while block := src.read(BLOCK_SIZE):
                    dst.write(block)
            result = hash_file(temp)
            if result['size'] != entries[0].file_size:
                raise ValueError('Incomplete APK extraction')
            # Publish exclusively, without hardlinks or overwriting an output.
            with temp.open('rb') as src, output_path.open('xb') as dst:
                while block := src.read(BLOCK_SIZE):
                    dst.write(block)
        finally:
            temp.unlink(missing_ok=True)
    return {'member': APK_MEMBER, **result}


def compare_archive(path, unpacked_records):
    if not zipfile.is_zipfile(path):
        return {'status': 'BLOCKED', 'reason': 'Original is not a readable ZIP container'}
    expected = {e['relative_path']: e for e in unpacked_records}
    actual = {}
    with zipfile.ZipFile(path) as archive:
        for info in safe_members(archive):
            if info.is_dir():
                continue
            with archive.open(info) as stream:
                size, sha = digest(stream)  # ZIP CRC checked on read
            actual[info.filename] = {'size': size, 'sha256': sha}
    missing = sorted(actual.keys() - expected.keys())
    extra = sorted(expected.keys() - actual.keys())
    different = sorted(k for k in actual.keys() & expected.keys()
                       if any(actual[k][field] != expected[k][field] for field in ('size', 'sha256')))
    return {'status': 'PASS' if not (missing or extra or different) else 'PARTIAL',
            'archive_members': len(actual), 'unpacked_files': len(expected),
            'missing_unpacked': missing, 'extra_unpacked': extra, 'different': different}


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def record_command(run, name, argv, *, timeout=600, cwd=None, env=None):
    """Full private stdout/stderr and machine-readable exit/timing evidence."""
    logs = Path(run) / 'logs'
    if any(p.exists() or p.is_symlink() for p in
           (logs / (name + suffix) for suffix in ('.stdout', '.stderr', '.json'))):
        raise FileExistsError('Command evidence already exists')
    logs.mkdir(exist_ok=True, mode=0o700)
    started = utc_now()
    with (logs / (name + '.stdout')).open('xb') as out, (logs / (name + '.stderr')).open('xb') as err:
        try:
            result = subprocess.run([str(x) for x in argv], stdout=out, stderr=err,
                                    cwd=cwd, env=env, timeout=timeout, check=False)
            rc, timed_out = result.returncode, False
        except subprocess.TimeoutExpired:
            rc, timed_out = 124, True
    record = {'argv': [str(x) for x in argv], 'started_at': started, 'ended_at': utc_now(),
              'returncode': rc, 'timeout': timed_out, 'cwd': str(cwd) if cwd else None}
    write_json(logs / (name + '.json'), record)
    return record
