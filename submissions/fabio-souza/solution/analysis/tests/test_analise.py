"""Testes das peças que já tiveram bug nesta análise (E7, E9, E10). Rodam sem os datasets."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from politica import local_accuracy, tau_marginal, tau_media  # noqa: E402
from roi import monthly_savings  # noqa: E402
from texto import known_share, normalize, tokens  # noqa: E402


# ------------------------------------------------------------------ texto (E9)
def test_normalize_remove_placeholder_digitos_e_pontuacao():
    assert normalize("I'm having an issue with the {product_purchased}. Order #123!") == "i m having an issue with the order"


def test_normalize_e_idempotente():
    once = normalize("Reset PASSWORD for user-42, please!")
    assert normalize(once) == once


def test_tokens_descartam_fragmentos_de_uma_letra_como_o_scikit_learn():
    # E9: contar "i" e "m" (de "I'm") como palavras desconhecidas inflava a trava de domínio de 41% para 95%.
    assert tokens(normalize("I'm having an issue")) == ["having", "an", "issue"]


def test_known_share_usa_os_mesmos_tokens_do_modelo():
    vocab = {"having": 0, "issue": 1}
    assert known_share(normalize("I'm having an issue"), vocab) == pytest.approx(2 / 3)
    assert known_share("", vocab) == 0.0


# ------------------------------------------------------------------ política de corte (E7)
def _synthetic(n=20_000, seed=0):
    """Confiança uniforme; acerto real igual à confiança (modelo calibrado)."""
    rng = np.random.default_rng(seed)
    conf = rng.uniform(0.2, 1.0, n)
    hit = rng.uniform(0, 1, n) < conf
    return conf, hit


def test_tau_marginal_garante_o_alvo_para_cada_ticket():
    conf, hit = _synthetic()
    tau = tau_marginal(conf, hit, 0.90)
    assert 0.85 <= tau <= 0.95
    assert local_accuracy(conf, hit).predict([tau])[0] >= 0.90


def test_regra_media_aceita_tickets_que_acertam_muito_menos_que_o_alvo():
    # E7: a média da fila fica em 90%, mas o ticket no corte acerta bem menos.
    conf, hit = _synthetic()
    tau = tau_media(conf, hit, 0.90)
    assert hit[conf >= tau].mean() >= 0.90
    assert local_accuracy(conf, hit).predict([tau])[0] < 0.85
    assert tau < tau_marginal(conf, hit, 0.90)


# ------------------------------------------------------------------ ROI (E10)
BASE = {
    "tickets_por_mes": 1000.0, "fracao_reembolso_cancelamento": 0.0, "fila_auto": 1.0, "precisao_auto": 1.0,
    "fila_assistida": 0.0, "top2_assistida": 1.0, "min_triagem_manual": 2.0, "multiplo_custo_erro": 4.0,
    "min_confirmacao_assistida": 0.5, "custo_hora_brl": 35.0, "horas_produtivas_por_fte_mes": 160.0,
}


def test_fila_automatica_perfeita_economiza_toda_a_triagem():
    r = monthly_savings(BASE)
    assert r["horas_mes"] == pytest.approx(1000 * 2 / 60)
    assert r["brl_mes"] == pytest.approx(r["horas_mes"] * 35)


def test_ponto_de_empate_e_1_menos_1_sobre_k():
    # E10: o erro contado duas vezes deslocava o empate para k/(1+k) = 80%; o correto é 1 - 1/k = 75%.
    r = monthly_savings({**BASE, "precisao_auto": 0.75})
    assert r["min_liquidos_por_ticket_auto"] == pytest.approx(0.0)


def test_reembolso_e_cancelamento_saem_da_automacao():
    half = monthly_savings({**BASE, "fracao_reembolso_cancelamento": 0.5})
    assert half["horas_mes"] == pytest.approx(monthly_savings(BASE)["horas_mes"] / 2)


def test_fila_assistida_com_sugestao_errada_custa_o_tempo_de_conferir():
    r = monthly_savings({**BASE, "fila_auto": 0.0, "fila_assistida": 1.0, "top2_assistida": 0.0})
    assert r["min_liquidos_por_ticket_assistido"] == pytest.approx(-0.5)
