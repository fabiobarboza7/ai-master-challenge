"""Classificador de triagem (Dataset 2): comparação de modelos e filas AUTO / ASSISTIDA / HUMANA.

Segue as regras C2-C3 e o Adendo 1 de process-log/hipoteses-pre-registradas.md:
- divisão 70/15/15 por grupos de quase-duplicados (sem vazamento treino -> teste);
- modelo e cortes escolhidos só na validação.

Duas políticas de corte são calculadas e reportadas:
- "media" (pré-registrada): menor corte em que a precisão MÉDIA da fila é >= 90%;
- "marginal" (correção, erro E7): menor corte em que a taxa de acerto LOCAL, a de tickets com aquela
  confiança, é >= 90%. A regra média aceita tickets que acertam ~45%, escondidos na média.

Requer: 02_auditoria_ds2.py. Saídas: outputs/03_classificador.json e outputs/cache/modelo_escolhido.pkl
"""

from __future__ import annotations

import pickle
import time

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold, train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.neighbors import NearestNeighbors
from sklearn.svm import LinearSVC

from common import OUT, SEED, load_ds2, save_json
from politica import GRID, MIN_LANE, ece, local_accuracy, tau_marginal, tau_media, top2_hit, wilson

TARGET = 0.90
SENSITIVITY_TARGETS = (0.85, 0.95)
CLASS_MIN_PRECISION = 0.85
CLASS_MIN_SUPPORT = 20

t0 = time.time()
df = load_ds2()
groups = np.load(OUT / "cache" / "ds2_grupos.npy")
texts = df["Document"].to_numpy()
classes = np.array(sorted(df["Topic_group"].unique()))
y = np.searchsorted(classes, df["Topic_group"].to_numpy())
n, K = len(y), len(classes)

# ------------------------------------------------------------------ divisão por grupos (C2)
fold = np.empty(n, dtype=int)
for f, (_, part) in enumerate(StratifiedGroupKFold(20, shuffle=True, random_state=SEED).split(texts, y, groups)):
    fold[part] = f
is_train, is_val, is_test = fold < 14, (fold >= 14) & (fold < 17), fold >= 17
assert not set(groups[is_train]) & set(groups[is_test]), "grupo de quase-duplicados vazou para o teste"
split_info = {k: int(m.sum()) for k, m in [("treino", is_train), ("validacao", is_val), ("teste", is_test)]}
print(f"Divisão por grupos: {split_info}")


# ------------------------------------------------------------------ políticas de corte
def fit_policy(proba, y_true, kind: str, target=TARGET) -> dict:
    """Escolhe tau_auto, categorias elegíveis (C3) e tau_assist usando só os dados passados (validação)."""
    conf, pred = proba.max(1), proba.argmax(1)
    hit, hit2 = pred == y_true, top2_hit(proba, y_true)
    eligible = np.ones(K, dtype=bool)
    for _ in range(K):
        allowed = eligible[pred]
        tau_auto = tau_media(conf, hit, target, allowed) if kind == "media" else tau_marginal(conf[allowed], hit[allowed], target)
        if tau_auto is None:
            return {"tipo": kind, "tau_auto": None}
        auto = (conf >= tau_auto) & eligible[pred]
        changed = False
        for c in range(K):
            m = auto & (pred == c)
            if eligible[c] and (m.sum() < CLASS_MIN_SUPPORT or hit[m].mean() < CLASS_MIN_PRECISION):
                eligible[c], changed = False, True
        if not changed:
            break
    not_auto = ~((conf >= tau_auto) & eligible[pred])
    if kind == "media":
        tau_assist = None
        for tau in GRID:
            band = not_auto & (conf >= tau)
            if band.sum() >= MIN_LANE and hit2[band].mean() >= target:
                tau_assist = float(tau)
                break
    else:
        tau_assist = tau_marginal(conf[not_auto], hit2[not_auto], target)
    return {"tipo": kind, "alvo": target, "tau_auto": tau_auto, "tau_assist": tau_assist, "elegiveis": eligible}


def apply_policy(proba, y_true, pol) -> dict:
    conf, pred = proba.max(1), proba.argmax(1)
    hit, hit2 = pred == y_true, top2_hit(proba, y_true)
    auto = (conf >= pol["tau_auto"]) & pol["elegiveis"][pred]
    assist = ~auto & (conf >= (pol["tau_assist"] if pol["tau_assist"] is not None else 1.1))
    human = ~auto & ~assist
    low = auto & (conf < 0.5)
    k = int(hit[auto].sum())
    return {
        "tau_auto": pol["tau_auto"], "tau_assist": pol["tau_assist"],
        "fila_auto": {"fracao": float(auto.mean()), "tickets": int(auto.sum()), "precisao": k / max(auto.sum(), 1),
                      "ic95": wilson(k, int(auto.sum())),
                      "tickets_com_confianca_abaixo_de_0_5": int(low.sum()),
                      "acerto_desses_tickets": float(hit[low].mean()) if low.any() else None},
        "fila_assistida": {"fracao": float(assist.mean()), "top2_contem_a_certa": float(hit2[assist].mean()) if assist.any() else None},
        "fila_humana": {"fracao": float(human.mean()), "acerto_do_modelo_nessa_faixa": float(hit[human].mean()) if human.any() else None},
        "por_categoria": {classes[c]: {"elegivel": bool(pol["elegiveis"][c]), "tickets_auto": int((auto & (pred == c)).sum()),
                                       "precisao_auto": float(hit[auto & (pred == c)].mean()) if (auto & (pred == c)).any() else None}
                          for c in range(K)},
    }


