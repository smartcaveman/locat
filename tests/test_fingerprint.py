"""Tests for the fingerprint module."""

import pytest
from locat.fingerprint import CodeFingerprinter


class TestCodeFingerprinter:
    """Test the CodeFingerprinter class."""

    def test_is_supported_file(self):
        """Test file extension detection."""
        fingerprinter = CodeFingerprinter()

        assert fingerprinter.is_supported_file("test.py")
        assert fingerprinter.is_supported_file("script.js")
        assert fingerprinter.is_supported_file("main.go")
        assert not fingerprinter.is_supported_file("image.png")
        assert not fingerprinter.is_supported_file("document.pdf")

    def test_normalize_code_whitespace(self):
        """Test whitespace normalization."""
        fingerprinter = CodeFingerprinter(ignore_whitespace=True)

        code = "def   hello():\n    print('world')\n\n"
        normalized = fingerprinter.normalize_code(code)

        assert normalized == "def hello(): print('world')"

    def test_normalize_code_comments(self):
        """Test comment removal."""
        fingerprinter = CodeFingerprinter(ignore_comments=True)

        code = """
# This is a comment
def hello():  # inline comment
    print('world')
    // another comment
"""
        normalized = fingerprinter.normalize_code(code)

        assert "# This is a comment" not in normalized
        assert "# inline comment" not in normalized
        assert "// another comment" not in normalized
        assert "print('world')" in normalized

    def test_generate_hash(self):
        """Test hash generation."""
        fingerprinter = CodeFingerprinter()

        code1 = "def hello(): pass"
        code2 = "def hello(): pass"
        code3 = "def goodbye(): pass"

        hash1 = fingerprinter.generate_hash(code1)
        hash2 = fingerprinter.generate_hash(code2)
        hash3 = fingerprinter.generate_hash(code3)

        # Same code should produce same hash
        assert hash1 == hash2

        # Different code should (very likely) produce different hash
        assert hash1 != hash3

    def test_generate_fuzzy_hash(self):
        """Test fuzzy hash generation with normalized code."""
        fingerprinter = CodeFingerprinter()

        code1 = "def hello():\n    print('world')"
        code2 = "def   hello():\n\n    print('world')"  # Different whitespace

        fuzzy1 = fingerprinter.generate_fuzzy_hash(code1)
        fuzzy2 = fingerprinter.generate_fuzzy_hash(code2)

        # Should match despite whitespace differences
        assert fuzzy1 == fuzzy2

    def test_generate_structural_hash(self):
        """Test structural hash generation."""
        fingerprinter = CodeFingerprinter()

        code1 = 'print("hello world")'
        code2 = 'print("goodbye world")'  # Different string

        struct1 = fingerprinter.generate_structural_hash(code1)
        struct2 = fingerprinter.generate_structural_hash(code2)

        # Should match as structure is the same
        assert struct1 == struct2

    def test_fingerprint_file(self):
        """Test complete file fingerprinting."""
        fingerprinter = CodeFingerprinter()

        content = "def main():\n    print('hello')\n"
        result = fingerprinter.fingerprint_file("test.py", content)

        assert "filepath" in result
        assert "exact_hash" in result
        assert "fuzzy_hash" in result
        assert "structural_hash" in result
        assert "size" in result
        assert result["filepath"] == "test.py"
        assert result["size"] == len(content)

    def test_fingerprint_lines(self):
        """Test line-based fingerprinting."""
        fingerprinter = CodeFingerprinter()

        content = "\n".join([f"line {i}" for i in range(10)])
        hashes = fingerprinter.fingerprint_lines(content, window_size=3)

        # Should have sliding windows
        assert len(hashes) == 8  # 10 lines - 3 + 1

        # Each hash should be valid
        for h in hashes:
            assert isinstance(h, str)
            assert len(h) > 0
