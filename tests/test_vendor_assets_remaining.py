"""Test remaining vendor_assets.py functions (vendor_materialize, vendor_bootstrap, verify_manifest_files)."""

import json
import zipfile
import io
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from pydantic_forms.vendor_assets import (
    vendor_materialize,
    vendor_bootstrap,
    verify_manifest_files,
)


class TestVendorMaterialize:
    """Test vendor_materialize function with mocking."""
    
    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    @patch('pydantic_forms.vendor_assets.npm_tarball_url')
    def test_vendor_materialize_with_license(
        self, mock_tarball_url, mock_http, mock_extract,
        mock_write, mock_load, mock_upsert, mock_save
    ):
        """Test vendor_materialize extracts CSS, JS, and LICENSE."""
        mock_tarball_url.return_value = 'https://registry.npmjs.org/@materializecss/materialize/-/materialize-2.1.1.tgz'
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
    
    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    @patch('pydantic_forms.vendor_assets.npm_tarball_url')
    def test_vendor_materialize_tries_license_md_fallback(
        self, mock_tarball_url, mock_http, mock_extract,
        mock_write, mock_load, mock_upsert, mock_save
    ):
        """Test vendor_materialize tries LICENSE.md if LICENSE not found."""
        mock_tarball_url.return_value = 'url'
        mock_http.return_value = b'tgz'
        # CSS, JS, LICENSE (not found), LICENSE.md (found)
        mock_extract.side_effect = [
            b'css',
            b'js',
            FileNotFoundError('LICENSE not found'),
            b'license md'
        ]
        mock_write.side_effect = [
            {'path': 'css', 'sha256': 'a', 'source_url': 'url'},
            {'path': 'js', 'sha256': 'b', 'source_url': 'url'},
            {'path': 'lic', 'sha256': 'c', 'source_url': 'url'},
        ]
        mock_load.return_value = {'schema_version': 1}
        
        result = vendor_materialize(version='2.1.1')
        
        assert mock_extract.call_count == 4
        assert mock_write.call_count == 3
    
    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    @patch('pydantic_forms.vendor_assets.npm_tarball_url')
    def test_vendor_materialize_sets_schema_version(
        self, mock_tarball_url, mock_http, mock_extract,
        mock_write, mock_load, mock_upsert, mock_save
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
    
    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
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
    
    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
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
    
    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
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
    
    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
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
    
    @patch('pydantic_forms.vendor_assets.sha256_file')
    @patch('pydantic_forms.vendor_assets.project_root')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_valid(self, mock_load, mock_root, mock_sha256):
        """Test verify_manifest_files with valid manifest."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [
                {
                    'name': 'htmx',
                    'files': [
                        {'path': 'pydantic_forms/assets/vendor/htmx/htmx.min.js', 'sha256': 'a' * 64}
                    ]
                }
            ]
        }
        # Create a mock Path that returns True for exists()
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        
        mock_root_path = MagicMock(spec=Path)
        mock_root_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_root.return_value = mock_root_path
        
        mock_sha256.return_value = 'a' * 64
        
        verify_manifest_files()  # Should not raise
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_missing_schema_version_raises(self, mock_load):
        """Test verify_manifest_files raises if schema_version missing."""
        mock_load.return_value = {'assets': []}
        
        with pytest.raises(ValueError, match='missing integer schema_version'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_schema_version_not_int_raises(self, mock_load):
        """Test verify_manifest_files raises if schema_version not int."""
        mock_load.return_value = {'schema_version': '1', 'assets': []}
        
        with pytest.raises(ValueError, match='missing integer schema_version'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_missing_assets_raises(self, mock_load):
        """Test verify_manifest_files raises if assets missing."""
        mock_load.return_value = {'schema_version': 1}
        
        with pytest.raises(ValueError, match='assets must be a list'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_assets_not_list_raises(self, mock_load):
        """Test verify_manifest_files raises if assets not list."""
        mock_load.return_value = {'schema_version': 1, 'assets': 'string'}
        
        with pytest.raises(ValueError, match='assets must be a list'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_require_nonempty_empty_raises(self, mock_load):
        """Test verify_manifest_files raises if require_nonempty and assets empty."""
        mock_load.return_value = {'schema_version': 1, 'assets': []}
        
        with pytest.raises(ValueError, match='has no assets'):
            verify_manifest_files(require_nonempty=True)
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_asset_not_dict_raises(self, mock_load):
        """Test verify_manifest_files raises if asset entry not dict."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': ['string']
        }
        
        with pytest.raises(ValueError, match='asset entries must be objects'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_missing_files_list_raises(self, mock_load):
        """Test verify_manifest_files raises if files list missing."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx'}]
        }
        
        with pytest.raises(ValueError, match='missing files list'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_files_not_list_raises(self, mock_load):
        """Test verify_manifest_files raises if files not list."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': 'string'}]
        }
        
        with pytest.raises(ValueError, match='missing files list'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_file_entry_not_dict_raises(self, mock_load):
        """Test verify_manifest_files raises if file entry not dict."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': ['string']}]
        }
        
        with pytest.raises(ValueError, match='file entries must be objects'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_missing_path_raises(self, mock_load):
        """Test verify_manifest_files raises if file missing path."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': [{}]}]
        }
        
        with pytest.raises(ValueError, match='missing path'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_empty_path_raises(self, mock_load):
        """Test verify_manifest_files raises if path empty."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': [{'path': ''}]}]
        }
        
        with pytest.raises(ValueError, match='missing path'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_missing_sha256_raises(self, mock_load):
        """Test verify_manifest_files raises if sha256 missing."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': [{'path': 'file.js'}]}]
        }
        
        with pytest.raises(ValueError, match='missing sha256'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_sha256_wrong_length_raises(self, mock_load):
        """Test verify_manifest_files raises if sha256 wrong length."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [{'name': 'htmx', 'files': [{'path': 'file.js', 'sha256': 'short'}]}]
        }
        
        with pytest.raises(ValueError, match='missing sha256'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.project_root')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_file_not_exists_raises(self, mock_load, mock_root):
        """Test verify_manifest_files raises if file doesn't exist."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [
                {
                    'name': 'htmx',
                    'files': [{'path': 'missing.js', 'sha256': 'a' * 64}]
                }
            ]
        }
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        
        mock_root_path = MagicMock(spec=Path)
        mock_root_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_root.return_value = mock_root_path
        
        with pytest.raises(FileNotFoundError, match='vendored file missing'):
            verify_manifest_files()
    
    @patch('pydantic_forms.vendor_assets.sha256_file')
    @patch('pydantic_forms.vendor_assets.project_root')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    def test_verify_manifest_files_sha256_mismatch_raises(self, mock_load, mock_root, mock_sha256):
        """Test verify_manifest_files raises if sha256 mismatch."""
        mock_load.return_value = {
            'schema_version': 1,
            'assets': [
                {
                    'name': 'htmx',
                    'files': [{'path': 'file.js', 'sha256': 'a' * 64}]
                }
            ]
        }
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        
        mock_root_path = MagicMock(spec=Path)
        mock_root_path.__truediv__ = MagicMock(return_value=mock_path)
        mock_root.return_value = mock_root_path
        
        mock_sha256.return_value = 'b' * 64  # Different hash
        
        with pytest.raises(ValueError, match='sha256 mismatch'):
            verify_manifest_files()
