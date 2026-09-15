"""Exporta o modelo, a política e os dados do protótipo (solution/app/public/data).

- model.json: vocabulário, idf, pesos (arredondados) e política de filas;
- paridade.json: tickets com probabilidades e fila calculadas aqui, para o teste do TypeScript;
- backtest.json: confiança, previsão e verdade dos 7.026 tickets de teste (para o controle de corte);
- exemplos.json: amostra ALEATÓRIA (semente fixa) de tickets por fila e do Dataset 1;
- relatorio.json: números do relatório usados nas telas.

O arredondamento só é aceito se não mudar nenhuma fila no teste em relação ao modelo em precisão total.
Requer: 01-06. Saídas: solution/app/public/data/*.json
"""

from __future__ import annotations

import json
import math
import pickle
import re
from collections import Counter

import numpy as np

from common import OUT, SEED, SOLUTION, load_ds1, load_ds2
from politica import top2_hit
from texto import known_share, normalize, tokens

APP_DATA = SOLUTION / "app" / "public" / "data"
RISK_PATTERN = r"refund|reembols|estorn|chargeback|cancel"
RISK_TYPES = ["Refund request", "Cancellation request"]
LABELS_PT = {"Access": "Acesso", "Administrative rights": "Permissões administrativas", "HR Support": "RH",
             "Hardware": "Hardware", "Internal Project": "Projeto interno", "Miscellaneous": "Diversos",
             "Purchase": "Compras", "Storage": "Armazenamento"}
EXECUTION_HUMAN = ["Access", "Administrative rights", "HR Support"]  # D10: IA só roteia; execução sempre humana

state = pickle.load(open(OUT / "cache" / "modelo_escolhido.pkl", "rb"))
vec, clf, classes, pol = state["vec"], state["clf"], state["classes"], state["policy"]
transfer = json.loads((OUT / "04_transferencia_ds1.json").read_text())
tau_known = transfer["trava_de_dominio"]["corte_fracao_de_palavras_conhecidas"]
vocab = vec.vocabulary_
terms = [t for t, _ in sorted(vocab.items(), key=lambda kv: kv[1])]


def probs(text_norm: str, idf, coef, intercept) -> np.ndarray:
    """TF-IDF sublinear + L2 + softmax da regressão logística: exatamente o que o TypeScript faz."""
    toks = tokens(text_norm)
    grams = toks + [f"{a} {b}" for a, b in zip(toks, toks[1:])]
    counts = Counter(g for g in grams if g in vocab)
    z = intercept.copy()
    if counts:
        idx = np.array([vocab[g] for g in counts])
        vals = np.array([1 + math.log(c) for c in counts.values()]) * idf[idx]
        vals /= np.sqrt((vals * vals).sum())
        z = z + coef[:, idx] @ vals
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def lane(p: np.ndarray, text_norm: str, raw_text: str, ticket_type: str | None) -> dict:
    if (ticket_type in RISK_TYPES) or re.search(RISK_PATTERN, raw_text, re.IGNORECASE):
        return {"fila": "humana", "motivo": "reembolso_cancelamento"}
    if known_share(text_norm, vocab) < tau_known:
        return {"fila": "humana", "motivo": "fora_do_dominio"}
    c = int(p.argmax())
    if p[c] >= pol["tau_auto"] and pol["elegiveis"][c]:
        return {"fila": "automatica", "motivo": "confianca_alta"}
    if p[c] >= pol["tau_assist"]:
        return {"fila": "assistida", "motivo": "confianca_media"}
    return {"fila": "humana", "motivo": "confianca_baixa"}


ds2 = load_ds2()
test_raw = ds2["Document"][state["is_test"]].to_numpy()
test_norm = [normalize(t) for t in test_raw]
y_test = np.searchsorted(classes, ds2["Topic_group"][state["is_test"]].to_numpy())
full = clf.predict_proba(vec.transform(test_norm))
full_lanes = [lane(full[i], test_norm[i], test_raw[i], None)["fila"] for i in range(len(test_norm))]

