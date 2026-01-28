#!/usr/bin/env python3
"""
PR OKR Mapper (Enhanced with Fallback Classification)

Maps OKRs to PRs using intelligent matching with embedding similarity, hybrid scoring,
and fallback classification for PRs that don't match any OKR.

Features:
- OpenAI embeddings with chunking support for large PRs
- Hybrid scoring (embeddings + lexical overlap + acronym boost)
- Confidence thresholds to ensure quality matches
- Zero-shot classification fallback for non-OKR PRs
- Accurate token counting with tiktoken
"""

import json
import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List, Set, Tuple
from common import load_all_config

# Global zero-shot classifier (lazy loaded)
_zero_shot_classifier = None
_tokenizer = None

# Configuration constants (can be overridden by user-settings.json)
FALLBACK_LABELS = ["cleanup", "dependency-updates", "refactoring", "no-classification"]
B_SCORE_THRESHOLD = 0.33      # Minimum confidence for OKR match
B_MARGIN_THRESHOLD = 0.03     # Minimum margin between 1st and 2nd best match
ACRONYM_BOOST_PER_MATCH = 0.08
ACRONYM_BOOST_MAX = 0.24
LEXICAL_WEIGHT = 0.12
EMBED_WEIGHT = 0.88           # 1.0 - LEXICAL_WEIGHT


# ============================================================================
# TEXT PROCESSING UTILITIES
# ============================================================================

def extract_acronyms(text: str) -> Set[str]:
    """
    Extract 2-10 character all-caps tokens (e.g., ESR, API, LAN, OASIS).
    
    Args:
        text: Input text
    
    Returns:
        Set of acronyms found in text
    """
    return set(re.findall(r"\b[A-Z][A-Z0-9]{1,9}\b", text or ""))


def tokenize_words(text: str) -> Set[str]:
    """
    Extract 3+ character lowercase alphanumeric tokens for lexical matching.
    
    Args:
        text: Input text
    
    Returns:
        Set of lowercase tokens
    """
    return set(re.findall(r"[a-z0-9]{3,}", (text or "").lower()))


def chunk_text(text: str, chunk_size: int = 2500, overlap: int = 300, max_chunks: int = 8) -> List[str]:
    """
    Chunk large text with overlap for better embedding coverage.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Overlap between chunks
        max_chunks: Maximum number of chunks
    
    Returns:
        List of text chunks
    """
    text = text or ""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    i = 0
    while i < len(text) and len(chunks) < max_chunks:
        chunks.append(text[i:i+chunk_size])
        i += (chunk_size - overlap)
    
    return chunks


def get_tokenizer():
    """Get or initialize tiktoken tokenizer (lazy loading)."""
    global _tokenizer
    if _tokenizer is None:
        try:
            import tiktoken
            try:
                _tokenizer = tiktoken.encoding_for_model("text-embedding-3-large")
            except:
                _tokenizer = tiktoken.get_encoding("cl100k_base")  # Fallback
        except ImportError:
            print("⚠️  tiktoken not installed, using character-based estimation")
            _tokenizer = False  # Marker to use fallback
    return _tokenizer


def estimate_tokens_accurate(text: str) -> int:
    """
    Accurate token count using tiktoken.
    
    Args:
        text: Text to count tokens for
    
    Returns:
        Token count
    """
    tokenizer = get_tokenizer()
    if tokenizer is False:
        # Fallback: ~4 characters per token
        return len(text) // 4
    return len(tokenizer.encode(text))


def get_zero_shot_classifier():
    """Get or initialize zero-shot classifier (lazy loading)."""
    global _zero_shot_classifier
    if _zero_shot_classifier is None:
        try:
            from transformers import pipeline
            print("📦 Loading zero-shot classification model (facebook/bart-large-mnli)...")
            _zero_shot_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # CPU (change to 0 for GPU)
            )
            print("✅ Zero-shot model loaded")
        except Exception as e:
            print(f"⚠️  Failed to load zero-shot classifier: {e}")
            _zero_shot_classifier = False  # Marker for failed load
    return _zero_shot_classifier


# ============================================================================
# EXISTING HELPER FUNCTIONS (UNCHANGED)
# ============================================================================

def check_pr_downloaded(pr_data_folder: Path, owner: str, repo: str, pr_number: int) -> bool:
    """
    Check if PR data has been downloaded.
    
    Args:
        pr_data_folder: Base PR data folder path
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
    
    Returns:
        True if all 3 PR files exist, False otherwise
    """
    pr_dir = pr_data_folder / owner / repo / f"pr_{pr_number}"
    
    if not pr_dir.exists():
        return False
    
    # Check if all 3 files exist
    meta_file = pr_dir / f"pr_{pr_number}_meta.csv"
    comments_file = pr_dir / f"pr_{pr_number}_comments.csv"
    files_file = pr_dir / f"pr_{pr_number}_files.csv"
    
    return meta_file.exists() and comments_file.exists() and files_file.exists()


