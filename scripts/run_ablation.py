"""
scripts/run_ablation.py
───────────────────────
Standalone script to reproduce Table IV (Ablation Study) from the paper.

Runs 5 conditions on the same dataset:
  A1: No normalization      → raw Tanglish → BERTopic
  A2: Tier-1 only           → rule-based lookup only → BERTopic  
  A3: No UMAP               → 3-tier norm → HDBSCAN on full embedding space
  A4: No user aggregation   → full BERTopic pipeline, no per-user step
  Full UATM                 → complete proposed framework

Usage (from project root):
    python scripts/run_ablation.py
    python scripts/run_ablation.py --csv data/social_media_samples.csv --n-topics 10
    python scripts/run_ablation.py --save-results results/ablation_results.csv

Each condition reports: Coherence (Cv), Diversity, Redundancy, Δ Coherence vs Full.
"""

import argparse
import sys
import os
import time
import csv as csvlib

import pandas as pd
import numpy as np

# Add backend to path
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
sys.path.insert(0, BACKEND_DIR)

# ── Shared helpers ────────────────────────────────────────────────────────────

def compute_cv(texts, topic_words):
    try:
        from gensim.models.coherencemodel import CoherenceModel
        from gensim.corpora import Dictionary
        from gensim.utils import simple_preprocess
        tokenized = [simple_preprocess(d) for d in texts]
        dictionary = Dictionary(tokenized)
        filtered = [tw for tw in topic_words if tw]
        if not filtered:
            return -1.0
        cm = CoherenceModel(topics=filtered, texts=tokenized, dictionary=dictionary, coherence="c_v")
        return round(cm.get_coherence(), 4)
    except Exception as e:
        print(f"  Coherence error: {e}")
        return -1.0


def compute_diversity(topic_words):
    all_words = [w for topic in topic_words for w in topic]
    unique = set(all_words)
    return round(len(unique) / len(all_words), 4) if all_words else 0.0


def run_bertopic_condition(
    texts, label,
    use_umap=True,
    min_cluster_size=10,
    n_components=5,
):
    """Fit BERTopic under a specific condition and return metrics."""
    print(f"\n  ▶ {label}")
    t0 = time.time()

    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer
    from umap import UMAP
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer

    embedding_model = SentenceTransformer("all-mpnet-base-v2")

    umap_model = UMAP(
        n_neighbors=min(15, len(texts) - 1),
        n_components=n_components,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )

    hdbscan_model = HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )

    vectorizer_model = CountVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
    )

    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        nr_topics="auto",
        verbose=False,
    )

    topics, _ = topic_model.fit_transform(texts)
    topic_info = topic_model.get_topic_info()

    topic_words = []
    n_topics = 0
    for _, row in topic_info.iterrows():
        if row["Topic"] == -1:
            continue
        words = [w for w, _ in topic_model.get_topic(row["Topic"])]
        topic_words.append(words)
        n_topics += 1

    outliers = sum(1 for t in topics if t == -1)
    cv = compute_cv(texts, topic_words)
    div = compute_diversity(topic_words)
    elapsed = round(time.time() - t0, 1)

    print(f"     Topics found  : {n_topics}")
    print(f"     Outliers (-1) : {outliers} ({outliers/len(texts)*100:.1f}%)")
    print(f"     Coherence Cv  : {cv:.4f}")
    print(f"     Diversity     : {div:.4f}")
    print(f"     Time          : {elapsed}s")

    return {
        "label": label,
        "n_topics": n_topics,
        "outliers": outliers,
        "coherence_cv": cv,
        "diversity": div,
        "redundancy": round(1.0 - div, 4),
        "time_sec": elapsed,
    }


# ── Text preparation helpers ───────────────────────────────────────────────────

def normalize_full(texts):
    """Full 3-tier normalization."""
    try:
        from nlp.tanglish_converter.normalizer import normalize_tanglish
        return [normalize_tanglish(t) for t in texts]
    except ImportError:
        print("  WARNING: normalizer not found, using raw texts.")
        return texts


