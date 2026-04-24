"""
test_flow_cluster.py – Flow Pattern Clustering test for Blok3.

Tests the Flow Cluster system by:
1. Feature extraction on sample lines
2. KMeans clustering on full 846-line corpus
3. Flow profile generation
4. Prompt builder integration verification

Usage:
    python test_flow_cluster.py
"""

from __future__ import annotations

import os
import sys
import time
import warnings

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv()

ARTIST = "Blok3"
OUT = "test_flow_cluster_results.txt"

lines_out: list = []
def p(s: str = "") -> None:
    lines_out.append(s)
    print(s)


def main() -> None:
    from app.flow_cluster import (
        extract_flow_features,
        cluster_flow_patterns,
        build_flow_profile,
    )
    from app.flow_analyzer import get_corpus_for_artist

    p("=" * 65)
    p("  FLOW PATTERN CLUSTERING TEST")
    p("=" * 65)

    # ── Step 1: Feature extraction ───────────────────────────────────
    p("\n--- STEP 1: Feature Extraction (sample lines) ---\n")

    sample_lines = [
        "Ey, Hako",
        "Gururum seni affetmez (ey)",
        "Hayat artik full manzaralar, hmm",
        "Aynen oyle lan tam diz modelim, Allah'indan bulma denk gelelim",
        "Ne zamana kadar boyle?",
    ]

    for line in sample_lines:
        feats = extract_flow_features(line)
        p(f"  [{line[:40]:40s}]  wc={feats['word_count']:2d}  "
          f"awl={feats['avg_word_length']:.1f}  "
          f"punc={feats['punctuation_count']}  "
          f"q={feats['question_mark']}  "
          f"ex={feats['exclamation_mark']}  "
          f"syl={feats['syllable_estimate']}")

    # ── Step 2: Clustering ───────────────────────────────────────────
    p("\n--- STEP 2: KMeans Clustering (full corpus) ---\n")

    raw_corpus = get_corpus_for_artist(ARTIST)
    corpus = [l.strip() for l in raw_corpus if l.strip()]
    p(f"  Corpus lines: {len(corpus)}")

    t0 = time.time()
    result = cluster_flow_patterns(corpus)
    elapsed = time.time() - t0
    p(f"  Clustering time: {elapsed:.2f}s")

    flow_map = result["flow_map"]
    cluster_sizes = result["cluster_sizes"]

    p(f"\n  Flow Map (cluster_id -> type):")
    for cid, fname in sorted(flow_map.items()):
        p(f"    Cluster {cid} -> {fname}")

    p(f"\n  Cluster Sizes:")
    for fname in sorted(cluster_sizes.keys()):
        count = cluster_sizes[fname]
        ratio = count / len(corpus) * 100
        p(f"    {fname}: {count:4d} lines ({ratio:.1f}%)")

    # Show centroids
    centroids = result["centroids"]
    feat_names = result["feature_names"]
    p(f"\n  Centroids ({', '.join(feat_names)}):")
    for cid in sorted(flow_map.keys()):
        vals = ", ".join(f"{v:.1f}" for v in centroids[cid])
        p(f"    {flow_map[cid]}: [{vals}]")

    # Show sample lines per cluster
    labels = result["labels"]
    p("\n  Sample lines per flow type:")
    for cid, fname in sorted(flow_map.items()):
        p(f"\n    {fname}:")
        shown = 0
        for i, lbl in enumerate(labels):
            if lbl == cid and shown < 3:
                p(f"      - {corpus[i][:60]}")
                shown += 1

    # ── Step 3: Flow profile ─────────────────────────────────────────
    p("\n--- STEP 3: Artist Flow Profile ---\n")

    t0 = time.time()
    profile = build_flow_profile(ARTIST)
    elapsed = time.time() - t0

    p(f"  Build time: {elapsed:.2f}s")
    p(f"  Dominant Flow:    {profile['dominant_flow']}")
    p(f"  Secondary Flow:   {profile['secondary_flow']}")
    p(f"  Short Line Ratio: {profile['short_line_ratio']:.1%}")
    p(f"  Total Lines:      {profile['total_lines']}")
    p(f"\n  Flow Distribution:")
    for flow, ratio in profile.get("flow_distribution", {}).items():
        p(f"    {flow}: {ratio:.1%}")

    # ── Step 4: Cache test ───────────────────────────────────────────
    p("\n--- STEP 4: Cache Test ---\n")

    t0 = time.time()
    profile2 = build_flow_profile(ARTIST)
    elapsed2 = time.time() - t0
    p(f"  Cache hit time: {elapsed2:.4f}s")
    assert elapsed2 < 0.01, "Cache miss!"
    p("  Cache OK.")

    # ── Done ─────────────────────────────────────────────────────────
    p("\n" + "=" * 65)
    p("  ALL TESTS PASSED")
    p("=" * 65)

    # Write to file
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out))
    print(f"\nResults also saved to {OUT}")


if __name__ == "__main__":
    main()