def check_okrs_exist(pr_data_folder: Path, owner: str, repo: str, pr_number: int, username: str) -> bool:
    """
    Check if okrs_{username}.csv already exists for this PR.
    
    Args:
        pr_data_folder: Base PR data folder path
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        username: Username for user-specific OKR file
    
    Returns:
        True if okrs_{username}.csv exists, False otherwise
    """
    pr_dir = pr_data_folder / owner / repo / f"pr_{pr_number}"
    okrs_file = pr_dir / f"okrs_{username}.csv"
    
    return okrs_file.exists()


def load_okrs_for_user(username: str, okr_folder: Path) -> Optional[pd.DataFrame]:
    """
    Load parsed OKRs for a specific user.
    
    Args:
        username: Username
        okr_folder: OKR folder path
    
    Returns:
        DataFrame with OKR texts or None if not found
    """
    okr_parsed_dir = okr_folder / 'parsed'
    okr_file = okr_parsed_dir / f"{username}_okrs_extracted.csv"
    
    if not okr_file.exists():
        return None
    
    try:
        okrs_df = pd.read_csv(okr_file)
        
        # Keep only Objective + Child Item; forward-fill merged Objective rows
        okrs_df = okrs_df[["Objectives", "Child Items"]].fillna("")
        okrs_df["Objectives"] = okrs_df["Objectives"].astype(str).str.strip()
        okrs_df["Child Items"] = okrs_df["Child Items"].astype(str).str.strip()
        okrs_df["Objectives"] = okrs_df["Objectives"].replace("", pd.NA).ffill().fillna("")
        
        # Create combined OKR text
        okrs_df["okr_text"] = okrs_df["Objectives"] + " | " + okrs_df["Child Items"]
        
        return okrs_df
    except Exception as e:
        print(f"         ❌ Error loading OKRs: {e}")
        return None


def load_pr_text(pr_data_folder: Path, owner: str, repo: str, pr_number: int) -> str:
    """
    Load PR text from meta, comments, and files.
    
    Args:
        pr_data_folder: Base PR data folder path
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
    
    Returns:
        Combined PR text
    """
    pr_dir = pr_data_folder / owner / repo / f"pr_{pr_number}"
    
    pr_title = ""
    pr_body = ""
    comments_text = []
    filenames = []
    patches = []
    
    # Load meta
    meta_path = pr_dir / f"pr_{pr_number}_meta.csv"
    if meta_path.exists():
        try:
            meta_df = pd.read_csv(meta_path)
            if len(meta_df) > 0:
                pr_title = str(meta_df.iloc[0].get("pr_title", "") or "")
                pr_body = str(meta_df.iloc[0].get("pr_body", "") or "")
        except Exception:
            pass
    
    # Load comments
    comments_path = pr_dir / f"pr_{pr_number}_comments.csv"
    if comments_path.exists():
        try:
            comments_df = pd.read_csv(comments_path)
            if "body" in comments_df.columns:
                comments_text = comments_df["body"].dropna().astype(str).tolist()
        except Exception:
            pass
    
    # Load files
    files_path = pr_dir / f"pr_{pr_number}_files.csv"
    if files_path.exists():
        try:
            files_df = pd.read_csv(files_path)
            if "filename" in files_df.columns:
                filenames = files_df["filename"].dropna().astype(str).tolist()
            if "patch" in files_df.columns:
                # Truncate patches to avoid huge texts
                patches = [str(p)[:800] for p in files_df["patch"].dropna().astype(str).tolist()]
        except Exception:
            pass
    
    # Combine all text
    combined_text = "\n".join(
        [pr_title, pr_body] + comments_text + filenames + patches
    ).strip()
    
    return combined_text[:20000]  # Limit to 20k characters


def map_okr_simple(pr_text: str, okr_texts: list) -> tuple:
    """
    Simple string matching-based OKR mapping (fallback when OpenAI not available).
    Uses TF-IDF cosine similarity.
    
    Args:
        pr_text: PR text
        okr_texts: List of OKR texts
    
    Returns:
        Tuple of (best_okr_index, confidence_score)
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    if not okr_texts or not pr_text:
        return (-1, 0.0)
    
    try:
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        vectors = vectorizer.fit_transform([pr_text] + okr_texts)
        
        # Calculate similarity
        pr_vector = vectors[0:1]
        okr_vectors = vectors[1:]
        similarities = cosine_similarity(pr_vector, okr_vectors)[0]
        
        best_idx = similarities.argmax()
        best_score = similarities[best_idx]
        
        return (int(best_idx), float(best_score))
    except Exception as e:
        print(f"         ⚠️  Simple matching error: {e}")
        return (-1, 0.0)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    Uses tiktoken if available, otherwise ~4 characters per token.
    """
    return estimate_tokens_accurate(text)


