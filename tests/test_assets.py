"""
Consolidated asset-related tests.

Merged from:
- test_vendor_assets_coverage.py
- test_vendor_assets_network_mocked.py
- test_vendor_assets_remaining.py
- test_vendor_assets_scaffolding.py
- test_asset_mode_pattern.py
- test_no_external_cdn_default.py
- test_no_external_cdn_more.py
"""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pydantic import Field

from pydantic_schemaforms.vendor_assets import (
    VendoredFile,
    project_root,
    manifest_path,
    sha256_bytes,
    sha256_file,
    ensure_parent_dir,
    upsert_asset_entry,
    env_truthy,
    _safe_member_bytes_from_tgz,
    _write_vendored_file,
    http_get_bytes,
    latest_htmx_version,
    npm_package_metadata,
    latest_npm_version,
    npm_tarball_url,
    vendor_htmx,
    vendor_imask,
    vendor_materialize,
    vendor_bootstrap,
    verify_manifest_files,
)

from pydantic_schemaforms.render_form import render_form_html
from pydantic_schemaforms.schema_form import FormModel
from pydantic_schemaforms.assets.runtime import vendored_asset_version


# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------


class _CdnCheckForm(FormModel):
    name: str = Field(default='', title='Name')


# ===========================================================================
# Tests from test_vendor_assets_coverage.py
# ===========================================================================


class TestVendoredFile:
    """Test VendoredFile dataclass."""

    def test_vendored_file_creation(self):
        """Test creating a VendoredFile."""
        vf = VendoredFile(
            path='assets/test.js',
            sha256='abc123',
            source_url='https://example.com/test.js',
        )
        assert vf.path == 'assets/test.js'
        assert vf.sha256 == 'abc123'
        assert vf.source_url == 'https://example.com/test.js'

    def test_vendored_file_frozen(self):
        """Test that VendoredFile is frozen."""
        vf = VendoredFile(
            path='test.js',
            sha256='hash',
            source_url='url',
        )
        with pytest.raises(Exception):  # dataclass frozen error
            vf.path = 'new_path'


class TestProjectRoot:
    """Test project_root function."""

    def test_project_root_returns_path(self):
        """Test that project_root returns a Path object."""
        root = project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_project_root_contains_pydantic_schemaforms(self):
        """Test that project root contains pydantic_schemaforms directory."""
        root = project_root()
        pydantic_schemaforms_dir = root / 'pydantic_schemaforms'
        assert pydantic_schemaforms_dir.exists()


class TestManifestPath:
    """Test manifest_path function."""

    def test_manifest_path_returns_path(self):
        """Test that manifest_path returns a Path object."""
        path = manifest_path()
        assert isinstance(path, Path)

    def test_manifest_path_contains_vendor_manifest(self):
        """Test that manifest path contains vendor_manifest.json."""
        path = manifest_path()
        assert 'vendor_manifest.json' in str(path)


class TestSha256Functions:
    """Test SHA256 hashing functions."""

    def test_sha256_bytes_empty(self):
        """Test SHA256 of empty bytes."""
        result = sha256_bytes(b'')
        expected = hashlib.sha256(b'').hexdigest()
        assert result == expected

    def test_sha256_bytes_hello_world(self):
        """Test SHA256 of 'hello world'."""
        data = b'hello world'
        result = sha256_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert result == expected
        assert len(result) == 64  # SHA256 produces 64 hex characters

    def test_sha256_bytes_returns_hex_string(self):
        """Test that sha256_bytes returns a hex string."""
        result = sha256_bytes(b'test')
        assert isinstance(result, str)
        assert len(result) == 64
        # Should be all hex characters
        assert all(c in '0123456789abcdef' for c in result)

    @patch('pydantic_schemaforms.vendor_assets.Path.read_bytes')
    def test_sha256_file(self, mock_read_bytes):
        """Test sha256_file function."""
        mock_read_bytes.return_value = b'file content'
        expected = hashlib.sha256(b'file content').hexdigest()

        path = Path('/fake/path.txt')
        result = sha256_file(path)

        assert result == expected
        mock_read_bytes.assert_called_once()


class TestEnsureParentDir:
    """Test ensure_parent_dir function."""

    @patch('pydantic_schemaforms.vendor_assets.Path.mkdir')
    def test_ensure_parent_dir_creates_parents(self, mock_mkdir):
        """Test that ensure_parent_dir creates parent directories."""
        path = Path('/fake/nested/directory/file.txt')
        ensure_parent_dir(path)

        # Should call mkdir on the parent with parents=True, exist_ok=True
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch('pydantic_schemaforms.vendor_assets.Path.mkdir')
    def test_ensure_parent_dir_with_existing_dir(self, mock_mkdir):
        """Test ensure_parent_dir with existing directory."""
        path = Path('/existing/file.txt')
        ensure_parent_dir(path)

        # Should still call mkdir (exist_ok=True handles existing dirs)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestUpsertAssetEntry:
    """Test upsert_asset_entry function."""

    def test_upsert_asset_entry_adds_new(self):
        """Test adding a new asset entry."""
        manifest = {}
        entry = {'name': 'test-lib', 'version': '1.0.0'}

        upsert_asset_entry(manifest, name='test-lib', entry=entry)

        assert 'assets' in manifest
        assert len(manifest['assets']) == 1
        assert manifest['assets'][0] == entry

    def test_upsert_asset_entry_updates_existing(self):
        """Test updating an existing asset entry."""
        manifest = {
            'assets': [
                {'name': 'lib-a', 'version': '1.0.0'},
                {'name': 'lib-b', 'version': '2.0.0'},
            ]
        }
        new_entry = {'name': 'lib-a', 'version': '1.5.0'}

        upsert_asset_entry(manifest, name='lib-a', entry=new_entry)

        assert len(manifest['assets']) == 2
        assert manifest['assets'][0] == new_entry
        assert manifest['assets'][1]['name'] == 'lib-b'

    def test_upsert_asset_entry_preserves_other_assets(self):
        """Test that updating one asset preserves others."""
        manifest = {
            'assets': [
                {'name': 'keep-me', 'version': '1.0.0'},
            ]
        }
        new_entry = {'name': 'new-lib', 'version': '2.0.0'}

        upsert_asset_entry(manifest, name='new-lib', entry=new_entry)

        assert len(manifest['assets']) == 2
        assert manifest['assets'][0]['name'] == 'keep-me'
        assert manifest['assets'][1] == new_entry

    def test_upsert_asset_entry_with_empty_manifest(self):
        """Test upsert with completely empty manifest."""
        manifest = {}
        entry = {'name': 'first', 'version': '0.1.0'}

        upsert_asset_entry(manifest, name='first', entry=entry)

        assert 'assets' in manifest
        assert manifest['assets'] == [entry]


