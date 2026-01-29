#!/usr/bin/env python3
"""
PR Comment Classification Pipeline

Classifies GitHub PR review comments into engineering feedback categories
using OpenAI GPT-4o-mini. Processes comments in batches with status tracking.

Categories:
- NITPICK_STYLE: Minor style/readability tweaks
- CODING_STANDARDS: Enforcing conventions/best practices
- TESTING: Requests tests/coverage
- DOCS_COMMENT: Requests documentation changes
- BUG_CORRECTNESS: Logic errors, incorrect behavior
- EDGE_CASES: Missing edge case handling
- RELIABILITY_RESILIENCE: Timeouts/retries/failure modes
- PERFORMANCE: Performance concerns
- SECURITY_PRIVACY: Security/privacy issues
- DESIGN_ARCHITECTURE: API design, abstractions
- DEPENDENCY_BUILD: Build/dependency/config issues
- PROCESS_RELEASE: Rollout/migration/compatibility
- PRODUCT_BEHAVIOR: User impact/semantics
- QUESTION_CLARIFICATION: Asks author intent
- PRAISE_ACK: Thanks/LGTM without actionable content
- OTHER: Doesn't fit or ambiguous

Usage:
    python prCommentClassification.py
"""

import json
import time
import random
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
import textwrap
from common import load_all_config, getDBPath, get_batch_size

# ============================================================================
# Configuration
# ============================================================================

OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_BATCH_SIZE = 50  # Fallback default (actual value from pipeline_config.json via get_batch_size())
TEXT_COL = "body"

# OpenAI pricing for gpt-4o-mini (per 1M tokens)
# https://openai.com/api/pricing/
OPENAI_PRICING = {
    "gpt-4o-mini": {
        "input": 0.150,   # $0.150 per 1M input tokens
        "output": 0.600   # $0.600 per 1M output tokens
    }
}

TAXONOMY = {
    "NITPICK_STYLE": "Minor style/readability tweaks; naming, formatting, small refactors, spelling.",
    "CODING_STANDARDS": "Enforcing conventions/best practices; patterns, consistency, logging style, error handling norms.",
    "TESTING": "Requests tests/coverage; test correctness; flaky tests; missing assertions.",
    "DOCS_COMMENT": "Requests documentation changes; code comments; READMEs; clarifications in docs.",

    "BUG_CORRECTNESS": "Logic errors; incorrect behavior; wrong conditions; potential functional bugs.",
    "EDGE_CASES": "Missing edge case handling; input validation; boundaries; nulls; unexpected states.",
    "RELIABILITY_RESILIENCE": "Timeouts/retries/failure modes/idempotency; error paths; resilience concerns.",
    "PERFORMANCE": "Perf concerns; latency; allocations; expensive calls; scalability; big-O.",
    "SECURITY_PRIVACY": "Secrets/auth/data exposure; injection; permissions; PII; security posture.",

    "DESIGN_ARCHITECTURE": "API design; boundaries; abstractions; tradeoffs; long-term maintainability.",
    "DEPENDENCY_BUILD": "Build/dependency/config/tooling issues; CI; versions; packaging.",
    "PROCESS_RELEASE": "Rollout/migration/backwards compatibility; deprecation; monitoring/alerts; release process.",
    "PRODUCT_BEHAVIOR": "User impact/semantics/requirements; UX expectations; product correctness.",

    "QUESTION_CLARIFICATION": "Asks author intent; requests more context; clarifying questions.",
    "PRAISE_ACK": "Thanks/LGTM/nice work without actionable content.",
    "AI_GENERATED": "Automated comments from AI/bot reviewers (CI checks, automated validations, etc.).",
    "OTHER": "Doesn't fit or ambiguous."
}

SEVERITY_SCALE = ["TRIVIAL", "LOW", "MEDIUM", "HIGH", "BLOCKER"]
TAXONOMY_KEYS = list(TAXONOMY.keys())

# Context fields to include in classification prompt
CONTEXT_FIELDS = ["repo", "pr_number", "pr_title", "pr_author", "comment_type", "path", "line", "side", "state", "created_at", "user"]


