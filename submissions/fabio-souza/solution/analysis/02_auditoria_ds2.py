"""Auditoria do Dataset 2 (texto real de tickets de TI): classes, tamanho e quase-duplicados (H7).

Saídas: outputs/02_auditoria_ds2.json e outputs/cache/ds2_grupos.npy (grupos de quase-duplicados, usado pelo 03)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from common import OUT, load_ds2, save_json
from dedup import groups_from_neighbors, nearest_neighbors

GROUP_THRESHOLD = 0.8

df = load_ds2()
n = len(df)
tokens = df["Document"].str.split().str.len()

res = {
    "linhas": n,
    "classes": df["Topic_group"].value_counts().to_dict(),
    "fracao_por_classe": df["Topic_group"].value_counts(normalize=True).round(4).to_dict(),
    "tokens_por_ticket": {q: float(tokens.quantile(v)) for q, v in
                          [("min", 0), ("p25", .25), ("mediana", .5), ("p75", .75), ("p95", .95), ("max", 1)]},
    "duplicatas_exatas": int(df.duplicated("Document").sum()),
    "texto_pre_processado": {
        "com_maiusculas": float(df["Document"].str.contains(r"[A-Z]").mean()),
        "com_digitos": float(df["Document"].str.contains(r"\d").mean()),
    },
}

sims, idx = nearest_neighbors(df["Document"], k=6)
best = sims[:, 1]  # vizinho mais próximo que não é o próprio texto
labels = df["Topic_group"].to_numpy()
neighbor_label = labels[idx[:, 1]]
near = {}
for t in (0.95, 0.9, 0.8):
    mask = best >= t
    near[str(t)] = {
        "fracao_com_quase_duplicado": float(mask.mean()),
        "tickets": int(mask.sum()),
        "rotulo_igual_ao_do_vizinho": float((labels[mask] == neighbor_label[mask]).mean()) if mask.any() else None,
    }
res["quase_duplicados"] = near
res["rotulo_igual_ao_vizinho_geral"] = float((labels == neighbor_label).mean())

groups = groups_from_neighbors(sims, idx, GROUP_THRESHOLD)
sizes = pd.Series(groups).value_counts()
res["grupos_para_divisao"] = {
    "limiar": GROUP_THRESHOLD,
    "grupos": int(len(sizes)),
    "tickets_em_grupos_com_mais_de_um": int(sizes[sizes > 1].sum()),
    "maior_grupo": int(sizes.max()),
}
(OUT / "cache").mkdir(parents=True, exist_ok=True)
np.save(OUT / "cache" / "ds2_grupos.npy", groups)
save_json(OUT / "02_auditoria_ds2.json", res)

print(f"Linhas {n}; classes {res['fracao_por_classe']}")
print(f"Tokens por ticket {res['tokens_por_ticket']}; duplicatas exatas {res['duplicatas_exatas']}")
for t, v in near.items():
    print(f"  cos >= {t}: {v['fracao_com_quase_duplicado']:.1%} dos tickets ({v['tickets']}), "
          f"mesmo rótulo do vizinho {v['rotulo_igual_ao_do_vizinho']:.1%}")
print(f"Mesmo rótulo do vizinho mais próximo (geral): {res['rotulo_igual_ao_vizinho_geral']:.1%}")
print("Grupos:", res["grupos_para_divisao"])
