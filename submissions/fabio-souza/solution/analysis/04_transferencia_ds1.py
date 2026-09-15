"""O classificador treinado no Dataset 2 (TI interna) serve para o Dataset 1 (suporte ao consumidor)? (H8)

Também mede quanto do Dataset 1 a regra de risco do Fabio (D3: reembolso/cancelamento -> humano) retira da automação.
Requer: 03_classificador.py. Saída: outputs/04_transferencia_ds1.json
"""

from __future__ import annotations

import pickle
import re

import numpy as np
import pandas as pd

from common import OUT, load_ds1, load_ds2, save_json
from texto import known_share as known_share_one
from texto import normalize

RISK_TYPES = {"Refund request", "Cancellation request"}
RISK_PATTERN = re.compile(r"refund|reembols|estorn|chargeback|cancel", re.IGNORECASE)

state = pickle.load(open(OUT / "cache" / "modelo_escolhido.pkl", "rb"))
vec, clf, classes, policy = state["vec"], state["clf"], state["classes"], state["policy"]
vocab = vec.vocabulary_


def lanes(proba: np.ndarray) -> dict:
    conf, pred = proba.max(1), proba.argmax(1)
    auto = (conf >= policy["tau_auto"]) & policy["elegiveis"][pred]
    assist = ~auto & (conf >= policy["tau_assist"])
    return {"auto": auto, "assist": assist, "human": ~auto & ~assist, "conf": conf, "pred": pred}


def describe(texts: pd.Series, proba: np.ndarray) -> dict:
    X = vec.transform(texts)
    unigram_hits = [known_share_one(doc, vocab) for doc in texts]
    L = lanes(proba)
    return {
        "tickets": len(texts),
        "termos_ativos_por_ticket_mediana": float(np.median(np.diff(X.indptr))),
        "fracao_de_palavras_no_vocabulario_mediana": float(np.median(unigram_hits)),
        "confianca_quantis": {q: float(np.quantile(L["conf"], v)) for q, v in [("p10", .1), ("p50", .5), ("p90", .9)]},
        "fila_auto": float(L["auto"].mean()), "fila_assistida": float(L["assist"].mean()),
        "fila_humana": float(L["human"].mean()),
        "categoria_prevista": pd.Series(classes[L["pred"]]).value_counts(normalize=True).round(4).to_dict(),
    }


ds2 = load_ds2()
test_texts = ds2["Document"][state["is_test"]].map(normalize)
ds2_desc = describe(test_texts, clf.predict_proba(vec.transform(test_texts)))

ds1 = load_ds1()
ds1_texts = ds1["Ticket Description"].fillna("").map(normalize)
proba1 = clf.predict_proba(vec.transform(ds1_texts))
ds1_desc = describe(ds1_texts, proba1)

L1 = lanes(proba1)
risk_by_type = ds1["Ticket Type"].isin(RISK_TYPES).to_numpy()
risk_by_text = ds1["Ticket Description"].fillna("").str.contains(RISK_PATTERN).to_numpy()
auto_after_rule = L1["auto"] & ~risk_by_type

# ------------------------------------------------------------------ trava de domínio (vocabulário conhecido)
def known_share(texts: pd.Series) -> np.ndarray:
    return np.array([known_share_one(normalize(doc), vocab) for doc in texts])


known_val = known_share(ds2["Document"][state["is_val"]])  # known_share normaliza internamente
known_test = known_share(test_texts)
known_ds1 = known_share(ds1_texts)
# Corte escolhido na validação do Dataset 2: aceita perder no máximo 1% dos tickets do próprio domínio.
tau_ood = float(np.quantile(known_val, 0.01))
test_lanes = lanes(clf.predict_proba(vec.transform(test_texts)))
ood_guard = {
    "corte_fracao_de_palavras_conhecidas": tau_ood,
    "criterio": "percentil 1 da validação do Dataset 2 (perde no máximo ~1% do domínio de treino)",
    "dataset2_teste_barrados": float((known_test < tau_ood).mean()),
    "dataset2_teste_fila_auto_com_trava": float((test_lanes["auto"] & (known_test >= tau_ood)).mean()),
    "dataset1_barrados": float((known_ds1 < tau_ood).mean()),
    "dataset1_fila_auto_com_trava": float((L1["auto"] & (known_ds1 >= tau_ood)).mean()),
    "dataset1_fila_auto_com_trava_e_regra_D3": float((auto_after_rule & (known_ds1 >= tau_ood)).mean()),
    "quantis_conhecidas": {
        "dataset2_validacao": {q: float(np.quantile(known_val, v)) for q, v in [("p1", .01), ("p5", .05), ("p50", .5)]},
        "dataset1": {q: float(np.quantile(known_ds1, v)) for q, v in [("p50", .5), ("p90", .9), ("p99", .99)]},
    },
}

