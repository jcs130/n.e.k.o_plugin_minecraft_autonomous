"""Select this plugin's packaged Windows dependencies without changing Neko."""

import hashlib
import json
import os
import platform
import shutil
import stat
import sys
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath

_DLL_HANDLES = []


def _members(manifest):
    if manifest.get('schema') != 'neko-mc-platform-python/v1':
        raise ValueError('plugin_python_layer_manifest_invalid')
    files = manifest.get('files')
    if not isinstance(files, dict) or not 1 <= len(files) <= 12000:
        raise ValueError('plugin_python_layer_manifest_invalid')
    for name, entry in files.items():
        parts = PurePosixPath(name).parts
        if (not parts or name != '/'.join(parts) or any(p in {'.', '..'} for p in parts)
                or any(c in name for c in '\\:\x00') or name.startswith('/')
                or not isinstance(entry, dict) or type(entry.get('size')) is not int or entry['size'] < 0
                or len(entry.get('sha256', '')) != 64):
            raise ValueError('plugin_python_layer_manifest_invalid')
    if sum(v['size'] for v in files.values()) > 200 * 1024 * 1024:
        raise ValueError('plugin_python_layer_too_large')
    return files


def _verify(root, files):
    try:
        if root.is_symlink() or getattr(root.lstat(), 'st_file_attributes', 0) & 0x400:
            return False
        actual = set()
        for path in root.rglob('*'):
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                return False
            if path.is_file() and not ('__pycache__' in path.parts and path.suffix == '.pyc'):
                actual.add(path.relative_to(root).as_posix())
        if actual != set(files):
            return False
        for name, expected in files.items():
            path = root
            for part in PurePosixPath(name).parts:
                path = path / part
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                    return False
            if not path.is_file() or info.st_size != expected['size']:
                return False
            with path.open('rb') as source:
                if hashlib.file_digest(source, 'sha256').hexdigest() != expected['sha256']:
                    return False
        return True
    except OSError:
        return False


def _commit_layer(temporary, target, files):
    """Retry only bounded Windows sharing/access races; never replace a cache."""
    delays = (0.05, 0.1, 0.2, 0.4, 0.8)
    for attempt in range(len(delays) + 1):
        try:
            temporary.rename(target)
            return
        except OSError as error:
            # Another probe may have committed exactly the same verified layer.
            if _verify(target, files):
                return
            if target.exists() or getattr(error, 'winerror', None) not in {5, 32, 33} or attempt == len(delays):
                raise
            time.sleep(delays[attempt])


def prepare_layer(assets, cache):
    """Verify fixed resource bytes, then prepare a short, immutable user cache."""
    manifest = json.loads((assets / 'win32-cp311-x64.json').read_text('utf-8'))
    files = _members(manifest)
    archive = assets / 'win32-cp311-x64.zip'
    if archive.is_symlink() or assets.is_symlink():
        raise ValueError('plugin_python_layer_link_forbidden')
    with archive.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if digest != manifest.get('archive_sha256'):
        raise ValueError('plugin_python_layer_integrity_failed')
    cache = Path(cache).absolute()
    if any(p.exists() and (p.is_symlink() or getattr(p.lstat(), 'st_file_attributes', 0) & 0x400)
           for p in (cache, *cache.parents)):
        raise ValueError('plugin_python_layer_link_forbidden')
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / ('w-' + digest[:32])
    if target.exists():
        if target.is_symlink() or not _verify(target, files):
            raise ValueError('plugin_python_cache_integrity_failed: reinstall this plugin resource cache')
        return target
    temporary = Path(tempfile.mkdtemp(prefix='.python-', dir=cache))
    try:
        with zipfile.ZipFile(archive) as packed:
            rows = packed.infolist()
            if len(rows) != len(files) or len({r.filename for r in rows}) != len(rows):
                raise ValueError('plugin_python_layer_members_invalid')
            for row in rows:
                expected = files.get(row.filename)
                if (expected is None or row.file_size != expected['size']
                        or stat.S_ISLNK(row.external_attr >> 16) or row.flag_bits & 1):
                    raise ValueError('plugin_python_layer_members_invalid')
                destination = temporary.joinpath(*PurePosixPath(row.filename).parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with packed.open(row) as source, destination.open('xb') as output:
                    shutil.copyfileobj(source, output)
        if not _verify(temporary, files):
            raise ValueError('plugin_python_layer_integrity_failed')
        _commit_layer(temporary, target, files)
        return target
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def activate():
    if sys.platform != 'win32':
        return None  # Official Linux vendor remains the standard SDK dependency layer.
    if (sys.implementation.name != 'cpython' or sys.version_info[:2] != (3, 11) or sys.maxsize <= 2**32
            or platform.machine().lower() not in {'amd64', 'x86_64'}):
        raise ValueError('minecraft_autonomous requires Neko CPython 3.11 x64 on Windows')
    assets = Path(__file__).parent / 'assets' / 'python-runtime'
    base = os.environ.get('LOCALAPPDATA')
    if not base:
        raise ValueError('plugin_python_cache_unavailable: LOCALAPPDATA is required')
    root = prepare_layer(assets, Path(base) / 'Neko' / 'minecraft-autonomous' / 'py')
    # A plugin runs in its own host child. Do not delete or reload SDK modules;
    # already imported host packages keep their own package paths and ABI pair.
    for relative in ('pywin32_system32', 'win32', 'win32/lib', ''):
        path = root / relative
        if path.is_dir() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
        if relative in {'pywin32_system32', 'win32'} and path.is_dir():
            _DLL_HANDLES.append(os.add_dll_directory(str(path)))
    return root


selected_layer = activate()
