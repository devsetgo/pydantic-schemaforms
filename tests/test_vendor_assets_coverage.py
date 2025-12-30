"""
Tests for vendor_assets.py to improve coverage.
Tests utility functions but not the actual vendoring functions that make network calls.
"""

import json
import hashlib
import io
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest

from pydantic_forms.vendor_assets import (
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
)


class TestVendoredFile:
    """Test VendoredFile dataclass."""

    def test_vendored_file_creation(self):
        """Test creating a VendoredFile."""
        vf = VendoredFile(
            path="assets/test.js",
            sha256="abc123",
            source_url="https://example.com/test.js",
        )
        assert vf.path == "assets/test.js"
        assert vf.sha256 == "abc123"
        assert vf.source_url == "https://example.com/test.js"

    def test_vendored_file_frozen(self):
        """Test that VendoredFile is frozen."""
        vf = VendoredFile(
            path="test.js",
            sha256="hash",
            source_url="url",
        )
        with pytest.raises(Exception):  # dataclass frozen error
            vf.path = "new_path"


class TestProjectRoot:
    """Test project_root function."""

    def test_project_root_returns_path(self):
        """Test that project_root returns a Path object."""
        root = project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_project_root_contains_pydantic_forms(self):
        """Test that project root contains pydantic_forms directory."""
        root = project_root()
        pydantic_forms_dir = root / "pydantic_forms"
        assert pydantic_forms_dir.exists()


class TestManifestPath:
    """Test manifest_path function."""

    def test_manifest_path_returns_path(self):
        """Test that manifest_path returns a Path object."""
        path = manifest_path()
        assert isinstance(path, Path)

    def test_manifest_path_contains_vendor_manifest(self):
        """Test that manifest path contains vendor_manifest.json."""
        path = manifest_path()
        assert "vendor_manifest.json" in str(path)


class TestSha256Functions:
    """Test SHA256 hashing functions."""

    def test_sha256_bytes_empty(self):
        """Test SHA256 of empty bytes."""
        result = sha256_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_sha256_bytes_hello_world(self):
        """Test SHA256 of 'hello world'."""
        data = b"hello world"
        result = sha256_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert result == expected
        assert len(result) == 64  # SHA256 produces 64 hex characters

    def test_sha256_bytes_returns_hex_string(self):
        """Test that sha256_bytes returns a hex string."""
        result = sha256_bytes(b"test")
        assert isinstance(result, str)
        assert len(result) == 64
        # Should be all hex characters
        assert all(c in "0123456789abcdef" for c in result)

    @patch("pydantic_forms.vendor_assets.Path.read_bytes")
    def test_sha256_file(self, mock_read_bytes):
        """Test sha256_file function."""
        mock_read_bytes.return_value = b"file content"
        expected = hashlib.sha256(b"file content").hexdigest()

        path = Path("/fake/path.txt")
        result = sha256_file(path)

        assert result == expected
        mock_read_bytes.assert_called_once()