# ------------------------------------------------------------------ travas alternativas (mesmo critério de corte)
from sklearn.neighbors import NearestNeighbors  # noqa: E402
from sklearn.preprocessing import normalize as l2_normalize  # noqa: E402

train_mask = ~state["is_val"] & ~state["is_test"]
y2 = np.searchsorted(classes, ds2["Topic_group"].to_numpy())
X_train = vec.transform(ds2["Document"][train_mask].map(normalize))
X_val = vec.transform(ds2["Document"][state["is_val"]].map(normalize))
X_test, X_ds1 = vec.transform(test_texts), vec.transform(ds1_texts)
centroids = l2_normalize(np.vstack([np.asarray(X_train[y2[train_mask] == k].mean(0)) for k in range(len(classes))]))
nn = NearestNeighbors(n_neighbors=1, metric="cosine", algorithm="brute", n_jobs=-1).fit(X_train)
signals = {
    "fracao_de_palavras_conhecidas": (known_val, known_test, known_ds1),
    "similaridade_com_centroide_da_categoria": tuple(np.asarray(X @ centroids.T).max(1) for X in (X_val, X_test, X_ds1)),
    "similaridade_com_ticket_mais_proximo_do_treino": tuple(1 - nn.kneighbors(X)[0][:, 0] for X in (X_val, X_test, X_ds1)),
}
alternatives = {}
for name, (s_val, s_test, s_ds1) in signals.items():
    cut = float(np.quantile(s_val, 0.01))
    alternatives[name] = {"corte": cut, "dataset2_teste_barrados": float((s_test < cut).mean()),
                          "dataset1_barrados": float((s_ds1 < cut).mean()),
                          "dataset1_fila_auto_com_trava": float((L1["auto"] & (s_ds1 >= cut)).mean())}
ood_guard["comparacao_de_travas"] = alternatives

res = {
    "trava_de_dominio": ood_guard,
    "dataset2_teste": ds2_desc,
    "dataset1_descricoes": ds1_desc,
    "queda_de_cobertura_auto_pp": 100 * (ds2_desc["fila_auto"] - ds1_desc["fila_auto"]),
    "regra_de_risco_D3": {
        "fracao_reembolso_ou_cancelamento_pelo_tipo": float(risk_by_type.mean()),
        "fila_auto_antes_da_regra": float(L1["auto"].mean()),
        "fila_auto_depois_da_regra": float(auto_after_rule.mean()),
        "detector_por_palavra_chave": {
            "fracao_de_descricoes_sinalizadas": float(risk_by_text.mean()),
            "recall_contra_o_tipo": float(risk_by_text[risk_by_type].mean()),
            "sinalizadas_entre_os_demais_tipos": float(risk_by_text[~risk_by_type].mean()),
        },
    },
}
save_json(OUT / "04_transferencia_ds1.json", res)

for name in ("dataset2_teste", "dataset1_descricoes"):
    d = res[name]
    print(f"{name}: termos ativos {d['termos_ativos_por_ticket_mediana']:.0f}, palavras no vocabulário "
          f"{d['fracao_de_palavras_no_vocabulario_mediana']:.0%}, confiança {d['confianca_quantis']}, "
          f"AUTO {d['fila_auto']:.1%} ASSIST {d['fila_assistida']:.1%} HUMANA {d['fila_humana']:.1%}")
    print("   previsto:", d["categoria_prevista"])
print(f"Queda de cobertura AUTO: {res['queda_de_cobertura_auto_pp']:.1f} p.p.")
print("Regra D3:", res["regra_de_risco_D3"])
print("Trava de domínio:", {k: v for k, v in ood_guard.items() if k != "comparacao_de_travas"})
for k, v in alternatives.items():
    print(f"  {k}: barra {v['dataset1_barrados']:.1%} do Dataset 1, deixa {v['dataset1_fila_auto_com_trava']:.1%} na fila auto "
          f"(custa {v['dataset2_teste_barrados']:.1%} do Dataset 2)")
