"""Optional client profiles never distribute credentials, game/server data or wrong-loader mods."""

import json
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import pytest


@pytest.mark.parametrize('loader', ['21.1.252', '21.1.265'])
@pytest.mark.parametrize('kind', ['human', 'eye'])
def test_optional_client_is_a_small_verified_download_manifest(loader, kind):
    root = Path(__file__).resolve().parents[1]
    name = f'catgirl-world-{kind}-neoforge-{loader}'
    archive = root / 'static/clients' / (name + '.mrpack')
    assert archive.stat().st_size < 16384
    with zipfile.ZipFile(archive) as opened:
        assert opened.namelist() == ['modrinth.index.json', 'overrides/config/RPG-HUD']
        assert opened.read('overrides/config/RPG-HUD') == b'Version=1.0\nH:hud_type=default\n'
        value = json.loads(opened.read('modrinth.index.json'))
    assert value == json.loads((root / 'docs/clients' / name / 'modrinth.index.json').read_text(encoding='utf-8'))
    assert value['dependencies'] == {'minecraft': '1.21.1', 'neoforge': loader}
    assert len(value['files']) == 3
    assert any(row['path'] == 'mods/[1.21.1][NeoForge] RPG-HUD 3.13.jar' for row in value['files'])
    for row in value['files']:
        assert row['path'].startswith('mods/') and row['path'].endswith('.jar')
        assert 'fabric' not in row['path'].lower() and 'spectatorplus' not in row['path'].lower()
        assert row['env'] == {'client': 'required', 'server': 'unsupported'}
        assert len(row['hashes']['sha1']) == 40 and len(row['hashes']['sha512']) == 128
        assert all(urlparse(url).scheme == 'https' and urlparse(url).hostname == 'cdn.modrinth.com' for url in row['downloads'])


def test_observer_downloads_refer_to_actual_packaged_client_files():
    import re
    root = Path(__file__).resolve().parents[1]
    page = (root / 'static/index.html').read_text(encoding='utf-8')
    files = re.findall(r'href="\./(clients/[^" ]+\.mrpack)"', page)
    assert len(files) == 4
    assert all((root / 'static' / name).is_file() for name in files)
