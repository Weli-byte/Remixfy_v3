"""
Flow Cluster – Automatic flow-type discovery from an artist's corpus.

Uses sklearn KMeans to cluster corpus lines into 4 flow types based on
extracted features (word count, word length, punctuation, syllable estimate).

Pure Python + sklearn.  No external API calls.  Results are cached
in-memory per artist for the lifetime of the process.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Flow type labels ─────────────────────────────────────────────────────

_N_CLUSTERS = 4

_FLOW_LABELS: Dict[str, str] = {
    "FLOW_A": "kisa satir flow (short conversational lines)",
    "FLOW_B": "soru flow (question-driven lines)",
    "FLOW_C": "agresif flow (aggressive, punctuated lines)",
    "FLOW_D": "uzun satir flow (long narrative lines)",
}

# ── Turkish vowels for syllable estimation ───────────────────────────────

_TR_VOWELS = set("aeıioöuüAEIİOÖUÜ")


# ── Feature extraction ──────────────────────────────────────────────────

def extract_flow_features(line: str) -> Dict[str, float]:
    """
    Extract flow features from a single corpus line.

    Returns
    -------
    dict with keys:
        word_count        – int, number of words
        avg_word_length   – float, average characters per word
        punctuation_count – int, total punctuation marks
        question_mark     – int (0 or 1), ends with '?'
        exclamation_mark  – int (0 or 1), ends with '!'
        syllable_estimate – int, estimated syllable count (Turkish vowel based)
    """
    stripped = line.strip()
    if not stripped:
        return {
            "word_count": 0,
            "avg_word_length": 0.0,
            "punctuation_count": 0,
            "question_mark": 0,
            "exclamation_mark": 0,
            "syllable_estimate": 0,
        }

    words = stripped.split()
    word_count = len(words)

    # Average word length (letters only)
    clean_words = [re.sub(r"[^\w]", "", w) for w in words]
    clean_words = [w for w in clean_words if w]
    avg_word_length = (
        round(sum(len(w) for w in clean_words) / len(clean_words), 2)
        if clean_words else 0.0
    )

    # Punctuation count
    punctuation_count = sum(1 for ch in stripped if ch in ".,;:!?\"'()-–…")

    # Terminal punctuation
    question_mark = 1 if stripped.endswith("?") else 0
    exclamation_mark = 1 if stripped.endswith("!") else 0

    # Syllable estimate (Turkish: count vowels)
    syllable_estimate = sum(1 for ch in stripped if ch in _TR_VOWELS)

    return {
        "word_count": word_count,
        "avg_word_length": avg_word_length,
        "punctuation_count": punctuation_count,
        "question_mark": question_mark,
        "exclamation_mark": exclamation_mark,
        "syllable_estimate": syllable_estimate,
    }


# ── Clustering ───────────────────────────────────────────────────────────

def cluster_flow_patterns(
    lines: List[str],
    n_clusters: int = _N_CLUSTERS,
) -> Dict[str, Any]:
    """
    Cluster corpus lines into distinct flow patterns using KMeans.

    Parameters
    ----------
    lines      : list[str] – corpus lines (non-empty)
    n_clusters : int       – number of flow types (default 4)

    Returns
    -------
    dict with keys:
        labels       – list[int], cluster label for each line (0..n-1)
        centroids    – np.ndarray, shape (n_clusters, n_features)
        flow_map     – dict mapping cluster_id → flow type name
        cluster_sizes – dict mapping flow_type → line count
        feature_names – list[str], names of the features used
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    # Extract features for every line
    feature_names = ["word_count", "punctuation_count", "syllable_estimate"]
    raw_features: List[List[float]] = []
    all_features: List[Dict[str, float]] = []

    for line in lines:
        feats = extract_flow_features(line)
        all_features.append(feats)
        raw_features.append([feats[f] for f in feature_names])

    X = np.array(raw_features, dtype=np.float64)

    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # KMeans
    kmeans = KMeans(
        n_clusters=min(n_clusters, len(lines)),
        n_init=10,
        random_state=42,
    )
    labels = kmeans.fit_predict(X_scaled)

    # Inverse-transform centroids for interpretability
    centroids_original = scaler.inverse_transform(kmeans.cluster_centers_)

    # ── Assign flow type names based on centroid characteristics ──────
    flow_map = _assign_flow_types(centroids_original, feature_names, all_features, labels)

    # Count lines per cluster
    cluster_sizes: Dict[str, int] = {}
    label_counts = Counter(labels)
    for cid, flow_name in flow_map.items():
        cluster_sizes[flow_name] = label_counts.get(cid, 0)

    logger.info(
        "Flow clustering done: %d lines → %d clusters. Sizes: %s",
        len(lines), min(n_clusters, len(lines)), cluster_sizes,
    )

    return {
        "labels": labels.tolist(),
        "centroids": centroids_original,
        "flow_map": flow_map,
        "cluster_sizes": cluster_sizes,
        "feature_names": feature_names,
    }


