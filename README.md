# locat Code Uniqueness Analyzer

This project aims to quantify the uniqueness of code on public GitHub repositories. It is based on the idea that much of the code in the ecosystem is boilerplate or duplicated logic, and by understanding the true amount of unique, novel code, we can build better tools for security analysis, code discovery, and AI training.

## Methodology

The core of this project is a statistical sampling approach. Instead of attempting to analyze all of GitHub (which is impossible), this script samples a statistically significant number of public repositories to estimate key parameters about code distribution and uniqueness.

### Key Parameters to Estimate:

1.  **`f̄` (Mean Files per Repo):** The average number of files (blobs) in a repository.
2.  **`l̄` (Mean LOC per File):** The average number of lines of code per file.
3.  **`r_file` (File Uniqueness Ratio):** The probability that a randomly selected file has a unique hash.
4.  **`r_line` (Line Uniqueness Ratio):** The probability that a randomly selected line of code has unique content.

### Hypotheses (H₀)

Our initial best guesses for these parameters are:

-   **H₀ (`f̄`):** 150 files/repo
-   **H₀ (`l̄`):** 120 LOC/file
-   **H₀ (`r_file`):** 10%
-   **H₀ (`r_line`):** 0.8%

The script will test these hypotheses against the collected sample data.

## How to Run

1.  **Install Dependencies:**

    ```bash
    pip install requests xxhash
    ```

2.  **Set Environment Variable:**
    You must provide a GitHub Personal Access Token (PAT) with `public_repo` scope. This is required to make API requests.

    ```bash
    export GITHUB_TOKEN="your_github_pat_here"
    ```

3.  **Run the Analyzer:**

    ```bash
    python scripts/analyzer.py
    ```

The script will print its progress and the final statistical results to the console.
