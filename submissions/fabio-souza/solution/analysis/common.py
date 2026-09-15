"""Caminhos, carga dos dados e utilitários estatísticos compartilhados pelos scripts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SOLUTION = Path(__file__).resolve().parents[1]
RAW = SOLUTION / "data" / "raw"
OUT = SOLUTION / "analysis" / "outputs"
APP_DATA = SOLUTION / "app" / "data"
SEED = 42

DS1_CSV = RAW / "customer_support_tickets.csv"
DS2_CSV = RAW / "all_tickets_processed_improved_v3.csv"


def load_ds1() -> pd.DataFrame:
    if not DS1_CSV.exists():
        raise SystemExit("Dados ausentes: rode `bash solution/data/download.sh` antes.")
    df = pd.read_csv(DS1_CSV)
    for col in ["Date of Purchase", "First Response Time", "Time to Resolution"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_ds2() -> pd.DataFrame:
    if not DS2_CSV.exists():
        raise SystemExit("Dados ausentes: rode `bash solution/data/download.sh` antes.")
    return pd.read_csv(DS2_CSV)


def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    return obj


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(obj), ensure_ascii=False, indent=2) + "\n")


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    """Correção de Holm-Bonferroni; devolve p-valores ajustados na mesma chave."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    adjusted, running = {}, 0.0
    for i, (key, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        adjusted[key] = running
    return adjusted


def cramers_v(table: pd.DataFrame) -> tuple[float, float, int]:
    """V de Cramér com correção de viés (Bergsma, 2013).

    O V ingênuo não é zero sob independência: em tabelas grandes ele fica perto de sqrt(gl / (n * k)).
    Ex.: 42 produtos x 16 assuntos com n = 8.469 dá V ingênuo ~0,07 mesmo com campos sorteados.
    """
    chi2, p, dof, _ = stats.chi2_contingency(table, correction=False)
    n = table.to_numpy().sum()
    r, c = table.shape
    phi2 = max(0.0, chi2 / n - (r - 1) * (c - 1) / (n - 1))
    r_corr = r - (r - 1) ** 2 / (n - 1)
    c_corr = c - (c - 1) ** 2 / (n - 1)
    return float(np.sqrt(phi2 / min(r_corr - 1, c_corr - 1))), float(p), int(dof)


def min_detectable_cramers_v(n: int, r: int, c: int, alpha=0.05, power=0.8) -> float:
    """Menor V de Cramér detectável com o poder pedido (qui-quadrado não central)."""
    dof = (r - 1) * (c - 1)
    crit = stats.chi2.ppf(1 - alpha, dof)
    lo, hi = 1e-4, 1.0
    for _ in range(60):
        w = (lo + hi) / 2
        if 1 - stats.ncx2.cdf(crit, dof, n * w * w) >= power:
            hi = w
        else:
            lo = w
    return hi / np.sqrt(min(r, c) - 1)


def min_detectable_spearman(n: int, alpha=0.05, power=0.8) -> float:
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return float(np.tanh(z / np.sqrt(n - 3)))


def min_detectable_anova_f(n: int, k: int, alpha=0.05, power=0.8) -> float:
    """Menor efeito f de Cohen detectável numa ANOVA de k grupos (proxy do Kruskal-Wallis)."""
    d1, d2 = k - 1, n - k
    crit = stats.f.ppf(1 - alpha, d1, d2)
    lo, hi = 1e-4, 1.0
    for _ in range(60):
        f = (lo + hi) / 2
        if 1 - stats.ncf.cdf(crit, d1, d2, n * f * f) >= power:
            hi = f
        else:
            lo = f
    return hi
