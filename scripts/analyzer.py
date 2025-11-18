import os
import requests
import random
import sys
import time
import xxhash
from statistics import mean

# --- Configuration & Hypotheses ---
# Your GitHub Personal Access Token (PAT)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# The total number of repositories to sample.
# A larger number provides more statistical power but takes longer.
SAMPLE_SIZE = 1000

# A conservative upper bound for public repository IDs.
# As of late 2024, this is well over 500 million.
MAX_REPO_ID = 500_000_000

# Our Null Hypotheses (H₀)
H0_MEAN_FILES_PER_REPO = 150
H0_MEAN_LOC_PER_FILE = 120
H0_FILE_UNIQUENESS_RATIO = 0.10
H0_LINE_UNIQUENESS_RATIO = 0.008

# --- Global State ---
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Global data structures for analysis
total_files_processed = 0
total_lines_processed = 0
repo_file_counts = []
file_loc_counts = []
unique_file_hashes = set()
unique_line_hashes = set()
processed_repo_count = 0

def get_rate_limit():
    """Checks the current GitHub API rate limit status."""
    try:
        response = requests.get("https://api.github.com/rate_limit", headers=HEADERS)
        response.raise_for_status()
        return response.json()["rate"]
    except requests.exceptions.RequestException as e:
        print(f"Error checking rate limit: {e}", file=sys.stderr)
        return None

def process_repository(repo_id):
    """Fetches and analyzes a single repository by its ID."""
    global total_files_processed, total_lines_processed, processed_repo_count

    try:
        # 1. Fetch Repo Data
        repo_url = f"https://api.github.com/repositories/{repo_id}"
        response = requests.get(repo_url, headers=HEADERS)
        if response.status_code == 404:
            print(f"Repo ID {repo_id}: Not found or private. Skipping.")
            return False
        response.raise_for_status()
        repo_data = response.json()

        if repo_data.get("fork", True):
            print(f"Repo ID {repo_id}: Is a fork. Skipping.")
            return False

        owner = repo_data["owner"]["login"]
        repo = repo_data["name"]
        default_branch = repo_data["default_branch"]
        print(f"Processing Repo ID {repo_id}: {owner}/{repo}")

        # 2. Get Git Tree
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
        response = requests.get(tree_url, headers=HEADERS)
        response.raise_for_status()
        tree_data = response.json()

        if tree_data.get("truncated", False):
            print(f"Repo ID {repo_id}: Tree is truncated. Skipping to avoid partial analysis.")
            return False

        files_in_repo = [item for item in tree_data["tree"] if item["type"] == "blob"]
        if not files_in_repo:
            print(f"Repo ID {repo_id}: No files found. Skipping.")
            return False # Count as processed but has no impact
            
        repo_file_counts.append(len(files_in_repo))

        # 3. Process Blobs (Files)
        for file_item in files_in_repo:
            file_sha = file_item["sha"]
            unique_file_hashes.add(file_sha)
            total_files_processed += 1

            # Fetch blob content
            blob_url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{file_sha}"
            blob_response = requests.get(blob_url, headers=HEADERS)
            blob_response.raise_for_status()

            # Per-file rate limiting: check remaining requests and sleep if low
            remaining = int(blob_response.headers.get("X-RateLimit-Remaining", "1"))
            if remaining < 10:
                reset_time = int(blob_response.headers.get("X-RateLimit-Reset", "0"))
                sleep_for = max(reset_time - int(time.time()), 1)
                print(f"  - Rate limit low ({remaining} left). Sleeping for {sleep_for} seconds.")
                time.sleep(sleep_for)
            else:
                time.sleep(0.5)  # Throttle per file to avoid hitting rate limits
            
            # This is a simplified way to decode, which might fail for some binary files.
            try:
                decoded_content = blob_response.json()['content']
                import base64
                decoded_content = base64.b64decode(decoded_content).decode('utf-8', 'ignore')
            except Exception:
                print(f"  - Skipping file {file_item['path']} (binary or unknown encoding)")
                continue

            lines = decoded_content.splitlines()
            loc = len(lines)
            file_loc_counts.append(loc)
            total_lines_processed += loc

            # Hash each line
            for line in lines:
                line_hash = xxhash.xxh128(line.encode('utf-8')).digest()
                unique_line_hashes.add(line_hash)

        processed_repo_count += 1
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error processing repo ID {repo_id}: {e}", file=sys.stderr)
        if e.response and e.response.status_code == 403:
            # Check for rate limit in headers or body
            rate_limit_remaining = e.response.headers.get("X-RateLimit-Remaining")
            if rate_limit_remaining == "0":
                print("GitHub API rate limit exceeded. Waiting before retrying...", file=sys.stderr)
                reset_time = e.response.headers.get("X-RateLimit-Reset")
                if reset_time:
                    wait_time = max(0, int(reset_time) - int(time.time())) + 5
                    print(f"Waiting for {wait_time} seconds until rate limit resets...", file=sys.stderr)
                    time.sleep(wait_time)
                else:
                    time.sleep(60) # Fallback wait
            else:
                # Try to get a more specific error message from the response body
                try:
                    error_json = e.response.json()
                    message = error_json.get("message", "")
                except Exception:
                    message = ""
                if message:
                    print(f"403 Forbidden: {message}", file=sys.stderr)
                else:
                    print("403 Forbidden: Access denied or insufficient permissions.", file=sys.stderr)
        return False