class TestEnvTruthy:
    """Test env_truthy function."""

    @patch.dict('os.environ', {'TEST_VAR': '1'})
    def test_env_truthy_with_one(self):
        """Test env_truthy with '1'."""
        assert env_truthy('TEST_VAR') is True

    @patch.dict('os.environ', {'TEST_VAR': 'true'})
    def test_env_truthy_with_true(self):
        """Test env_truthy with 'true'."""
        assert env_truthy('TEST_VAR') is True

    @patch.dict('os.environ', {'TEST_VAR': 'TRUE'})
    def test_env_truthy_with_uppercase_true(self):
        """Test env_truthy with 'TRUE'."""
        assert env_truthy('TEST_VAR') is True

    @patch.dict('os.environ', {'TEST_VAR': 'yes'})
    def test_env_truthy_with_yes(self):
        """Test env_truthy with 'yes'."""
        assert env_truthy('TEST_VAR') is True

    @patch.dict('os.environ', {'TEST_VAR': 'YES'})
    def test_env_truthy_with_uppercase_yes(self):
        """Test env_truthy with 'YES'."""
        assert env_truthy('TEST_VAR') is True

    @patch.dict('os.environ', {'TEST_VAR': 'on'})
    def test_env_truthy_with_on(self):
        """Test env_truthy with 'on'."""
        assert env_truthy('TEST_VAR') is True

    @patch.dict('os.environ', {'TEST_VAR': 'ON'})
    def test_env_truthy_with_uppercase_on(self):
        """Test env_truthy with 'ON'."""
        assert env_truthy('TEST_VAR') is True

    @patch.dict('os.environ', {'TEST_VAR': '0'})
    def test_env_truthy_with_zero(self):
        """Test env_truthy with '0'."""
        assert env_truthy('TEST_VAR') is False

    @patch.dict('os.environ', {'TEST_VAR': 'false'})
    def test_env_truthy_with_false(self):
        """Test env_truthy with 'false'."""
        assert env_truthy('TEST_VAR') is False

    @patch.dict('os.environ', {'TEST_VAR': ''})
    def test_env_truthy_with_empty_string(self):
        """Test env_truthy with empty string."""
        assert env_truthy('TEST_VAR') is False

    @patch.dict('os.environ', {}, clear=True)
    def test_env_truthy_with_unset_var(self):
        """Test env_truthy with unset variable."""
        assert env_truthy('NONEXISTENT_VAR') is False

    @patch.dict('os.environ', {'TEST_VAR': '  1  '})
    def test_env_truthy_with_whitespace(self):
        """Test env_truthy handles whitespace."""
        assert env_truthy('TEST_VAR') is True


class TestSafeMemberBytesFromTgz:
    """Test _safe_member_bytes_from_tgz function."""

    def test_extract_file_with_package_prefix(self):
        """Test extracting a file with 'package/' prefix."""
        # Create a fake tar.gz with a file
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tf:
            info = tarfile.TarInfo(name='package/test.txt')
            info.size = 12
            tf.addfile(info, io.BytesIO(b'hello world!'))

        tar_bytes = tar_buffer.getvalue()
        result = _safe_member_bytes_from_tgz(tar_bytes, 'test.txt')

        assert result == b'hello world!'

    def test_extract_file_without_prefix(self):
        """Test extracting a file without prefix."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tf:
            info = tarfile.TarInfo(name='plain.txt')
            info.size = 5
            tf.addfile(info, io.BytesIO(b'plain'))

        tar_bytes = tar_buffer.getvalue()
        result = _safe_member_bytes_from_tgz(tar_bytes, 'plain.txt')

        assert result == b'plain'

    def test_extract_file_with_explicit_package_prefix(self):
        """Test extracting with 'package/' in request."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tf:
            info = tarfile.TarInfo(name='package/nested/file.js')
            info.size = 7
            tf.addfile(info, io.BytesIO(b'content'))

        tar_bytes = tar_buffer.getvalue()
        result = _safe_member_bytes_from_tgz(tar_bytes, 'nested/file.js')

        assert result == b'content'

    def test_extract_missing_file_raises_error(self):
        """Test that missing file raises FileNotFoundError."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tf:
            info = tarfile.TarInfo(name='package/exists.txt')
            info.size = 4
            tf.addfile(info, io.BytesIO(b'data'))

        tar_bytes = tar_buffer.getvalue()

        with pytest.raises(FileNotFoundError, match='missing file in npm tarball'):
            _safe_member_bytes_from_tgz(tar_bytes, 'nonexistent.txt')

    def test_extract_directory_raises_error(self):
        """Test that directory member raises ValueError."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tf:
            # Add a directory
            info = tarfile.TarInfo(name='package/dir')
            info.type = tarfile.DIRTYPE
            tf.addfile(info)

        tar_bytes = tar_buffer.getvalue()

        with pytest.raises(ValueError, match='not a file'):
            _safe_member_bytes_from_tgz(tar_bytes, 'dir')


class TestWriteVendoredFile:
    """Test _write_vendored_file function."""

    @patch('pydantic_schemaforms.vendor_assets.project_root')
    @patch('pydantic_schemaforms.vendor_assets.ensure_parent_dir')
    @patch('pydantic_schemaforms.vendor_assets.Path.write_bytes')
    def test_write_vendored_file(self, mock_write_bytes, mock_ensure_dir, mock_project_root):
        """Test writing a vendored file."""
        mock_project_root.return_value = Path('/project')

        data = b'file content'
        rel_path = Path('assets/vendor/lib.js')
        source_url = 'https://example.com/lib.js'

        result = _write_vendored_file(
            rel_path=rel_path,
            data=data,
            source_url=source_url,
        )

        # Check that parent dir is ensured
        mock_ensure_dir.assert_called_once()

        # Check that file is written
        mock_write_bytes.assert_called_once_with(data)

        # Check return value
        assert result['path'] == 'assets/vendor/lib.js'
        assert result['sha256'] == hashlib.sha256(data).hexdigest()
        assert result['source_url'] == source_url

    @patch('pydantic_schemaforms.vendor_assets.project_root')
    @patch('pydantic_schemaforms.vendor_assets.ensure_parent_dir')
    @patch('pydantic_schemaforms.vendor_assets.Path.write_bytes')
    def test_write_vendored_file_creates_correct_path(
        self, mock_write_bytes, mock_ensure_dir, mock_project_root
    ):
        """Test that correct absolute path is created."""
        mock_project_root.return_value = Path('/root')

        rel_path = Path('sub/file.txt')
        _write_vendored_file(
            rel_path=rel_path,
            data=b'test',
            source_url='http://test.com',
        )

        # Verify ensure_parent_dir was called with the right path
        call_args = mock_ensure_dir.call_args[0][0]
        assert '/root/sub/file.txt' in str(call_args)


