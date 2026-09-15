"""Quanto a automação da triagem economiza? Função paramétrica com origem declarada em cada insumo.

Não existe dado de tempo confiável (01), então nenhum tempo é "medido": tempos são PREMISSAS explícitas com faixa,
e a operação troca pelo valor real dela. O que é medido: tamanho e precisão das filas (03/04), volume das
alavancas adicionais (02) e curva de aprendizado (05).
Requer: 02, 03, 04, 05. Saída: outputs/06_roi.json
"""

from __future__ import annotations

import json
import pickle

import numpy as np

from common import OUT, load_ds2, save_json
from politica import top2_hit
from roi import monthly_savings
from texto import known_share, normalize

state = pickle.load(open(OUT / "cache" / "modelo_escolhido.pkl", "rb"))
vec, clf, classes, pol = state["vec"], state["clf"], state["classes"], state["policy"]
transfer = json.loads((OUT / "04_transferencia_ds1.json").read_text())
curve = json.loads((OUT / "05_curva_de_aprendizado.json").read_text())["resumo"]
audit2 = json.loads((OUT / "02_auditoria_ds2.json").read_text())

# ------------------------------------------------------------------ filas medidas no teste, já com a trava de domínio
ds2 = load_ds2()
test_texts = ds2["Document"][state["is_test"]].map(normalize)
y_test = np.searchsorted(classes, ds2["Topic_group"][state["is_test"]].to_numpy())
proba = clf.predict_proba(vec.transform(test_texts))
conf, pred = proba.max(1), proba.argmax(1)
vocab = vec.vocabulary_
known = np.array([known_share(d, vocab) for d in test_texts])
in_domain = known >= transfer["trava_de_dominio"]["corte_fracao_de_palavras_conhecidas"]
auto = (conf >= pol["tau_auto"]) & pol["elegiveis"][pred] & in_domain
assist = ~auto & (conf >= pol["tau_assist"]) & in_domain
hit, hit2 = pred == y_test, top2_hit(proba, y_test)

P = {
    "tickets_por_mes": {"valor": 2500.0, "faixa": [1500.0, 4000.0], "origem": "BRIEF",
                        "nota": "~30 mil/ano no brief. O Dataset 1 tem 8.469 linhas numa janela de 27 h e não serve para medir volume."},
    "fracao_reembolso_cancelamento": {"valor": 0.407, "faixa": [0.20, 0.50], "origem": "DATASET 1 (sintético)",
                                      "nota": "Vai sempre para humano (decisão D3 do Fabio). No Dataset 1 os 5 tipos têm ~20% cada; o valor real precisa ser medido."},
    "fila_auto": {"valor": float(auto.mean()), "origem": "MEDIDO", "nota": "Teste do Dataset 2 com corte por ticket de 90% e trava de domínio."},
    "precisao_auto": {"valor": float(hit[auto].mean()), "origem": "MEDIDO", "nota": "Fração da fila automática roteada para a categoria certa."},
    "fila_assistida": {"valor": float(assist.mean()), "origem": "MEDIDO", "nota": "Atendente confirma 1 de 2 sugestões."},
    "top2_assistida": {"valor": float(hit2[assist].mean()), "origem": "MEDIDO", "nota": "Fração da fila assistida em que a categoria certa está nas 2 sugestões."},
    "min_triagem_manual": {"valor": 2.0, "faixa": [1.0, 4.0], "origem": "PREMISSA",
                           "nota": "Ler o ticket, decidir a fila e encaminhar. Medir cronometrando 50 tickets."},
    "multiplo_custo_erro": {"valor": 4.0, "faixa": [2.0, 8.0], "origem": "PREMISSA (D5)",
                            "nota": "Um ticket na fila errada custa N vezes a triagem: o agente errado lê, devolve, e o cliente espera."},
    "min_confirmacao_assistida": {"valor": 0.5, "faixa": [0.25, 1.0], "origem": "PREMISSA", "nota": "Conferir 2 sugestões e clicar."},
    "custo_hora_brl": {"valor": 35.0, "origem": "FABIO (D11)",
                       "nota": "Salário + encargos de atendente júnior. Decisão do candidato: fixa em todos os cenários."},
    "horas_produtivas_por_fte_mes": {"valor": 160.0, "origem": "PREMISSA", "nota": "Horas produtivas de uma pessoa em tempo integral."},
}


base = monthly_savings(P)

# ------------------------------------------------------------------ sensibilidade: cada incerteza no mínimo e no máximo
tornado = []
for key, spec in P.items():
    if "faixa" not in spec or spec["origem"] == "MEDIDO":
        continue
    lo, hi = ({**P, key: {**spec, "valor": b}} for b in spec["faixa"])
    h_lo, h_hi = monthly_savings(lo)["horas_mes"], monthly_savings(hi)["horas_mes"]
    tornado.append({"parametro": key, "origem": spec["origem"], "faixa": spec["faixa"],
                    "horas_mes_no_minimo": h_lo, "horas_mes_no_maximo": h_hi, "amplitude": abs(h_hi - h_lo)})
tornado.sort(key=lambda r: -r["amplitude"])

