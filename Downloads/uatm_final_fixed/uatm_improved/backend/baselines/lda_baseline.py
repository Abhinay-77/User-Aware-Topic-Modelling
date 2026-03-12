"""
backend/baselines/lda_baseline.py
──────────────────────────────────
LDA baseline for paper Table III comparison.

Runs LDA on the same preprocessed corpus that BERTopic uses,
then computes the same Gensim Cv coherence and diversity metrics
so the numbers are directly comparable.

Usage:
    # From uatm_improved/backend/
    python -m baselines.lda_baseline

    # Or with a custom CSV:
    python -m baselines.lda_baseline --csv ../data/social_media_samples.csv \
                                     --text-col text \
                                     --n-topics 10
"""

import argparse
import sys
import os
import math
import time
from typing import List, Dict, Tuple, Any

import numpy as np
import pandas as pd

try:
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import CountVectorizer as SKCountVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("ERROR: scikit-learn not installed. Run: pip install scikit-learn")
    sys.exit(1)

try:
    from gensim.models.coherencemodel import CoherenceModel
    from gensim.corpora import Dictionary
    from gensim.utils import simple_preprocess
    GENSIM_AVAILABLE = True
except ImportError:
    GENSIM_AVAILABLE = False
    print("WARNING: gensim not installed. Coherence will not be computed.")
    print("         Run: pip install gensim")


# ── Diversity metric (identical to BERTopicService._topic_diversity) ──────────

def topic_diversity(topic_words: List[List[str]]) -> float:
    """Proportion of unique keywords across all topics."""
    all_words = [w for topic in topic_words for w in topic]
    unique_words = set(all_words)
    if not all_words:
        return 0.0
    return round(len(unique_words) / len(all_words), 4)


# ── Coherence metric (identical to BERTopicService._compute_coherence) ────────

def compute_coherence_cv(
    texts: List[str],
    topic_words: List[List[str]],
) -> float:
    """Gensim Cv coherence — identical metric used for BERTopic comparison."""
    if not GENSIM_AVAILABLE:
        return -1.0
    try:
        tokenized = [simple_preprocess(d) for d in texts]
        dictionary = Dictionary(tokenized)
        # Filter empty topic word lists
        filtered = [tw for tw in topic_words if tw]
        if not filtered:
            return -1.0
        cm = CoherenceModel(
            topics=filtered,
            texts=tokenized,
            dictionary=dictionary,
            coherence="c_v",
        )
        return round(cm.get_coherence(), 4)
    except Exception as e:
        print(f"Coherence error: {e}")
        return -1.0


# ── LDA Runner ────────────────────────────────────────────────────────────────

class LDABaseline:
    def __init__(
        self,
        n_topics: int = 10,
        n_iterations: int = 1000,
        random_state: int = 42,
        top_n_words: int = 10,
    ):
        self.n_topics = n_topics
        self.n_iterations = n_iterations
        self.random_state = random_state
        self.top_n_words = top_n_words
        self.model = None
        self.vectorizer = None

    def run(self, texts: List[str]) -> Dict[str, Any]:
        """
        Fit LDA on texts, compute coherence and diversity.

        Returns dict matching BERTopicService.run_topic_modeling() output
        structure so results can be directly compared.
        """
        print(f"\n{'='*60}")
        print(f"  LDA BASELINE")
        print(f"  Documents : {len(texts)}")
        print(f"  Topics    : {self.n_topics}")
        print(f"  Iterations: {self.n_iterations}")
        print(f"{'='*60}\n")

        # ── Vectorise ──────────────────────────────────────────────────────
        print("Step 1/4  Building document-term matrix …")
        self.vectorizer = SKCountVectorizer(
            stop_words="english",
            ngram_range=(1, 1),   # LDA works best with unigrams
            min_df=2,
            max_df=0.95,
            max_features=5000,
        )
        dtm = self.vectorizer.fit_transform(texts)
        vocab = self.vectorizer.get_feature_names_out()
        print(f"          Vocabulary size: {len(vocab)}")
        print(f"          DTM shape: {dtm.shape}")

        # ── Fit LDA ───────────────────────────────────────────────────────
        print("Step 2/4  Fitting LDA …")
        t0 = time.time()
        self.model = LatentDirichletAllocation(
            n_components=self.n_topics,
            max_iter=self.n_iterations,
            learning_method="online",    # online VB — faster for larger corpora
            learning_offset=50.0,
            random_state=self.random_state,
            n_jobs=-1,
            verbose=0,
        )
        self.model.fit(dtm)
        elapsed = time.time() - t0
        print(f"          Done in {elapsed:.1f}s  "
              f"(perplexity={self.model.perplexity(dtm):.1f})")

        # ── Extract topic words ────────────────────────────────────────────
        print("Step 3/4  Extracting topic keywords …")
        topic_words = []
        topics_list = []
        for idx, component in enumerate(self.model.components_):
            top_indices = component.argsort()[-self.top_n_words:][::-1]
            words = [vocab[i] for i in top_indices]
            topic_words.append(words)

            # Estimate document count per topic
            doc_topic = self.model.transform(dtm)
            dominant_topic = doc_topic.argmax(axis=1)
            count = int((dominant_topic == idx).sum())

            topics_list.append({
                "topic_id": idx,
                "name": f"Topic {idx}: {words[0]}",
                "keywords": words,
                "count": count,
            })
            print(f"  Topic {idx:2d} ({count:4d} docs): {', '.join(words[:6])}")

        # ── Metrics ───────────────────────────────────────────────────────
        print("Step 4/4  Computing coherence (Cv) and diversity …")
        cv_score = compute_coherence_cv(texts, topic_words)
        div_score = topic_diversity(topic_words)
        redundancy = round(1.0 - div_score, 4)

        print(f"\n{'='*60}")
        print(f"  RESULTS")
        print(f"  Coherence (Cv) : {cv_score:.4f}")
        print(f"  Diversity      : {div_score:.4f}")
        print(f"  Redundancy     : {redundancy:.4f}")
        print(f"{'='*60}\n")

        return {
            "model": "LDA",
            "n_topics": self.n_topics,
            "n_documents": len(texts),
            "topics": topics_list,
            "topic_words": topic_words,
            "coherence_cv": cv_score,
            "diversity": div_score,
            "redundancy": redundancy,
            "perplexity": round(self.model.perplexity(dtm), 2),
        }


