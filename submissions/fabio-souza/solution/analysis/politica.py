"""Regras de corte de confiança e métricas das filas, compartilhadas entre os scripts."""

from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression

MIN_LANE = 50
# A grade começava em 0,30 e o piso fixava os cortes (erro E6). Com 8 classes a confiança mínima é 0,125.
GRID = np.round(np.arange(0.0, 0.996, 0.005), 3)


def top2_hit(proba: np.ndarray, y_true: np.ndarray) -> np.ndarray:
    return (np.argsort(-proba, axis=1)[:, :2] == y_true[:, None]).any(1)


def local_accuracy(conf: np.ndarray, hit: np.ndarray) -> IsotonicRegression:
    """Taxa de acerto em função da confiança, monotônica (regressão isotônica)."""
    return IsotonicRegression(increasing=True, out_of_bounds="clip", y_min=0, y_max=1).fit(conf, hit.astype(float))


def tau_marginal(conf: np.ndarray, hit: np.ndarray, target: float) -> float | None:
    """Menor corte em que a taxa de acerto LOCAL (tickets com aquela confiança) é >= target."""
    ok = np.nonzero(local_accuracy(conf, hit).predict(GRID) >= target)[0]
    return float(GRID[ok[0]]) if len(ok) else None


def tau_media(conf: np.ndarray, hit: np.ndarray, target: float, allowed: np.ndarray | None = None) -> float | None:
    """Regra pré-registrada (falha, erro E7): menor corte com precisão MÉDIA da fila >= target."""
    allowed = np.ones_like(hit, dtype=bool) if allowed is None else allowed
    for tau in GRID:
        m = (conf >= tau) & allowed
        if m.sum() >= MIN_LANE and hit[m].mean() >= target:
            return float(tau)
    return None


def ece(proba: np.ndarray, y_true: np.ndarray, bins: int = 15) -> float:
    conf, correct = proba.max(1), proba.argmax(1) == y_true
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            total += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(total)


def wilson(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return (float("nan"), float("nan"))
    p, den = hits / total, 1 + z * z / total
    center = (p + z * z / (2 * total)) / den
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / den
    return float(center - half), float(center + half)
