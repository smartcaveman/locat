"""
Code fingerprinting module for generating unique identifiers for code blocks.
"""

import hashlib
import re
from typing import Dict, List, Optional, Set
import xxhash


class CodeFingerprinter:
    """
    Generates fingerprints for code to identify similar or duplicate code blocks.
    Uses multiple hashing strategies to detect both exact and near-duplicate code.
    """

    # Common file extensions to analyze
    SUPPORTED_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".java",
        ".go",
        ".rs",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".rb",
        ".php",
        ".cs",
        ".swift",
        ".kt",
        ".scala",
        ".sh",
        ".bash",
    }

    def __init__(self, ignore_whitespace: bool = True, ignore_comments: bool = True):
        """
        Initialize the fingerprinter.

        Args:
            ignore_whitespace: If True, normalize whitespace before hashing
            ignore_comments: If True, remove comments before hashing
        """
        self.ignore_whitespace = ignore_whitespace
        self.ignore_comments = ignore_comments

    def is_supported_file(self, filepath: str) -> bool:
        """Check if a file extension is supported for analysis."""
        return any(filepath.endswith(ext) for ext in self.SUPPORTED_EXTENSIONS)

    def normalize_code(self, code: str, language: Optional[str] = None) -> str:
        """
        Normalize code by removing comments and whitespace if configured.

        Args:
            code: The source code to normalize
            language: Programming language (for language-specific normalization)

        Returns:
            Normalized code string
        """
        normalized = code

        if self.ignore_comments:
            # Remove common single-line comments
            normalized = re.sub(r"//.*?$", "", normalized, flags=re.MULTILINE)
            normalized = re.sub(r"#.*?$", "", normalized, flags=re.MULTILINE)
            # Remove multi-line comments (C-style)
            normalized = re.sub(r"/\*.*?\*/", "", normalized, flags=re.DOTALL)

        if self.ignore_whitespace:
            # Normalize whitespace
            normalized = re.sub(r"\s+", " ", normalized)
            normalized = normalized.strip()

        return normalized

    def generate_hash(self, code: str) -> str:
        """
        Generate a fast hash for exact duplicate detection.

        Args:
            code: The source code to hash

        Returns:
            Hexadecimal hash string
        """
        return xxhash.xxh64(code.encode("utf-8")).hexdigest()

    def generate_fuzzy_hash(self, code: str) -> str:
        """
        Generate a fuzzy hash for near-duplicate detection.
        Uses normalized code to find similar code blocks.

        Args:
            code: The source code to hash

        Returns:
            Hexadecimal hash string
        """
        normalized = self.normalize_code(code)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def generate_structural_hash(self, code: str) -> str:
        """
        Generate a structural hash that focuses on code structure.
        Removes variable names, string literals, etc. to match similar logic.

        Args:
            code: The source code to hash

        Returns:
            Hexadecimal hash string
        """
        # Remove string literals
        structural = re.sub(r'"[^"]*"', '""', code)
        structural = re.sub(r"'[^']*'", "''", structural)

        # Remove numbers
        structural = re.sub(r"\b\d+\b", "0", structural)

        # Normalize and hash
        structural = self.normalize_code(structural)
        return hashlib.md5(structural.encode("utf-8")).hexdigest()

    def fingerprint_file(self, filepath: str, content: str) -> Dict[str, str]:
        """
        Generate multiple fingerprints for a file.

        Args:
            filepath: Path to the file
            content: File content

        Returns:
            Dictionary with different hash types
        """
        return {
            "filepath": filepath,
            "exact_hash": self.generate_hash(content),
            "fuzzy_hash": self.generate_fuzzy_hash(content),
            "structural_hash": self.generate_structural_hash(content),
            "size": len(content),
        }

    def fingerprint_lines(self, content: str, window_size: int = 5) -> List[str]:
        """
        Generate fingerprints for sliding windows of code lines.
        Useful for detecting smaller code block duplication.

        Args:
            content: File content
            window_size: Number of lines per window

        Returns:
            List of hashes for each window
        """
        lines = content.split("\n")
        hashes = []

        for i in range(len(lines) - window_size + 1):
            window = "\n".join(lines[i : i + window_size])
            normalized = self.normalize_code(window)
            if normalized:  # Skip empty windows
                hashes.append(hashlib.sha256(normalized.encode("utf-8")).hexdigest())

        return hashes