# ── Ablation runner ───────────────────────────────────────────────────────────

class AblationRunner:
    """
    Runs the 4 ablation conditions from Table IV of the paper.
    Requires ML packages (bertopic, sentence-transformers, umap-learn, hdbscan).
    """

    def __init__(self, n_topics: int = 10, top_n_words: int = 10):
        self.n_topics = n_topics
        self.top_n_words = top_n_words

    def _run_bertopic(
        self,
        texts: List[str],
        label: str,
        use_umap: bool = True,
        min_cluster_size: int = 10,
    ) -> Dict[str, Any]:
        """Run one BERTopic condition and return metrics."""
        try:
            from bertopic import BERTopic
            from sentence_transformers import SentenceTransformer
            from umap import UMAP
            from hdbscan import HDBSCAN
            from sklearn.feature_extraction.text import CountVectorizer
        except ImportError as e:
            print(f"  ML packages not available: {e}")
            return {"label": label, "coherence_cv": -1.0, "diversity": -1.0}

        print(f"\n── {label} ──")
        embedding_model = SentenceTransformer("all-mpnet-base-v2")

        if use_umap:
            umap_model = UMAP(
                n_neighbors=min(15, len(texts) - 1),
                n_components=5,
                min_dist=0.0,
                metric="cosine",
                random_state=42,
            )
        else:
            # A3: No UMAP — cluster in full embedding space
            # BERTopic with UMAP set to identity-like (high n_components)
            umap_model = UMAP(
                n_neighbors=min(15, len(texts) - 1),
                n_components=min(50, len(texts) - 1),  # much higher = less reduction
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
        topics_list = []
        for _, row in topic_info.iterrows():
            if row["Topic"] == -1:
                continue
            words = [w for w, _ in topic_model.get_topic(row["Topic"])]
            topic_words.append(words)
            topics_list.append({
                "topic_id": int(row["Topic"]),
                "name": f"Topic {int(row['Topic'])}: {words[0] if words else ''}",
                "keywords": words,
                "count": int(row["Count"]),
            })

        outlier_count = sum(1 for t in topics if t == -1)
        cv = compute_coherence_cv(texts, topic_words)
        div = topic_diversity(topic_words)

        print(f"   Topics found  : {len(topics_list)}")
        print(f"   Outliers      : {outlier_count}")
        print(f"   Coherence (Cv): {cv}")
        print(f"   Diversity     : {div}")

        return {
            "label": label,
            "n_topics_found": len(topics_list),
            "outlier_count": outlier_count,
            "coherence_cv": cv,
            "diversity": div,
            "redundancy": round(1 - div, 4) if div >= 0 else -1,
            "topics": topics_list,
        }

    def run(
        self,
        raw_texts: List[str],
        normalized_texts: List[str],
        tier1_texts: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Run all 4 ablation conditions.

        Args:
            raw_texts:        Original Tanglish text (no preprocessing)
            normalized_texts: Full 3-tier normalised text (used by full model)
            tier1_texts:      Only rule-based Tier 1 normalisation applied
        """
        results = []
        min_cs = max(3, len(normalized_texts) // 25)

        # A1: No normalization
        r = self._run_bertopic(raw_texts, "A1: No Normalization", min_cluster_size=min_cs)
        results.append(r)

        # A2: Tier-1 only
        r = self._run_bertopic(tier1_texts, "A2: Tier-1 Only (Rule-Based)", min_cluster_size=min_cs)
        results.append(r)

        # A3: No UMAP
        r = self._run_bertopic(normalized_texts, "A3: No UMAP (High-Dim Clustering)", use_umap=False, min_cluster_size=min_cs)
        results.append(r)

        # A4: No user aggregation (full pipeline, no user-level step)
        #     This is identical to full BERTopic on normalized text;
        #     user aggregation is post-hoc so it doesn't affect corpus metrics.
        r = self._run_bertopic(normalized_texts, "A4: No User Aggregation (Full Corpus BERTopic)", min_cluster_size=min_cs)
        results.append(r)

        return results


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run LDA baseline and ablation study for UATM paper."
    )
    parser.add_argument("--csv",       default="../data/social_media_samples.csv")
    parser.add_argument("--text-col",  default="text")
    parser.add_argument("--n-topics",  type=int, default=10)
    parser.add_argument("--lda-iter",  type=int, default=1000)
    parser.add_argument("--ablation",  action="store_true",
                        help="Also run ablation conditions (requires ML packages)")
    args = parser.parse_args()

    # Load data
    csv_path = os.path.join(os.path.dirname(__file__), args.csv)
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV not found at {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    if args.text_col not in df.columns:
        print(f"ERROR: Column '{args.text_col}' not in {list(df.columns)}")
        sys.exit(1)

    texts = df[args.text_col].dropna().astype(str).tolist()
    print(f"Loaded {len(texts)} documents from {csv_path}")

    # ── Run LDA ───────────────────────────────────────────────────────────
    lda = LDABaseline(
        n_topics=args.n_topics,
        n_iterations=args.lda_iter,
    )
    lda_results = lda.run(texts)

    # ── Run ablation if requested ──────────────────────────────────────────
    if args.ablation:
        print("\n" + "="*60)
        print("  ABLATION STUDY")
        print("="*60)
        print("Normalizing texts for ablation conditions …")

        # Import normalizer
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        try:
            from nlp.tanglish_converter.normalizer import normalize_tanglish
            from nlp.tanglish_converter.transliterator import transliterate_tanglish_to_telugu
        except ImportError:
            print("WARNING: normalizer not importable. Using raw texts for all conditions.")
            normalize_tanglish = lambda x: x
            transliterate_tanglish_to_telugu = lambda x: x

        # A1: raw (no processing)
        raw_texts = texts

        # A2: Tier-1 only — just dictionary lookup normalisation, no ML
        tier1_texts = []
        from nlp.tanglish_converter.transliterator import TANGLISH_DICT
        for t in texts:
            words = t.lower().split()
            tier1 = [TANGLISH_DICT.get(w, w) for w in words]
            # Convert Telugu chars back to empty space (keep structure)
            tier1_cleaned = []
            for w in tier1:
                if any('\u0c00' <= c <= '\u0c7f' for c in w):
                    # It was transliterated — keep as telugu placeholder
                    tier1_cleaned.append(w)
                else:
                    tier1_cleaned.append(w)
            tier1_texts.append(' '.join(tier1_cleaned))

        # Normalized: full pipeline
        normalized_texts = [normalize_tanglish(t) for t in texts]

        runner = AblationRunner(n_topics=args.n_topics)
        ablation_results = runner.run(raw_texts, normalized_texts, tier1_texts)

        # Print comparison table
        print("\n" + "="*70)
        print("  ABLATION RESULTS SUMMARY")
        print(f"  {'Condition':<40} {'Cv':>8} {'Diversity':>10} {'Δ Cv':>8}")
        print("="*70)
        full_cv = None
        for r in ablation_results:
            if "Full" in r["label"]:
                full_cv = r["coherence_cv"]
        for r in ablation_results:
            delta = ""
            if full_cv and full_cv > 0 and r["coherence_cv"] > 0:
                pct = (r["coherence_cv"] - full_cv) / full_cv * 100
                delta = f"{pct:+.1f}%"
            print(f"  {r['label']:<40} {r['coherence_cv']:>8.4f} {r['diversity']:>10.4f} {delta:>8}")
        print("="*70)

    # ── Final comparison ───────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  FINAL COMPARISON (for paper Table III)")
    print(f"  {'Model':<30} {'Cv':>8} {'Diversity':>10} {'Redundancy':>12}")
    print("="*60)
    print(f"  {'LDA (this script)':<30} "
          f"{lda_results['coherence_cv']:>8.4f} "
          f"{lda_results['diversity']:>10.4f} "
          f"{lda_results['redundancy']:>12.4f}")
    print("  (Run BERTopic via the API to get UATM numbers)")
    print("="*60)

    return lda_results


if __name__ == "__main__":
    main()