def calculate_embedding_cost(tokens: int, model: str = "text-embedding-3-large") -> float:
    """
    Calculate OpenAI embedding cost.
    
    Pricing (as of 2024):
    - text-embedding-3-small: $0.02 / 1M tokens
    - text-embedding-3-large: $0.13 / 1M tokens
    """
    if "large" in model:
        cost_per_million = 0.13
    else:
        cost_per_million = 0.02
    
    return (tokens / 1_000_000) * cost_per_million


def map_okr_openai(pr_text: str, okr_texts: list, openai_api_key: str) -> tuple:
    """
    OpenAI embedding-based OKR mapping.
    
    Args:
        pr_text: PR text
        okr_texts: List of OKR texts
        openai_api_key: OpenAI API key
    
    Returns:
        Tuple of (best_okr_index, confidence_score, tokens_used, cost)
    """
    try:
        from openai import OpenAI
        import numpy as np
        
        client = OpenAI(api_key=openai_api_key)
        model = "text-embedding-3-large"
        
        # Estimate tokens
        pr_text_truncated = pr_text[:8000]
        pr_tokens = estimate_tokens(pr_text_truncated)
        okr_tokens = sum(estimate_tokens(okr) for okr in okr_texts)
        total_tokens = pr_tokens + okr_tokens
        
        # Get embeddings
        pr_response = client.embeddings.create(input=[pr_text_truncated], model=model)
        pr_embedding = np.array(pr_response.data[0].embedding)
        
        # Batch embed OKRs (only once per user, cached in memory)
        okr_response = client.embeddings.create(input=okr_texts, model=model)
        okr_embeddings = np.array([data.embedding for data in okr_response.data])
        
        # Calculate cosine similarity
        pr_norm = pr_embedding / np.linalg.norm(pr_embedding)
        okr_norms = okr_embeddings / np.linalg.norm(okr_embeddings, axis=1, keepdims=True)
        similarities = np.dot(okr_norms, pr_norm)
        
        best_idx = similarities.argmax()
        best_score = similarities[best_idx]
        
        # Calculate cost
        cost = calculate_embedding_cost(total_tokens, model)
        
        return (int(best_idx), float(best_score), total_tokens, cost)
    except Exception as e:
        print(f"         ⚠️  OpenAI mapping error: {e}")
        return (-1, 0.0, 0, 0.0)


# ============================================================================
# ENHANCED OKR MATCHING WITH PRECOMPUTATION
# ============================================================================

def precompute_okr_data(okrs_df: pd.DataFrame, openai_api_key: Optional[str]) -> Dict:
    """
    Precompute embeddings, acronyms, and keywords for ALL OKRs once.
    This avoids redundant computation for every PR.
    
    Args:
        okrs_df: DataFrame with OKR texts
        openai_api_key: Optional OpenAI API key
    
    Returns:
        Dictionary with precomputed data:
        {
            "okr_texts": list,
            "okr_embeddings": np.array,
            "okr_acronyms": list[set],
            "okr_keywords": list[set]
        }
    """
    okr_texts = okrs_df["okr_text"].tolist()
    okr_acronyms = [extract_acronyms(text) for text in okr_texts]
    okr_keywords = [tokenize_words(text) for text in okr_texts]
    
    # Precompute OKR embeddings
    if openai_api_key:
        print(f"      🌐 Precomputing embeddings for {len(okr_texts)} OKRs...")
        okr_embeddings = get_okr_embeddings_batch(okr_texts, openai_api_key)
    else:
        # TF-IDF vectors (computed on-demand during matching)
        okr_embeddings = None
    
    return {
        "okr_texts": okr_texts,
        "okr_embeddings": okr_embeddings,
        "okr_acronyms": okr_acronyms,
        "okr_keywords": okr_keywords,
        "okrs_df": okrs_df
    }


def get_okr_embeddings_batch(okr_texts: List[str], openai_api_key: str) -> np.array:
    """
    Get embeddings for all OKRs in one batch call.
    
    Args:
        okr_texts: List of OKR texts
        openai_api_key: OpenAI API key
    
    Returns:
        numpy array of embeddings (normalized)
    """
    try:
        from openai import OpenAI
        from sklearn.preprocessing import normalize as sklearn_normalize
        
        client = OpenAI(api_key=openai_api_key)
        model = "text-embedding-3-large"
        
        # Batch embed all OKRs
        response = client.embeddings.create(input=okr_texts, model=model)
        embeddings = np.array([data.embedding for data in response.data])
        
        # Normalize for cosine similarity
        embeddings = sklearn_normalize(embeddings)
        
        print(f"         ✅ {len(okr_texts)} OKR embeddings ready (dim: {embeddings.shape[1]})")
        return embeddings
    except Exception as e:
        print(f"         ⚠️  Failed to precompute OKR embeddings: {e}")
        return None