def summary(proba, y_true) -> dict:
    pred, conf = proba.argmax(1), proba.max(1)
    out = {"acuracia": float(accuracy_score(y_true, pred)), "f1_macro": float(f1_score(y_true, pred, average="macro")),
           "ece": ece(proba, y_true)}
    iso = local_accuracy(conf, pred == y_true)
    for kind in ("media", "marginal"):
        pol = fit_policy(proba, y_true, kind)
        ok = pol["tau_auto"] is not None
        out[f"cobertura_auto_regra_{kind}"] = apply_policy(proba, y_true, pol)["fila_auto"]["fracao"] if ok else 0.0
        # taxa de acerto de um ticket com confiança exatamente no corte: o pior caso que entra na fila automática
        out[f"acerto_local_no_corte_regra_{kind}"] = float(iso.predict([pol["tau_auto"]])[0]) if ok else None
    return out


# ------------------------------------------------------------------ candidatos (escolha só na validação)
def tfidf(max_features):
    return TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=max_features, dtype=np.float64)


candidates, fitted = {}, {}
prior = np.bincount(y[is_train], minlength=K) / is_train.sum()
candidates["classe_majoritaria"] = (np.tile(prior, (is_val.sum(), 1)), 0)

vec_1nn = TfidfVectorizer(sublinear_tf=True, min_df=2).fit(texts[is_train])
nn = NearestNeighbors(n_neighbors=1, metric="cosine", algorithm="brute", n_jobs=-1).fit(vec_1nn.transform(texts[is_train]))
dist, idx = nn.kneighbors(vec_1nn.transform(texts[is_val]))
proba_1nn = np.full((is_val.sum(), K), 1e-9)
proba_1nn[np.arange(is_val.sum()), y[is_train][idx[:, 0]]] = 1 - dist[:, 0]  # confiança = similaridade
candidates["vizinho_mais_proximo"] = (proba_1nn, len(vec_1nn.vocabulary_))

for mf in (5_000, 20_000, 50_000):
    vec = tfidf(mf).fit(texts[is_train])
    Xtr, Xva = vec.transform(texts[is_train]), vec.transform(texts[is_val])
    for C in (2.0, 8.0):
        clf = LogisticRegression(C=C, max_iter=3000).fit(Xtr, y[is_train])
        name = f"tfidf{mf // 1000}k_regressao_logistica_C{C:g}"
        candidates[name] = (clf.predict_proba(Xva), len(vec.vocabulary_))
        fitted[name] = (vec, clf)
    print(f"  vocabulário {mf}: {time.time() - t0:.0f}s")
    if mf == 50_000:
        svm = CalibratedClassifierCV(LinearSVC(C=0.5), method="sigmoid", cv=3).fit(Xtr, y[is_train])
        candidates["tfidf50k_svm_linear_calibrado"] = (svm.predict_proba(Xva), len(vec.vocabulary_))
        nb = ComplementNB(alpha=0.3).fit(Xtr, y[is_train])
        candidates["tfidf50k_naive_bayes_complementar"] = (nb.predict_proba(Xva), len(vec.vocabulary_))

comparison = {}
for name, (proba, feats) in candidates.items():
    comparison[name] = {**summary(proba, y[is_val]), "features": feats}
    print(f"  VAL {name}: " + ", ".join(f"{k}={v:.3f}" for k, v in comparison[name].items()
                                        if k != "features" and v is not None))


def pick(metric: str) -> dict:
    """Maior cobertura; empate (< 1 p.p. do melhor de TODOS os candidatos) -> modelo exportável com menos features."""
    best_all = max(comparison, key=lambda k: comparison[k][metric])
    tied = [k for k in fitted if comparison[best_all][metric] - comparison[k][metric] < 0.01]
    chosen_k = (min(tied, key=lambda k: (comparison[k]["features"], -comparison[k][metric])) if tied
                else max(fitted, key=lambda k: comparison[k][metric]))
    return {"melhor_de_todos": best_all, "escolhido_exportavel": chosen_k, "empata_com_o_melhor": bool(tied)}


selection = {"regra_media_pre_registrada": pick("cobertura_auto_regra_media"),
             "regra_marginal_corrigida": pick("cobertura_auto_regra_marginal")}