# ============================================================================
# Database Functions
# ============================================================================

def connect_to_database(db_path: Path, quiet: bool = False) -> Optional[sqlite3.Connection]:
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(db_path)
        if not quiet:
            print(f"✅ Connected to database: {db_path}")
        return conn
    except Exception as e:
        if not quiet:
            print(f"❌ Database connection error: {e}")
        return None


def check_comments_exist_in_db(conn: sqlite3.Connection, df: pd.DataFrame) -> pd.Series:
    """
    Check which comments already exist in the database.
    
    Args:
        conn: Database connection
        df: DataFrame with comments (must have pr_number, comment_id, user columns)
    
    Returns:
        Boolean Series indicating which rows already exist in database
    """
    if conn is None or len(df) == 0:
        return pd.Series([False] * len(df), index=df.index)
    
    cursor = conn.cursor()
    exists_flags = []
    
    for idx, row in df.iterrows():
        pr_number = int(row.get("pr_number", 0))
        comment_id = int(row.get("comment_id", 0))
        username = str(row.get("user", ""))
        
        # Check if this comment exists in the database
        cursor.execute("""
            SELECT COUNT(*) FROM pr_comment_details 
            WHERE pr_number = ? AND comment_id = ? AND username = ?
        """, (pr_number, comment_id, username))
        
        count = cursor.fetchone()[0]
        exists_flags.append(count > 0)
    
    return pd.Series(exists_flags, index=df.index)