class TestEnsureParentDir:
    """Test ensure_parent_dir function."""

    @patch("pydantic_forms.vendor_assets.Path.mkdir")
    def test_ensure_parent_dir_creates_parents(self, mock_mkdir):
        """Test that ensure_parent_dir creates parent directories."""
        path = Path("/fake/nested/directory/file.txt")
        ensure_parent_dir(path)

        # Should call mkdir on the parent with parents=True, exist_ok=True
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("pydantic_forms.vendor_assets.Path.mkdir")
    def test_ensure_parent_dir_with_existing_dir(self, mock_mkdir):
        """Test ensure_parent_dir with existing directory."""
        path = Path("/existing/file.txt")
        ensure_parent_dir(path)

        # Should still call mkdir (exist_ok=True handles existing dirs)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestUpsertAssetEntry:
    """Test upsert_asset_entry function."""

    def test_upsert_asset_entry_adds_new(self):
        """Test adding a new asset entry."""
        manifest = {}
        entry = {"name": "test-lib", "version": "1.0.0"}

        upsert_asset_entry(manifest, name="test-lib", entry=entry)

        assert "assets" in manifest
        assert len(manifest["assets"]) == 1
        assert manifest["assets"][0] == entry

    def test_upsert_asset_entry_updates_existing(self):
        """Test updating an existing asset entry."""
        manifest = {
            "assets": [
                {"name": "lib-a", "version": "1.0.0"},
                {"name": "lib-b", "version": "2.0.0"},
            ]
        }
        new_entry = {"name": "lib-a", "version": "1.5.0"}

        upsert_asset_entry(manifest, name="lib-a", entry=new_entry)

        assert len(manifest["assets"]) == 2
        assert manifest["assets"][0] == new_entry
        assert manifest["assets"][1]["name"] == "lib-b"

    def test_upsert_asset_entry_preserves_other_assets(self):
        """Test that updating one asset preserves others."""
        manifest = {
            "assets": [
                {"name": "keep-me", "version": "1.0.0"},
            ]
        }
        new_entry = {"name": "new-lib", "version": "2.0.0"}

        upsert_asset_entry(manifest, name="new-lib", entry=new_entry)

        assert len(manifest["assets"]) == 2
        assert manifest["assets"][0]["name"] == "keep-me"
        assert manifest["assets"][1] == new_entry

    def test_upsert_asset_entry_with_empty_manifest(self):
        """Test upsert with completely empty manifest."""
        manifest = {}
        entry = {"name": "first", "version": "0.1.0"}

        upsert_asset_entry(manifest, name="first", entry=entry)

        assert "assets" in manifest
        assert manifest["assets"] == [entry]


class TestEnvTruthy:
    """Test env_truthy function."""

    @patch.dict("os.environ", {"TEST_VAR": "1"})
    def test_env_truthy_with_one(self):
        """Test env_truthy with '1'."""
        assert env_truthy("TEST_VAR") is True

    @patch.dict("os.environ", {"TEST_VAR": "true"})
    def test_env_truthy_with_true(self):
        """Test env_truthy with 'true'."""
        assert env_truthy("TEST_VAR") is True

    @patch.dict("os.environ", {"TEST_VAR": "TRUE"})
    def test_env_truthy_with_uppercase_true(self):
        """Test env_truthy with 'TRUE'."""
        assert env_truthy("TEST_VAR") is True

    @patch.dict("os.environ", {"TEST_VAR": "yes"})
    def test_env_truthy_with_yes(self):
        """Test env_truthy with 'yes'."""
        assert env_truthy("TEST_VAR") is True

    @patch.dict("os.environ", {"TEST_VAR": "YES"})
    def test_env_truthy_with_uppercase_yes(self):
        """Test env_truthy with 'YES'."""
        assert env_truthy("TEST_VAR") is True

    @patch.dict("os.environ", {"TEST_VAR": "on"})
    def test_env_truthy_with_on(self):
        """Test env_truthy with 'on'."""
        assert env_truthy("TEST_VAR") is True

    @patch.dict("os.environ", {"TEST_VAR": "ON"})
    def test_env_truthy_with_uppercase_on(self):
        """Test env_truthy with 'ON'."""
        assert env_truthy("TEST_VAR") is True

    @patch.dict("os.environ", {"TEST_VAR": "0"})
    def test_env_truthy_with_zero(self):
        """Test env_truthy with '0'."""
        assert env_truthy("TEST_VAR") is False

    @patch.dict("os.environ", {"TEST_VAR": "false"})
    def test_env_truthy_with_false(self):
        """Test env_truthy with 'false'."""
        assert env_truthy("TEST_VAR") is False

    @patch.dict("os.environ", {"TEST_VAR": ""})
    def test_env_truthy_with_empty_string(self):
        """Test env_truthy with empty string."""
        assert env_truthy("TEST_VAR") is False

    @patch.dict("os.environ", {}, clear=True)
    def test_env_truthy_with_unset_var(self):
        """Test env_truthy with unset variable."""
        assert env_truthy("NONEXISTENT_VAR") is False

    @patch.dict("os.environ", {"TEST_VAR": "  1  "})
    def test_env_truthy_with_whitespace(self):
        """Test env_truthy handles whitespace."""
        assert env_truthy("TEST_VAR") is True