# ===========================================================================
# Tests from test_vendor_assets_network_mocked.py
# ===========================================================================


class TestHttpGetBytes:
    """Test http_get_bytes function with mocking."""

    @patch('pydantic_schemaforms.vendor_assets.urlopen')
    @patch('pydantic_schemaforms.vendor_assets.Request')
    def test_http_get_bytes_returns_bytes(self, mock_request, mock_urlopen):
        """Test http_get_bytes returns bytes from URL."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'test content'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False
        mock_urlopen.return_value = mock_response

        result = http_get_bytes('https://example.com/file.js')

        assert result == b'test content'
        mock_request.assert_called_once_with(
            'https://example.com/file.js',
            headers={'User-Agent': 'pydantic-schemaforms-vendor-script'},
        )

    @patch('pydantic_schemaforms.vendor_assets.urlopen')
    @patch('pydantic_schemaforms.vendor_assets.Request')
    def test_http_get_bytes_custom_user_agent(self, mock_request, mock_urlopen):
        """Test http_get_bytes with custom user agent."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'data'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False
        mock_urlopen.return_value = mock_response

        http_get_bytes('https://example.com/api', user_agent='custom-agent')

        mock_request.assert_called_once_with(
            'https://example.com/api', headers={'User-Agent': 'custom-agent'}
        )


class TestLatestHtmxVersion:
    """Test latest_htmx_version function with mocking."""

    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    def test_latest_htmx_version_with_v_prefix(self, mock_http):
        """Test latest_htmx_version strips 'v' prefix."""
        mock_http.return_value = json.dumps({'tag_name': 'v2.0.3'}).encode('utf-8')

        result = latest_htmx_version()

        assert result == '2.0.3'
        mock_http.assert_called_once()

    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    def test_latest_htmx_version_without_v_prefix(self, mock_http):
        """Test latest_htmx_version without 'v' prefix."""
        mock_http.return_value = json.dumps({'tag_name': '2.0.3'}).encode('utf-8')

        result = latest_htmx_version()

        assert result == '2.0.3'

    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    def test_latest_htmx_version_with_whitespace(self, mock_http):
        """Test latest_htmx_version strips whitespace."""
        mock_http.return_value = json.dumps({'tag_name': ' v2.0.3 '}).encode('utf-8')

        result = latest_htmx_version()

        assert result == '2.0.3'

    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    def test_latest_htmx_version_empty_tag(self, mock_http):
        """Test latest_htmx_version with empty tag."""
        mock_http.return_value = json.dumps({'tag_name': ''}).encode('utf-8')

        result = latest_htmx_version()

        assert result == ''


class TestNpmPackageMetadata:
    """Test npm_package_metadata function with mocking."""

    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    def test_npm_package_metadata_returns_dict(self, mock_http):
        """Test npm_package_metadata returns metadata dict."""
        metadata = {'name': 'imask', 'version': '7.6.1'}
        mock_http.return_value = json.dumps(metadata).encode('utf-8')

        result = npm_package_metadata('imask')

        assert result == metadata
        mock_http.assert_called_once_with('https://registry.npmjs.org/imask')

    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    def test_npm_package_metadata_not_dict_raises(self, mock_http):
        """Test npm_package_metadata raises when response is not dict."""
        mock_http.return_value = json.dumps(['array']).encode('utf-8')

        with pytest.raises(ValueError, match='was not an object'):
            npm_package_metadata('badpackage')


class TestLatestNpmVersion:
    """Test latest_npm_version function with mocking."""

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_returns_latest(self, mock_metadata):
        """Test latest_npm_version returns latest version."""
        mock_metadata.return_value = {'dist-tags': {'latest': '7.6.1', 'beta': '8.0.0-beta.1'}}

        result = latest_npm_version('imask')

        assert result == '7.6.1'

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_strips_whitespace(self, mock_metadata):
        """Test latest_npm_version strips whitespace."""
        mock_metadata.return_value = {'dist-tags': {'latest': '  7.6.1  '}}

        result = latest_npm_version('imask')

        assert result == '7.6.1'

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_missing_dist_tags_raises(self, mock_metadata):
        """Test latest_npm_version raises when dist-tags missing."""
        mock_metadata.return_value = {}

        with pytest.raises(ValueError, match='missing dist-tags'):
            latest_npm_version('badpackage')

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_dist_tags_not_dict_raises(self, mock_metadata):
        """Test latest_npm_version raises when dist-tags not dict."""
        mock_metadata.return_value = {'dist-tags': 'string'}

        with pytest.raises(ValueError, match='missing dist-tags'):
            latest_npm_version('badpackage')

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_missing_latest_raises(self, mock_metadata):
        """Test latest_npm_version raises when latest tag missing."""
        mock_metadata.return_value = {'dist-tags': {'beta': '8.0.0'}}

        with pytest.raises(ValueError, match='missing latest dist-tag'):
            latest_npm_version('badpackage')

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_empty_latest_raises(self, mock_metadata):
        """Test latest_npm_version raises when latest tag empty."""
        mock_metadata.return_value = {'dist-tags': {'latest': '  '}}

        with pytest.raises(ValueError, match='missing latest dist-tag'):
            latest_npm_version('badpackage')