def insert_classified_comments_to_db(conn: sqlite3.Connection, df: pd.DataFrame, 
                                    classified_results: List[Dict], start_idx: int, 
                                    quiet: bool = False) -> Dict:
    """
    Insert classified comments into pr_comment_details table.
    
    Args:
        conn: Database connection
        df: Original DataFrame with comment data
        classified_results: List of classification results
        start_idx: Starting index in the DataFrame
        quiet: If True, suppress print statements
    
    Returns:
        Dictionary with insertion statistics
    """
    inserted = 0
    updated = 0
    errors = 0
    
    cursor = conn.cursor()
    
    for i, result in enumerate(classified_results):
        idx = start_idx + i
        if idx >= len(df):
            break
        
        row = df.iloc[idx]
        
        try:
            # Extract data from row
            pr_number = int(row.get("pr_number", 0))
            comment_id = int(row.get("comment_id", 0))
            username = str(row.get("user", ""))
            comment_type = str(row.get("comment_type", ""))
            created_at = str(row.get("created_at", ""))
            is_reviewer = 1 if row.get("is_reviewer", False) else 0
            line = int(row.get("line", 0)) if pd.notna(row.get("line")) else None
            side = str(row.get("side", "")) if pd.notna(row.get("side")) else None
            pr_author = str(row.get("pr_author", ""))
            
            # Extract classification data
            primary_category = result.get("primary_category", "OTHER")
            secondary_categories = ",".join(result.get("secondary_categories", []))
            severity = result.get("severity", "TRIVIAL")
            confidence = float(result.get("confidence", 0.0))
            actionability = result.get("actionability", "NON_ACTIONABLE")
            rationale = result.get("rationale", "")
            is_ai_reviewer = 1 if result.get("is_ai_reviewer", False) else 0
            
            # Extract signals
            signals = result.get("signals", {})
            is_nitpick = 1 if signals.get("is_nitpick", False) else 0
            mentions_tests = 1 if signals.get("mentions_tests", False) else 0
            mentions_bug = 1 if signals.get("mentions_bug", False) else 0
            mentions_design = 1 if signals.get("mentions_design", False) else 0
            mentions_performance = 1 if signals.get("mentions_performance", False) else 0
            mentions_reliability = 1 if signals.get("mentions_reliability", False) else 0
            mentions_security = 1 if signals.get("mentions_security", False) else 0
            
            # Insert or replace into database
            cursor.execute("""
                INSERT OR REPLACE INTO pr_comment_details (
                    pr_number, comment_type, comment_id, username, created_at,
                    is_reviewer, line, side, pr_author,
                    primary_category, secondary_categories, severity, confidence,
                    actionability, rationale, is_ai_reviewer,
                    is_nitpick, mentions_tests, mentions_bug, mentions_design,
                    mentions_performance, mentions_reliability, mentions_security
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pr_number, comment_type, comment_id, username, created_at,
                is_reviewer, line, side, pr_author,
                primary_category, secondary_categories, severity, confidence,
                actionability, rationale, is_ai_reviewer,
                is_nitpick, mentions_tests, mentions_bug, mentions_design,
                mentions_performance, mentions_reliability, mentions_security
            ))
            
            inserted += 1
            
        except Exception as e:
            errors += 1
            if not quiet:
                print(f"            ⚠️  Error inserting comment {idx}: {e}")
    
    # Commit the transaction
    conn.commit()
    
    if not quiet and inserted > 0:
        print(f"         💾 Database: Inserted {inserted} comments")
    
    return {'inserted': inserted, 'updated': updated, 'errors': errors}


# ============================================================================
# Helper Functions
# ============================================================================

def load_status(status_file: Path) -> Dict:
    """Load classification status for a user"""
    if not status_file.exists():
        return {
            "status": "not_started",
            "last_processed_index": -1,
            "total_comments": 0,
            "classified_comments": 0,
            "errors": [],
            "last_updated": None
        }
    
    with open(status_file, 'r') as f:
        return json.load(f)


def save_status(status_file: Path, status: Dict):
    """Save classification status for a user"""
    status["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)


def build_prompt(comment_body: str, context: dict) -> str:
    """Build classification prompt for OpenAI"""
    ctx_lines = "\n".join([f"- {k}: {v}" for k, v in context.items() if v is not None and str(v) != "nan"])
    taxonomy_desc = "\n".join([f"- {k}: {TAXONOMY[k]}" for k in TAXONOMY_KEYS])

    return textwrap.dedent(f"""
    You are classifying a GitHub PR review comment into engineering feedback categories.
    Return ONLY valid JSON (no markdown, no extra text).

    Taxonomy:
    {taxonomy_desc}

    Severity scale (choose one): {SEVERITY_SCALE}

    Rules:
    - Pure praise/LGTM/thanks without actionable request => PRAISE_ACK (NON_ACTIONABLE).
    - Formatting/naming/readability low impact => NITPICK_STYLE (severity TRIVIAL/LOW).
    - Production behavior might be wrong => BUG_CORRECTNESS / EDGE_CASES / RELIABILITY_RESILIENCE.
    - Structure/tradeoffs/interfaces => DESIGN_ARCHITECTURE.
    - Asking intent/context => QUESTION_CLARIFICATION.
    - Include up to 3 secondary categories if relevant.
    - Confidence should reflect how clearly the comment matches the category.

    Output JSON schema:
    {{
      "primary_category": "<one of {TAXONOMY_KEYS}>",
      "secondary_categories": ["<0-3 from taxonomy>"],
      "severity": "<one of {SEVERITY_SCALE}>",
      "confidence": <float 0.0-1.0>,
      "actionability": "<ACTIONABLE|NON_ACTIONABLE>",
      "rationale": "<1-2 short sentences>",
      "signals": {{
        "is_nitpick": <true|false>,
        "mentions_tests": <true|false>,
        "mentions_bug": <true|false>,
        "mentions_design": <true|false>,
        "mentions_performance": <true|false>,
        "mentions_reliability": <true|false>,
        "mentions_security": <true|false>
      }}
    }}

    Context:
    {ctx_lines}

    Comment:
    {comment_body}
    """).strip()


def invoke_openai_json(client: OpenAI, prompt: str, model: str = OPENAI_MODEL, 
                       max_tokens: int = 700, temperature: float = 0.0, retries: int = 5) -> Tuple[Dict, int, int]:
    """
    Call OpenAI API with retries
    
    Returns:
        Tuple of (result_dict, input_tokens, output_tokens)
    """
    for attempt in range(retries):
        try:
            print(f"            🌐 OpenAI API call: {model} (attempt {attempt + 1}/{retries})")
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            result = json.loads(resp.choices[0].message.content)
            input_tokens = resp.usage.prompt_tokens
            output_tokens = resp.usage.completion_tokens
            return result, input_tokens, output_tokens
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep((2 ** attempt) + random.random())


def classify_comment(client: OpenAI, comment_body: str, context: dict) -> Tuple[Dict, int, int]:
    """
    Classify a single comment
    
    Returns:
        Tuple of (classification_dict, input_tokens, output_tokens)
    """
    prompt = build_prompt(comment_body, context)
    return invoke_openai_json(client, prompt)


def get_default_classification(is_empty: bool = False) -> Dict:
    """Return default classification for empty/error cases"""
    if is_empty:
        # Empty comments are typically approvals (LGTM with no text)
        return {
            "primary_category": "PRAISE_ACK",
            "secondary_categories": [],
            "severity": "TRIVIAL",
            "confidence": 0.9,
            "actionability": "NON_ACTIONABLE",
            "rationale": "Empty comment body - likely approval/acknowledgment.",
            "is_ai_reviewer": False,
            "signals": {
                "is_nitpick": False,
                "mentions_tests": False,
                "mentions_bug": False,
                "mentions_design": False,
                "mentions_performance": False,
                "mentions_reliability": False,
                "mentions_security": False
            }
        }
    else:
        # Classification error
        return {
            "primary_category": "OTHER",
            "secondary_categories": [],
            "severity": "TRIVIAL",
            "confidence": 0.2,
            "actionability": "NON_ACTIONABLE",
            "rationale": "Classification error.",
            "is_ai_reviewer": False,
            "signals": {
                "is_nitpick": False,
                "mentions_tests": False,
                "mentions_bug": False,
                "mentions_design": False,
                "mentions_performance": False,
                "mentions_reliability": False,
                "mentions_security": False
            }
        }


def apply_guardrails(classification: Dict) -> Dict:
    """Apply validation guardrails to classification output"""
    if classification.get("primary_category") not in TAXONOMY_KEYS:
        classification["primary_category"] = "OTHER"
    
    if classification.get("severity") not in SEVERITY_SCALE:
        classification["severity"] = "LOW"
    
    if not isinstance(classification.get("secondary_categories", []), list):
        classification["secondary_categories"] = []
    
    if not isinstance(classification.get("confidence", 0.0), (int, float)):
        classification["confidence"] = 0.0
    
    return classification


def calculate_cost(input_tokens: int, output_tokens: int, model: str = OPENAI_MODEL) -> float:
    """Calculate cost in USD for OpenAI API call"""
    pricing = OPENAI_PRICING.get(model, OPENAI_PRICING["gpt-4o-mini"])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def is_ai_reviewer(username: str, ai_reviewer_prefixes: List[str]) -> bool:
    """Check if username matches AI reviewer prefixes"""
    if not username or not ai_reviewer_prefixes:
        return False
    username_lower = str(username).lower()
    return any(username_lower.startswith(prefix.lower()) for prefix in ai_reviewer_prefixes)


def get_ai_generated_classification(comment_body: str) -> Dict:
    """Return classification for AI-generated comments without calling OpenAI"""
    return {
        "primary_category": "AI_GENERATED",
        "secondary_categories": [],
        "severity": "LOW",
        "confidence": 1.0,
        "actionability": "NON_ACTIONABLE",
        "rationale": "Automated comment from AI/bot reviewer - skipped OpenAI classification.",
        "is_ai_reviewer": True,
        "signals": {
            "is_nitpick": False,
            "mentions_tests": False,
            "mentions_bug": False,
            "mentions_design": False,
            "mentions_performance": False,
            "mentions_reliability": False,
            "mentions_security": False
        }
    }


def classify_comments_batch(client: OpenAI, df: pd.DataFrame, start_idx: int, 
                            end_idx: int, cache: Dict, token_cache: Dict, 
                            ai_reviewer_prefixes: List[str]) -> Tuple[List[Dict], List[Tuple[int, str]], float]:
    """
    Classify a batch of comments
    
    Returns:
        Tuple of (results, errors, batch_cost)
    """
    results = []
    errors = []
    batch_cost = 0.0
    
    for i in range(start_idx, min(end_idx, len(df))):
        row = df.iloc[i]
        comment = str(row.get(TEXT_COL, "") or "").strip()
        
        # Build context from available fields
        context = {k: row.get(k) for k in CONTEXT_FIELDS if k in df.columns}
        
        # Get PR number for display
        pr_number = row.get("pr_number", "N/A")
        comment_user = row.get("user", "N/A")
        
        # Check if AI reviewer
        is_ai = is_ai_reviewer(comment_user, ai_reviewer_prefixes)
        
        # Handle empty comments
        if not comment:
            result = get_default_classification(is_empty=True)
            result["is_ai_reviewer"] = is_ai
            results.append(result)
            ai_tag = " [AI]" if is_ai else ""
            print(f"            [{i}] PR #{pr_number} - {comment_user}{ai_tag}: [EMPTY] → PRAISE_ACK (approval)")
            continue
        
        # Skip OpenAI classification for AI reviewers
        if is_ai:
            result = get_ai_generated_classification(comment)
            results.append(result)
            comment_preview = comment[:60] + "..." if len(comment) > 60 else comment
            print(f"            [{i}] PR #{pr_number} - {comment_user} [AI]:")
            print(f"                 \"{comment_preview}\"")
            print(f"                 → AI_GENERATED (skipped OpenAI classification)")
            continue
        
        # Check cache for human comments
        cache_key = comment
        try:
            if cache_key in cache:
                # Use cached classification
                out = cache[cache_key]
                input_tokens, output_tokens = token_cache.get(cache_key, (0, 0))
            else:
                # Classify and cache
                out, input_tokens, output_tokens = classify_comment(client, comment, context)
                cache[cache_key] = out
                token_cache[cache_key] = (input_tokens, output_tokens)
                
                # Calculate cost for this call
                call_cost = calculate_cost(input_tokens, output_tokens)
                batch_cost += call_cost
            
            # Apply guardrails
            out = apply_guardrails(out)
            
            # Add AI reviewer flag (will be False for human comments)
            out["is_ai_reviewer"] = False
            results.append(out)
            
            # Print comment with classification
            comment_preview = comment[:60] + "..." if len(comment) > 60 else comment
            category = out.get("primary_category", "OTHER")
            severity = out.get("severity", "LOW")
            confidence = out.get("confidence", 0.0)
            print(f"            [{i}] PR #{pr_number} - {comment_user}:")
            print(f"                 \"{comment_preview}\"")
            print(f"                 → {category} (severity: {severity}, confidence: {confidence:.2f})")
            
        except Exception as e:
            error_msg = str(e)
            errors.append((i, error_msg))
            error_result = get_default_classification()
            error_result["rationale"] = f"Model error: {error_msg[:100]}"
            error_result["is_ai_reviewer"] = False
            results.append(error_result)
            print(f"            [{i}] PR #{pr_number} - {comment_user}: ERROR → {error_msg[:50]}")
    
    return results, errors, batch_cost


def process_comment_file(client: OpenAI, csv_path: Path, status_file: Path, 
                        ai_reviewer_prefixes: List[str], db_conn: Optional[sqlite3.Connection] = None,
                        batch_size: int = DEFAULT_BATCH_SIZE, single_batch_mode: bool = False) -> bool:
    """
    Process a single comment file with batching and status tracking
    
    Args:
        client: OpenAI client
        csv_path: Path to the CSV file to process
        status_file: Path to the status file
        ai_reviewer_prefixes: List of AI reviewer username prefixes
        db_conn: Optional database connection for inserting classified comments
        batch_size: Number of comments to process per batch
        single_batch_mode: If True, process only one batch per run and exit
    """
    
    # Load status
    status = load_status(status_file)
    
    # Check if already completed
    if status["status"] == "completed":
        print(f"      ✅ Already completed: {csv_path.name}")
        return True
    
    # Load CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"      ❌ Error loading CSV: {e}")
        return False
    
    if len(df) == 0:
        print(f"      ℹ️  Empty file: {csv_path.name}")
        status["status"] = "completed"
        status["total_comments"] = 0
        status["classified_comments"] = 0
        save_status(status_file, status)
        return True
    
    # Check if TEXT_COL exists
    if TEXT_COL not in df.columns:
        print(f"      ❌ Column '{TEXT_COL}' not found in {csv_path.name}")
        return False
    
    # Check if already classified (has classification columns)
    classification_cols = ["primary_category", "severity", "confidence", "actionability"]
    already_classified = all(col in df.columns for col in classification_cols)
    
    if already_classified and status["status"] == "completed":
        print(f"      ✅ Already classified: {csv_path.name}")
        return True
    
    # Filter out comments that already exist in database
    if db_conn is not None:
        print(f"      🔍 Checking for already-classified comments in database...")
        existing_mask = check_comments_exist_in_db(db_conn, df)
        existing_count = existing_mask.sum()
        
        if existing_count > 0:
            print(f"      ⏭️  Found {existing_count} already-classified comments, skipping them")
            # Mark existing comments as "processed" in the DataFrame
            df = df[~existing_mask].copy()
            
            if len(df) == 0:
                print(f"      ✅ All comments already classified in database")
                status["status"] = "completed"
                status["total_comments"] = existing_count
                status["classified_comments"] = existing_count
                save_status(status_file, status)
                return True
            
            # Reset index for the filtered DataFrame
            df = df.reset_index(drop=True)
            print(f"      📊 Remaining to classify: {len(df)} comments")
    
    # Initialize status
    if status["status"] == "not_started":
        status["status"] = "in_progress"
        status["total_comments"] = len(df)
        status["classified_comments"] = 0
        status["last_processed_index"] = -1
        status["errors"] = []
        save_status(status_file, status)
    
    # Resume from last position
    start_idx = status["last_processed_index"] + 1
    total = len(df)
    cache = {}
    token_cache = {}  # Cache for token counts
    total_cost = 0.0
    
    print(f"      📄 File: {csv_path.name}")
    print(f"      📊 Total comments: {total}")
    print(f"      🔄 Starting from index: {start_idx}")
    print(f"      📦 Batch size: {batch_size}")
    print()
    
    # Process in batches
    all_results = []
    batch_num = 0
    batches_processed = 0
    
    for batch_start in range(start_idx, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch_num += 1
        
        print(f"         Batch {batch_num}: Processing comments {batch_start}-{batch_end-1}...")
        
        try:
            results, errors, batch_cost = classify_comments_batch(
                client, df, batch_start, batch_end, cache, token_cache, ai_reviewer_prefixes
            )
            all_results.extend(results)
            total_cost += batch_cost
            batches_processed += 1
            
            # Insert batch results into database if connection provided
            if db_conn is not None:
                db_result = insert_classified_comments_to_db(db_conn, df, results, batch_start, quiet=False)
                if db_result['errors'] > 0:
                    print(f"         ⚠️  Database insertion had {db_result['errors']} error(s)")
            
            # Update status
            status["last_processed_index"] = batch_end - 1
            status["classified_comments"] = batch_end
            if errors:
                status["errors"].extend([(idx, err) for idx, err in errors])
            
            # Update status to in_progress if not yet completed
            if batch_end < total:
                status["status"] = "in_progress"
            
            save_status(status_file, status)
            
            # Print batch summary
            if batch_cost > 0:
                print(f"         💰 Batch cost: ${batch_cost:.6f}")
            print()
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
            
            # If single batch mode, stop after one batch
            if single_batch_mode:
                print(f"      🛑 Single batch mode: Stopping after 1 batch")
                print(f"      📊 Progress: {batch_end}/{total} comments ({(batch_end/total)*100:.1f}%)")
                print(f"      ▶️  Run again to continue from comment {batch_end}")
                break
            
        except Exception as e:
            print(f"         ❌ Batch error: {e}")
            status["errors"].append((batch_start, str(e)))
            save_status(status_file, status)
            return False
    
    # Convert results to DataFrame and append columns
    if all_results:
        res_df = pd.json_normalize(all_results)
        
        # Combine with original data (only the processed rows)
        df_processed = df.iloc[start_idx:start_idx + len(all_results)].reset_index(drop=True)
        df_aug = pd.concat([df_processed, res_df], axis=1)
        
        # If we processed from the beginning, save the augmented data
        # Otherwise, we need to merge with existing data
        if start_idx == 0:
            df_aug.to_csv(csv_path, index=False)
        else:
            # Load existing classified data and append new results
            df_existing = df.iloc[:start_idx]
            df_combined = pd.concat([df_existing, df_aug], ignore_index=True)
            df_combined.to_csv(csv_path, index=False)
        
        print(f"      ✅ Classified {len(all_results)} comments in this run")
        print(f"      💾 Updated: {csv_path.name}")
        if total_cost > 0:
            print(f"      💰 Cost for this run: ${total_cost:.6f}")
    
    # Check if all comments have been processed
    current_end = status["last_processed_index"] + 1
    if current_end >= total:
        # Mark as completed
        status["status"] = "completed"
        status["classified_comments"] = total
        if total_cost > 0:
            # Accumulate total cost
            status["total_cost"] = status.get("total_cost", 0.0) + total_cost
        save_status(status_file, status)
        print(f"      🎉 All comments classified!")
    else:
        # Save in-progress status
        if total_cost > 0:
            # Accumulate total cost
            status["total_cost"] = status.get("total_cost", 0.0) + total_cost
        save_status(status_file, status)
    
    return True


def classify_user_comments(username: str, comments_folder: Path, task_folder: Path, 
                          openai_client: OpenAI, ai_reviewer_prefixes: List[str],
                          db_conn: Optional[sqlite3.Connection] = None,
                          batch_size: int = DEFAULT_BATCH_SIZE, single_batch_mode: bool = False) -> Dict[str, bool]:
    """Classify comments for a single user and insert into database"""
    
    results = {}
    
    # Read task files to get date ranges
    task_types = ["authored", "reviewer"]
    
    for task_type in task_types:
        # Read task file
        task_file = task_folder / f"pr_{task_type}_{username}.json"
        
        if not task_file.exists():
            print(f"   ⚠️  Task file not found: {task_file.name}")
            continue
        
        try:
            with open(task_file, 'r') as f:
                task_data = json.load(f)
            
            start_date = task_data.get('start_date')
            end_date = task_data.get('end_date')
            
            if not start_date or not end_date:
                print(f"   ⚠️  Missing date range in {task_file.name}")
                continue
            
            print(f"   ✅ Task file: {task_file.name}")
            print(f"   📅 Date range: {start_date} to {end_date}")
            
            # Determine file type name for CSV filename
            if task_type == "authored":
                file_type = "authored"
            elif task_type == "reviewer":
                file_type = "reviewed"
            else:
                file_type = task_type
            
            # Construct comment file path
            # Pattern: username_comments_on_{authored|reviewed}_prs_start-date_end-date.csv
            comment_file = comments_folder / f"{username}_comments_on_{file_type}_prs_{start_date}_{end_date}.csv"
            
            if not comment_file.exists():
                print(f"   ⚠️  Comment file not found: {comment_file.name}")
                continue
            
            # Status file with dates for uniqueness
            status_file = task_folder / f"{username}_comments_classification_{file_type}_status.json"
            
            print(f"\n   📝 Processing: {comment_file.name}")
            success = process_comment_file(openai_client, comment_file, status_file, ai_reviewer_prefixes, 
                                          db_conn, batch_size, single_batch_mode)
            results[f"{file_type}_{start_date}_{end_date}"] = success
        
        except Exception as e:
            print(f"   ❌ Error reading {task_file.name}: {e}")
            continue
    
    return results


def main():
    """Main pipeline function"""
    print("=" * 80)
    print("PR Comment Classification Pipeline")
    print("=" * 80)
    
    # Load all configuration
    all_config = load_all_config()
    config = all_config['config']
    settings = all_config['settings']
    users = all_config['users']
    paths = all_config['paths']
    
    base_dir = paths['base_dir']
    pr_data_folder = paths['pr_data_folder']
    task_folder = base_dir / config.get('task_folder', 'pipeline-tasks')
    comments_folder = pr_data_folder / config.get('comments_folder', 'comments')
    
    print(f"📁 Base directory: {base_dir}")
    print(f"📂 Comments folder: {comments_folder}")
    print(f"📂 Task folder: {task_folder}")
    print()
    
    # Get OpenAI API key
    openai_api_key = settings.get('openai_api_key')
    if not openai_api_key:
        print("❌ OpenAI API key not found in user-settings.json")
        print("   Please add 'openai_api_key' to your settings.")
        return
    
    # Get AI reviewer prefixes from settings
    ai_reviewer_prefixes = settings.get('ai_reviewer_prefixes', ["github-actions", "svc-"])
    
    # Get batch size from pipeline config
    batch_size = get_batch_size(config)
    
    # Get single batch mode from settings
    single_batch_mode = settings.get('comment_classification_single_batch_mode', True)
    
    # Initialize OpenAI client
    openai_client = OpenAI(api_key=openai_api_key)
    print(f"✅ OpenAI client initialized (model: {OPENAI_MODEL})")
    print(f"📦 Batch size: {batch_size} comments")
    if single_batch_mode:
        print(f"🛑 Single batch mode: ENABLED (will process 1 batch per run)")
    print(f"🤖 AI reviewer prefixes: {ai_reviewer_prefixes}")
    print()
    
    # Connect to database
    db_path = getDBPath(base_dir)
    db_conn = connect_to_database(db_path, quiet=False)
    if not db_conn:
        print("⚠️  Warning: Database connection failed. Comments will be classified but not inserted into database.")
    print()
    
    # Create folders if they don't exist
    task_folder.mkdir(parents=True, exist_ok=True)
    comments_folder.mkdir(parents=True, exist_ok=True)
    
    print(f"👥 Found {len(users)} users")
    print()
    
    # Process each user
    total_users = len(users)
    successful = 0
    failed = 0
    overall_cost = 0.0
    
    for idx, user in enumerate(users, 1):
        username = user.get('userName')
        if not username:
            print(f"⚠️  Skipping user with no userName")
            continue
        
        print(f"\n{'='*80}")
        print(f"👤 User {idx}/{total_users}: {username}")
        print(f"{'='*80}")
        
        try:
            results = classify_user_comments(username, comments_folder, task_folder, openai_client, 
                                            ai_reviewer_prefixes, db_conn, batch_size, single_batch_mode)
            
            # Accumulate costs from status files
            for file_key in results.keys():
                # Parse the file key to get file_type, start_date, end_date
                parts = file_key.split('_')
                if len(parts) >= 3:
                    file_type = parts[0]
                    start_date = parts[1] if len(parts) > 1 else "unknown"
                    end_date = parts[2] if len(parts) > 2 else "unknown"
                    status_file = task_folder / f"{username}_comments_classification_{file_type}_status.json"
                    if status_file.exists():
                        with open(status_file, 'r') as f:
                            status_data = json.load(f)
                            file_cost = status_data.get('total_cost', 0.0)
                            overall_cost += file_cost
            
            if results and all(results.values()):
                successful += 1
                print(f"\n   ✅ Classification completed for {username}")
            else:
                failed += 1
                print(f"\n   ⚠️  Some files failed for {username}")
        
        except Exception as e:
            failed += 1
            print(f"\n   ❌ Error processing {username}: {e}")
    
    # Close database connection
    if db_conn:
        db_conn.close()
        print(f"\n✅ Database connection closed")
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 Classification Summary")
    print(f"{'='*80}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {total_users}")
    if overall_cost > 0:
        print(f"💰 Total OpenAI Cost: ${overall_cost:.6f}")
    print()


if __name__ == "__main__":
    main()
