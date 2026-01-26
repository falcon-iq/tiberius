"""
GitHub Common Functions
Handles GitHub API requests for PR search
"""

import time
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional


def validate_date(date_str: str) -> str:
    """Validate date format YYYY-MM-DD"""
    datetime.strptime(date_str, "%Y-%m-%d")
    return date_str


def github_request_get(url: str, headers: Dict, params: Optional[Dict] = None, timeout: int = 60):
    """
    Make a GET request to GitHub API with rate limit handling.
    
    Args:
        url: GitHub API URL
        headers: Request headers including auth token
        params: Query parameters
        timeout: Request timeout in seconds
    
    Returns:
        Response object
    """
    while True:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        
        # Handle rate limiting
        if resp.status_code in (403, 429):
            remaining = resp.headers.get("X-RateLimit-Remaining")
            reset = resp.headers.get("X-RateLimit-Reset")
            
            if remaining == "0" and reset:
                wait_s = max(1, int(reset) - int(time.time()) + 2)
                print(f"⏳ Rate limit hit. Waiting {wait_s}s...")
                time.sleep(wait_s)
                continue
            
            # General backoff for other 403/429
            print(f"⏳ Rate limit or forbidden. Waiting 10s...")
            time.sleep(10)
            continue
        
        resp.raise_for_status()
        return resp


def github_paginated_get(url: str, headers: Dict, params: Optional[Dict] = None) -> List[Dict]:
    """
    Make paginated GET requests to GitHub API.
    
    Args:
        url: GitHub API URL
        headers: Request headers including auth token
        params: Query parameters
    
    Returns:
        List of all items from all pages
    """
    items = []
    page = 1
    params = params.copy() if params else {}
    
    while True:
        params.update({"per_page": 100, "page": page})
        data = github_request_get(url, headers, params=params).json()
        
        if not data:
            break
        
        items.extend(data)
        
        if len(data) < 100:
            break
        
        page += 1
    
    return items


def search_prs_authored(org: str, author: str, start_date: str, end_date: str, token: str) -> List[Dict]:
    """
    Search for PRs authored by a user in an organization.
    
    Args:
        org: GitHub organization name
        author: GitHub username (author)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        token: GitHub personal access token
    
    Returns:
        List of PR items from GitHub search API
    """
    validate_date(start_date)
    validate_date(end_date)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    url = "https://api.github.com/search/issues"
    q = f"org:{org} is:pr author:{author} created:{start_date}..{end_date}"
    
    items_all = []
    page = 1
    
    while True:
        payload = github_request_get(url, headers, params={
            "q": q, 
            "per_page": 100, 
            "page": page,
            "sort": "created",
            "order": "desc"
        }).json()
        items = payload.get("items", [])
        
        if not items:
            break
        
        items_all.extend(items)
        
        if len(items) < 100:
            break
        
        page += 1
    
    return items_all


def search_prs_reviewed(org: str, reviewer: str, start_date: str, end_date: str, token: str) -> List[Dict]:
    """
    Search for PRs reviewed by a user in an organization.
    
    Args:
        org: GitHub organization name
        reviewer: GitHub username (reviewer)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        token: GitHub personal access token
    
    Returns:
        List of PR items from GitHub search API
    """
    validate_date(start_date)
    validate_date(end_date)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    url = "https://api.github.com/search/issues"
    q = f"org:{org} is:pr -author:{reviewer} reviewed-by:{reviewer} created:{start_date}..{end_date}"
    
    items_all = []
    page = 1
    
    while True:
        payload = github_request_get(url, headers, params={
            "q": q, 
            "per_page": 100, 
            "page": page,
            "sort": "created",
            "order": "desc"
        }).json()
        items = payload.get("items", [])
        
        if not items:
            break
        
        items_all.extend(items)
        
        if len(items) < 100:
            break
        
        page += 1
    
    return items_all


def parse_owner_repo_from_item(item: Dict) -> tuple:
    """
    Extract owner and repo from GitHub search result item.
    
    Args:
        item: GitHub search result item
    
    Returns:
        Tuple of (owner, repo)
    """
    repo_url = item.get("repository_url")
    owner_repo = repo_url.split("/repos/")[1]
    owner, repo = owner_repo.split("/", 1)
    return owner, repo


