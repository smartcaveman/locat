#!/usr/bin/env python3
"""
Example script showing how to use locat programmatically.
"""

import json
from locat import CodeAnalyzer


def main():
    """Analyze a repository and print results."""
    # Create analyzer (optionally pass GitHub token for higher rate limits)
    analyzer = CodeAnalyzer(github_token=None)

    # Analyze a repository
    repo = "smartcaveman/locat"
    print(f"Analyzing repository: {repo}")

    try:
        results = analyzer.analyze_repository(repo)

        # Print summary
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)

        repo_info = results.get("repository", {})
        print(f"\nRepository: {repo_info.get('full_name', 'Unknown')}")
        print(f"Description: {repo_info.get('description', 'N/A')}")
        print(f"Language: {repo_info.get('language', 'N/A')}")

        print(f"\nFiles analyzed: {results['files_analyzed']}")
        print(f"Total size: {results['total_size_bytes']:,} bytes")

        metrics = results["metrics"]
        print("\n" + "-" * 60)
        print("UNIQUENESS METRICS")
        print("-" * 60)
        print(f"Total files: {metrics['total_files']}")
        print(f"Uniqueness (exact): {metrics['uniqueness_score_exact']:.2f}%")
        print(f"Uniqueness (fuzzy): {metrics['uniqueness_score_fuzzy']:.2f}%")
        print(f"Uniqueness (structural): {metrics['uniqueness_score_structural']:.2f}%")

        # Get duplicate files
        duplicates = analyzer.get_duplicate_files("fuzzy")
        if duplicates:
            print(f"\nFound {len(duplicates)} groups of fuzzy duplicates")
            for i, (hash_val, files) in enumerate(list(duplicates.items())[:3], 1):
                print(f"\nGroup {i} ({len(files)} files):")
                for file in files[:5]:  # Show first 5 files
                    print(f"  - {file}")

        # Save detailed results
        output_file = "analysis_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to: {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
