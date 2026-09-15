"""Quantos tickets rotulados a empresa precisa para chegar a uma fila automática útil?

Treina o modelo escolhido (mesmos hiperparâmetros) com amostras crescentes do treino. A política marginal é
ajustada na validação e a cobertura/precisão é medida no teste, igual ao 03.
Requer: 03_classificador.py. Saída: outputs/05_curva_de_aprendizado.json
"""

from __future__ import annotations

import pickle
import time

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from common import OUT, SEED, load_ds2, save_json
from politica import tau_marginal
from texto import normalize

state = pickle.load(open(OUT / "cache" / "modelo_escolhido.pkl", "rb"))
vec0, clf0, classes = state["vec"], state["clf"], state["classes"]
is_val, is_test = state["is_val"], state["is_test"]

df = load_ds2()
texts = df["Document"].map(normalize).to_numpy()
y = np.searchsorted(classes, df["Topic_group"].to_numpy())
train_idx = np.nonzero(~is_val & ~is_test)[0]
rng = np.random.default_rng(SEED)

sizes = [500, 1_000, 2_000, 5_000, 10_000, 20_000, len(train_idx)]
rows = []
t0 = time.time()
for size in sizes:
    for rep in range(3 if size < len(train_idx) else 1):
        sub = rng.choice(train_idx, size=size, replace=False) if size < len(train_idx) else train_idx
        # fit + transform (e não fit_transform), igual ao 03: as matrizes diferem em ~1e-16 e o otimizador
        # para em pontos ligeiramente diferentes, o que mudaria alguns tickets de fronteira.
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=vec0.max_features).fit(texts[sub])
        clf = LogisticRegression(C=clf0.C, max_iter=3000).fit(vec.transform(texts[sub]), y[sub])
        pv, pt = clf.predict_proba(vec.transform(texts[is_val])), clf.predict_proba(vec.transform(texts[is_test]))
        tau = tau_marginal(pv.max(1), pv.argmax(1) == y[is_val], 0.90)
        auto = pt.max(1) >= tau if tau is not None else np.zeros(len(pt), bool)
        rows.append({"tickets_rotulados": size, "repeticao": rep, "tau_auto": tau,
                     "acuracia_teste": float((pt.argmax(1) == y[is_test]).mean()),
                     "cobertura_auto_teste": float(auto.mean()),
                     "precisao_auto_teste": float((pt.argmax(1)[auto] == y[is_test][auto]).mean()) if auto.any() else None})
        print(f"  {size:>6} rep{rep}: {rows[-1]} ({time.time() - t0:.0f}s)")

summary = []
for size in sizes:
    r = [x for x in rows if x["tickets_rotulados"] == size]
    summary.append({"tickets_rotulados": size,
                    "cobertura_auto_media": float(np.mean([x["cobertura_auto_teste"] for x in r])),
                    "cobertura_auto_min": float(np.min([x["cobertura_auto_teste"] for x in r])),
                    "cobertura_auto_max": float(np.max([x["cobertura_auto_teste"] for x in r])),
                    "precisao_auto_media": float(np.mean([x["precisao_auto_teste"] for x in r if x["precisao_auto_teste"] is not None])),
                    "acuracia_media": float(np.mean([x["acuracia_teste"] for x in r]))})
save_json(OUT / "05_curva_de_aprendizado.json", {"execucoes": rows, "resumo": summary})
for s in summary:
    print(f"{s['tickets_rotulados']:>6} rotulados -> AUTO {s['cobertura_auto_media']:.1%} "
          f"[{s['cobertura_auto_min']:.1%}-{s['cobertura_auto_max']:.1%}] precisão {s['precisao_auto_media']:.1%} "
          f"acurácia {s['acuracia_media']:.1%}")
