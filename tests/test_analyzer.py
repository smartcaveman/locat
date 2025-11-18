"""Tests for the analyzer module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from locat.analyzer import CodeAnalyzer


class TestCodeAnalyzer:
    """Test the CodeAnalyzer class."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = CodeAnalyzer()

        assert analyzer is not None
        assert analyzer.scanner is not None
        assert analyzer.fingerprinter is not None

    def test_track_duplicates(self):
        """Test duplicate tracking."""
        analyzer = CodeAnalyzer()

        fingerprint1 = {
            "filepath": "file1.py",
            "exact_hash": "hash1",
            "fuzzy_hash": "fuzzy1",
            "structural_hash": "struct1",
        }

        fingerprint2 = {
            "filepath": "file2.py",
            "exact_hash": "hash1",  # Same as file1
            "fuzzy_hash": "fuzzy2",
            "structural_hash": "struct2",
        }

        analyzer._track_duplicates(fingerprint1)
        analyzer._track_duplicates(fingerprint2)

        # Should detect exact duplicate
        assert "file1.py" in analyzer.duplicate_groups["exact"]
        assert "file2.py" in analyzer.duplicate_groups["exact"]

    def test_calculate_metrics_empty(self):
        """Test metrics calculation with no files."""
        analyzer = CodeAnalyzer()

        metrics = analyzer._calculate_metrics([], 0)

        assert metrics["total_files"] == 0
        assert metrics["uniqueness_score_exact"] == 0.0
        assert metrics["uniqueness_score_fuzzy"] == 0.0

    def test_calculate_metrics_with_files(self):
        """Test metrics calculation with sample files."""
        analyzer = CodeAnalyzer()

        fingerprints = [
            {
                "filepath": "file1.py",
                "exact_hash": "hash1",
                "fuzzy_hash": "fuzzy1",
                "structural_hash": "struct1",
            },
            {
                "filepath": "file2.py",
                "exact_hash": "hash2",
                "fuzzy_hash": "fuzzy1",  # Fuzzy duplicate
                "structural_hash": "struct2",
            },
            {
                "filepath": "file3.py",
                "exact_hash": "hash3",
                "fuzzy_hash": "fuzzy3",
                "structural_hash": "struct3",
            },
        ]

        # Track duplicates
        for fp in fingerprints:
            analyzer._track_duplicates(fp)

        metrics = analyzer._calculate_metrics(fingerprints, 1000)

        assert metrics["total_files"] == 3
        assert metrics["unique_files_exact"] == 3  # All different
        assert metrics["unique_files_fuzzy"] == 2  # One duplicate
        assert metrics["uniqueness_score_exact"] == 100.0
        assert metrics["uniqueness_score_fuzzy"] == pytest.approx(66.67, rel=0.01)

    def test_get_duplicate_files(self):
        """Test retrieving duplicate file groups."""
        analyzer = CodeAnalyzer()

        fingerprints = [
            {
                "filepath": "file1.py",
                "exact_hash": "hash1",
                "fuzzy_hash": "fuzzy1",
                "structural_hash": "struct1",
            },
            {
                "filepath": "file2.py",
                "exact_hash": "hash1",  # Exact duplicate
                "fuzzy_hash": "fuzzy1",
                "structural_hash": "struct1",
            },
        ]

        for fp in fingerprints:
            analyzer._track_duplicates(fp)

        duplicates = analyzer.get_duplicate_files("exact")

        assert len(duplicates) == 1
        assert "hash1" in duplicates
        assert "file1.py" in duplicates["hash1"]
        assert "file2.py" in duplicates["hash1"]