if not selection["regra_marginal_corrigida"]["empata_com_o_melhor"]:
    raise SystemExit("O melhor modelo pela regra marginal não é exportável; revisar antes de seguir.")
chosen = selection["regra_marginal_corrigida"]["escolhido_exportavel"]
print(f"Seleção: {selection}")
vec, clf = fitted[chosen]
proba_val = clf.predict_proba(vec.transform(texts[is_val]))
proba_test = clf.predict_proba(vec.transform(texts[is_test]))

policies = {kind: fit_policy(proba_val, y[is_val], kind) for kind in ("media", "marginal")}
results = {kind: {"validacao": apply_policy(proba_val, y[is_val], pol), "teste": apply_policy(proba_test, y[is_test], pol)}
           for kind, pol in policies.items()}

sens = {}
for target in SENSITIVITY_TARGETS:
    pol = fit_policy(proba_val, y[is_val], "marginal", target)
    sens[str(target)] = apply_policy(proba_test, y[is_test], pol) if pol["tau_auto"] is not None else None

pred_test = proba_test.argmax(1)
cm = confusion_matrix(y[is_test], pred_test, labels=range(K))
confusions = sorted(({"real": classes[i], "previsto": classes[j], "tickets": int(cm[i, j]),
                      "fracao_da_classe_real": float(cm[i, j] / cm[i].sum())}
                     for i in range(K) for j in range(K) if i != j and cm[i, j]), key=lambda p: -p["tickets"])

# ------------------------------------------------------------------ quanto a divisão aleatória superestimaria?
idx_tr, idx_te = train_test_split(np.arange(n), test_size=0.15, stratify=y, random_state=SEED)
vec_r = tfidf(vec.max_features).fit(texts[idx_tr])
clf_r = LogisticRegression(C=clf.C, max_iter=3000).fit(vec_r.transform(texts[idx_tr]), y[idx_tr])
leak = {"divisao_aleatoria": summary(clf_r.predict_proba(vec_r.transform(texts[idx_te])), y[idx_te]),
        "divisao_por_grupos": summary(proba_test, y[is_test])}

# ------------------------------------------------------------------ curvas para os gráficos (modelo escolhido)
conf_v, hit_v = proba_val.max(1), proba_val.argmax(1) == y[is_val]
iso = local_accuracy(conf_v, hit_v)
curve = {"grid": GRID.tolist(), "acerto_local_validacao": iso.predict(GRID).tolist(),
         "precisao_media_da_fila_validacao": [float(hit_v[conf_v >= t].mean()) if (conf_v >= t).sum() >= MIN_LANE else None for t in GRID],
         "cobertura_validacao": [float((conf_v >= t).mean()) for t in GRID]}

save_json(OUT / "03_classificador.json", {
    "divisao": split_info, "comparacao_validacao": comparison,
    "selecao": selection, "escolhido": chosen,
    "politicas": {k: {"tau_auto": p["tau_auto"], "tau_assist": p["tau_assist"],
                      "elegiveis": classes[p["elegiveis"]].tolist()} for k, p in policies.items()},
    "resultados": results, "sensibilidade_regra_marginal_teste": sens,
    "confusoes_mais_comuns_teste": confusions[:10],
    "matriz_confusao_teste": {"classes": classes.tolist(), "valores": cm.tolist()},
    "vazamento": leak, "curvas": curve,
})
with open(OUT / "cache" / "modelo_escolhido.pkl", "wb") as fh:
    pickle.dump({"vec": vec, "clf": clf, "classes": classes, "policy": policies["marginal"],
                 "is_test": is_test, "is_val": is_val}, fh)

for kind in ("media", "marginal"):
    for part in ("validacao", "teste"):
        r = results[kind][part]
        print(f"{kind:8s} {part:9s} tau_auto={r['tau_auto']} tau_assist={r['tau_assist']} | "
              f"AUTO {r['fila_auto']['fracao']:.1%} prec {r['fila_auto']['precisao']:.1%} "
              f"(conf<0,5: {r['fila_auto']['tickets_com_confianca_abaixo_de_0_5']} tickets, acerto {r['fila_auto']['acerto_desses_tickets']}) | "
              f"ASSIST {r['fila_assistida']['fracao']:.1%} top2 {r['fila_assistida']['top2_contem_a_certa']} | "
              f"HUMANA {r['fila_humana']['fracao']:.1%}")
print("Elegíveis:", {k: classes[p["elegiveis"]].tolist() for k, p in policies.items()})
print("Sensibilidade (teste):", {k: (v["fila_auto"]["fracao"], v["fila_auto"]["precisao"]) if v else None for k, v in sens.items()})
print("Vazamento:", {k: (round(v["acuracia"], 4), round(v["cobertura_auto_regra_marginal"], 4)) for k, v in leak.items()})
print("Confusões:", [(c["real"], c["previsto"], c["tickets"]) for c in confusions[:5]])
print(f"Total {time.time() - t0:.0f}s")
