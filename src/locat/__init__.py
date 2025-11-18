"""
locat - Code uniqueness quantification tool for GitHub repositories.

This package provides tools to analyze GitHub repositories and quantify
the uniqueness of code, identifying boilerplate and duplicated logic.
"""

__version__ = "0.1.0"

from .analyzer import CodeAnalyzer
from .fingerprint import CodeFingerprinter
from .scanner import RepositoryScanner

__all__ = ["CodeAnalyzer", "CodeFingerprinter", "RepositoryScanner"]
