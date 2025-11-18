"""
Code analyzer module for calculating uniqueness metrics.
"""

import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple
from .fingerprint import CodeFingerprinter
from .scanner import RepositoryScanner

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """
    Analyzes code repositories to quantify uniqueness and detect duplication.
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the analyzer.

        Args:
            github_token: GitHub API token (optional)
        """
        self.scanner = RepositoryScanner(github_token=github_token)
        self.fingerprinter = CodeFingerprinter()
        self.file_hashes: Dict[str, Dict[str, List[str]]] = {
            "exact": defaultdict(list),
            "fuzzy": defaultdict(list),
            "structural": defaultdict(list),
        }
        self.duplicate_groups: Dict[str, Set[str]] = defaultdict(set)

    def analyze_repository(
        self, repo_identifier: str, branch: Optional[str] = None
    ) -> Dict:
        """
        Analyze a GitHub repository for code uniqueness.

        Args:
            repo_identifier: Repository in format 'owner/repo'
            branch: Specific branch to analyze (optional)

        Returns:
            Analysis results dictionary
        """
        logger.info(f"Starting analysis of {repo_identifier}")

        # Get repository info
        try:
            repo_info = self.scanner.get_repo_info(repo_identifier)
        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            repo_info = {}

        # Clone repository
        repo_path = self.scanner.clone_repository(repo_identifier, branch)

        # Scan files
        files = self.scanner.scan_files(
            repo_path, extensions=self.fingerprinter.SUPPORTED_EXTENSIONS
        )

        logger.info(f"Found {len(files)} code files to analyze")

        # Analyze each file
        file_fingerprints = []
        total_size = 0
        analyzed_count = 0

        for file_info in files:
            content = self.scanner.read_file(file_info["absolute_path"])
            if content is None:
                continue

            fingerprint = self.fingerprinter.fingerprint_file(
                file_info["path"], content
            )

            file_fingerprints.append(fingerprint)
            total_size += file_info["size"]
            analyzed_count += 1

            # Track duplicates
            self._track_duplicates(fingerprint)

        # Calculate metrics
        metrics = self._calculate_metrics(file_fingerprints, total_size)

        return {
            "repository": repo_info,
            "files_analyzed": analyzed_count,
            "total_files": len(files),
            "total_size_bytes": total_size,
            "metrics": metrics,
            "file_fingerprints": file_fingerprints,
        }

    def analyze_multiple_repositories(self, repo_identifiers: List[str]) -> Dict:
        """
        Analyze multiple repositories to find cross-repository duplication.

        Args:
            repo_identifiers: List of repositories in format 'owner/repo'

        Returns:
            Combined analysis results
        """
        all_results = []
        combined_fingerprints = []

        for repo_id in repo_identifiers:
            try:
                result = self.analyze_repository(repo_id)
                all_results.append(result)
                combined_fingerprints.extend(result["file_fingerprints"])
            except Exception as e:
                logger.error(f"Failed to analyze {repo_id}: {e}")
                continue

        # Reset duplicate tracking
        self.file_hashes.clear()
        self.duplicate_groups.clear()

        # Re-track duplicates across all repositories
        for fp in combined_fingerprints:
            self._track_duplicates(fp)

        # Calculate cross-repo metrics
        total_size = sum(r["total_size_bytes"] for r in all_results)
        cross_repo_metrics = self._calculate_metrics(combined_fingerprints, total_size)

        return {
            "repositories_analyzed": len(all_results),
            "individual_results": all_results,
            "cross_repository_metrics": cross_repo_metrics,
        }

    def _track_duplicates(self, fingerprint: Dict):
        """Track duplicate files based on their hashes."""
        filepath = fingerprint["filepath"]

        # Track exact duplicates
        exact_hash = fingerprint["exact_hash"]
        self.file_hashes["exact"][exact_hash].append(filepath)
        if len(self.file_hashes["exact"][exact_hash]) > 1:
            self.duplicate_groups["exact"].update(self.file_hashes["exact"][exact_hash])

        # Track fuzzy duplicates
        fuzzy_hash = fingerprint["fuzzy_hash"]
        self.file_hashes["fuzzy"][fuzzy_hash].append(filepath)
        if len(self.file_hashes["fuzzy"][fuzzy_hash]) > 1:
            self.duplicate_groups["fuzzy"].update(self.file_hashes["fuzzy"][fuzzy_hash])

        # Track structural duplicates
        structural_hash = fingerprint["structural_hash"]
        self.file_hashes["structural"][structural_hash].append(filepath)
        if len(self.file_hashes["structural"][structural_hash]) > 1:
            self.duplicate_groups["structural"].update(
                self.file_hashes["structural"][structural_hash]
            )

    def _calculate_metrics(self, fingerprints: List[Dict], total_size: int) -> Dict:
        """Calculate uniqueness metrics from fingerprints."""
        if not fingerprints:
            return {
                "total_files": 0,
                "unique_files_exact": 0,
                "unique_files_fuzzy": 0,
                "unique_files_structural": 0,
                "uniqueness_score_exact": 0.0,
                "uniqueness_score_fuzzy": 0.0,
                "uniqueness_score_structural": 0.0,
                "duplicate_groups": {},
            }

        total_files = len(fingerprints)

        # Count unique files
        unique_exact = len(set(fp["exact_hash"] for fp in fingerprints))
        unique_fuzzy = len(set(fp["fuzzy_hash"] for fp in fingerprints))
        unique_structural = len(set(fp["structural_hash"] for fp in fingerprints))

        # Calculate uniqueness scores (0-100%)
        uniqueness_exact = (unique_exact / total_files * 100) if total_files > 0 else 0
        uniqueness_fuzzy = (unique_fuzzy / total_files * 100) if total_files > 0 else 0
        uniqueness_structural = (
            (unique_structural / total_files * 100) if total_files > 0 else 0
        )

        # Find duplicate groups
        duplicate_info = {
            "exact": {},
            "fuzzy": {},
            "structural": {},
        }

        for hash_type in ["exact", "fuzzy", "structural"]:
            for hash_val, files in self.file_hashes[hash_type].items():
                if len(files) > 1:
                    duplicate_info[hash_type][hash_val] = list(files)

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "unique_files_exact": unique_exact,
            "unique_files_fuzzy": unique_fuzzy,
            "unique_files_structural": unique_structural,
            "uniqueness_score_exact": round(uniqueness_exact, 2),
            "uniqueness_score_fuzzy": round(uniqueness_fuzzy, 2),
            "uniqueness_score_structural": round(uniqueness_structural, 2),
            "duplicate_groups": duplicate_info,
            "duplication_summary": {
                "exact_duplicates": sum(
                    len(files) - 1 for files in duplicate_info["exact"].values()
                ),
                "fuzzy_duplicates": sum(
                    len(files) - 1 for files in duplicate_info["fuzzy"].values()
                ),
                "structural_duplicates": sum(
                    len(files) - 1 for files in duplicate_info["structural"].values()
                ),
            },
        }

    def get_duplicate_files(self, hash_type: str = "fuzzy") -> Dict[str, List[str]]:
        """
        Get groups of duplicate files.

        Args:
            hash_type: Type of hash to use ('exact', 'fuzzy', or 'structural')

        Returns:
            Dictionary mapping hash to list of duplicate file paths
        """
        duplicates = {}
        for hash_val, files in self.file_hashes[hash_type].items():
            if len(files) > 1:
                duplicates[hash_val] = list(files)
        return duplicates