chosen_decimals, quant_report = None, {}
for decimals in (3, 4, 5):
    idf_q, coef_q, b_q = (np.round(a, decimals) for a in (vec.idf_, clf.coef_, clf.intercept_))
    q = np.vstack([probs(t, idf_q, coef_q, b_q) for t in test_norm])
    q_lanes = [lane(q[i], test_norm[i], test_raw[i], None)["fila"] for i in range(len(test_norm))]
    quant_report[decimals] = {"filas_iguais": float(np.mean([a == b for a, b in zip(full_lanes, q_lanes)])),
                              "categoria_igual": float((q.argmax(1) == full.argmax(1)).mean()),
                              "max_dif_probabilidade": float(np.abs(q - full).max())}
    print(f"  {decimals} casas: {quant_report[decimals]}")
    if quant_report[decimals]["filas_iguais"] == 1.0 and quant_report[decimals]["categoria_igual"] == 1.0:
        chosen_decimals = decimals
        break
if chosen_decimals is None:
    raise SystemExit("Arredondamento muda filas; exportar com mais casas.")

idf_q, coef_q, b_q = (np.round(a, chosen_decimals) for a in (vec.idf_, clf.coef_, clf.intercept_))
proba_q = np.vstack([probs(t, idf_q, coef_q, b_q) for t in test_norm])
conf, pred, hit2 = proba_q.max(1), proba_q.argmax(1), top2_hit(proba_q, y_test)
known = np.array([known_share(t, vocab) for t in test_norm])

audit = {k: json.loads((OUT / f).read_text()) for k, f in [
    ("ds1", "01_auditoria_ds1.json"), ("ds2", "02_auditoria_ds2.json"), ("clf", "03_classificador.json"),
    ("transf", "04_transferencia_ds1.json"), ("curva", "05_curva_de_aprendizado.json"), ("roi", "06_roi.json")]}

APP_DATA.mkdir(parents=True, exist_ok=True)
model = {
    "descricao": "TF-IDF (1-2 gramas, tf sublinear, L2) + regressão logística multinomial treinada no Dataset 2",
    "classes": classes.tolist(), "rotulos_pt": LABELS_PT,
    "vocabulario": terms, "idf": idf_q.tolist(), "coef": coef_q.tolist(), "intercepto": b_q.tolist(),
    "casas_decimais": chosen_decimals, "arredondamento": quant_report[chosen_decimals],
    "politica": {
        "tau_auto": pol["tau_auto"], "tau_assist": pol["tau_assist"], "precisao_alvo_por_ticket": pol["alvo"],
        "categorias_elegiveis": classes[pol["elegiveis"]].tolist(),
        "corte_palavras_conhecidas": tau_known,
        "padrao_reembolso_cancelamento": RISK_PATTERN, "tipos_reembolso_cancelamento": RISK_TYPES,
        "execucao_sempre_humana": EXECUTION_HUMAN,
        "presets": [
            {"alvo": float(t), "tau_auto": r["tau_auto"], "tau_assist": r["tau_assist"],
             "categorias_elegiveis": [c for c, v in r["por_categoria"].items() if v["elegivel"]]}
            for t, r in sorted([(0.90, audit["clf"]["resultados"]["marginal"]["teste"])]
                               + [(float(k), v) for k, v in audit["clf"]["sensibilidade_regra_marginal_teste"].items()])
        ],
    },
}
(APP_DATA / "model.json").write_text(json.dumps(model, ensure_ascii=False, separators=(",", ":")))

rng = np.random.default_rng(SEED)
parity_idx = rng.choice(len(test_norm), size=200, replace=False)
ds1 = load_ds1()
ds1_idx = rng.choice(len(ds1), size=40, replace=False)
handwritten = [  # escritos pela IA para exercitar as regras (não são dados do challenge)
    ("Quero o reembolso da minha compra, o produto chegou quebrado", None),
    ("please cancel my subscription and refund the last invoice", None),
    ("Não consigo acessar minha conta desde ontem", None),
    ("", None),
    ("laptop screen broken need replacement asap", None),
]
cases = []
for i in parity_idx:
    cases.append({"origem": "dataset2_teste", "texto": test_raw[i], "tipo": None})
for i in ds1_idx:
    cases.append({"origem": "dataset1", "texto": ds1["Ticket Description"].iloc[i], "tipo": ds1["Ticket Type"].iloc[i]})
for text, ttype in handwritten:
    cases.append({"origem": "escrito_pela_ia", "texto": text, "tipo": ttype})
for c in cases:
    tn = normalize(c["texto"])
    p = probs(tn, idf_q, coef_q, b_q)
    c.update({"normalizado": tn, "palavras_conhecidas": known_share(tn, vocab), "probabilidades": p.tolist(),
              **lane(p, tn, c["texto"], c["tipo"])})
