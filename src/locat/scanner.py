"""
Repository scanner module for cloning and traversing GitHub repositories.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from git import Repo
from github import Github, GithubException
import logging

logger = logging.getLogger(__name__)


class RepositoryScanner:
    """
    Scans GitHub repositories and extracts code files for analysis.
    """

    def __init__(
        self, github_token: Optional[str] = None, clone_dir: Optional[str] = None
    ):
        """
        Initialize the repository scanner.

        Args:
            github_token: GitHub API token (optional, for higher rate limits)
            clone_dir: Directory to clone repositories into
        """
        self.github_token = github_token
        self.clone_dir = clone_dir or tempfile.mkdtemp(prefix="locat_")
        self.github_client = Github(github_token) if github_token else Github()

        # Ensure clone directory exists
        os.makedirs(self.clone_dir, exist_ok=True)

    def parse_repo_url(self, repo_identifier: str) -> Tuple[str, str]:
        """
        Parse a repository identifier into owner and name.

        Args:
            repo_identifier: Repository in format 'owner/repo' or full URL

        Returns:
            Tuple of (owner, repo_name)
        """
        # Handle full URLs - check for github.com as the domain
        if repo_identifier.startswith(
            "https://github.com/"
        ) or repo_identifier.startswith("http://github.com/"):
            parts = repo_identifier.rstrip("/").split("/")
            if len(parts) >= 5:  # https://github.com/owner/repo
                return parts[-2], parts[-1].replace(".git", "")

        # Handle owner/repo format
        parts = repo_identifier.split("/")
        if len(parts) == 2:
            return parts[0], parts[1]

        raise ValueError(f"Invalid repository identifier: {repo_identifier}")

    def clone_repository(
        self, repo_identifier: str, branch: Optional[str] = None
    ) -> str:
        """
        Clone a GitHub repository to local storage.

        Args:
            repo_identifier: Repository in format 'owner/repo'
            branch: Specific branch to clone (optional)

        Returns:
            Path to cloned repository
        """
        owner, repo_name = self.parse_repo_url(repo_identifier)
        repo_path = os.path.join(self.clone_dir, f"{owner}_{repo_name}")

        # Skip if already cloned
        if os.path.exists(repo_path):
            logger.info(f"Repository already cloned at {repo_path}")
            return repo_path

        # Clone the repository
        clone_url = f"https://github.com/{owner}/{repo_name}.git"
        logger.info(f"Cloning {clone_url} to {repo_path}")

        try:
            if branch:
                Repo.clone_from(clone_url, repo_path, branch=branch, depth=1)
            else:
                Repo.clone_from(clone_url, repo_path, depth=1)
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise

        return repo_path

    def get_repo_info(self, repo_identifier: str) -> Dict:
        """
        Get metadata about a repository from GitHub API.

        Args:
            repo_identifier: Repository in format 'owner/repo'

        Returns:
            Dictionary with repository metadata
        """
        owner, repo_name = self.parse_repo_url(repo_identifier)

        try:
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            return {
                "owner": owner,
                "name": repo_name,
                "full_name": repo.full_name,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language,
                "size": repo.size,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            }
        except GithubException as e:
            logger.error(f"Failed to fetch repository info: {e}")
            raise

    def scan_files(
        self, repo_path: str, extensions: Optional[set] = None
    ) -> List[Dict]:
        """
        Scan a repository for code files.

        Args:
            repo_path: Path to the cloned repository
            extensions: Set of file extensions to include (e.g., {'.py', '.js'})

        Returns:
            List of file information dictionaries
        """
        files = []
        repo_path_obj = Path(repo_path)

        for file_path in repo_path_obj.rglob("*"):
            # Skip directories and hidden files
            if file_path.is_dir() or file_path.name.startswith("."):
                continue

            # Skip common non-code directories
            if any(
                part.startswith(".")
                or part in ["node_modules", "vendor", "__pycache__", "dist", "build"]
                for part in file_path.parts
            ):
                continue

            # Filter by extension if specified
            if extensions and file_path.suffix not in extensions:
                continue

            try:
                # Get relative path from repo root
                rel_path = file_path.relative_to(repo_path_obj)

                files.append(
                    {
                        "path": str(rel_path),
                        "absolute_path": str(file_path),
                        "extension": file_path.suffix,
                        "size": file_path.stat().st_size,
                    }
                )
            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")
                continue

        return files

    def read_file(self, filepath: str) -> Optional[str]:
        """
        Read the content of a file.

        Args:
            filepath: Path to the file

        Returns:
            File content as string, or None if read fails
        """
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to read file {filepath}: {e}")
            return None