def main():
    """Main function to run the sampling and analysis."""
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print(f"--- Starting GitHub Uniqueness Analyzer ---")
    print(f"Target sample size: {SAMPLE_SIZE} repositories")

    successful_samples = 0
    attempted_repo_ids = set()
    while successful_samples < SAMPLE_SIZE:
        # Randomly select a repo ID that hasn't been tried yet
        repo_id = random.randint(1, MAX_REPO_ID)
        if repo_id in attempted_repo_ids:
            continue
        attempted_repo_ids.add(repo_id)

        rate_limit_info = get_rate_limit()
        if rate_limit_info and rate_limit_info["remaining"] < 100:
            reset_time = rate_limit_info['reset']
            wait_time = max(0, reset_time - time.time()) + 10
            print(f"Approaching rate limit. Waiting for {wait_time:.0f} seconds...")
            time.sleep(wait_time)

        if process_repository(repo_id):
            successful_samples += 1
    print(f"\n--- Analysis Complete ---")
    print(f"Successfully processed {processed_repo_count} / {SAMPLE_SIZE} target repositories.")

    if processed_repo_count == 0:
        print("No repositories were processed. Exiting.")
        sys.exit(1)

    # Calculate Final Sample Statistics
    sample_mean_files = mean(repo_file_counts) if repo_file_counts else 0
    sample_mean_loc = mean(file_loc_counts) if file_loc_counts else 0
    sample_file_uniqueness = len(unique_file_hashes) / total_files_processed if total_files_processed > 0 else 0
    sample_line_uniqueness = len(unique_line_hashes) / total_lines_processed if total_lines_processed > 0 else 0

    print("\n--- Statistical Results ---")
    print(f"\n1. Mean Files per Repo:")
    print(f"   - Sample Mean (f̄): {sample_mean_files:.2f}")
    print(f"   - H₀: {H0_MEAN_FILES_PER_REPO}")

    print(f"\n2. Mean LOC per File:")
    print(f"   - Sample Mean (l̄): {sample_mean_loc:.2f}")
    print(f"   - H₀: {H0_MEAN_LOC_PER_FILE}")

    print(f"\n3. File Uniqueness Ratio:")
    print(f"   - Sample Ratio (r_file): {sample_file_uniqueness:.4%}")
    print(f"   - H₀: {H0_FILE_UNIQUENESS_RATIO:.4%}")

    print(f"\n4. Line Uniqueness Ratio:")
    print(f"   - Sample Ratio (r_line): {sample_line_uniqueness:.4%}")
    print(f"   - H₀: {H0_LINE_UNIQUENESS_RATIO:.4%}")

if __name__ == "__main__":
    main()