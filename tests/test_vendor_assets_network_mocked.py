"""Test vendor_assets.py network-dependent functions with mocking."""

import json
from unittest.mock import patch, MagicMock
import pytest

from pydantic_forms.vendor_assets import (
    http_get_bytes,
    latest_htmx_version,
    npm_package_metadata,
    latest_npm_version,
    npm_tarball_url,
    vendor_htmx,
    vendor_imask,
)


class TestHttpGetBytes:
    """Test http_get_bytes function with mocking."""

    @patch('pydantic_forms.vendor_assets.urlopen')
    @patch('pydantic_forms.vendor_assets.Request')
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
            headers={'User-Agent': 'pydantic-forms-vendor-script'}
        )

    @patch('pydantic_forms.vendor_assets.urlopen')
    @patch('pydantic_forms.vendor_assets.Request')
    def test_http_get_bytes_custom_user_agent(self, mock_request, mock_urlopen):
        """Test http_get_bytes with custom user agent."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'data'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False
        mock_urlopen.return_value = mock_response

        http_get_bytes('https://example.com/api', user_agent='custom-agent')

        mock_request.assert_called_once_with(
            'https://example.com/api',
            headers={'User-Agent': 'custom-agent'}
        )


class TestLatestHtmxVersion:
    """Test latest_htmx_version function with mocking."""

    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    def test_latest_htmx_version_with_v_prefix(self, mock_http):
        """Test latest_htmx_version strips 'v' prefix."""
        mock_http.return_value = json.dumps({'tag_name': 'v2.0.3'}).encode('utf-8')

        result = latest_htmx_version()

        assert result == '2.0.3'
        mock_http.assert_called_once()

    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    def test_latest_htmx_version_without_v_prefix(self, mock_http):
        """Test latest_htmx_version without 'v' prefix."""
        mock_http.return_value = json.dumps({'tag_name': '2.0.3'}).encode('utf-8')

        result = latest_htmx_version()

        assert result == '2.0.3'

    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    def test_latest_htmx_version_with_whitespace(self, mock_http):
        """Test latest_htmx_version strips whitespace."""
        mock_http.return_value = json.dumps({'tag_name': ' v2.0.3 '}).encode('utf-8')

        result = latest_htmx_version()

        assert result == '2.0.3'

    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    def test_latest_htmx_version_empty_tag(self, mock_http):
        """Test latest_htmx_version with empty tag."""
        mock_http.return_value = json.dumps({'tag_name': ''}).encode('utf-8')

        result = latest_htmx_version()

        assert result == ''


class TestNpmPackageMetadata:
    """Test npm_package_metadata function with mocking."""

    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    def test_npm_package_metadata_returns_dict(self, mock_http):
        """Test npm_package_metadata returns metadata dict."""
        metadata = {'name': 'imask', 'version': '7.6.1'}
        mock_http.return_value = json.dumps(metadata).encode('utf-8')

        result = npm_package_metadata('imask')

        assert result == metadata
        mock_http.assert_called_once_with('https://registry.npmjs.org/imask')

    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    def test_npm_package_metadata_not_dict_raises(self, mock_http):
        """Test npm_package_metadata raises when response is not dict."""
        mock_http.return_value = json.dumps(['array']).encode('utf-8')

        with pytest.raises(ValueError, match='was not an object'):
            npm_package_metadata('badpackage')


class TestLatestNpmVersion:
    """Test latest_npm_version function with mocking."""

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_returns_latest(self, mock_metadata):
        """Test latest_npm_version returns latest version."""
        mock_metadata.return_value = {
            'dist-tags': {'latest': '7.6.1', 'beta': '8.0.0-beta.1'}
        }

        result = latest_npm_version('imask')

        assert result == '7.6.1'

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_strips_whitespace(self, mock_metadata):
        """Test latest_npm_version strips whitespace."""
        mock_metadata.return_value = {
            'dist-tags': {'latest': '  7.6.1  '}
        }

        result = latest_npm_version('imask')

        assert result == '7.6.1'

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_missing_dist_tags_raises(self, mock_metadata):
        """Test latest_npm_version raises when dist-tags missing."""
        mock_metadata.return_value = {}

        with pytest.raises(ValueError, match='missing dist-tags'):
            latest_npm_version('badpackage')

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_dist_tags_not_dict_raises(self, mock_metadata):
        """Test latest_npm_version raises when dist-tags not dict."""
        mock_metadata.return_value = {'dist-tags': 'string'}

        with pytest.raises(ValueError, match='missing dist-tags'):
            latest_npm_version('badpackage')

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_missing_latest_raises(self, mock_metadata):
        """Test latest_npm_version raises when latest tag missing."""
        mock_metadata.return_value = {'dist-tags': {'beta': '8.0.0'}}

        with pytest.raises(ValueError, match='missing latest dist-tag'):
            latest_npm_version('badpackage')

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_latest_npm_version_empty_latest_raises(self, mock_metadata):
        """Test latest_npm_version raises when latest tag empty."""
        mock_metadata.return_value = {'dist-tags': {'latest': '  '}}

        with pytest.raises(ValueError, match='missing latest dist-tag'):
            latest_npm_version('badpackage')


class TestNpmTarballUrl:
    """Test npm_tarball_url function with mocking."""

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_returns_url(self, mock_metadata):
        """Test npm_tarball_url returns tarball URL."""
        mock_metadata.return_value = {
            'versions': {
                '7.6.1': {
                    'dist': {
                        'tarball': 'https://registry.npmjs.org/imask/-/imask-7.6.1.tgz'
                    }
                }
            }
        }

        result = npm_tarball_url('imask', '7.6.1')

        assert result == 'https://registry.npmjs.org/imask/-/imask-7.6.1.tgz'

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_strips_whitespace(self, mock_metadata):
        """Test npm_tarball_url strips whitespace from URL."""
        mock_metadata.return_value = {
            'versions': {
                '7.6.1': {
                    'dist': {
                        'tarball': '  https://registry.npmjs.org/imask/-/imask-7.6.1.tgz  '
                    }
                }
            }
        }

        result = npm_tarball_url('imask', '7.6.1')

        assert result == 'https://registry.npmjs.org/imask/-/imask-7.6.1.tgz'

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_missing_version_raises(self, mock_metadata):
        """Test npm_tarball_url raises when version missing."""
        mock_metadata.return_value = {
            'versions': {'7.6.0': {}}
        }

        with pytest.raises(ValueError, match='missing version 7.6.1'):
            npm_tarball_url('imask', '7.6.1')

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_versions_not_dict_raises(self, mock_metadata):
        """Test npm_tarball_url raises when versions not dict."""
        mock_metadata.return_value = {'versions': 'string'}

        with pytest.raises(ValueError, match='missing version'):
            npm_tarball_url('badpackage', '1.0.0')

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_version_meta_not_dict_raises(self, mock_metadata):
        """Test npm_tarball_url raises when version metadata invalid."""
        mock_metadata.return_value = {
            'versions': {'7.6.1': 'string'}
        }

        with pytest.raises(ValueError, match='invalid'):
            npm_tarball_url('imask', '7.6.1')

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_missing_dist_raises(self, mock_metadata):
        """Test npm_tarball_url raises when dist missing."""
        mock_metadata.return_value = {
            'versions': {'7.6.1': {}}
        }

        with pytest.raises(ValueError, match='missing dist'):
            npm_tarball_url('imask', '7.6.1')

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_dist_not_dict_raises(self, mock_metadata):
        """Test npm_tarball_url raises when dist not dict."""
        mock_metadata.return_value = {
            'versions': {'7.6.1': {'dist': 'string'}}
        }

        with pytest.raises(ValueError, match='missing dist'):
            npm_tarball_url('imask', '7.6.1')

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_missing_tarball_raises(self, mock_metadata):
        """Test npm_tarball_url raises when tarball missing."""
        mock_metadata.return_value = {
            'versions': {'7.6.1': {'dist': {}}}
        }

        with pytest.raises(ValueError, match='missing tarball url'):
            npm_tarball_url('imask', '7.6.1')

    @patch('pydantic_forms.vendor_assets.npm_package_metadata')
    def test_npm_tarball_url_empty_tarball_raises(self, mock_metadata):
        """Test npm_tarball_url raises when tarball URL empty."""
        mock_metadata.return_value = {
            'versions': {'7.6.1': {'dist': {'tarball': '  '}}}
        }

        with pytest.raises(ValueError, match='missing tarball url'):
            npm_tarball_url('imask', '7.6.1')


class TestVendorHtmx:
    """Test vendor_htmx function with mocking."""

    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    @patch('pydantic_forms.vendor_assets.latest_htmx_version')
    def test_vendor_htmx_with_explicit_version(
        self, mock_latest, mock_http, mock_write, mock_load, mock_upsert, mock_save
    ):
        """Test vendor_htmx with explicit version."""
        mock_http.side_effect = [b'js content', b'license content']
        mock_write.side_effect = [
            {'path': 'pydantic_forms/assets/vendor/htmx/htmx.min.js', 'sha256': 'abcd1234', 'source_url': 'https://example.com/htmx.min.js'},
            {'path': 'pydantic_forms/assets/vendor/htmx/LICENSE', 'sha256': 'efgh5678', 'source_url': 'https://example.com/LICENSE'},
        ]
        mock_load.return_value = {'schema_version': 1, 'assets': []}

        result = vendor_htmx(version='2.0.3')

        assert result.path == 'pydantic_forms/assets/vendor/htmx/htmx.min.js'
        assert result.sha256 == 'abcd1234'
        mock_latest.assert_not_called()
        assert mock_http.call_count == 2
        assert mock_write.call_count == 2
        mock_upsert.assert_called_once()
        mock_save.assert_called_once()

    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    @patch('pydantic_forms.vendor_assets.latest_htmx_version')
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

    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
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

    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    @patch('pydantic_forms.vendor_assets.npm_tarball_url')
    @patch('pydantic_forms.vendor_assets.latest_npm_version')
    def test_vendor_imask_with_explicit_version(
        self, mock_latest, mock_tarball_url, mock_http, mock_extract,
        mock_write, mock_load, mock_upsert, mock_save
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

    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    @patch('pydantic_forms.vendor_assets.npm_tarball_url')
    @patch('pydantic_forms.vendor_assets.latest_npm_version')
    def test_vendor_imask_without_version_fetches_latest(
        self, mock_latest, mock_tarball_url, mock_http, mock_extract,
        mock_write, mock_load, mock_upsert, mock_save
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

    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    @patch('pydantic_forms.vendor_assets.npm_tarball_url')
    def test_vendor_imask_tries_license_md_fallback(
        self, mock_tarball_url, mock_http, mock_extract,
        mock_write, mock_load, mock_upsert, mock_save
    ):
        """Test vendor_imask tries LICENSE.md if LICENSE not found."""
        mock_tarball_url.return_value = 'url'
        mock_http.return_value = b'tgz'
        # First extract succeeds (js), second fails (LICENSE), third succeeds (LICENSE.md)
        mock_extract.side_effect = [
            b'js content',
            FileNotFoundError('LICENSE not found'),
            b'license md content'
        ]
        mock_write.side_effect = [
            {'path': 'js', 'sha256': 'a', 'source_url': 'url'},
            {'path': 'lic', 'sha256': 'b', 'source_url': 'url'},
        ]
        mock_load.return_value = {'schema_version': 1}

        vendor_imask(version='7.6.1')

        assert mock_extract.call_count == 3
        assert mock_write.call_count == 2

    @patch('pydantic_forms.vendor_assets.write_manifest')
    @patch('pydantic_forms.vendor_assets.upsert_asset_entry')
    @patch('pydantic_forms.vendor_assets.load_manifest')
    @patch('pydantic_forms.vendor_assets._write_vendored_file')
    @patch('pydantic_forms.vendor_assets._safe_member_bytes_from_tgz')
    @patch('pydantic_forms.vendor_assets.http_get_bytes')
    @patch('pydantic_forms.vendor_assets.npm_tarball_url')
    def test_vendor_imask_sets_schema_version(
        self, mock_tarball_url, mock_http, mock_extract,
        mock_write, mock_load, mock_upsert, mock_save
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
