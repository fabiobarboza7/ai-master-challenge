"""Normalização de texto e trava de domínio. O protótipo (app/lib/triage) implementa exatamente estas regras."""

from __future__ import annotations

import re

import numpy as np

_NON_LETTERS = re.compile(r"[^a-z]+")


def normalize(text: str) -> str:
    """Aproxima o pré-processamento do Dataset 2: minúsculas, só letras a-z, sem placeholders nem dígitos."""
    return _NON_LETTERS.sub(" ", text.replace("{product_purchased}", " ").lower()).strip()


def tokens(normalized: str) -> list[str]:
    """Mesmo resultado do tokenizador padrão do scikit-learn ((?u)\\b\\w\\w+\\b) sobre texto já normalizado."""
    return [t for t in normalized.split(" ") if len(t) >= 2]


def known_share(normalized: str, vocabulary: dict) -> float:
    """Fração das palavras do ticket que o modelo conhece (unigramas do vocabulário)."""
    toks = tokens(normalized)
    return float(np.mean([t in vocabulary for t in toks])) if toks else 0.0
