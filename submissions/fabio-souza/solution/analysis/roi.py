"""Função de economia mensal da triagem automática (usada por 06_roi.py e espelhada no protótipo)."""

from __future__ import annotations


def monthly_savings(p: dict) -> dict:
    """Minutos/mês = tickets elegíveis x [fila auto x ganho líquido auto + fila assistida x ganho líquido assistida]."""
    v = {k: x["valor"] if isinstance(x, dict) else x for k, x in p.items()}
    eligible = v["tickets_por_mes"] * (1 - v["fracao_reembolso_cancelamento"])
    t = v["min_triagem_manual"]
    # Todo ticket automático pula a triagem manual (ganha t). Os errados custam k x t na fila errada: o agente
    # lê, devolve e alguém re-triagem. Descontar o erro sem somar a triagem poupada contava o erro duas vezes (E10).
    net_auto = t - (1 - v["precisao_auto"]) * v["multiplo_custo_erro"] * t
    net_assist = v["top2_assistida"] * (t - v["min_confirmacao_assistida"]) - (1 - v["top2_assistida"]) * v["min_confirmacao_assistida"]
    minutes_auto = eligible * v["fila_auto"] * net_auto
    minutes_assist = eligible * v["fila_assistida"] * net_assist
    hours = (minutes_auto + minutes_assist) / 60
    return {"tickets_elegiveis_mes": eligible, "tickets_auto_mes": eligible * v["fila_auto"],
            "tickets_assistidos_mes": eligible * v["fila_assistida"],
            "min_liquidos_por_ticket_auto": net_auto, "min_liquidos_por_ticket_assistido": net_assist,
            "horas_mes": hours, "horas_mes_fila_auto": minutes_auto / 60, "horas_mes_fila_assistida": minutes_assist / 60,
            "fte": hours / v["horas_produtivas_por_fte_mes"], "brl_mes": hours * v["custo_hora_brl"],
            "brl_ano": 12 * hours * v["custo_hora_brl"]}