scenarios = {}
for name, pick in {"pessimista": 0, "otimista": 1}.items():
    p = dict(P)
    for key, spec in P.items():
        if "faixa" in spec and spec["origem"] != "MEDIDO":
            # pessimista = combinação de faixas que MENOS economiza; otimista = a que MAIS economiza
            lo, hi = spec["faixa"]
            h_lo = monthly_savings({**P, key: {**spec, "valor": lo}})["horas_mes"]
            h_hi = monthly_savings({**P, key: {**spec, "valor": hi}})["horas_mes"]
            worst, best = (lo, hi) if h_lo <= h_hi else (hi, lo)
            p[key] = {**spec, "valor": worst if pick == 0 else best}
    scenarios[name] = {"parametros": {k: v["valor"] for k, v in p.items()}, **monthly_savings(p)}

# ------------------------------------------------------------------ quanto rotular: só a fila automática, pela curva
MIN_PER_LABEL = 0.5  # PREMISSA: rotular um ticket histórico que já tem fila registrada leva ~30 s
labeling = []
for row in curve:
    p = {**P, "fila_auto": {"valor": row["cobertura_auto_media"]}, "precisao_auto": {"valor": row["precisao_auto_media"]},
         "fila_assistida": {"valor": 0.0}}
    s = monthly_savings(p)
    cost = row["tickets_rotulados"] * MIN_PER_LABEL / 60 * P["custo_hora_brl"]["valor"]
    labeling.append({"tickets_rotulados": row["tickets_rotulados"], "fila_auto": row["cobertura_auto_media"],
                     "horas_mes_so_fila_auto": s["horas_mes"], "brl_mes_so_fila_auto": s["brl_mes"],
                     "custo_rotulagem_brl": cost, "meses_para_pagar_rotulagem": cost / s["brl_mes"] if s["brl_mes"] > 0 else None})

# ------------------------------------------------------------------ alavancas além da triagem (volume medido, tempo premissa)
purchase_template_share = audit2["grupos_para_divisao"]["maior_grupo"] / audit2["linhas"]
near_dup_share = audit2["quase_duplicados"]["0.9"]["fracao_com_quase_duplicado"]
V = P["tickets_por_mes"]["valor"]
levers = {
    "formulario_para_pedido_de_compra": {
        "volume_medido": purchase_template_share, "origem_volume": "MEDIDO (Dataset 2: 976 tickets com o mesmo template)",
        "premissas": {"min_por_ticket": 8.0, "fracao_eliminada_pelo_formulario": 0.8},
        "horas_mes": V * purchase_template_share * 8.0 * 0.8 / 60,
        "nota": "Automação na origem (formulário + integração), sem IA: o texto é sempre o mesmo pedido de alocação.",
    },
    "resposta_sugerida_por_ticket_gemeo": {
        "volume_medido": near_dup_share, "origem_volume": "MEDIDO (Dataset 2: 12,3% com quase-duplicado, cosseno >= 0,9)",
        "premissas": {"min_poupados_por_ticket": 3.0, "adocao_pelos_atendentes": 0.5},
        "horas_mes": V * near_dup_share * 3.0 * 0.5 / 60,
        "nota": "Mostrar a resposta do ticket gêmeo ao atendente; nunca fechar como duplicado sem humano.",
    },
}

save_json(OUT / "06_roi.json", {
    "formula": ("horas/mês = tickets/mês × (1 − fração reembolso/cancelamento) × "
                "[fila_auto × (t − (1 − precisão) × k × t) + fila_assistida × (top2 × (t − c) − (1 − top2) × c)] / 60; "
                "t = min de triagem manual, k = múltiplo do custo de erro, c = min de confirmação"),
    "ponto_de_empate_da_fila_auto": {"precisao_minima": 1 - 1 / P["multiplo_custo_erro"]["valor"],
                                     "nota": "Abaixo desta precisão, a fila automática custa mais do que economiza (com k = 4, 75%)."},
    "parametros": P, "base": base, "sensibilidade": tornado, "cenarios": scenarios,
    "rotulagem": {"min_por_rotulo_premissa": MIN_PER_LABEL, "por_volume": labeling},
    "alavancas_adicionais": levers,
})

print("Parâmetros medidos:", {k: round(v["valor"], 4) for k, v in P.items() if v["origem"] == "MEDIDO"})
print(f"BASE: {base['horas_mes']:.1f} h/mês ({base['fte']:.2f} FTE) = R$ {base['brl_mes']:,.0f}/mês, R$ {base['brl_ano']:,.0f}/ano "
      f"| auto {base['horas_mes_fila_auto']:.1f} h + assistida {base['horas_mes_fila_assistida']:.1f} h "
      f"| líquido por ticket auto {base['min_liquidos_por_ticket_auto']:.2f} min, assistido {base['min_liquidos_por_ticket_assistido']:.2f} min")
for name, s in scenarios.items():
    print(f"{name}: {s['horas_mes']:.1f} h/mês = R$ {s['brl_mes']:,.0f}/mês")
for r in tornado:
    print(f"  sensibilidade {r['parametro']}: {r['horas_mes_no_minimo']:.1f} .. {r['horas_mes_no_maximo']:.1f} h/mês")
for r in labeling:
    print(f"  rotular {r['tickets_rotulados']:>6}: auto {r['fila_auto']:.0%} -> {r['horas_mes_so_fila_auto']:.1f} h/mês, "
          f"custo R$ {r['custo_rotulagem_brl']:,.0f}, paga em {r['meses_para_pagar_rotulagem']:.1f} meses")
for k, lv in levers.items():
    print(f"  alavanca {k}: {lv['horas_mes']:.1f} h/mês")
