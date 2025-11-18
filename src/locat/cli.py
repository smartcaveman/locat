"""
Command-line interface for locat.
"""

import json
import logging
import os
import sys
from typing import Optional

import click
from .analyzer import CodeAnalyzer


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    locat - Code uniqueness quantification tool for GitHub repositories.

    Analyze GitHub repositories to quantify code uniqueness and identify
    boilerplate or duplicated logic across codebases.
    """
    pass


@cli.command()
@click.argument("repository")
@click.option("--token", envvar="GITHUB_TOKEN", help="GitHub API token")
@click.option("--branch", help="Specific branch to analyze")
@click.option("--output", "-o", help="Output file for results (JSON)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def analyze(
    repository: str,
    token: Optional[str],
    branch: Optional[str],
    output: Optional[str],
    verbose: bool,
):
    """
    Analyze a single GitHub repository for code uniqueness.

    REPOSITORY can be in format 'owner/repo' or a full GitHub URL.

    Example:
        locat analyze torvalds/linux
        locat analyze https://github.com/python/cpython --branch main
    """
    setup_logging(verbose)

    analyzer = CodeAnalyzer(github_token=token)

    click.echo(f"Analyzing repository: {repository}")
    if branch:
        click.echo(f"Branch: {branch}")

    try:
        results = analyzer.analyze_repository(repository, branch)

        # Display summary
        _display_summary(results)

        # Save to file if requested
        if output:
            with open(output, "w") as f:
                json.dump(results, f, indent=2)
            click.echo(f"\nDetailed results saved to: {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("repositories", nargs=-1, required=True)
@click.option("--token", envvar="GITHUB_TOKEN", help="GitHub API token")
@click.option("--output", "-o", help="Output file for results (JSON)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def compare(
    repositories: tuple, token: Optional[str], output: Optional[str], verbose: bool
):
    """
    Compare multiple repositories to find cross-repository code duplication.

    REPOSITORIES should be space-separated list of repo identifiers.

    Example:
        locat compare facebook/react vuejs/vue angular/angular
    """
    setup_logging(verbose)

    analyzer = CodeAnalyzer(github_token=token)

    click.echo(f"Comparing {len(repositories)} repositories...")

    try:
        results = analyzer.analyze_multiple_repositories(list(repositories))

        # Display summary
        click.echo("\n" + "=" * 60)
        click.echo("CROSS-REPOSITORY ANALYSIS")
        click.echo("=" * 60)

        metrics = results["cross_repository_metrics"]
        _display_metrics(metrics)

        # Individual repository summaries
        click.echo("\n" + "-" * 60)
        click.echo("INDIVIDUAL REPOSITORIES")
        click.echo("-" * 60)

        for result in results["individual_results"]:
            repo_name = result.get("repository", {}).get("full_name", "Unknown")
            click.echo(f"\n{repo_name}:")
            click.echo(f"  Files analyzed: {result['files_analyzed']}")
            click.echo(
                f"  Uniqueness (fuzzy): {result['metrics']['uniqueness_score_fuzzy']:.2f}%"
            )

        # Save to file if requested
        if output:
            with open(output, "w") as f:
                json.dump(results, f, indent=2)
            click.echo(f"\nDetailed results saved to: {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("result_file", type=click.Path(exists=True))
@click.option(
    "--hash-type",
    type=click.Choice(["exact", "fuzzy", "structural"]),
    default="fuzzy",
    help="Type of duplication to show",
)
@click.option(
    "--min-duplicates", type=int, default=2, help="Minimum number of duplicates to show"
)
def duplicates(result_file: str, hash_type: str, min_duplicates: int):
    """
    Display duplicate code groups from a previous analysis.

    RESULT_FILE should be a JSON file from a previous analyze or compare command.

    Example:
        locat duplicates results.json --hash-type fuzzy
    """
    try:
        with open(result_file, "r") as f:
            results = json.load(f)
    except Exception as e:
        click.echo(f"Error reading results file: {e}", err=True)
        sys.exit(1)

    # Extract metrics
    if "cross_repository_metrics" in results:
        metrics = results["cross_repository_metrics"]
    else:
        metrics = results.get("metrics", {})

    duplicate_groups = metrics.get("duplicate_groups", {}).get(hash_type, {})

    if not duplicate_groups:
        click.echo(f"No {hash_type} duplicates found.")
        return

    click.echo(f"\n{hash_type.upper()} DUPLICATE GROUPS")
    click.echo("=" * 60)

    displayed = 0
    for hash_val, files in duplicate_groups.items():
        if len(files) >= min_duplicates:
            displayed += 1
            click.echo(f"\nGroup {displayed} ({len(files)} files):")
            for file in files:
                click.echo(f"  - {file}")

    if displayed == 0:
        click.echo(f"No duplicate groups with at least {min_duplicates} files.")


def _display_summary(results: dict):
    """Display a summary of analysis results."""
    click.echo("\n" + "=" * 60)
    click.echo("ANALYSIS SUMMARY")
    click.echo("=" * 60)

    repo_info = results.get("repository", {})
    if repo_info:
        click.echo(f"\nRepository: {repo_info.get('full_name', 'Unknown')}")
        if repo_info.get("description"):
            click.echo(f"Description: {repo_info['description']}")
        click.echo(f"Language: {repo_info.get('language', 'N/A')}")
        click.echo(f"Stars: {repo_info.get('stars', 0):,}")

    click.echo(f"\nFiles analyzed: {results['files_analyzed']}")
    click.echo(f"Total size: {results['total_size_bytes']:,} bytes")

    _display_metrics(results["metrics"])


def _display_metrics(metrics: dict):
    """Display uniqueness metrics."""
    click.echo("\n" + "-" * 60)
    click.echo("UNIQUENESS METRICS")
    click.echo("-" * 60)

    click.echo(f"\nTotal files: {metrics['total_files']}")

    click.echo("\nUnique files:")
    click.echo(
        f"  Exact matches:       {metrics['unique_files_exact']:>6} "
        f"({metrics['uniqueness_score_exact']:>6.2f}%)"
    )
    click.echo(
        f"  Fuzzy matches:       {metrics['unique_files_fuzzy']:>6} "
        f"({metrics['uniqueness_score_fuzzy']:>6.2f}%)"
    )
    click.echo(
        f"  Structural matches:  {metrics['unique_files_structural']:>6} "
        f"({metrics['uniqueness_score_structural']:>6.2f}%)"
    )

    dup_summary = metrics.get("duplication_summary", {})
    if dup_summary:
        click.echo("\nDuplicate files found:")
        click.echo(
            f"  Exact duplicates:       {dup_summary.get('exact_duplicates', 0):>6}"
        )
        click.echo(
            f"  Fuzzy duplicates:       {dup_summary.get('fuzzy_duplicates', 0):>6}"
        )
        click.echo(
            f"  Structural duplicates:  {dup_summary.get('structural_duplicates', 0):>6}"
        )

    # Interpretation
    fuzzy_score = metrics["uniqueness_score_fuzzy"]
    click.echo("\n" + "-" * 60)
    click.echo("INTERPRETATION")
    click.echo("-" * 60)

    if fuzzy_score >= 80:
        interpretation = "HIGH uniqueness - This codebase has mostly unique code."
    elif fuzzy_score >= 60:
        interpretation = "MODERATE uniqueness - Some duplication present."
    elif fuzzy_score >= 40:
        interpretation = "LOW uniqueness - Significant duplication detected."
    else:
        interpretation = "VERY LOW uniqueness - Heavy duplication or boilerplate."

    click.echo(f"\nUniqueness Score (fuzzy): {fuzzy_score:.2f}%")
    click.echo(f"Assessment: {interpretation}")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
