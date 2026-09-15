"""Detecção de tickets quase duplicados por similaridade de cosseno TF-IDF."""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors


def nearest_neighbors(texts, k: int = 6):
    """Devolve (similaridades, índices) dos k vizinhos mais próximos de cada texto (inclui ele mesmo)."""
    X = TfidfVectorizer(sublinear_tf=True, min_df=2).fit_transform(texts)
    nn = NearestNeighbors(n_neighbors=k, metric="cosine", algorithm="brute", n_jobs=-1).fit(X)
    dist, idx = nn.kneighbors(X)
    return 1.0 - dist, idx


def groups_from_neighbors(sims: np.ndarray, idx: np.ndarray, threshold: float) -> np.ndarray:
    """Agrupa (union-find) textos ligados por similaridade >= threshold. Textos isolados viram grupos próprios."""
    parent = np.arange(len(idx))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    rows, cols = np.nonzero(sims >= threshold)
    for r, c in zip(rows, cols):
        j = idx[r, c]
        if j != r:
            a, b = find(r), find(j)
            if a != b:
                parent[b] = a
    return np.array([find(i) for i in range(len(idx))])