def get_pr_embeddings_with_chunking(pr_text: str, openai_api_key: str) -> np.array:
    """
    Get PR embeddings with automatic chunking for large texts.
    
    Args:
        pr_text: PR text
        openai_api_key: OpenAI API key
    
    Returns:
        numpy array of embeddings (shape: (1, dim) or (n_chunks, dim))
    """
    from openai import OpenAI
    
    client = OpenAI(api_key=openai_api_key)
    model = "text-embedding-3-large"
    
    # Estimate tokens
    tokens = estimate_tokens(pr_text)
    
    if tokens <= 8000:  # OpenAI limit
        # Single embedding
        pr_text_truncated = pr_text[:30000]  # Character safety limit
        response = client.embeddings.create(input=[pr_text_truncated], model=model)
        embedding = np.array([response.data[0].embedding])
        return embedding
    else:
        # Chunk for very large texts
        chunks = chunk_text(pr_text, chunk_size=7000, overlap=300, max_chunks=4)
        print(f"         📝 Large PR ({tokens} tokens), chunking into {len(chunks)} parts")
        response = client.embeddings.create(input=chunks, model=model)
        embeddings = np.array([data.embedding for data in response.data])
        return embeddings


def hybrid_score(embed_sim: float, pr_words: Set[str], okr_words: Set[str], 
                 acronym_overlap: int) -> float:
    """
    Compute hybrid similarity score combining embeddings, lexical overlap, and acronyms.
    
    Formula:
        (0.88 * embedding) + (0.12 * jaccard) + acronym_boost
    
    Args:
        embed_sim: Embedding similarity (cosine)
        pr_words: PR word tokens
        okr_words: OKR word tokens
        acronym_overlap: Number of matching acronyms
    
    Returns:
        Hybrid score
    """
    # Jaccard similarity for lexical overlap
    if not pr_words or not okr_words:
        jacc = 0.0
    else:
        jacc = len(pr_words & okr_words) / max(1, len(pr_words | okr_words))
    
    # Acronym boost (capped at 0.24)
    acronym_boost = min(ACRONYM_BOOST_MAX, ACRONYM_BOOST_PER_MATCH * acronym_overlap)
    
    return (EMBED_WEIGHT * embed_sim) + (LEXICAL_WEIGHT * jacc) + acronym_boost


def stage_b_enhanced_match(pr_text: str, okr_data: Dict, openai_api_key: Optional[str],
                          score_threshold: float, margin_threshold: float) -> Tuple:
    """
    Enhanced PR-to-OKR matching with acronym filtering, chunking, and hybrid scoring.
    
    Args:
        pr_text: PR text
        okr_data: Precomputed OKR data
        openai_api_key: Optional OpenAI API key
        score_threshold: Minimum score for OKR match
        margin_threshold: Minimum margin between 1st and 2nd best
    
    Returns:
        Tuple of (best_okr_idx, best_score, margin, was_filtered, tokens_used, cost)
    """
    okr_texts = okr_data["okr_texts"]
    okr_acronyms = okr_data["okr_acronyms"]
    okr_keywords = okr_data["okr_keywords"]
    okr_embeddings = okr_data["okr_embeddings"]
    
    # Extract PR features
    pr_acronyms = extract_acronyms(pr_text)
    pr_words = tokenize_words(pr_text)
    
    # Filter OKR candidates by acronym overlap
    strong_acronyms = {a for a in pr_acronyms if len(a) <= 8}
    candidate_indices = list(range(len(okr_texts)))
    was_filtered = False
    
    if strong_acronyms:
        hits = [j for j, okr_acr in enumerate(okr_acronyms) if len(okr_acr & strong_acronyms) > 0]
        if hits:
            candidate_indices = hits
            was_filtered = True
    
    tokens_used = 0
    cost = 0.0
    
    # Get similarities
    if openai_api_key and okr_embeddings is not None:
        # OpenAI embeddings
        pr_embeddings = get_pr_embeddings_with_chunking(pr_text, openai_api_key)
        
        # Track tokens and cost
        pr_text_truncated = pr_text[:30000]
        pr_tokens = estimate_tokens(pr_text_truncated)
        okr_tokens = sum(estimate_tokens(okr_texts[i]) for i in candidate_indices)
        tokens_used = pr_tokens + okr_tokens
        cost = calculate_embedding_cost(tokens_used, "text-embedding-3-large")
        
        # Compute cosine similarity against candidate OKRs
        from sklearn.metrics.pairwise import cosine_similarity
        candidate_embeddings = okr_embeddings[candidate_indices]
        sims = cosine_similarity(pr_embeddings, candidate_embeddings)
        
        # Max similarity across chunks (if multiple)
        max_sims = sims.max(axis=0) if pr_embeddings.shape[0] > 1 else sims[0]
    else:
        # TF-IDF fallback
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        candidate_texts = [okr_texts[i] for i in candidate_indices]
        vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        vectors = vectorizer.fit_transform([pr_text] + candidate_texts)
        
        pr_vector = vectors[0:1]
        okr_vectors = vectors[1:]
        sims = cosine_similarity(pr_vector, okr_vectors)[0]
        max_sims = sims
    
    # Hybrid scoring
    hybrid_scores = []
    for k, okr_idx in enumerate(candidate_indices):
        acr_overlap = len(pr_acronyms & okr_acronyms[okr_idx])
        score = hybrid_score(float(max_sims[k]), pr_words, okr_keywords[okr_idx], acr_overlap)
        hybrid_scores.append(score)
    
    hybrid_scores = np.array(hybrid_scores)
    best_k = int(np.argmax(hybrid_scores))
    best_okr_idx = candidate_indices[best_k]
    best_score = float(hybrid_scores[best_k])
    
    # Calculate margin
    sorted_scores = np.sort(hybrid_scores)[::-1]
    margin = float(sorted_scores[0] - sorted_scores[1]) if len(sorted_scores) > 1 else 1.0
    
    return (best_okr_idx, best_score, margin, was_filtered, tokens_used, cost)


