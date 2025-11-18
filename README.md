# locat

**Code Uniqueness Quantification Tool for GitHub Repositories**

This project aims to quantify the uniqueness of code on public GitHub repositories. It is based on the idea that much of the code in the ecosystem is boilerplate or duplicated logic, and by understanding the true amount of unique, novel code, we can build better tools for security analysis, code discovery, and AI training.

## Features

- **Multi-level Duplicate Detection**: Identifies duplicates using three strategies:
  - **Exact matching**: Finds byte-for-byte identical files
  - **Fuzzy matching**: Detects similar code with normalized whitespace and comments
  - **Structural matching**: Identifies code with similar logic patterns regardless of variable names or literals

- **Uniqueness Scoring**: Calculates comprehensive metrics to quantify how much unique code exists in a repository

- **Cross-Repository Analysis**: Compare multiple repositories to find shared boilerplate and duplicated patterns

- **Multiple Language Support**: Analyzes Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, Ruby, PHP, C#, Swift, Kotlin, Scala, and shell scripts

- **CLI Interface**: Easy-to-use command-line tool for analyzing repositories

## Installation

```bash
# Clone the repository
git clone https://github.com/smartcaveman/locat.git
cd locat

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Quick Start

### Analyze a Single Repository

```bash
# Basic analysis
locat analyze torvalds/linux

# With GitHub token for higher API rate limits
export GITHUB_TOKEN=your_token_here
locat analyze python/cpython --branch main

# Save detailed results to a file
locat analyze facebook/react -o results.json
```

### Compare Multiple Repositories

```bash
# Find cross-repository duplication
locat compare facebook/react vuejs/vue angular/angular -o comparison.json
```

### View Duplicate Groups

```bash
# Show duplicate files from previous analysis
locat duplicates results.json --hash-type fuzzy --min-duplicates 2
```

## Usage

### Command: `analyze`

Analyze a single GitHub repository for code uniqueness.

```bash
locat analyze REPOSITORY [OPTIONS]
```

**Arguments:**
- `REPOSITORY`: Repository identifier (format: `owner/repo` or full GitHub URL)

**Options:**
- `--token TEXT`: GitHub API token (or set `GITHUB_TOKEN` environment variable)
- `--branch TEXT`: Specific branch to analyze
- `-o, --output FILE`: Save results to JSON file
- `-v, --verbose`: Enable verbose output

**Example Output:**
```
Analyzing repository: torvalds/linux

============================================================
ANALYSIS SUMMARY
============================================================

Repository: torvalds/linux
Description: Linux kernel source tree
Language: C
Stars: 150,000

Files analyzed: 5,432
Total size: 25,678,901 bytes

------------------------------------------------------------
UNIQUENESS METRICS
------------------------------------------------------------

Total files: 5,432

Unique files:
  Exact matches:       5,120  ( 94.26%)
  Fuzzy matches:       4,890  ( 90.02%)
  Structural matches:  4,502  ( 82.88%)

Duplicate files found:
  Exact duplicates:          312
  Fuzzy duplicates:          542
  Structural duplicates:     930

------------------------------------------------------------
INTERPRETATION
------------------------------------------------------------

Uniqueness Score (fuzzy): 90.02%
Assessment: HIGH uniqueness - This codebase has mostly unique code.
```

### Command: `compare`

Compare multiple repositories to find cross-repository code duplication.

```bash
locat compare REPOSITORY1 REPOSITORY2 ... [OPTIONS]
```

**Arguments:**
- `REPOSITORIES`: Space-separated list of repository identifiers

**Options:**
- `--token TEXT`: GitHub API token
- `-o, --output FILE`: Save results to JSON file
- `-v, --verbose`: Enable verbose output

### Command: `duplicates`

Display duplicate code groups from a previous analysis.

```bash
locat duplicates RESULT_FILE [OPTIONS]
```

**Arguments:**
- `RESULT_FILE`: JSON file from previous `analyze` or `compare` command

**Options:**
- `--hash-type CHOICE`: Type of duplication (`exact`, `fuzzy`, or `structural`)
- `--min-duplicates INT`: Minimum number of duplicates to display

## Understanding the Metrics

### Uniqueness Scores

- **Exact Match Score (0-100%)**: Percentage of files that are byte-for-byte unique
- **Fuzzy Match Score (0-100%)**: Percentage of files that are unique after normalizing whitespace and comments
- **Structural Match Score (0-100%)**: Percentage of files with unique logical structure

### Score Interpretation

- **80-100%**: HIGH uniqueness - Mostly original code
- **60-79%**: MODERATE uniqueness - Some duplication present
- **40-59%**: LOW uniqueness - Significant duplication detected
- **0-39%**: VERY LOW uniqueness - Heavy duplication or boilerplate

### Duplicate Types

- **Exact Duplicates**: Identical files (copy-paste)
- **Fuzzy Duplicates**: Similar files with minor formatting differences
- **Structural Duplicates**: Files with similar logic patterns

## Use Cases

### 1. Security Analysis
Identify common vulnerability patterns across repositories to prioritize security reviews.

```bash
locat compare repo1/app repo2/app repo3/app -o security-analysis.json
```

### 2. Code Discovery
Find unique implementations and novel approaches by filtering out boilerplate.

```bash
locat analyze interesting/project -o discovery.json
locat duplicates discovery.json --hash-type structural
```

### 3. AI Training Dataset Curation
Quantify code uniqueness to build better training datasets that avoid over-representation of common patterns.

```bash
# Analyze multiple repos and identify unique code blocks
locat compare org/repo1 org/repo2 org/repo3 -o training-data.json
```

### 4. License Compliance
Detect potential code copying between projects with different licenses.

### 5. Code Quality Assessment
Measure how much of a codebase is unique vs. copied/generated boilerplate.

## Architecture

### Components

1. **RepositoryScanner**: Clones and traverses GitHub repositories
2. **CodeFingerprinter**: Generates multiple types of hashes for code blocks
3. **CodeAnalyzer**: Calculates uniqueness metrics and detects duplicates
4. **CLI**: Command-line interface for user interaction

### Hashing Strategies

- **XXHash**: Fast exact matching for duplicate detection
- **SHA-256**: Fuzzy matching with normalized code
- **MD5**: Structural matching focusing on code patterns

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional)
# pip install pre-commit
# pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=locat --cov-report=html

# Run specific test file
pytest tests/test_fingerprint.py
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## Configuration

Set the `GITHUB_TOKEN` environment variable to increase API rate limits:

```bash
export GITHUB_TOKEN=your_personal_access_token
```

Generate a token at: https://github.com/settings/tokens

## Limitations

- Only analyzes source code files (excludes binary files, images, etc.)
- Requires cloning repositories (needs disk space)
- GitHub API rate limits apply (higher with authentication)
- Analysis time depends on repository size

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - see LICENSE file for details

## Author

smartcaveman

## Acknowledgments

Built to help understand code uniqueness in the GitHub ecosystem and improve tools for security analysis, code discovery, and AI training.
