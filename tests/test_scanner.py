"""Tests for the scanner module."""

import os
import pytest
import tempfile
from pathlib import Path
from locat.scanner import RepositoryScanner


class TestRepositoryScanner:
    """Test the RepositoryScanner class."""

    def test_parse_repo_url_simple(self):
        """Test parsing simple owner/repo format."""
        scanner = RepositoryScanner()

        owner, repo = scanner.parse_repo_url("torvalds/linux")

        assert owner == "torvalds"
        assert repo == "linux"

    def test_parse_repo_url_full(self):
        """Test parsing full GitHub URL."""
        scanner = RepositoryScanner()

        owner, repo = scanner.parse_repo_url("https://github.com/python/cpython")

        assert owner == "python"
        assert repo == "cpython"

    def test_parse_repo_url_with_git(self):
        """Test parsing URL with .git suffix."""
        scanner = RepositoryScanner()

        owner, repo = scanner.parse_repo_url("https://github.com/rust-lang/rust.git")

        assert owner == "rust-lang"
        assert repo == "rust"

    def test_parse_repo_url_invalid(self):
        """Test parsing invalid repository identifier."""
        scanner = RepositoryScanner()

        with pytest.raises(ValueError):
            scanner.parse_repo_url("invalid")

    def test_scan_files(self):
        """Test file scanning in a directory."""
        scanner = RepositoryScanner()

        # Create temporary directory with test files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test.py").write_text("print('hello')")
            (Path(tmpdir) / "script.js").write_text("console.log('world')")
            (Path(tmpdir) / "README.md").write_text("# Test")

            # Create subdirectory
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "main.go").write_text("package main")

            # Scan files
            files = scanner.scan_files(tmpdir)

            # Should find all non-hidden files
            paths = [f["path"] for f in files]
            assert any("test.py" in p for p in paths)
            assert any("script.js" in p for p in paths)
            assert any("README.md" in p for p in paths)
            assert any("main.go" in p for p in paths)

    def test_scan_files_with_extensions(self):
        """Test file scanning with extension filter."""
        scanner = RepositoryScanner()

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("print('hello')")
            (Path(tmpdir) / "script.js").write_text("console.log('world')")

            # Scan only Python files
            files = scanner.scan_files(tmpdir, extensions={".py"})

            paths = [f["path"] for f in files]
            assert len(paths) == 1
            assert "test.py" in paths[0]

    def test_read_file(self):
        """Test file reading."""
        scanner = RepositoryScanner()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_content = "Hello, World!"
            test_file.write_text(test_content)

            content = scanner.read_file(str(test_file))

            assert content == test_content

    def test_read_file_nonexistent(self):
        """Test reading non-existent file."""
        scanner = RepositoryScanner()

        content = scanner.read_file("/nonexistent/file.txt")

        assert content is None