def classify_fallback(pr_text: str) -> Tuple[str, float]:
    """
    Classify PR into fallback category using zero-shot model.
    
    Args:
        pr_text: PR text (will be truncated to 4000 chars)
    
    Returns:
        Tuple of (category, confidence)
    """
    classifier = get_zero_shot_classifier()
    
    if classifier is False:
        # Classifier failed to load, use default
        return ("no-classification", 1.0)
    
    try:
        result = classifier(pr_text[:4000], FALLBACK_LABELS)
        return (result["labels"][0], float(result["scores"][0]))
    except Exception as e:
        print(f"         ⚠️  Zero-shot classification error: {e}")
        return ("no-classification", 1.0)


def classify_one_pr(pr_text: str, okr_data: Dict, openai_api_key: Optional[str],
                   score_threshold: float = 0.33, margin_threshold: float = 0.03) -> Dict:
    """
    Classify a single PR: try OKR matching first, fallback if below threshold.
    
    Args:
        pr_text: PR text
        okr_data: Precomputed OKR data
        openai_api_key: Optional OpenAI API key
        score_threshold: Minimum confidence for OKR match
        margin_threshold: Minimum margin between 1st and 2nd best
    
    Returns:
        Dictionary with classification result:
        {
            "label": str (OKR text or category),
            "confidence": float,
            "classification_type": str ("okr" or "fallback"),
            "method": str,
            "okr_idx": int or None,
            "margin": float,
            "tokens": int,
            "cost": float
        }
    """
    # Handle empty text
    if not pr_text or not pr_text.strip():
        return {
            "label": "no-classification",
            "confidence": 1.0,
            "classification_type": "fallback",
            "method": "empty",
            "okr_idx": None,
            "margin": 0.0,
            "tokens": 0,
            "cost": 0.0
        }
    
    # Stage 1: Try OKR matching
    okr_idx, score, margin, filtered, tokens, cost = stage_b_enhanced_match(
        pr_text, okr_data, openai_api_key, score_threshold, margin_threshold
    )
    
    # Check thresholds
    if score >= score_threshold and margin >= margin_threshold:
        # OKR match succeeded
        method = f"stage_b_filtered={filtered}"
        if openai_api_key:
            method += "_openai"
        
        return {
            "label": okr_data["okr_texts"][okr_idx],
            "confidence": score,
            "classification_type": "okr",
            "method": method,
            "okr_idx": okr_idx,
            "margin": margin,
            "tokens": tokens,
            "cost": cost
        }
    
    # Stage 2: Fallback classification
    category, conf = classify_fallback(pr_text)
    return {
        "label": category,
        "confidence": conf,
        "classification_type": "fallback",
        "method": "zero_shot",
        "okr_idx": None,
        "margin": margin,
        "tokens": tokens,  # Include tokens from failed OKR match
        "cost": cost
    }


def save_classification_result(result: Dict, okr_data: Dict, output_file: Path):
    """
    Save classification result to CSV.
    
    Args:
        result: Classification result dictionary
        okr_data: Precomputed OKR data
        output_file: Output CSV file path
    """
    if result["classification_type"] == "okr":
        # OKR match
        matched_okr = okr_data["okrs_df"].iloc[result["okr_idx"]]
        output_data = {
            "okr_objective": [matched_okr["Objectives"]],
            "okr_child_item": [matched_okr["Child Items"]],
            "okr_text": [matched_okr["okr_text"]],
            "confidence": [result["confidence"]],
            "method": [result["method"]],
            "classification_type": ["okr"],
            "category": [""],  # Empty for OKR matches
            "margin": [result["margin"]]
        }
    else:
        # Fallback category
        output_data = {
            "okr_objective": [""],
            "okr_child_item": [""],
            "okr_text": [""],
            "confidence": [result["confidence"]],
            "method": [result["method"]],
            "classification_type": ["fallback"],
            "category": [result["label"]],  # cleanup, refactoring, etc.
            "margin": [result["margin"]]
        }
    
    pd.DataFrame(output_data).to_csv(output_file, index=False)


