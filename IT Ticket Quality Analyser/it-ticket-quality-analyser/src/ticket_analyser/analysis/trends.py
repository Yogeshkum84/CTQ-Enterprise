"""Trending and clustering of Incidents/Requests.

Uses TF-IDF + MiniBatchKMeans for fast local clustering on commodity hardware.
All models are fit on-device; nothing is sent off-box.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass
class ClusterResult:
    df: pd.DataFrame                     # original df with cluster label column
    top_terms: dict[int, List[str]]      # per-cluster representative terms
    sizes: pd.Series                     # rows per cluster


def build_trends(df: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
    """Count tickets per ticket_type x priority x period.

    ``freq`` uses pandas offset aliases (D, W, M, Q).
    """
    if "opened_at" not in df.columns:
        raise ValueError("opened_at column required for trending")
    g = (
        df.dropna(subset=["opened_at"])
        .assign(_period=lambda d: d["opened_at"].dt.to_period(freq).dt.to_timestamp())
        .groupby(["_period", df.get("ticket_type", "Unknown"), df.get("priority", "Unknown")], dropna=False)
        .size()
        .rename("count")
        .reset_index()
        .rename(columns={"_period": "period"})
    )
    return g


def cluster_issues(
    df: pd.DataFrame,
    text_cols: Tuple[str, ...] = ("short_description", "description"),
    n_clusters: int = 12,
    min_rows: int = 20,
    random_state: int = 42,
) -> ClusterResult:
    """Cluster tickets by their narrative text to surface repeat themes."""
    sub = df.copy()
    sub["_text"] = (
        sub.reindex(columns=list(text_cols))
        .fillna("")
        .agg(" ".join, axis=1)
        .str.strip()
    )
    sub = sub[sub["_text"].str.len() > 0]
    if len(sub) < max(min_rows, n_clusters):
        sub["issue_cluster"] = -1
        return ClusterResult(df=sub.drop(columns=["_text"]), top_terms={}, sizes=pd.Series(dtype=int))

    vec = TfidfVectorizer(max_features=5000, stop_words="english", ngram_range=(1, 2), min_df=2)
    X = vec.fit_transform(sub["_text"])
    n_clusters = min(n_clusters, X.shape[0] - 1)
    km = MiniBatchKMeans(n_clusters=n_clusters, n_init=5, random_state=random_state, batch_size=256)
    labels = km.fit_predict(X)
    sub["issue_cluster"] = labels

    terms = np.array(vec.get_feature_names_out())
    order = km.cluster_centers_.argsort()[:, ::-1]
    top_terms = {int(i): terms[order[i][:7]].tolist() for i in range(n_clusters)}
    sizes = sub.groupby("issue_cluster").size().sort_values(ascending=False)

    return ClusterResult(df=sub.drop(columns=["_text"]), top_terms=top_terms, sizes=sizes)