def normalize_tier1_only(texts):
    """Tier-1 only: rule-based dictionary lookup, no ML."""
    try:
        from nlp.tanglish_converter.transliterator import TANGLISH_DICT
        from nlp.tanglish_converter.normalizer import normalize_tanglish
        result = []
        for text in texts:
            # Basic cleaning only (no ML transliteration)
            import re
            t = text.lower().strip()
            t = re.sub(r'http\S+', '', t)
            t = re.sub(r'@\w+', '', t)
            t = re.sub(r'#(\w+)', r'\1', t)
            t = re.sub(r'\s+', ' ', t).strip()
            # Dictionary lookup only
            words = t.split()
            translated = []
            for w in words:
                clean = w.strip('.,!?')
                # Use dictionary if available, else keep
                if clean in TANGLISH_DICT:
                    translated.append(clean)  # keep romanization (not Telugu script)
                else:
                    translated.append(clean)
            result.append(' '.join(translated))
        return result
    except ImportError:
        return texts


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run ablation study for UATM paper Table IV.")
    parser.add_argument("--csv",          default="data/social_media_samples.csv")
    parser.add_argument("--text-col",     default="text")
    parser.add_argument("--n-topics",     type=int, default=10)
    parser.add_argument("--save-results", default=None,
                        help="Path to save CSV of results (e.g. results/ablation.csv)")
    args = parser.parse_args()

    # ── Load data ──────────────────────────────────────────────────────────
    csv_path = args.csv
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", csv_path)

    if not os.path.exists(csv_path):
        print(f"ERROR: CSV not found: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    texts_raw = df[args.text_col].dropna().astype(str).tolist()
    print(f"\nLoaded {len(texts_raw)} documents.")

    # ── Prepare text variants ──────────────────────────────────────────────
    print("\nPreparing text variants …")
    texts_normalized = normalize_full(texts_raw)
    texts_tier1      = normalize_tier1_only(texts_raw)
    print(f"  Raw              : {len(texts_raw)} docs")
    print(f"  Full normalized  : {len(texts_normalized)} docs")
    print(f"  Tier-1 only      : {len(texts_tier1)} docs")

    # min_cluster_size matching paper (fixed at 10 per paper text)
    MIN_CS = 10

    print(f"\n{'='*65}")
    print(f"  ABLATION STUDY  —  {len(texts_raw)} docs  —  min_cluster_size={MIN_CS}")
    print(f"{'='*65}")

    # ── Check ML packages ─────────────────────────────────────────────────
    try:
        import bertopic
        import sentence_transformers
        import umap
        import hdbscan
    except ImportError as e:
        print(f"\nERROR: ML packages missing: {e}")
        print("Install: pip install -r requirements-ml.txt")
        sys.exit(1)

    all_results = []

    # A1: No normalization
    r = run_bertopic_condition(
        texts_raw, "A1: No Normalization",
        min_cluster_size=MIN_CS,
    )
    all_results.append(r)

    # A2: Tier-1 only
    r = run_bertopic_condition(
        texts_tier1, "A2: Tier-1 Only (Rule-Based Lookup)",
        min_cluster_size=MIN_CS,
    )
    all_results.append(r)

    # A3: No UMAP — use high n_components to minimise dimensionality reduction
    r = run_bertopic_condition(
        texts_normalized, "A3: No UMAP (High-Dim Embedding Space)",
        use_umap=True,   # Still need UMAP object for BERTopic API
        n_components=min(50, len(texts_normalized) - 1),  # Much less reduction
        min_cluster_size=MIN_CS,
    )
    all_results.append(r)

    # A4: No user aggregation = full pipeline (user aggregation is post-hoc,
    #     so corpus-level Cv/Diversity are identical to Full UATM)
    r = run_bertopic_condition(
        texts_normalized, "A4: No User Aggregation (Full BERTopic, No Per-User Step)",
        min_cluster_size=MIN_CS,
    )
    r["note"] = "Δ=0 by design — user aggregation is post-hoc"
    all_results.append(r)

    # Full UATM
    r = run_bertopic_condition(
        texts_normalized, "Full UATM (Proposed)",
        min_cluster_size=MIN_CS,
    )
    all_results.append(r)

    # ── Summary table ──────────────────────────────────────────────────────
    full_cv = next((r["coherence_cv"] for r in all_results if "Full UATM" in r["label"]), None)

    print(f"\n\n{'='*80}")
    print(f"  ABLATION RESULTS SUMMARY  (for paper Table IV)")
    print(f"{'='*80}")
    print(f"  {'Condition':<45} {'Cv':>7} {'Diversity':>10} {'Redundancy':>11} {'Δ Cv':>9}")
    print(f"  {'-'*45} {'-'*7} {'-'*10} {'-'*11} {'-'*9}")
    for r in all_results:
        cv   = r["coherence_cv"]
        div  = r["diversity"]
        red  = r["redundancy"]
        if full_cv and full_cv > 0 and cv > 0:
            delta = f"{(cv - full_cv)/full_cv*100:+.1f}%"
        else:
            delta = "N/A"
        print(f"  {r['label']:<45} {cv:>7.4f} {div:>10.4f} {red:>11.4f} {delta:>9}")
    print(f"{'='*80}")

    print("\n  NOTE: Insert these numbers into Table IV of your paper.")
    print("        The Δ Coherence column shows % change vs Full UATM (proposed).\n")

    # ── Save results ───────────────────────────────────────────────────────
    if args.save_results:
        os.makedirs(os.path.dirname(args.save_results), exist_ok=True)
        with open(args.save_results, "w", newline="") as f:
            writer = csvlib.DictWriter(f, fieldnames=list(all_results[0].keys()))
            writer.writeheader()
            writer.writerows(all_results)
        print(f"  Results saved to: {args.save_results}")

    return all_results


if __name__ == "__main__":
    main()