# ============================================================================
# LEGACY FUNCTION (Replaced by classify_one_pr)
# ============================================================================

def map_okrs_for_pr_with_classification(pr_data_folder: Path, owner: str, repo: str, pr_number: int, 
                                       username: str, okr_data: Dict, openai_api_key: Optional[str],
                                       score_threshold: float = 0.33, margin_threshold: float = 0.03) -> Dict:
    """
    Map OKRs for a specific PR using enhanced classification (with fallback).
    
    Args:
        pr_data_folder: Base PR data folder path
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        username: Username for user-specific OKR file
        okr_data: Precomputed OKR data for this user
        openai_api_key: Optional OpenAI API key for advanced matching
        score_threshold: Minimum confidence for OKR match
        margin_threshold: Minimum margin between 1st and 2nd best
    
    Returns:
        Dictionary with success status, classification type, tokens, and cost
    """
    pr_dir = pr_data_folder / owner / repo / f"pr_{pr_number}"
    okrs_file = pr_dir / f"okrs_{username}.csv"
    
    result = {
        "success": False,
        "classification_type": None,
        "category": None,
        "tokens": 0,
        "cost": 0.0
    }
    
    try:
        # Load PR text
        pr_text = load_pr_text(pr_data_folder, owner, repo, pr_number)
        if not pr_text or len(pr_text) < 10:
            print(f"         ⚠️  No meaningful PR text found")
            return result
        
        # Classify PR (OKR match or fallback category)
        classification = classify_one_pr(pr_text, okr_data, openai_api_key, 
                                        score_threshold, margin_threshold)
        
        # Save result to CSV
        save_classification_result(classification, okr_data, okrs_file)
        
        result["success"] = True
        result["classification_type"] = classification["classification_type"]
        result["category"] = classification.get("label") if classification["classification_type"] == "fallback" else None
        result["tokens"] = classification["tokens"]
        result["cost"] = classification["cost"]
        
        return result
    except Exception as e:
        print(f"         ❌ Failed to classify PR: {e}")
        import traceback
        traceback.print_exc()
        return result


def load_status(status_filepath: Path) -> Dict:
    """
    Load status from status file, or create new status if file doesn't exist.
    
    Args:
        status_filepath: Path to status file
    
    Returns:
        Status dictionary
    """
    if status_filepath.exists():
        with open(status_filepath, 'r') as f:
            return json.load(f)
    else:
        return {
            "status": "not_started",
            "current_row": 0,
            "mapped_count": 0,
            "skipped_count": 0
        }


def save_status(status_filepath: Path, status_data: Dict):
    """
    Save status to status file.
    
    Args:
        status_filepath: Path to status file
        status_data: Status dictionary
    """
    with open(status_filepath, 'w') as f:
        json.dump(status_data, f, indent=2)