def _assign_flow_types(
    centroids: np.ndarray,
    feature_names: List[str],
    all_features: List[Dict[str, float]],
    labels: np.ndarray,
) -> Dict[int, str]:
    """
    Assign human-readable flow type names to cluster IDs based on
    centroid characteristics.

    Strategy:
    - Lowest avg word_count           → FLOW_A (short)
    - Highest question_mark ratio     → FLOW_B (question)
    - Highest punctuation_count       → FLOW_C (aggressive)
    - Highest word_count              → FLOW_D (long)
    """
    n = centroids.shape[0]
    used: set = set()
    flow_map: Dict[int, str] = {}

    # Get feature indices
    wc_idx = feature_names.index("word_count")
    punct_idx = feature_names.index("punctuation_count")

    # Calculate question ratio per cluster
    question_ratios: Dict[int, float] = {}
    for cid in range(n):
        mask = labels == cid
        cluster_feats = [all_features[i] for i, m in enumerate(mask) if m]
        if cluster_feats:
            q_count = sum(1 for f in cluster_feats if f["question_mark"] == 1)
            question_ratios[cid] = q_count / len(cluster_feats)
        else:
            question_ratios[cid] = 0.0

    # 1. FLOW_B: highest question ratio (if meaningful, > 5%)
    best_q = max(range(n), key=lambda c: question_ratios[c])
    if question_ratios[best_q] > 0.05:
        flow_map[best_q] = "FLOW_B"
        used.add(best_q)

    # 2. FLOW_A: lowest word_count centroid
    remaining = [c for c in range(n) if c not in used]
    if remaining:
        shortest = min(remaining, key=lambda c: centroids[c][wc_idx])
        flow_map[shortest] = "FLOW_A"
        used.add(shortest)

    # 3. FLOW_C: highest punctuation centroid
    remaining = [c for c in range(n) if c not in used]
    if remaining:
        most_punct = max(remaining, key=lambda c: centroids[c][punct_idx])
        flow_map[most_punct] = "FLOW_C"
        used.add(most_punct)

    # 4. FLOW_D: remaining (longest word_count by default)
    remaining = [c for c in range(n) if c not in used]
    for cid in remaining:
        flow_map[cid] = "FLOW_D"

    return flow_map


# ── Artist flow profile ─────────────────────────────────────────────────

# Per-artist cache: artist_name (lowered) → profile dict
_profile_cache: Dict[str, Dict[str, Any]] = {}


def build_flow_profile(artist_name: str) -> Dict[str, Any]:
    """
    Build a flow profile for an artist by clustering their corpus.

    Results are cached in-memory.

    Returns
    -------
    dict with keys:
        dominant_flow    – str, most common flow type
        secondary_flow   – str, second most common flow type
        flow_distribution – dict, flow_type → ratio (0.0-1.0)
        short_line_ratio – float, ratio of lines with ≤5 words
        cluster_sizes    – dict, flow_type → line count
        total_lines      – int
    """
    key = artist_name.strip().lower()

    # Cache hit
    if key in _profile_cache:
        logger.debug("Flow profile cache hit for '%s'.", artist_name)
        return _profile_cache[key]

    # Load corpus
    from app.flow_analyzer import get_corpus_for_artist

    raw_corpus = get_corpus_for_artist(artist_name)
    lines = [l.strip() for l in raw_corpus if l.strip()]

    if len(lines) < _N_CLUSTERS:
        logger.warning(
            "Too few lines (%d) for '%s' – returning empty flow profile.",
            len(lines), artist_name,
        )
        empty: Dict[str, Any] = {
            "dominant_flow": "FLOW_A",
            "secondary_flow": "FLOW_D",
            "flow_distribution": {},
            "short_line_ratio": 0.0,
            "cluster_sizes": {},
            "total_lines": len(lines),
        }
        _profile_cache[key] = empty
        return empty

    # Cluster
    result = cluster_flow_patterns(lines)

    cluster_sizes = result["cluster_sizes"]
    total = len(lines)

    # Sort flow types by count (descending)
    sorted_flows = sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True)

    dominant_flow = sorted_flows[0][0] if sorted_flows else "FLOW_A"
    secondary_flow = sorted_flows[1][0] if len(sorted_flows) > 1 else dominant_flow

    # Flow distribution (ratios)
    flow_distribution = {
        flow: round(count / total, 3) for flow, count in sorted_flows
    }

    # Short line ratio (≤5 words)
    short_count = sum(1 for l in lines if len(l.split()) <= 5)
    short_line_ratio = round(short_count / total, 3)

    profile: Dict[str, Any] = {
        "dominant_flow": dominant_flow,
        "secondary_flow": secondary_flow,
        "flow_distribution": flow_distribution,
        "short_line_ratio": short_line_ratio,
        "cluster_sizes": cluster_sizes,
        "total_lines": total,
    }

    logger.info(
        "Flow profile for '%s': dominant=%s (%.0f%%), secondary=%s (%.0f%%), "
        "short_ratio=%.0f%%",
        artist_name,
        dominant_flow,
        flow_distribution.get(dominant_flow, 0) * 100,
        secondary_flow,
        flow_distribution.get(secondary_flow, 0) * 100,
        short_line_ratio * 100,
    )

    _profile_cache[key] = profile
    return profile


# ── Cache management ─────────────────────────────────────────────────────

def clear_cache() -> None:
    """Drop all cached flow profiles."""
    _profile_cache.clear()
    logger.info("Flow cluster cache cleared.")