class TestSafeMemberBytesFromTgz:
    """Test _safe_member_bytes_from_tgz function."""

    def test_extract_file_with_package_prefix(self):
        """Test extracting a file with 'package/' prefix."""
        # Create a fake tar.gz with a file
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            info = tarfile.TarInfo(name="package/test.txt")
            info.size = 12
            tf.addfile(info, io.BytesIO(b"hello world!"))

        tar_bytes = tar_buffer.getvalue()
        result = _safe_member_bytes_from_tgz(tar_bytes, "test.txt")

        assert result == b"hello world!"

    def test_extract_file_without_prefix(self):
        """Test extracting a file without prefix."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            info = tarfile.TarInfo(name="plain.txt")
            info.size = 5
            tf.addfile(info, io.BytesIO(b"plain"))

        tar_bytes = tar_buffer.getvalue()
        result = _safe_member_bytes_from_tgz(tar_bytes, "plain.txt")

        assert result == b"plain"

    def test_extract_file_with_explicit_package_prefix(self):
        """Test extracting with 'package/' in request."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            info = tarfile.TarInfo(name="package/nested/file.js")
            info.size = 7
            tf.addfile(info, io.BytesIO(b"content"))

        tar_bytes = tar_buffer.getvalue()
        result = _safe_member_bytes_from_tgz(tar_bytes, "nested/file.js")

        assert result == b"content"

    def test_extract_missing_file_raises_error(self):
        """Test that missing file raises FileNotFoundError."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            info = tarfile.TarInfo(name="package/exists.txt")
            info.size = 4
            tf.addfile(info, io.BytesIO(b"data"))

        tar_bytes = tar_buffer.getvalue()

        with pytest.raises(FileNotFoundError, match="missing file in npm tarball"):
            _safe_member_bytes_from_tgz(tar_bytes, "nonexistent.txt")

    def test_extract_directory_raises_error(self):
        """Test that directory member raises ValueError."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            # Add a directory
            info = tarfile.TarInfo(name="package/dir")
            info.type = tarfile.DIRTYPE
            tf.addfile(info)

        tar_bytes = tar_buffer.getvalue()

        with pytest.raises(ValueError, match="not a file"):
            _safe_member_bytes_from_tgz(tar_bytes, "dir")


class TestWriteVendoredFile:
    """Test _write_vendored_file function."""

    @patch("pydantic_forms.vendor_assets.project_root")
    @patch("pydantic_forms.vendor_assets.ensure_parent_dir")
    @patch("pydantic_forms.vendor_assets.Path.write_bytes")
    def test_write_vendored_file(self, mock_write_bytes, mock_ensure_dir, mock_project_root):
        """Test writing a vendored file."""
        mock_project_root.return_value = Path("/project")
        
        data = b"file content"
        rel_path = Path("assets/vendor/lib.js")
        source_url = "https://example.com/lib.js"

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
        assert result["path"] == "assets/vendor/lib.js"
        assert result["sha256"] == hashlib.sha256(data).hexdigest()
        assert result["source_url"] == source_url

    @patch("pydantic_forms.vendor_assets.project_root")
    @patch("pydantic_forms.vendor_assets.ensure_parent_dir")
    @patch("pydantic_forms.vendor_assets.Path.write_bytes")
    def test_write_vendored_file_creates_correct_path(self, mock_write_bytes, mock_ensure_dir, mock_project_root):
        """Test that correct absolute path is created."""
        mock_project_root.return_value = Path("/root")
        
        rel_path = Path("sub/file.txt")
        _write_vendored_file(
            rel_path=rel_path,
            data=b"test",
            source_url="http://test.com",
        )

        # Verify ensure_parent_dir was called with the right path
        call_args = mock_ensure_dir.call_args[0][0]
        assert "/root/sub/file.txt" in str(call_args)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