def main():
    """Main execution function"""
    try:
        print("=" * 80)
        print("🗺️  PR OKR MAPPER (Enhanced with Fallback Classification)")
        print("=" * 80)
        print()
        
        # Load configuration
        print("🔄 Loading configuration...")
        all_config = load_all_config()
        
        config = all_config['config']
        settings = all_config['settings']
        users = all_config['users']
        paths = all_config['paths']
        
        task_folder = paths['task_folder']
        pr_data_folder = paths['pr_data_folder']
        search_folder = pr_data_folder / 'search'
        okr_folder = paths['okr_folder']
        
        # Get OpenAI API key from settings (optional)
        openai_api_key = settings.get('openai_api_key')
        
        # Load classification configuration
        okr_matching_config = settings.get('okr_matching', {})
        score_threshold = okr_matching_config.get('score_threshold', B_SCORE_THRESHOLD)
        margin_threshold = okr_matching_config.get('margin_threshold', B_MARGIN_THRESHOLD)
        use_fallback = okr_matching_config.get('use_zero_shot_fallback', True)
        force_recalculate = settings.get('force_recalculate_okrs', False)
        
        print(f"✅ Configuration loaded")
        print(f"   Task folder: {task_folder}")
        print(f"   PR data folder: {pr_data_folder}")
        print(f"   Search folder: {search_folder}")
        print(f"   OKR folder: {okr_folder}")
        print(f"   Users: {len(users)}")
        print(f"   OpenAI API key: {'✅ Available' if openai_api_key else '❌ Not available (using TF-IDF)'}")
        print(f"   Score threshold: {score_threshold}")
        print(f"   Margin threshold: {margin_threshold}")
        print(f"   Fallback classification: {'✅ Enabled' if use_fallback else '❌ Disabled'}")
        print(f"   Force recalculate: {'✅ Yes' if force_recalculate else '❌ No'}")
        
        # Iterate through users
        print("\n" + "=" * 80)
        print("🔄 CLASSIFYING PRs (OKR Mapping + Fallback)")
        print("=" * 80)
        
        task_types = ["authored", "reviewer"]
        total_okr_matches = 0
        total_fallback_classifications = 0
        total_skipped = 0
        total_tokens = 0
        total_cost = 0.0
        MAPPING_LIMIT_PER_USER = 10  # Classify 10 PRs per user (excluding skipped)
        
        # Track fallback category counts
        fallback_stats = {label: 0 for label in FALLBACK_LABELS}
        
        for user in users:
            username = user['userName']
            first_name = user.get('firstName', '')
            last_name = user.get('lastName', '')
            full_name = f"{first_name} {last_name}".strip()
            
            print(f"\n👤 User: {full_name} ({username})")
            print("-" * 80)
            
            # Load and precompute OKRs for this user (once!)
            okrs_df = load_okrs_for_user(username, okr_folder)
            if okrs_df is None or len(okrs_df) == 0:
                print(f"   ⚠️  No OKRs found for {username} - skipping user")
                continue
            
            print(f"   📊 Loaded {len(okrs_df)} OKRs for {username}")
            okr_data = precompute_okr_data(okrs_df, openai_api_key)
            
            # Track classified count per user
            user_classified = 0
            
            for task_type in task_types:
                if user_classified >= MAPPING_LIMIT_PER_USER:
                    print(f"\n   ✅ Reached classification limit of {MAPPING_LIMIT_PER_USER} PRs for {username} - moving to next user")
                    break
                
                task_filename = f"pr_{task_type}_{username}.json"
                task_filepath = task_folder / task_filename
                
                # Status file for OKR mapping
                okr_status_filename = f"pr_{task_type}_okr_{username}_status.json"
                okr_status_filepath = task_folder / okr_status_filename
                
                print(f"\n   📋 Task Type: {task_type}")
                
                # Check if task file exists
                if not task_filepath.exists():
                    print(f"      ⚠️  Task file not found: {task_filename}")
                    continue
                
                # Read task file
                with open(task_filepath, 'r') as f:
                    task_data = json.load(f)
                
                print(f"      ✅ Task file: {task_filename}")
                
                # Check if CSV data file exists
                start_date = task_data.get('start_date')
                end_date = task_data.get('end_date')
                csv_filename = f"pr_{task_type}_{username}_{start_date}_{end_date}.csv"
                csv_filepath = search_folder / csv_filename
                
                if not csv_filepath.exists():
                    print(f"      ❌ CSV data file NOT found: {csv_filename}")
                    continue
                
                print(f"      ✅ CSV data file exists: {csv_filename}")
                
                # Load classification status
                okr_status = load_status(okr_status_filepath)
                current_row = okr_status.get('current_row', 0)
                classified_count = okr_status.get('mapped_count', 0)  # Keeping key name for compatibility
                skipped_count = okr_status.get('skipped_count', 0)
                
                # Check if classification is complete
                if okr_status.get('status') == 'completed':
                    print(f"      ✅ Classification already completed - skipping")
                    total_okr_matches += classified_count  # Conservative estimate
                    total_skipped += skipped_count
                    continue
                
                # Read CSV file
                try:
                    df = pd.read_csv(csv_filepath)
                    total_prs = len(df)
                    print(f"      📄 Found {total_prs} PRs in CSV")
                    
                    if total_prs == 0:
                        print(f"      ℹ️  No PRs to classify")
                        okr_status['status'] = 'completed'
                        save_status(okr_status_filepath, okr_status)
                        continue
                    
                    # Check if already completed
                    if current_row >= total_prs:
                        print(f"      ✅ All PRs already processed ({current_row}/{total_prs})")
                        okr_status['status'] = 'completed'
                        save_status(okr_status_filepath, okr_status)
                        total_okr_matches += classified_count
                        total_skipped += skipped_count
                        continue
                    
                    print(f"      📍 Starting from row: {current_row}")
                    print(f"      📊 Previous: {classified_count} classified, {skipped_count} skipped")
                    
                    # Set status to in_progress
                    okr_status['status'] = 'in_progress'
                    save_status(okr_status_filepath, okr_status)
                    
                    # Process PRs starting from current_row
                    batch_classified = 0
                    batch_skipped = 0
                    batch_okr_matches = 0
                    batch_fallback = 0
                    
                    print(f"      🔄 Classifying PRs (starting from row {current_row + 1})...")
                    
                    for idx in range(current_row, total_prs):
                        # Stop if we've reached the per-user classification limit
                        if user_classified >= MAPPING_LIMIT_PER_USER:
                            print(f"      🛑 Reached classification limit of {MAPPING_LIMIT_PER_USER} PRs for this user")
                            break
                        
                        row = df.iloc[idx]
                        owner = row.get('owner')
                        repo = row.get('repo')
                        pr_number = int(row.get('pr_number'))
                        
                        # Check if PR data is downloaded
                        if not check_pr_downloaded(pr_data_folder, owner, repo, pr_number):
                            print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [NOT DOWNLOADED - SKIPPED]")
                            
                            # Update status
                            current_row = idx + 1
                            okr_status['current_row'] = current_row
                            save_status(okr_status_filepath, okr_status)
                            continue
                        
                        # Check if okrs_{username}.csv already exists (unless force_recalculate)
                        if not force_recalculate and check_okrs_exist(pr_data_folder, owner, repo, pr_number, username):
                            batch_skipped += 1
                            total_skipped += 1
                            print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [ALREADY CLASSIFIED - SKIPPED]")
                            
                            # Update status
                            current_row = idx + 1
                            okr_status['current_row'] = current_row
                            okr_status['skipped_count'] = skipped_count + batch_skipped
                            save_status(okr_status_filepath, okr_status)
                            continue
                        
                        # Classify this PR (OKR match or fallback)
                        try:
                            classification_result = map_okrs_for_pr_with_classification(
                                pr_data_folder, owner, repo, pr_number, username,
                                okr_data, openai_api_key, score_threshold, margin_threshold
                            )
                            
                            if classification_result["success"]:
                                batch_classified += 1
                                user_classified += 1
                                
                                # Track OKR vs fallback
                                if classification_result["classification_type"] == "okr":
                                    batch_okr_matches += 1
                                    total_okr_matches += 1
                                    result_label = "OKR MATCH"
                                else:
                                    batch_fallback += 1
                                    total_fallback_classifications += 1
                                    category = classification_result.get("category", "unknown")
                                    result_label = f"FALLBACK: {category}"
                                    if category in fallback_stats:
                                        fallback_stats[category] += 1
                                
                                # Track costs
                                pr_tokens = classification_result.get("tokens", 0)
                                pr_cost = classification_result.get("cost", 0.0)
                                total_tokens += pr_tokens
                                total_cost += pr_cost
                                
                                # Print classification result with cost info
                                if openai_api_key and pr_cost > 0:
                                    print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [{result_label}]")
                                    print(f"            💰 Tokens: {pr_tokens:,} | Cost: ${pr_cost:.6f} | Cumulative: ${total_cost:.6f}")
                                else:
                                    print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [{result_label}]")
                            else:
                                print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [CLASSIFICATION FAILED]")
                            
                            # Update status after each PR
                            current_row = idx + 1
                            okr_status['current_row'] = current_row
                            okr_status['mapped_count'] = classified_count + batch_classified
                            okr_status['skipped_count'] = skipped_count + batch_skipped
                            save_status(okr_status_filepath, okr_status)
                        
                        except Exception as e:
                            print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [ERROR: {str(e)}]")
                            
                            # Update current_row even on error
                            current_row = idx + 1
                            okr_status['current_row'] = current_row
                            save_status(okr_status_filepath, okr_status)
                    
                    print(f"      📊 Batch Summary: {batch_classified} classified ({batch_okr_matches} OKR, {batch_fallback} fallback), {batch_skipped} skipped")
                    print(f"      📍 Progress: {current_row}/{total_prs} PRs processed")
                    
                    # Check if all PRs are processed
                    if current_row >= total_prs:
                        okr_status['status'] = 'completed'
                        okr_status['current_row'] = total_prs
                        save_status(okr_status_filepath, okr_status)
                        print(f"      ✅ All PRs processed! Updated status to: completed")
                    else:
                        print(f"      ⏸️  Stopped. Run again to continue from row {current_row + 1}")
                
                except Exception as e:
                    print(f"      ❌ Error processing CSV: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Print per-user summary
            if user_classified > 0:
                print(f"\n   📊 Summary for {username}: {user_classified} PRs classified")
        
        print("\n" + "=" * 80)
        print("✅ PR CLASSIFICATION COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Overall Summary:")
        print(f"   ✅ OKR matches: {total_okr_matches}")
        print(f"   🔄 Fallback classifications: {total_fallback_classifications}")
        print(f"   ⏭️  Skipped: {total_skipped}")
        print(f"   📝 Total classified: {total_okr_matches + total_fallback_classifications}")
        
        if total_fallback_classifications > 0:
            print(f"\n📊 Fallback Category Breakdown:")
            for category, count in sorted(fallback_stats.items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    print(f"   {category}: {count}")
        
        if openai_api_key and total_cost > 0:
            print(f"\n💰 OpenAI API Usage:")
            print(f"   Total tokens: {total_tokens:,}")
            print(f"   Total cost: ${total_cost:.6f}")
            total_classified = total_okr_matches + total_fallback_classifications
            if total_classified > 0:
                print(f"   Average cost per PR: ${total_cost/total_classified:.6f}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        import sys
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