def extract_pr_full(owner: str, repo: str, pr_number: int, token: str, base_output_dir) -> str:
    """
    Download full PR details (metadata, comments, files) from GitHub.
    
    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        token: GitHub token
        base_output_dir: Base directory for output
    
    Returns:
        "skipped" if already exists, "downloaded" if newly downloaded
    """
    from pathlib import Path
    
    out_dir = Path(base_output_dir) / owner / repo / f"pr_{pr_number}"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if all 3 files already exist - skip if so
    meta_file = out_dir / f"pr_{pr_number}_meta.csv"
    comments_file = out_dir / f"pr_{pr_number}_comments.csv"
    files_file = out_dir / f"pr_{pr_number}_files.csv"
    
    if meta_file.exists() and comments_file.exists() and files_file.exists():
        return "skipped"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Get PR metadata
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    pr = github_request_get(pr_url, headers).json()
    
    pr_meta = {
        "owner": owner,
        "repo": repo,
        "pr_number": pr_number,
        "pr_title": pr.get("title"),
        "pr_body": pr.get("body"),
        "pr_state": pr.get("state"),
        "pr_draft": pr.get("draft"),
        "pr_author": pr.get("user", {}).get("login"),
        "pr_created_at": pr.get("created_at"),
        "pr_updated_at": pr.get("updated_at"),
        "pr_merged_at": pr.get("merged_at"),
        "pr_mergeable_state": pr.get("mergeable_state"),
        "pr_additions": pr.get("additions"),
        "pr_deletions": pr.get("deletions"),
        "pr_changed_files": pr.get("changed_files"),
        "pr_commits_count": pr.get("commits"),
        "pr_issue_comments_count": pr.get("comments"),
        "pr_review_comments_count": pr.get("review_comments"),
        "pr_html_url": pr.get("html_url"),
    }
    pd.DataFrame([pr_meta]).to_csv(meta_file, index=False)
    
    # Get comments
    issue_comments = github_paginated_get(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments", 
        headers
    )
    review_comments = github_paginated_get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments",
        headers
    )
    reviews = github_paginated_get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
        headers
    )
    
    rows = []
    for c in issue_comments:
        rows.append({
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "comment_type": "ISSUE_COMMENT",
            "comment_id": c.get("id"),
            "user": c.get("user", {}).get("login"),
            "created_at": c.get("created_at"),
            "body": c.get("body"),
            "state": None,
            "is_reviewer": False,
            "path": None,
            "line": None,
            "side": None
        })
    
    for c in review_comments:
        rows.append({
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "comment_type": "REVIEW_INLINE_COMMENT",
            "comment_id": c.get("id"),
            "user": c.get("user", {}).get("login"),
            "created_at": c.get("created_at"),
            "body": c.get("body"),
            "state": None,
            "is_reviewer": True,
            "path": c.get("path"),
            "line": c.get("line"),
            "side": c.get("side")
        })
    
    for r in reviews:
        rows.append({
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "comment_type": "REVIEW_SUMMARY",
            "comment_id": r.get("id"),
            "user": r.get("user", {}).get("login"),
            "created_at": r.get("submitted_at"),
            "body": r.get("body"),
            "state": r.get("state"),
            "is_reviewer": True,
            "path": None,
            "line": None,
            "side": None
        })
    
    pd.DataFrame(rows).to_csv(comments_file, index=False)
    
    # Get files
    pr_files = github_paginated_get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files",
        headers
    )
    
    file_rows = []
    for f in pr_files:
        file_rows.append({
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "filename": f.get("filename"),
            "status": f.get("status"),
            "additions": f.get("additions"),
            "deletions": f.get("deletions"),
            "changes": f.get("changes"),
            "blob_url": f.get("blob_url"),
            "raw_url": f.get("raw_url"),
            "patch": f.get("patch")
        })
    
    pd.DataFrame(file_rows).to_csv(files_file, index=False)
    
    return "downloaded"


def search_and_save_prs(
    task_type: str,
    username: str,
    pr_username: str,
    org: str,
    start_date: str,
    end_date: str,
    token: str,
    output_csv_path
) -> int:
    """
    Search for PRs and save to CSV file.
    
    Args:
        task_type: "authored" or "reviewer"
        username: Internal username
        pr_username: GitHub username (with _LinkedIn suffix if needed)
        org: GitHub organization
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        token: GitHub token
        output_csv_path: Path to save CSV file
    
    Returns:
        Number of PRs found
    """
    print(f"      🔍 Searching GitHub for {task_type} PRs...")
    print(f"         User: {pr_username}")
    print(f"         Date range: {start_date} to {end_date}")
    
    # Search based on task type
    if task_type == "authored":
        items = search_prs_authored(org, pr_username, start_date, end_date, token)
    elif task_type == "reviewer":
        items = search_prs_reviewed(org, pr_username, start_date, end_date, token)
    else:
        raise ValueError(f"Invalid task_type: {task_type}")
    
    print(f"      ✅ Found {len(items)} PRs")
    
    # Parse and save to CSV
    if items:
        index_rows = []
        for item in items:
            owner, repo = parse_owner_repo_from_item(item)
            index_rows.append({
                "org": org,
                "owner": owner,
                "repo": repo,
                "pr_number": item.get("number"),
                "title": item.get("title"),
                "state": item.get("state"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "html_url": item.get("html_url")
            })
        
        # Create output directory if needed
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV with sorting
        df = pd.DataFrame(index_rows)
        df = df.sort_values(["created_at", "owner", "repo", "pr_number"])
        df.to_csv(output_csv_path, index=False)
        
        print(f"      💾 Saved to: {output_csv_path.name}")
    else:
        # Create empty CSV
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["org", "owner", "repo", "pr_number", "title", "state", "created_at", "updated_at", "html_url"]).to_csv(
            output_csv_path, index=False
        )
        print(f"      💾 Saved empty CSV to: {output_csv_path.name}")
    
    return len(items)
