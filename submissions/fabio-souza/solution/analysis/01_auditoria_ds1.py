"""Auditoria do Dataset 1: o que os dados permitem (e o que não permitem) afirmar sobre a operação.

Testa as alegações A1-A4 e as hipóteses H1-H5 e H9 de process-log/hipoteses-pre-registradas.md.
Saída: outputs/01_auditoria_ds1.json
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

from common import (
    OUT,
    SEED,
    cramers_v,
    holm,
    load_ds1,
    min_detectable_anova_f,
    min_detectable_cramers_v,
    min_detectable_spearman,
    save_json,
)

BRIEF_TICKETS_PER_YEAR = 30_000
ALPHA = 0.05
MIN_CELULA = 30  # células menores não têm poder para nada; ficam de fora com a contagem declarada

df = load_ds1()
n = len(df)
res: dict = {}

# ---------------------------------------------------------------- H1 / A3: volume e semântica do tempo
frt, ttr = df["First Response Time"], df["Time to Resolution"]
stamps = pd.concat([frt, ttr]).dropna()
res["volume_e_tempo"] = {
    "linhas": n,
    "volume_anual_no_brief": BRIEF_TICKETS_PER_YEAR,
    "fracao_do_brief": n / BRIEF_TICKETS_PER_YEAR,
    "colunas_de_tempo": ["Date of Purchase", "First Response Time", "Time to Resolution"],
    "existe_carimbo_de_abertura": False,
    "compra_min": df["Date of Purchase"].min(),
    "compra_max": df["Date of Purchase"].max(),
    "respostas_inicio": stamps.min(),
    "respostas_fim": stamps.max(),
    "janela_de_respostas_horas": (stamps.max() - stamps.min()).total_seconds() / 3600,
}

# ---------------------------------------------------------------- ausência estrutural por status
cols = ["First Response Time", "Time to Resolution", "Resolution", "Customer Satisfaction Rating"]
res["preenchimento_por_status"] = (
    df.groupby("Ticket Status")[cols].apply(lambda g: g.notna().mean()).round(4).to_dict(orient="index")
)
res["status"] = df["Ticket Status"].value_counts().to_dict()
res["fracao_nao_fechados"] = float((df["Ticket Status"] != "Closed").mean())

# ---------------------------------------------------------------- A2: consistência temporal (fechados)
closed = df[df["Ticket Status"] == "Closed"].copy()
closed["gap_h"] = (closed["Time to Resolution"] - closed["First Response Time"]).dt.total_seconds() / 3600
gap = closed["gap_h"]
res["consistencia_temporal"] = {
    "fechados": len(closed),
    "fracao_resolucao_antes_da_1a_resposta": float((gap < 0).mean()),
    "gap_horas": {q: float(gap.quantile(v)) for q, v in [("min", 0), ("p25", .25), ("mediana", .5), ("p75", .75), ("max", 1)]},
}

# ---------------------------------------------------------------- assinaturas de geração sintética
uniform = {}
for col in ["Ticket Type", "Ticket Subject", "Ticket Status", "Ticket Priority", "Ticket Channel",
            "Customer Gender", "Product Purchased"]:
    counts = df[col].value_counts()
    chi2, p = stats.chisquare(counts)
    uniform[col] = {"categorias": len(counts), "min": int(counts.min()), "max": int(counts.max()),
                    "razao_max_min": float(counts.max() / counts.min()), "p_aderencia_uniforme": float(p)}
csat_counts = closed["Customer Satisfaction Rating"].value_counts().sort_index()
chi2, p = stats.chisquare(csat_counts)
uniform["Customer Satisfaction Rating (fechados)"] = {
    "categorias": len(csat_counts), "min": int(csat_counts.min()), "max": int(csat_counts.max()),
    "razao_max_min": float(csat_counts.max() / csat_counts.min()), "p_aderencia_uniforme": float(p),
    "contagem_por_nota": {int(k): int(v) for k, v in csat_counts.items()},
}
# Idade é inteira (18-70): KS assume distribuição contínua e erra com empates; qui-quadrado por idade.
age_counts = df["Customer Age"].value_counts().reindex(range(df["Customer Age"].min(), df["Customer Age"].max() + 1),
                                                       fill_value=0)
chi2, p = stats.chisquare(age_counts)
uniform["Customer Age"] = {"categorias": len(age_counts), "min": int(age_counts.min()), "max": int(age_counts.max()),
                           "razao_max_min": float(age_counts.max() / max(age_counts.min(), 1)),
                           "p_aderencia_uniforme": float(p)}
res["aderencia_a_distribuicao_uniforme"] = uniform

emails = df["Customer Email"].str.split("@").str[1]
res["dominios_de_email"] = emails.value_counts().to_dict()

pairs = [("Ticket Type", "Ticket Subject"), ("Ticket Type", "Ticket Priority"), ("Ticket Type", "Ticket Channel"),
         ("Ticket Priority", "Ticket Channel"), ("Product Purchased", "Ticket Type"),
         ("Product Purchased", "Ticket Subject")]
indep, pv = {}, {}
for a, b in pairs:
    table = pd.crosstab(df[a], df[b])
    v, p, dof = cramers_v(table)
    key = f"{a} x {b}"
    indep[key] = {"v_cramer": v, "p": p, "gl": dof,
                  "v_minimo_detectavel": min_detectable_cramers_v(n, *table.shape)}
    pv[key] = p
for key, p_adj in holm(pv).items():
    indep[key]["p_holm"] = p_adj
res["independencia_entre_campos"] = indep

refund_subject = df[df["Ticket Subject"] == "Refund request"]
res["coerencia_semantica"] = {
    "assunto_refund_request_com_tipo_refund_request": float((refund_subject["Ticket Type"] == "Refund request").mean()),
    "esperado_se_aleatorio": 1 / df["Ticket Type"].nunique(),
    "tipos_do_assunto_refund_request": refund_subject["Ticket Type"].value_counts().to_dict(),
}

# ---------------------------------------------------------------- A4 / H9: o texto do Dataset 1 é informativo?
desc = df["Ticket Description"].fillna("")
first_line = desc.str.split("\n").str[0]
res["texto_descricao"] = {
    "fracao_com_placeholder_product_purchased": float(desc.str.contains(r"\{product_purchased\}").mean()),
    "primeiras_linhas_distintas": int(first_line.nunique()),
    "template_mais_comum": first_line.value_counts().index[0],
    "fracao_template_mais_comum": float(first_line.value_counts().iloc[0] / n),
}


def text_signal(texts: pd.Series, labels: pd.Series) -> dict:
    """Acurácia fora da amostra (5 folds) de TF-IDF + regressão logística vs. a classe majoritária."""
    pipe = make_pipeline(TfidfVectorizer(min_df=2, sublinear_tf=True),
                         LogisticRegression(max_iter=2000))
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    pred = cross_val_predict(pipe, texts, labels, cv=cv)
    hits = int((pred == labels.to_numpy()).sum())
    chance = float(labels.value_counts(normalize=True).max())
    test = stats.binomtest(hits, len(labels), chance, alternative="greater")
    return {"acuracia": hits / len(labels), "acaso_classe_majoritaria": chance, "p_binomial": float(test.pvalue),
            "classes": int(labels.nunique())}


clean = desc.str.replace(r"\{product_purchased\}", " ", regex=True)
res["sinal_do_texto"] = {
    "descricao -> tipo": text_signal(clean, df["Ticket Type"]),
    "descricao -> assunto": text_signal(clean, df["Ticket Subject"]),
    "resolucao -> tipo (fechados)": text_signal(closed["Resolution"].fillna(""), closed["Ticket Type"]),
}

# ---------------------------------------------------------------- A1 / H4: o que explica a satisfação?
csat = closed["Customer Satisfaction Rating"]
tests, pv = {}, {}
for col in ["Customer Age", "gap_h"]:
    rho, p = stats.spearmanr(closed[col], csat)
    tests[f"spearman CSAT x {col}"] = {"rho": float(rho), "p": float(p)}
    pv[f"spearman CSAT x {col}"] = float(p)
closed["hora_1a_resposta"] = (closed["First Response Time"] - stamps.min()).dt.total_seconds() / 3600
rho, p = stats.spearmanr(closed["hora_1a_resposta"], csat)
tests["spearman CSAT x momento da 1a resposta"] = {"rho": float(rho), "p": float(p)}
pv["spearman CSAT x momento da 1a resposta"] = float(p)
for col in ["Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject", "Customer Gender",
            "Product Purchased"]:
    groups = [g.to_numpy() for _, g in closed.groupby(col)["Customer Satisfaction Rating"]]
    h, p = stats.kruskal(*groups)
    k = len(groups)
    tests[f"kruskal CSAT por {col}"] = {
        "H": float(h), "p": float(p), "grupos": k,
        "epsilon2": float(max(0.0, (h - k + 1) / (len(closed) - k))),
        "media_por_grupo": closed.groupby(col)["Customer Satisfaction Rating"].mean().round(3).to_dict()
        if k <= 16 else None,
    }
    pv[f"kruskal CSAT por {col}"] = float(p)
for key, p_adj in holm(pv).items():
    tests[key]["p_holm"] = p_adj
res["satisfacao"] = {
    "n_fechados_com_nota": int(csat.notna().sum()),
    "media": float(csat.mean()),
    "testes": tests,
    "algum_significativo_apos_holm": any(t["p_holm"] < ALPHA for t in tests.values()),
    "poder_80pct": {
        "rho_minimo_detectavel": min_detectable_spearman(len(closed)),
        "f_minimo_detectavel_4_grupos": min_detectable_anova_f(len(closed), 4),
        "referencia_cohen": "efeito pequeno: rho = 0,10; f = 0,10",
    },
}

# ---------------------------------------------------------------- H2 / H3: onde o fluxo trava?
flow, pv = {}, {}
df["nao_fechado"] = df["Ticket Status"] != "Closed"
df["sem_1a_resposta"] = df["Ticket Status"] == "Open"
for target in ["nao_fechado", "sem_1a_resposta"]:
    for col in ["Ticket Channel", "Ticket Priority", "Ticket Type"]:
        table = pd.crosstab(df[col], df[target])
        v, p, _ = cramers_v(table)
        key = f"{target} x {col}"
        flow[key] = {"v_cramer": v, "p": p,
                     "fracao_por_grupo": df.groupby(col)[target].mean().round(4).to_dict(),
                     "v_minimo_detectavel": min_detectable_cramers_v(n, *table.shape)}
        pv[key] = p
for key, p_adj in holm(pv).items():
    flow[key]["p_holm"] = p_adj
res["fluxo"] = {"fracao_nao_fechados": float(df["nao_fechado"].mean()),
                "fracao_sem_1a_resposta": float(df["sem_1a_resposta"].mean()),
                "testes": flow,
                "algum_significativo_apos_holm": any(t["p_holm"] < ALPHA for t in flow.values())}

# ---------------------------------------------------------------- combinações canal x prioridade x tipo
# O enunciado pergunta quais COMBINAÇÕES geram os piores tempos, não quais variáveis isoladas.
# Cada célula é testada contra todo o resto (χ² 2x2), com Holm sobre as 80 comparações.
df["celula"] = df["Ticket Channel"] + " | " + df["Ticket Priority"] + " | " + df["Ticket Type"]
df["gap_h"] = closed["gap_h"]  # só os fechados têm gap; o resto fica NaN
cells, pv = {}, {}
for name, sub in df.groupby("celula"):
    if len(sub) < MIN_CELULA:
        continue
    table = pd.DataFrame({"celula": [int(sub["nao_fechado"].sum()), int((~sub["nao_fechado"]).sum())],
                          "resto": [int(df.loc[df["celula"] != name, "nao_fechado"].sum()),
                                    int((~df.loc[df["celula"] != name, "nao_fechado"]).sum())]})
    v, p, _ = cramers_v(table.T)
    cells[name] = {"tickets": int(len(sub)), "fracao_nao_fechados": round(float(sub["nao_fechado"].mean()), 4),
                   "gap_mediano_horas": (round(float(sub["gap_h"].median()), 3)
                                         if sub["gap_h"].notna().any() else None),
                   "v_cramer": v, "p": p}
    pv[name] = p
for name, p_adj in holm(pv).items():
    cells[name]["p_holm"] = p_adj
piores = sorted(cells.items(), key=lambda kv: -kv[1]["fracao_nao_fechados"])
res["combinacoes"] = {
    "definicao": "canal × prioridade × tipo; cada célula testada contra o resto (χ², Holm)",
    "celulas_testadas": len(cells),
    "tickets_minimos_por_celula": MIN_CELULA,
    "celulas_ignoradas_por_tamanho": int(df["celula"].nunique() - len(cells)),
    "faixa_de_nao_fechados": [round(piores[-1][1]["fracao_nao_fechados"], 4),
                              round(piores[0][1]["fracao_nao_fechados"], 4)],
    "piores_5": [{"combinacao": k, **v} for k, v in piores[:5]],
    "algum_significativo_apos_holm": any(c["p_holm"] < ALPHA for c in cells.values()),
    "menor_p_holm": min(c["p_holm"] for c in cells.values()) if cells else None,
}

save_json(OUT / "01_auditoria_ds1.json", res)

# ---------------------------------------------------------------- resumo legível
vt = res["volume_e_tempo"]
print(f"Linhas: {n} ({vt['fracao_do_brief']:.0%} do volume anual do brief)")
print(f"Janela de todas as respostas/resoluções: {vt['janela_de_respostas_horas']:.1f} h "
      f"({vt['respostas_inicio']} -> {vt['respostas_fim']}); carimbo de abertura: não existe")
print(f"Não fechados: {res['fracao_nao_fechados']:.1%}; preenchimento por status: {res['preenchimento_por_status']}")
ct = res["consistencia_temporal"]
print(f"Fechados com resolução ANTES da 1ª resposta: {ct['fracao_resolucao_antes_da_1a_resposta']:.1%}; gap(h) {ct['gap_horas']}")
for k, u in uniform.items():
    print(f"  uniforme? {k}: {u}")
print("Domínios de e-mail:", res["dominios_de_email"])
for k, v in indep.items():
    print(f"  indep {k}: V={v['v_cramer']:.3f} p_holm={v['p_holm']:.3f} (V mín detect.={v['v_minimo_detectavel']:.3f})")
print("Coerência:", res["coerencia_semantica"])
print("Texto:", res["texto_descricao"])
for k, v in res["sinal_do_texto"].items():
    print(f"  sinal {k}: acc={v['acuracia']:.3f} acaso={v['acaso_classe_majoritaria']:.3f} p={v['p_binomial']:.3g}")
for k, v in tests.items():
    print(f"  CSAT {k}: p={v['p']:.3f} p_holm={v['p_holm']:.3f} "
          + (f"rho={v['rho']:.4f}" if "rho" in v else f"eps2={v['epsilon2']:.4f}"))
print("Poder:", res["satisfacao"]["poder_80pct"], "| algum significativo:", res["satisfacao"]["algum_significativo_apos_holm"])
for k, v in flow.items():
    print(f"  fluxo {k}: V={v['v_cramer']:.3f} p_holm={v['p_holm']:.3f} {v['fracao_por_grupo']}")