class TestNpmTarballUrl:
    """Test npm_tarball_url function with mocking."""

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_returns_url(self, mock_metadata):
        """Test npm_tarball_url returns tarball URL."""
        mock_metadata.return_value = {
            'versions': {
                '7.6.1': {'dist': {'tarball': 'https://registry.npmjs.org/imask/-/imask-7.6.1.tgz'}}
            }
        }

        result = npm_tarball_url('imask', '7.6.1')

        assert result == 'https://registry.npmjs.org/imask/-/imask-7.6.1.tgz'

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_strips_whitespace(self, mock_metadata):
        """Test npm_tarball_url strips whitespace from URL."""
        mock_metadata.return_value = {
            'versions': {
                '7.6.1': {
                    'dist': {'tarball': '  https://registry.npmjs.org/imask/-/imask-7.6.1.tgz  '}
                }
            }
        }

        result = npm_tarball_url('imask', '7.6.1')

        assert result == 'https://registry.npmjs.org/imask/-/imask-7.6.1.tgz'

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_missing_version_raises(self, mock_metadata):
        """Test npm_tarball_url raises when version missing."""
        mock_metadata.return_value = {'versions': {'7.6.0': {}}}

        with pytest.raises(ValueError, match='missing version 7.6.1'):
            npm_tarball_url('imask', '7.6.1')

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_versions_not_dict_raises(self, mock_metadata):
        """Test npm_tarball_url raises when versions not dict."""
        mock_metadata.return_value = {'versions': 'string'}

        with pytest.raises(ValueError, match='missing version'):
            npm_tarball_url('badpackage', '1.0.0')

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_version_meta_not_dict_raises(self, mock_metadata):
        """Test npm_tarball_url raises when version metadata invalid."""
        mock_metadata.return_value = {'versions': {'7.6.1': 'string'}}

        with pytest.raises(ValueError, match='invalid'):
            npm_tarball_url('imask', '7.6.1')

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_missing_dist_raises(self, mock_metadata):
        """Test npm_tarball_url raises when dist missing."""
        mock_metadata.return_value = {'versions': {'7.6.1': {}}}

        with pytest.raises(ValueError, match='missing dist'):
            npm_tarball_url('imask', '7.6.1')

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_dist_not_dict_raises(self, mock_metadata):
        """Test npm_tarball_url raises when dist not dict."""
        mock_metadata.return_value = {'versions': {'7.6.1': {'dist': 'string'}}}

        with pytest.raises(ValueError, match='missing dist'):
            npm_tarball_url('imask', '7.6.1')

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_missing_tarball_raises(self, mock_metadata):
        """Test npm_tarball_url raises when tarball missing."""
        mock_metadata.return_value = {'versions': {'7.6.1': {'dist': {}}}}

        with pytest.raises(ValueError, match='missing tarball url'):
            npm_tarball_url('imask', '7.6.1')

    @patch('pydantic_schemaforms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_empty_tarball_raises(self, mock_metadata):
        """Test npm_tarball_url raises when tarball URL empty."""
        mock_metadata.return_value = {'versions': {'7.6.1': {'dist': {'tarball': '  '}}}}

        with pytest.raises(ValueError, match='missing tarball url'):
            npm_tarball_url('imask', '7.6.1')


class TestVendorHtmx:
    """Test vendor_htmx function with mocking."""

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    @patch('pydantic_schemaforms.vendor_assets.latest_htmx_version')
    def test_vendor_htmx_with_explicit_version(
        self, mock_latest, mock_http, mock_write, mock_load, mock_upsert, mock_save
    ):
        """Test vendor_htmx with explicit version."""
        mock_http.side_effect = [b'js content', b'license content']
        mock_write.side_effect = [
            {
                'path': 'pydantic_schemaforms/assets/vendor/htmx/htmx.min.js',
                'sha256': 'abcd1234',
                'source_url': 'https://example.com/htmx.min.js',
            },
            {
                'path': 'pydantic_schemaforms/assets/vendor/htmx/LICENSE',
                'sha256': 'efgh5678',
                'source_url': 'https://example.com/LICENSE',
            },
        ]
        mock_load.return_value = {'schema_version': 1, 'assets': []}

        result = vendor_htmx(version='2.0.3')

        assert result.path == 'pydantic_schemaforms/assets/vendor/htmx/htmx.min.js'
        assert result.sha256 == 'abcd1234'
        mock_latest.assert_not_called()
        assert mock_http.call_count == 2
        assert mock_write.call_count == 2
        mock_upsert.assert_called_once()
        mock_save.assert_called_once()

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    @patch('pydantic_schemaforms.vendor_assets.latest_htmx_version')
    def test_vendor_htmx_without_version_fetches_latest(
        self, mock_latest, mock_http, mock_write, mock_load, mock_upsert, mock_save
    ):
        """Test vendor_htmx without version fetches latest."""
        mock_latest.return_value = '2.0.3'
        mock_http.side_effect = [b'js content', b'license content']
        mock_write.side_effect = [
            {'path': 'htmx.min.js', 'sha256': 'abcd', 'source_url': 'url1'},
            {'path': 'LICENSE', 'sha256': 'efgh', 'source_url': 'url2'},
        ]
        mock_load.return_value = {'schema_version': 1}

        vendor_htmx()

        mock_latest.assert_called_once()
        assert mock_http.call_count == 2

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    def test_vendor_htmx_sets_schema_version(
        self, mock_http, mock_write, mock_load, mock_upsert, mock_save
    ):
        """Test vendor_htmx sets schema_version if missing."""
        mock_http.side_effect = [b'js', b'lic']
        mock_write.side_effect = [
            {'path': 'a', 'sha256': 'b', 'source_url': 'c'},
            {'path': 'd', 'sha256': 'e', 'source_url': 'f'},
        ]
        mock_load.return_value = {}  # No schema_version

        vendor_htmx(version='2.0.3')

        # Check that manifest passed to write_manifest has schema_version
        saved_manifest = mock_save.call_args[0][0]
        assert saved_manifest['schema_version'] == 1


class TestVendorImask:
    """Test vendor_imask function with mocking."""

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    @patch('pydantic_schemaforms.vendor_assets.npm_tarball_url')
    @patch('pydantic_schemaforms.vendor_assets.latest_npm_version')
    def test_vendor_imask_with_explicit_version(
        self,
        mock_latest,
        mock_tarball_url,
        mock_http,
        mock_extract,
        mock_write,
        mock_load,
        mock_upsert,
        mock_save,
    ):
        """Test vendor_imask with explicit version."""
        mock_tarball_url.return_value = 'https://registry.npmjs.org/imask/-/imask-7.6.1.tgz'
        mock_http.return_value = b'tarball content'
        mock_extract.side_effect = [b'js content', b'license content']
        mock_write.side_effect = [
            {'path': 'imask.min.js', 'sha256': 'abc', 'source_url': 'url1'},
            {'path': 'LICENSE', 'sha256': 'def', 'source_url': 'url2'},
        ]
        mock_load.return_value = {'schema_version': 1}

        result = vendor_imask(version='7.6.1')

        assert result.path == 'imask.min.js'
        assert result.sha256 == 'abc'
        mock_latest.assert_not_called()
        mock_tarball_url.assert_called_once_with('imask', '7.6.1')
        assert mock_extract.call_count == 2
        assert mock_write.call_count == 2
        mock_upsert.assert_called_once()
        mock_save.assert_called_once()

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    @patch('pydantic_schemaforms.vendor_assets.npm_tarball_url')
    @patch('pydantic_schemaforms.vendor_assets.latest_npm_version')
    def test_vendor_imask_without_version_fetches_latest(
        self,
        mock_latest,
        mock_tarball_url,
        mock_http,
        mock_extract,
        mock_write,
        mock_load,
        mock_upsert,
        mock_save,
    ):
        """Test vendor_imask without version fetches latest."""
        mock_latest.return_value = '7.6.1'
        mock_tarball_url.return_value = 'https://url'
        mock_http.return_value = b'tgz'
        mock_extract.side_effect = [b'js', b'lic']
        mock_write.side_effect = [
            {'path': 'a', 'sha256': 'b', 'source_url': 'c'},
            {'path': 'd', 'sha256': 'e', 'source_url': 'f'},
        ]
        mock_load.return_value = {'schema_version': 1}

        vendor_imask()

        mock_latest.assert_called_once_with('imask')

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    @patch('pydantic_schemaforms.vendor_assets.npm_tarball_url')
    def test_vendor_imask_tries_license_md_fallback(
        self,
        mock_tarball_url,
        mock_http,
        mock_extract,
        mock_write,
        mock_load,
        mock_upsert,
        mock_save,
    ):
        """Test vendor_imask tries LICENSE.md if LICENSE not found."""
        mock_tarball_url.return_value = 'url'
        mock_http.return_value = b'tgz'
        # First extract succeeds (js), second fails (LICENSE), third succeeds (LICENSE.md)
        mock_extract.side_effect = [
            b'js content',
            FileNotFoundError('LICENSE not found'),
            b'license md content',
        ]
        mock_write.side_effect = [
            {'path': 'js', 'sha256': 'a', 'source_url': 'url'},
            {'path': 'lic', 'sha256': 'b', 'source_url': 'url'},
        ]
        mock_load.return_value = {'schema_version': 1}

        vendor_imask(version='7.6.1')

        assert mock_extract.call_count == 3
        assert mock_write.call_count == 2

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    @patch('pydantic_schemaforms.vendor_assets.npm_tarball_url')
    def test_vendor_imask_sets_schema_version(
        self,
        mock_tarball_url,
        mock_http,
        mock_extract,
        mock_write,
        mock_load,
        mock_upsert,
        mock_save,
    ):
        """Test vendor_imask sets schema_version if missing."""
        mock_tarball_url.return_value = 'url'
        mock_http.return_value = b'tgz'
        mock_extract.side_effect = [b'js', b'lic']
        mock_write.side_effect = [
            {'path': 'a', 'sha256': 'b', 'source_url': 'c'},
            {'path': 'd', 'sha256': 'e', 'source_url': 'f'},
        ]
        mock_load.return_value = {}  # No schema_version

        vendor_imask(version='7.6.1')

        saved_manifest = mock_save.call_args[0][0]
        assert saved_manifest['schema_version'] == 1


# ===========================================================================
# Tests from test_vendor_assets_remaining.py
# ===========================================================================


class TestVendorMaterialize:
    """Test vendor_materialize function with mocking."""

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    @patch('pydantic_schemaforms.vendor_assets.npm_tarball_url')
    def test_vendor_materialize_with_license(
        self,
        mock_tarball_url,
        mock_http,
        mock_extract,
        mock_write,
        mock_load,
        mock_upsert,
        mock_save,
    ):
        """Test vendor_materialize extracts CSS, JS, and LICENSE."""
        mock_tarball_url.return_value = (
            'https://registry.npmjs.org/@materializecss/materialize/-/materialize-2.1.1.tgz'
        )
        mock_http.return_value = b'tarball content'
        mock_extract.side_effect = [b'css content', b'js content', b'license content']
        mock_write.side_effect = [
            {'path': 'materialize.min.css', 'sha256': 'css_hash', 'source_url': 'url1'},
            {'path': 'materialize.min.js', 'sha256': 'js_hash', 'source_url': 'url2'},
            {'path': 'LICENSE', 'sha256': 'lic_hash', 'source_url': 'url3'},
        ]
        mock_load.return_value = {'schema_version': 1}

        result = vendor_materialize(version='2.1.1')

        assert result.path == 'materialize.min.js'
        assert result.sha256 == 'js_hash'
        mock_tarball_url.assert_called_once_with('@materializecss/materialize', '2.1.1')
        assert mock_extract.call_count == 3
        assert mock_write.call_count == 3
        mock_upsert.assert_called_once()
        mock_save.assert_called_once()

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    @patch('pydantic_schemaforms.vendor_assets.npm_tarball_url')
    def test_vendor_materialize_tries_license_md_fallback(
        self,
        mock_tarball_url,
        mock_http,
        mock_extract,
        mock_write,
        mock_load,
        mock_upsert,
        mock_save,
    ):
        """Test vendor_materialize tries LICENSE.md if LICENSE not found."""
        mock_tarball_url.return_value = 'url'
        mock_http.return_value = b'tgz'
        # CSS, JS, LICENSE (not found), LICENSE.md (found)
        mock_extract.side_effect = [
            b'css',
            b'js',
            FileNotFoundError('LICENSE not found'),
            b'license md',
        ]
        mock_write.side_effect = [
            {'path': 'css', 'sha256': 'a', 'source_url': 'url'},
            {'path': 'js', 'sha256': 'b', 'source_url': 'url'},
            {'path': 'lic', 'sha256': 'c', 'source_url': 'url'},
        ]
        mock_load.return_value = {'schema_version': 1}

        vendor_materialize(version='2.1.1')

        assert mock_extract.call_count == 4
        assert mock_write.call_count == 3

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    @patch('pydantic_schemaforms.vendor_assets.npm_tarball_url')
    def test_vendor_materialize_sets_schema_version(
        self,
        mock_tarball_url,
        mock_http,
        mock_extract,
        mock_write,
        mock_load,
        mock_upsert,
        mock_save,
    ):
        """Test vendor_materialize sets schema_version if missing."""
        mock_tarball_url.return_value = 'url'
        mock_http.return_value = b'tgz'
        mock_extract.side_effect = [b'css', b'js', b'lic']
        mock_write.side_effect = [
            {'path': 'a', 'sha256': 'x', 'source_url': 'url'},
            {'path': 'b', 'sha256': 'y', 'source_url': 'url'},
            {'path': 'c', 'sha256': 'z', 'source_url': 'url'},
        ]
        mock_load.return_value = {}  # No schema_version

        vendor_materialize(version='2.1.1')

        saved_manifest = mock_save.call_args[0][0]
        assert saved_manifest['schema_version'] == 1


class TestVendorBootstrap:
    """Test vendor_bootstrap function with mocking."""

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    def test_vendor_bootstrap_extracts_from_zip(
        self, mock_http, mock_write, mock_load, mock_upsert, mock_save
    ):
        """Test vendor_bootstrap extracts CSS and JS from ZIP."""
        # Create a mock ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('bootstrap-5.3.0-dist/css/bootstrap.min.css', b'css content')
            zf.writestr('bootstrap-5.3.0-dist/js/bootstrap.bundle.min.js', b'js content')
        zip_bytes = zip_buffer.getvalue()

        # http_get_bytes returns zip then license
        mock_http.side_effect = [zip_bytes, b'license content']
        mock_write.side_effect = [
            {'path': 'bootstrap.min.css', 'sha256': 'css_hash', 'source_url': 'zip_url'},
            {'path': 'bootstrap.bundle.min.js', 'sha256': 'js_hash', 'source_url': 'zip_url'},
            {'path': 'LICENSE', 'sha256': 'lic_hash', 'source_url': 'lic_url'},
        ]
        mock_load.return_value = {'schema_version': 1}

        result = vendor_bootstrap(version='5.3.0')

        assert result.path == 'bootstrap.bundle.min.js'
        assert result.sha256 == 'js_hash'
        assert mock_http.call_count == 2
        assert mock_write.call_count == 3
        mock_upsert.assert_called_once()
        mock_save.assert_called_once()

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    def test_vendor_bootstrap_missing_css_raises(
        self, mock_http, mock_write, mock_load, mock_upsert, mock_save
    ):
        """Test vendor_bootstrap raises if CSS missing from ZIP."""
        # Create ZIP without CSS
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('bootstrap-5.3.0-dist/js/bootstrap.bundle.min.js', b'js content')
        zip_bytes = zip_buffer.getvalue()

        mock_http.return_value = zip_bytes

        with pytest.raises(FileNotFoundError, match='missing bootstrap.min.css'):
            vendor_bootstrap(version='5.3.0')

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    def test_vendor_bootstrap_missing_js_raises(
        self, mock_http, mock_write, mock_load, mock_upsert, mock_save
    ):
        """Test vendor_bootstrap raises if JS missing from ZIP."""
        # Create ZIP without JS
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('bootstrap-5.3.0-dist/css/bootstrap.min.css', b'css content')
        zip_bytes = zip_buffer.getvalue()

        mock_http.return_value = zip_bytes

        with pytest.raises(FileNotFoundError, match='missing bootstrap.bundle.min.js'):
            vendor_bootstrap(version='5.3.0')

    @patch('pydantic_schemaforms.vendor_assets.write_manifest')
    @patch('pydantic_schemaforms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    @patch('pydantic_schemaforms.vendor_assets._write_vendored_file')
    @patch('pydantic_schemaforms.vendor_assets.http_get_bytes')
    def test_vendor_bootstrap_sets_schema_version(
        self, mock_http, mock_write, mock_load, mock_upsert, mock_save
    ):
        """Test vendor_bootstrap sets schema_version if missing."""
        # Create valid ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('css/bootstrap.min.css', b'css')
            zf.writestr('js/bootstrap.bundle.min.js', b'js')
        zip_bytes = zip_buffer.getvalue()

        mock_http.side_effect = [zip_bytes, b'license']
        mock_write.side_effect = [
            {'path': 'a', 'sha256': 'x', 'source_url': 'url'},
            {'path': 'b', 'sha256': 'y', 'source_url': 'url'},
            {'path': 'c', 'sha256': 'z', 'source_url': 'url'},
        ]
        mock_load.return_value = {}  # No schema_version

        vendor_bootstrap(version='5.3.0')

        saved_manifest = mock_save.call_args[0][0]
        assert saved_manifest['schema_version'] == 1


class TestVerifyManifestFiles:
    """Test verify_manifest_files function."""

    @patch('pydantic_schemaforms.vendor_assets.sha256_file')
    @patch('pydantic_schemaforms.vendor_assets.project_root')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_valid(self, mock_load, mock_root, mock_sha256):
        """Test verify_manifest_files with valid manifest."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [
                {
                    'name': 'htmx',
                    'files': [
                        {
                            'path': 'pydantic_schemaforms/assets/vendor/htmx/htmx.min.js',
                            'sha256': 'a' * 64,
                        }
                    ],
                }
            ],
        }
        # Create a mock Path that returns True for exists()
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        mock_root_path = MagicMock(spec=Path)
        mock_root_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_root.return_value = mock_root_path

        mock_sha256.return_value = 'a' * 64

        verify_manifest_files()  # Should not raise

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_missing_schema_version_raises(self, mock_load):
        """Test verify_manifest_files raises if schema_version missing."""
        mock_load.return_value = {'assets': []}

        with pytest.raises(ValueError, match='missing integer schema_version'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_schema_version_not_int_raises(self, mock_load):
        """Test verify_manifest_files raises if schema_version not int."""
        mock_load.return_value = {'schema_version': '1', 'assets': []}

        with pytest.raises(ValueError, match='missing integer schema_version'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_missing_assets_raises(self, mock_load):
        """Test verify_manifest_files raises if assets missing."""
        mock_load.return_value = {'schema_version': 1}

        with pytest.raises(ValueError, match='assets must be a list'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_assets_not_list_raises(self, mock_load):
        """Test verify_manifest_files raises if assets not list."""
        mock_load.return_value = {'schema_version': 1, 'assets': 'string'}

        with pytest.raises(ValueError, match='assets must be a list'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_require_nonempty_empty_raises(self, mock_load):
        """Test verify_manifest_files raises if require_nonempty and assets empty."""
        mock_load.return_value = {'schema_version': 1, 'assets': []}

        with pytest.raises(ValueError, match='has no assets'):
            verify_manifest_files(require_nonempty=True)

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_asset_not_dict_raises(self, mock_load):
        """Test verify_manifest_files raises if asset entry not dict."""
        mock_load.return_value = {'schema_version': 1, 'assets': ['string']}

        with pytest.raises(ValueError, match='asset entries must be objects'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_missing_files_list_raises(self, mock_load):
        """Test verify_manifest_files raises if files list missing."""
        mock_load.return_value = {'schema_version': 1, 'assets': [{'name': 'htmx'}]}

        with pytest.raises(ValueError, match='missing files list'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_files_not_list_raises(self, mock_load):
        """Test verify_manifest_files raises if files not list."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': 'string'}],
        }

        with pytest.raises(ValueError, match='missing files list'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_file_entry_not_dict_raises(self, mock_load):
        """Test verify_manifest_files raises if file entry not dict."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': ['string']}],
        }

        with pytest.raises(ValueError, match='file entries must be objects'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_missing_path_raises(self, mock_load):
        """Test verify_manifest_files raises if file missing path."""
        mock_load.return_value = {'schema_version': 1, 'assets': [{'name': 'htmx', 'files': [{}]}]}

        with pytest.raises(ValueError, match='missing path'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_empty_path_raises(self, mock_load):
        """Test verify_manifest_files raises if path empty."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': [{'path': ''}]}],
        }

        with pytest.raises(ValueError, match='missing path'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_missing_sha256_raises(self, mock_load):
        """Test verify_manifest_files raises if sha256 missing."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': [{'path': 'file.js'}]}],
        }

        with pytest.raises(ValueError, match='missing sha256'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_sha256_wrong_length_raises(self, mock_load):
        """Test verify_manifest_files raises if sha256 wrong length."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': [{'path': 'file.js', 'sha256': 'short'}]}],
        }

        with pytest.raises(ValueError, match='missing sha256'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.project_root')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_file_not_exists_raises(self, mock_load, mock_root):
        """Test verify_manifest_files raises if file doesn't exist."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': [{'path': 'missing.js', 'sha256': 'a' * 64}]}],
        }
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False

        mock_root_path = MagicMock(spec=Path)
        mock_root_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_root.return_value = mock_root_path

        with pytest.raises(FileNotFoundError, match='vendored file missing'):
            verify_manifest_files()

    @patch('pydantic_schemaforms.vendor_assets.sha256_file')
    @patch('pydantic_schemaforms.vendor_assets.project_root')
    @patch('pydantic_schemaforms.vendor_assets.load_manifest')
    def test_verify_manifest_files_sha256_mismatch_raises(self, mock_load, mock_root, mock_sha256):
        """Test verify_manifest_files raises if sha256 mismatch."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': [{'path': 'file.js', 'sha256': 'a' * 64}]}],
        }
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        mock_root_path = MagicMock(spec=Path)
        mock_root_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_root.return_value = mock_root_path

        mock_sha256.return_value = 'b' * 64  # Different hash

        with pytest.raises(ValueError, match='sha256 mismatch'):
            verify_manifest_files()


# ===========================================================================
# Tests from test_vendor_assets_scaffolding.py
# ===========================================================================


def test_vendor_manifest_exists_and_has_expected_shape() -> None:
    path = manifest_path()
    assert path.exists(), f'Missing vendor manifest at {path}'

    payload = json.loads(path.read_text(encoding='utf-8'))
    assert isinstance(payload.get('schema_version'), int)
    assert 'assets' in payload
    assert isinstance(payload['assets'], list)


def test_vendor_assets_dir_exists() -> None:
    vendor_dir = manifest_path().parent
    assert vendor_dir.exists()
    assert (vendor_dir / 'vendor_manifest.json').exists()


def test_vendor_manifest_checksums_verify() -> None:
    verify_manifest_files(require_nonempty=True)


# ===========================================================================
# Tests from test_asset_mode_pattern.py
# ===========================================================================


def test_enhanced_renderer_include_assets_vendored_inlines_bootstrap() -> None:
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_schemaforms.schema_form import FormModel, Field

    class Demo(FormModel):
        name: str = Field(title='Name')

    renderer = EnhancedFormRenderer(
        framework='bootstrap',
        include_framework_assets=True,
        asset_mode='vendored',
    )
    html = renderer.render_form_from_model(Demo)
    assert '<style>' in html
    assert 'cdn.jsdelivr.net' not in html
    # Sanity check vendored bootstrap content is present (protects against packaging issues)
    assert 'Bootstrap' in html
    assert 'v5.3.0' in html
    # Bootstrap Icons must be inlined too — library emits bi bi-* classes
    assert 'bootstrap-icons' in html
    assert 'data:font/woff2;base64,' in html

    renderer_cdn = EnhancedFormRenderer(
        framework='bootstrap',
        include_framework_assets=True,
        asset_mode='cdn',
    )
    html_cdn = renderer_cdn.render_form_from_model(Demo)
    assert 'cdn.jsdelivr.net/npm/bootstrap@5.3.0' in html_cdn
    assert 'cdn.jsdelivr.net/npm/bootstrap-icons@' in html_cdn


def test_render_form_html_self_contained_bootstrap_inlines_assets() -> None:
    from pydantic_schemaforms.enhanced_renderer import render_form_html
    from pydantic_schemaforms.schema_form import FormModel, Field

    class Demo(FormModel):
        name: str = Field(title='Name')

    html = render_form_html(
        Demo,
        framework='bootstrap',
        self_contained=True,
        submit_url='/demo',
    )
    assert '<style>' in html
    assert 'cdn.jsdelivr.net' not in html
    assert 'Bootstrap' in html
    assert 'v5.3.0' in html
    # Icons must be self-contained too
    assert 'bootstrap-icons' in html
    assert 'data:font/woff2;base64,' in html


def test_bootstrap_icons_css_tag_modes() -> None:
    from pydantic_schemaforms.assets.runtime import bootstrap_icons_css_tag

    # vendored: inline <style> with embedded woff2
    tag = bootstrap_icons_css_tag(asset_mode='vendored')
    assert tag.startswith('<style>')
    assert 'bootstrap-icons' in tag
    assert 'data:font/woff2;base64,' in tag
    assert 'url("fonts/' not in tag  # relative path must be replaced

    # cdn: pinned jsdelivr link
    cdn_tag = bootstrap_icons_css_tag(asset_mode='cdn')
    assert 'cdn.jsdelivr.net' in cdn_tag
    assert 'bootstrap-icons' in cdn_tag
    assert '<link' in cdn_tag

    # none: empty
    assert bootstrap_icons_css_tag(asset_mode='none') == ''


def test_bootstrap_icons_css_content_is_raw_css() -> None:
    from pydantic_schemaforms.assets.runtime import bootstrap_icons_css_content

    css = bootstrap_icons_css_content()
    assert 'bootstrap-icons' in css
    assert 'data:font/woff2;base64,' in css
    assert not css.startswith('<')  # raw CSS, not a tag


def test_material_theme_does_not_include_bootstrap_icons() -> None:
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_schemaforms.schema_form import FormModel, Field

    class Demo(FormModel):
        name: str = Field(title='Name')

    renderer = EnhancedFormRenderer(
        framework='material',
        include_framework_assets=True,
        asset_mode='vendored',
    )
    html = renderer.render_form_from_model(Demo)
    # Bootstrap Icons are Bootstrap-specific; material theme must not inject them
    assert 'data:font/woff2;base64,' not in html


def test_form_builder_include_assets_requires_cdn_mode() -> None:
    from pydantic_schemaforms.integration.builder import FormBuilder

    builder = FormBuilder(
        framework='bootstrap',
        include_framework_assets=True,
        asset_mode='vendored',
    ).text_input('name', 'Name')

    html = builder.render()
    assert 'cdn.jsdelivr.net' not in html

    builder_cdn = FormBuilder(
        framework='bootstrap',
        include_framework_assets=True,
        asset_mode='cdn',
    ).text_input('name', 'Name')

    html_cdn = builder_cdn.render()
    assert 'cdn.jsdelivr.net/npm/bootstrap@5.3.0' in html_cdn


def test_render_form_html_material_uses_single_dispatch_path() -> None:
    """render_form_html(framework='material') must go through EnhancedFormRenderer.

    Previously the material branch was hardcoded to SimpleMaterialRenderer and
    silently ignored include_framework_assets / asset_mode / self_contained.
    The unified path means those flags now work correctly for all frameworks.
    """
    from pydantic_schemaforms.enhanced_renderer import render_form_html
    from pydantic_schemaforms.schema_form import FormModel, Field

    class Demo(FormModel):
        name: str = Field(title='Name')
        email: str = Field(..., ui_element='email', title='Email')

    # Material form rendered without explicit assets — no embedded CSS/JS
    plain = render_form_html(Demo, framework='material', submit_url='/demo')
    assert 'md-input' in plain or 'md-form' in plain  # Material markup present

    # self_contained=True now works for material (was silently ignored before)
    self_cont = render_form_html(
        Demo, framework='material', submit_url='/demo', self_contained=True
    )
    assert 'md-input' in self_cont or 'md-form' in self_cont
    # The embedded CSS block must be present since self_contained implies include_framework_assets
    assert '<style>' in self_cont


def test_enhanced_form_renderer_material_output_matches_simple_material_renderer() -> None:
    """EnhancedFormRenderer(framework='material') and SimpleMaterialRenderer produce identical HTML."""
    import re
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_schemaforms.simple_material_renderer import SimpleMaterialRenderer
    from pydantic_schemaforms.schema_form import FormModel, Field

    class Demo(FormModel):
        name: str = Field(..., title='Name')
        email: str = Field(..., ui_element='email', title='Email')
        role: str = Field(..., ui_element='select', options=['admin', 'user'], title='Role')
        active: bool = Field(True, title='Active')

    def norm(s: str) -> str:
        return re.sub(r'\s+', ' ', s).strip()

    smr_html = norm(SimpleMaterialRenderer().render_form_from_model(Demo, submit_url='/t'))
    efr_html = norm(
        EnhancedFormRenderer(framework='material').render_form_from_model(Demo, submit_url='/t')
    )

    assert smr_html == efr_html


def test_simple_material_renderer_is_backward_compat_alias() -> None:
    """SimpleMaterialRenderer is kept as a thin subclass of EnhancedFormRenderer."""
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_schemaforms.simple_material_renderer import (
        SimpleMaterialRenderer,
        MaterialDesign3Renderer,
    )

    renderer = SimpleMaterialRenderer()
    assert isinstance(renderer, EnhancedFormRenderer)
    assert renderer.framework == 'material'

    alias = MaterialDesign3Renderer()
    assert isinstance(alias, EnhancedFormRenderer)
    assert alias.framework == 'material'


# ===========================================================================
# Tests from test_no_external_cdn_default.py
# ===========================================================================


def test_render_form_default_has_no_unpkg() -> None:
    html = render_form_html(_CdnCheckForm, submit_url='/test')
    assert 'unpkg.com' not in html


def test_render_form_cdn_mode_includes_unpkg() -> None:
    html = render_form_html(_CdnCheckForm, asset_mode='cdn', submit_url='/test')
    assert 'unpkg.com' in html
    v = vendored_asset_version('htmx')
    assert v is not None
    assert f'htmx.org@{v}' in html


def test_self_contained_form_has_no_cdn_urls() -> None:
    from pydantic_schemaforms.enhanced_renderer import render_form_html as enhanced_render

    html = enhanced_render(_CdnCheckForm, submit_url='/test', self_contained=True)
    assert 'cdn.jsdelivr.net' not in html
    assert 'unpkg.com' not in html
    # Bootstrap Icons woff2 must be embedded, not fetched from network
    assert 'data:font/woff2;base64,' in html


def test_bootstrap_icons_vendored_version_is_recorded() -> None:
    v = vendored_asset_version('bootstrap-icons')
    assert v is not None
    assert v.count('.') >= 1  # semver-ish


# ===========================================================================
# Tests from test_no_external_cdn_more.py
# ===========================================================================


def test_render_form_page_offline_by_default() -> None:
    from pydantic_schemaforms.integration.builder import create_login_form, render_form_page

    html = render_form_page(create_login_form(), title='Login')
    assert 'cdn.jsdelivr.net' not in html
    assert 'fonts.googleapis.com' not in html


def test_render_form_page_cdn_opt_in_includes_bootstrap() -> None:
    from pydantic_schemaforms.integration.builder import create_login_form, render_form_page

    html = render_form_page(
        create_login_form(),
        title='Login',
        include_framework_assets=True,
        asset_mode='cdn',
    )
    assert 'cdn.jsdelivr.net/npm/bootstrap@5.3.0' in html
    assert 'cdn.jsdelivr.net/npm/bootstrap-icons@' in html


def test_render_form_page_vendored_includes_bootstrap_icons() -> None:
    from pydantic_schemaforms.integration.builder import create_login_form, render_form_page

    html = render_form_page(
        create_login_form(),
        title='Login',
        include_framework_assets=True,
        asset_mode='vendored',
    )
    assert 'cdn.jsdelivr.net' not in html
    assert 'data:font/woff2;base64,' in html


def test_form_design_framework_urls_offline_by_default() -> None:
    from pydantic_schemaforms.form_layouts import FormDesign

    design = FormDesign(ui_theme='bootstrap')
    assert design.get_framework_css_url() == ''
    assert design.get_framework_js_url() == ''


def test_material_theme_css_has_no_google_fonts_imports() -> None:
    from pydantic_schemaforms.rendering.themes import MaterialEmbeddedTheme

    css = MaterialEmbeddedTheme._build_css()
    assert 'fonts.googleapis.com' not in css
    assert 'fonts.gstatic.com' not in css