(APP_DATA / "paridade.json").write_text(json.dumps(cases, ensure_ascii=False))

risk_kw = np.array([bool(re.search(RISK_PATTERN, t, re.IGNORECASE)) for t in test_raw])
backtest = {"classes": classes.tolist(), "confianca": conf.tolist(), "prevista": pred.tolist(),
            "real": y_test.tolist(), "top2_certo": hit2.astype(int).tolist(),
            "palavras_conhecidas": np.round(known, 3).tolist(), "palavra_chave_reembolso_cancelamento": risk_kw.astype(int).tolist()}
lane_counts = Counter(lane(proba_q[i], test_norm[i], test_raw[i], None)["fila"] for i in range(len(test_norm)))
backtest["referencia_python"] = {"filas": dict(lane_counts), "tau_auto": pol["tau_auto"], "tau_assist": pol["tau_assist"]}
(APP_DATA / "backtest.json").write_text(json.dumps(backtest, separators=(",", ":")))

examples = []
lane_of = np.array([lane(proba_q[i], test_norm[i], test_raw[i], None)["fila"] for i in range(len(test_norm))])
for name in ("automatica", "assistida", "humana"):
    for i in rng.choice(np.nonzero(lane_of == name)[0], size=4, replace=False):
        examples.append({"origem": "Dataset 2 (teste)", "texto": test_raw[i], "tipo": None,
                         "categoria_real": classes[y_test[i]], "sorteado_na_fila": name})
for i in rng.choice(len(ds1), size=4, replace=False):
    examples.append({"origem": "Dataset 1", "texto": ds1["Ticket Description"].iloc[i], "tipo": ds1["Ticket Type"].iloc[i],
                     "categoria_real": None, "sorteado_na_fila": None})
(APP_DATA / "exemplos.json").write_text(json.dumps(examples, ensure_ascii=False, indent=1))

report = {
    "ds1": {k: audit["ds1"][k] for k in ("volume_e_tempo", "consistencia_temporal", "fracao_nao_fechados", "coerencia_semantica")}
    | {"satisfacao": {k: audit["ds1"]["satisfacao"][k] for k in ("n_fechados_com_nota", "algum_significativo_apos_holm", "poder_80pct")},
       "csat_por_nota": audit["ds1"]["aderencia_a_distribuicao_uniforme"]["Customer Satisfaction Rating (fechados)"]["contagem_por_nota"],
       "sinal_do_texto": audit["ds1"]["sinal_do_texto"]},
    "ds2": {k: audit["ds2"][k] for k in ("linhas", "fracao_por_classe", "quase_duplicados", "grupos_para_divisao")},
    "classificador": {k: audit["clf"][k] for k in ("divisao", "comparacao_validacao", "selecao", "escolhido", "politicas",
                                                   "sensibilidade_regra_marginal_teste", "confusoes_mais_comuns_teste", "vazamento")}
    | {"teste": {k: audit["clf"]["resultados"][k]["teste"] for k in ("media", "marginal")}, "curvas": audit["clf"]["curvas"]},
    "transferencia": audit["transf"], "curva_de_aprendizado": audit["curva"]["resumo"], "roi": audit["roi"],
}
(APP_DATA / "relatorio.json").write_text(json.dumps(report, ensure_ascii=False))

for f in sorted(APP_DATA.glob("*.json")):
    print(f"{f.name}: {f.stat().st_size / 1e6:.2f} MB")
print(f"Casas decimais: {chosen_decimals}; filas do teste por modelo exportado: "
      f"{dict(zip(*np.unique(lane_of, return_counts=True)))}")
auto_no_rule = (conf >= pol["tau_auto"]) & pol["elegiveis"][pred] & (known >= tau_known)
print(f"Palavra-chave de reembolso/cancelamento no Dataset 2 (TI, sem essas categorias): {risk_kw.mean():.1%} dos tickets; "
      f"fila automática {auto_no_rule.mean():.1%} sem a regra -> {(auto_no_rule & ~risk_kw).mean():.1%} com a regra; "
      f"exemplos: {[t[:60] for t in test_raw[risk_kw][:3]]}")
print("Paridade: filas nos casos ->", Counter(c["fila"] for c in cases), "| motivos ->", Counter(c["motivo"] for c in cases))
